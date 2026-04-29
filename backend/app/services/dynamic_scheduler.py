"""
Dynamic Scheduler Service

This module provides the DynamicScheduler class for managing individual user notification
jobs based on their preferences. It integrates with APScheduler to create, cancel, and
reschedule notification jobs dynamically.

Requirements: 5.1, 5.2, 5.4, 5.5
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.core.timezone_converter import TimezoneConverter
from app.repositories.user_notification_preferences import UserNotificationPreferences
from app.services.base import BaseService

logger = get_logger(__name__)


from app.services._ds_send_mixin import DsSendMixin
from app.services._ds_stats_mixin import DsStatsMixin


class DynamicScheduler(BaseService, DsSendMixin, DsStatsMixin):
    """
    Dynamic scheduler for managing individual user notification jobs.

    This service handles:
    - Creating notification jobs based on user preferences
    - Canceling notification jobs when users disable notifications
    - Rescheduling jobs when user preferences are updated
    - Managing job lifecycle and cleanup
    - Integrating with APScheduler for reliable job execution

    Requirements: 5.1, 5.2, 5.4, 5.5
    """

    def __init__(self, scheduler: AsyncIOScheduler):
        """
        Initialize the DynamicScheduler.

        Args:
            scheduler: APScheduler instance for job management
        """
        super().__init__()
        self.scheduler = scheduler
        self.logger = get_logger(f"{__name__}.DynamicScheduler")

    async def schedule_user_notification(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ) -> None:
        """
        Schedule a notification job for a user based on their preferences.

        Creates a new job or updates an existing job for the user. The job will be
        scheduled to run at the user's preferred time in their timezone.

        Args:
            user_id: UUID of the user
            preferences: User's notification preferences

        Raises:
            ServiceError: If scheduling fails

        Requirements: 5.1, 5.2
        """
        try:
            self.logger.info(
                "Scheduling user notification",
                user_id=str(user_id),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
            )

            # Skip scheduling if notifications are disabled
            if preferences.frequency == "disabled" or not preferences.dm_enabled:
                self.logger.info(
                    "Notifications disabled for user, skipping scheduling",
                    user_id=str(user_id),
                    frequency=preferences.frequency,
                    dm_enabled=preferences.dm_enabled,
                )
                return

            # Calculate next notification time
            next_notification_time = self.get_next_notification_time(preferences)
            if not next_notification_time:
                self.logger.warning(
                    "Could not calculate next notification time",
                    user_id=str(user_id),
                    preferences=preferences.frequency,
                )
                return

            # Create job ID for the user
            job_id = f"user_notification_{user_id}"

            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.logger.info(
                    "Removed existing job for user", user_id=str(user_id), job_id=job_id
                )

            # Create date trigger for the next notification time
            trigger = DateTrigger(run_date=next_notification_time)

            # Add the job to scheduler
            self.scheduler.add_job(
                func=self._send_user_notification,
                trigger=trigger,
                id=job_id,
                name=f"User Notification - {user_id}",
                args=[user_id, preferences],
                replace_existing=True,
            )

            self.logger.info(
                "Successfully scheduled user notification",
                user_id=str(user_id),
                job_id=job_id,
                next_run_time=next_notification_time.isoformat(),
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to schedule user notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "frequency": preferences.frequency,
                    "notification_time": str(preferences.notification_time),
                    "timezone": preferences.timezone,
                },
            )

    async def cancel_user_notification(self, user_id: UUID) -> None:
        """
        Cancel all notification jobs for a user.

        Removes any existing notification jobs for the specified user from the scheduler.

        Args:
            user_id: UUID of the user

        Raises:
            ServiceError: If cancellation fails

        Requirements: 5.5
        """
        try:
            self.logger.info("Canceling user notification", user_id=str(user_id))

            job_id = f"user_notification_{user_id}"

            # Check if job exists
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.remove_job(job_id)
                self.logger.info(
                    "Successfully canceled user notification",
                    user_id=str(user_id),
                    job_id=job_id,
                )
            else:
                self.logger.info(
                    "No notification job found for user",
                    user_id=str(user_id),
                    job_id=job_id,
                )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to cancel user notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    async def reschedule_user_notification(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ) -> None:
        """
        Reschedule a user's notification job with updated preferences.

        This method cancels the existing job and creates a new one with the updated
        preferences. It's equivalent to calling cancel_user_notification followed
        by schedule_user_notification.

        Args:
            user_id: UUID of the user
            preferences: Updated user notification preferences

        Raises:
            ServiceError: If rescheduling fails

        Requirements: 5.2
        """
        try:
            self.logger.info(
                "Rescheduling user notification",
                user_id=str(user_id),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
            )

            # Cancel existing job
            await self.cancel_user_notification(user_id)

            # Schedule new job with updated preferences
            await self.schedule_user_notification(user_id, preferences)

            self.logger.info(
                "Successfully rescheduled user notification",
                user_id=str(user_id),
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to reschedule user notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "frequency": preferences.frequency,
                    "notification_time": str(preferences.notification_time),
                    "timezone": preferences.timezone,
                },
            )

    def get_next_notification_time(
        self, preferences: UserNotificationPreferences
    ) -> Optional[datetime]:
        """
        Calculate the next notification time based on user preferences.

        Uses the TimezoneConverter utility to handle timezone conversion and
        calculate the appropriate next notification time based on frequency.

        Args:
            preferences: User notification preferences

        Returns:
            datetime: Next notification time in UTC, or None if disabled

        Requirements: 5.3
        """
        try:
            # Convert time object to string format for TimezoneConverter
            notification_time_str = preferences.notification_time.strftime("%H:%M")

            # Use TimezoneConverter to calculate next notification time
            next_time = TimezoneConverter.get_next_notification_time(
                frequency=preferences.frequency,
                notification_time=notification_time_str,
                timezone=preferences.timezone,
                notification_day_of_week=preferences.notification_day_of_week,
                notification_day_of_month=preferences.notification_day_of_month,
            )

            if next_time:
                self.logger.debug(
                    "Calculated next notification time",
                    frequency=preferences.frequency,
                    notification_time=notification_time_str,
                    notification_day_of_week=preferences.notification_day_of_week,
                    notification_day_of_month=preferences.notification_day_of_month,
                    timezone=preferences.timezone,
                    next_time=next_time.isoformat(),
                )

            return next_time

        except Exception as e:
            self.logger.error(
                "Failed to calculate next notification time",
                error=str(e),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
            )
            return None
