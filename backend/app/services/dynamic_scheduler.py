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


class DynamicScheduler(BaseService):
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

    async def _send_user_notification(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ) -> None:
        """
        Internal method to send notification to a user.

        This method is called by the scheduler when a notification job is triggered.
        It handles the actual notification sending and reschedules the next notification
        if the user still has notifications enabled.

        Uses LockManager to prevent duplicate notifications when multiple instances
        (e.g., local development + Render deployment) are running simultaneously.

        Now includes quiet hours checking to respect user's do-not-disturb settings.

        Args:
            user_id: UUID of the user
            preferences: User notification preferences at the time of scheduling

        Requirements: 5.1, 5.2, 10.1, 10.2, 11.1, 11.2
        """
        try:
            self.logger.info("Sending scheduled notification to user", user_id=str(user_id))

            # Import here to avoid circular imports
            from app.bot.client import bot
            from app.services.dm_notification_service import DMNotificationService
            from app.services.lock_manager import LockManager
            from app.services.quiet_hours_service import QuietHoursService
            from app.services.supabase_service import SupabaseService

            # Initialize services
            supabase = SupabaseService()
            lock_manager = LockManager(supabase.client)
            quiet_hours_service = QuietHoursService(supabase)

            # Check quiet hours before proceeding
            current_time = datetime.utcnow()
            is_in_quiet_hours, quiet_hours_settings = await quiet_hours_service.is_in_quiet_hours(
                user_id, current_time
            )

            if is_in_quiet_hours:
                self.logger.info(
                    "User is in quiet hours, queuing notification for later",
                    user_id=str(user_id),
                    quiet_hours_start=quiet_hours_settings.start_time.strftime("%H:%M")
                    if quiet_hours_settings
                    else None,
                    quiet_hours_end=quiet_hours_settings.end_time.strftime("%H:%M")
                    if quiet_hours_settings
                    else None,
                    timezone=quiet_hours_settings.timezone if quiet_hours_settings else None,
                )

                # Get next available notification time after quiet hours
                next_available_time = await quiet_hours_service.get_next_notification_time(
                    user_id, current_time
                )

                if next_available_time:
                    # Reschedule the notification for after quiet hours
                    job_id = f"user_notification_{user_id}"

                    # Remove current job
                    if self.scheduler.get_job(job_id):
                        self.scheduler.remove_job(job_id)

                    # Create new job for after quiet hours
                    from apscheduler.triggers.date import DateTrigger

                    trigger = DateTrigger(run_date=next_available_time)

                    self.scheduler.add_job(
                        func=self._send_user_notification,
                        trigger=trigger,
                        id=job_id,
                        name=f"User Notification - {user_id} (After Quiet Hours)",
                        args=[user_id, preferences],
                        replace_existing=True,
                    )

                    self.logger.info(
                        "Rescheduled notification after quiet hours",
                        user_id=str(user_id),
                        next_run_time=next_available_time.isoformat(),
                    )
                else:
                    self.logger.warning(
                        "Could not determine next available time after quiet hours",
                        user_id=str(user_id),
                    )

                return

            # Proceed with normal notification flow if not in quiet hours
            self.logger.info(
                "User not in quiet hours, proceeding with notification", user_id=str(user_id)
            )

            # Attempt to acquire notification lock to prevent duplicates
            scheduled_time = datetime.utcnow()
            notification_type = f"{preferences.frequency}_digest"

            lock = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
                ttl_minutes=30,  # Lock expires in 30 minutes
            )

            if not lock:
                self.logger.info(
                    "Notification already being processed by another instance, skipping",
                    user_id=str(user_id),
                    notification_type=notification_type,
                )
                return

            self.logger.info(
                "Successfully acquired notification lock",
                user_id=str(user_id),
                lock_id=str(lock.id),
                instance_id=lock_manager.instance_id,
            )

            try:
                # Check if bot is ready
                if not bot.is_ready():
                    self.logger.warning(
                        "Bot is not ready, skipping notification",
                        user_id=str(user_id),
                    )
                    # Release lock as failed
                    await lock_manager.release_lock(lock.id, "failed")
                    return

                # Get user's discord_id from database
                try:
                    user = await supabase.get_user_by_id(user_id)
                    if not user or not user.get("discord_id"):
                        self.logger.error(
                            "Could not find discord_id for user",
                            user_id=str(user_id),
                        )
                        await lock_manager.release_lock(lock.id, "failed")
                        return

                    discord_id = user["discord_id"]
                except Exception as e:
                    self.logger.error(
                        "Failed to get user discord_id",
                        user_id=str(user_id),
                        error=str(e),
                    )
                    await lock_manager.release_lock(lock.id, "failed")
                    return

                # Create DM notification service and send notification
                dm_service = DMNotificationService(bot)
                success = await dm_service.send_personalized_digest(discord_id)

                if success:
                    self.logger.info(
                        "Successfully sent notification to user",
                        user_id=str(user_id),
                    )
                    # Release lock as completed
                    await lock_manager.release_lock(lock.id, "completed")
                else:
                    self.logger.warning(
                        "Failed to send notification to user",
                        user_id=str(user_id),
                    )
                    # Release lock as failed
                    await lock_manager.release_lock(lock.id, "failed")

                # Reschedule next notification if user still has notifications enabled
                # We need to get fresh preferences in case they changed
                try:
                    from app.repositories.user_notification_preferences import (
                        UserNotificationPreferencesRepository,
                    )

                    # Get fresh preferences
                    prefs_repo = UserNotificationPreferencesRepository(supabase.client)
                    current_preferences = await prefs_repo.get_by_user_id(user_id)

                    if current_preferences and current_preferences.frequency != "disabled":
                        # Schedule next notification
                        await self.schedule_user_notification(user_id, current_preferences)
                        self.logger.info(
                            "Scheduled next notification for user",
                            user_id=str(user_id),
                            frequency=current_preferences.frequency,
                        )
                    else:
                        self.logger.info(
                            "User has disabled notifications, not rescheduling",
                            user_id=str(user_id),
                        )

                except Exception as reschedule_error:
                    self.logger.error(
                        "Failed to reschedule next notification",
                        error=str(reschedule_error),
                        user_id=str(user_id),
                    )

            except Exception as send_error:
                # Release lock as failed if sending fails
                await lock_manager.release_lock(lock.id, "failed")
                raise send_error

        except Exception as e:
            self.logger.error(
                "Failed to send scheduled notification",
                error=str(e),
                user_id=str(user_id),
                exc_info=True,
            )

    async def get_user_job_info(self, user_id: UUID) -> Optional[dict]:
        """
        Get information about a user's scheduled notification job.

        Args:
            user_id: UUID of the user

        Returns:
            dict: Job information including next run time, or None if no job exists
        """
        try:
            job_id = f"user_notification_{user_id}"
            job = self.scheduler.get_job(job_id)

            if job:
                return {
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            return None

        except Exception as e:
            self.logger.error(
                "Failed to get user job info",
                error=str(e),
                user_id=str(user_id),
            )
            return None

    async def cleanup_expired_jobs(self) -> int:
        """
        Clean up expired or orphaned notification jobs.

        This method removes jobs that are no longer needed, such as jobs for
        users who have disabled notifications or deleted their accounts.

        Returns:
            int: Number of jobs cleaned up
        """
        try:
            self.logger.info("Starting cleanup of expired notification jobs")

            cleaned_count = 0
            jobs = self.scheduler.get_jobs()

            for job in jobs:
                # Only process user notification jobs
                if not job.id.startswith("user_notification_"):
                    continue

                try:
                    # Extract user_id from job_id
                    user_id_str = job.id.replace("user_notification_", "")
                    user_id = UUID(user_id_str)

                    # Check if user still has notifications enabled
                    from app.repositories.user_notification_preferences import (
                        UserNotificationPreferencesRepository,
                    )
                    from app.services.supabase_service import SupabaseService

                    supabase = SupabaseService()
                    prefs_repo = UserNotificationPreferencesRepository(supabase.client)
                    preferences = await prefs_repo.get_by_user_id(user_id)

                    # Remove job if user has no preferences or notifications disabled
                    if not preferences or preferences.frequency == "disabled":
                        self.scheduler.remove_job(job.id)
                        cleaned_count += 1
                        self.logger.info(
                            "Cleaned up expired job",
                            job_id=job.id,
                            user_id=str(user_id),
                        )

                except Exception as job_error:
                    self.logger.warning(
                        "Failed to process job during cleanup",
                        job_id=job.id,
                        error=str(job_error),
                    )

            self.logger.info(
                "Completed cleanup of expired notification jobs",
                cleaned_count=cleaned_count,
            )

            return cleaned_count

        except Exception as e:
            self.logger.error(
                "Failed to cleanup expired jobs",
                error=str(e),
                exc_info=True,
            )
            return 0

    async def get_scheduler_stats(self) -> dict:
        """
        Get statistics about the dynamic scheduler.

        Returns:
            dict: Scheduler statistics including job counts and status
        """
        try:
            jobs = self.scheduler.get_jobs()
            user_notification_jobs = [
                job for job in jobs if job.id.startswith("user_notification_")
            ]

            return {
                "total_jobs": len(jobs),
                "user_notification_jobs": len(user_notification_jobs),
                "scheduler_running": self.scheduler.running,
                "scheduler_state": str(self.scheduler.state),
            }

        except Exception as e:
            self.logger.error(
                "Failed to get scheduler stats",
                error=str(e),
            )
            return {
                "total_jobs": 0,
                "user_notification_jobs": 0,
                "scheduler_running": False,
                "scheduler_state": "unknown",
                "error": str(e),
            }

    async def restore_all_user_schedules(self) -> dict:
        """
        Restore notification schedules for all users from database.

        This method should be called on application startup to restore
        all user notification schedules that were lost due to service restart.

        Returns:
            dict: Statistics about the restoration process
        """
        try:
            self.logger.info("Starting restoration of all user notification schedules")

            from app.repositories.user_notification_preferences import (
                UserNotificationPreferencesRepository,
            )
            from app.services.supabase_service import SupabaseService

            supabase = SupabaseService()
            prefs_repo = UserNotificationPreferencesRepository(supabase.client)

            # Get all users with active notification preferences
            all_preferences = await prefs_repo.get_all_active_preferences()

            restored_count = 0
            skipped_count = 0
            failed_count = 0

            for preferences in all_preferences:
                try:
                    # Skip if notifications are disabled
                    if preferences.frequency == "disabled" or not preferences.dm_enabled:
                        skipped_count += 1
                        continue

                    # Schedule the user notification
                    await self.schedule_user_notification(preferences.user_id, preferences)
                    restored_count += 1

                    self.logger.debug(
                        "Restored notification schedule",
                        user_id=str(preferences.user_id),
                        frequency=preferences.frequency,
                    )

                except Exception as user_error:
                    failed_count += 1
                    self.logger.warning(
                        "Failed to restore schedule for user",
                        user_id=str(preferences.user_id),
                        error=str(user_error),
                    )

            result = {
                "total_users": len(all_preferences),
                "restored": restored_count,
                "skipped": skipped_count,
                "failed": failed_count,
            }

            self.logger.info(
                "Completed restoration of user notification schedules",
                **result,
            )

            return result

        except Exception as e:
            self.logger.error(
                "Failed to restore user schedules",
                error=str(e),
                exc_info=True,
            )
            return {
                "total_users": 0,
                "restored": 0,
                "skipped": 0,
                "failed": 0,
                "error": str(e),
            }
