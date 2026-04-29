"""Mixin extracted from service."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)


class DsStatsMixin:
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
