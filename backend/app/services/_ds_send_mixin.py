"""Mixin extracted from service."""
from __future__ import annotations

from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)


class DsSendMixin:
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
                    quiet_hours_start=(
                        quiet_hours_settings.start_time.strftime("%H:%M")
                        if quiet_hours_settings
                        else None
                    ),
                    quiet_hours_end=(
                        quiet_hours_settings.end_time.strftime("%H:%M")
                        if quiet_hours_settings
                        else None
                    ),
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
