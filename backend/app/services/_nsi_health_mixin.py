"""Health/cleanup mixin for NotificationSystemIntegration."""
from typing import Dict

from app.core.logger import get_logger
from app.services.preference_event_system import (
    PreferenceChangeEvent,
)

logger = get_logger(__name__)


class NsiHealthMixin:
    async def get_system_health(self) -> Dict:
        """
        Get comprehensive system health information.

        Returns:
            Dict: System health status across all components
        """
        try:
            self.logger.debug("Getting notification system health")

            health = {
                "overall_status": "healthy",
                "components": {},
                "statistics": {},
            }

            # Check PreferenceService health
            try:
                # Test basic preference service functionality
                test_users = await self.preference_service.get_users_with_frequency("weekly")
                health["components"]["preference_service"] = {
                    "status": "healthy",
                    "active_users": len(test_users),
                }
            except Exception as e:
                health["components"]["preference_service"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["overall_status"] = "degraded"

            # Check DynamicScheduler health
            if self.dynamic_scheduler:
                try:
                    scheduler_stats = await self.dynamic_scheduler.get_scheduler_stats()
                    health["components"]["dynamic_scheduler"] = {
                        "status": "healthy",
                        "stats": scheduler_stats,
                    }
                except Exception as e:
                    health["components"]["dynamic_scheduler"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
                    health["overall_status"] = "degraded"
            else:
                health["components"]["dynamic_scheduler"] = {
                    "status": "unavailable",
                    "error": "Dynamic scheduler not initialized",
                }
                health["overall_status"] = "degraded"

            # Check LockManager health
            try:
                lock_stats = await self.lock_manager.get_lock_statistics()
                health["components"]["lock_manager"] = {
                    "status": "healthy",
                    "stats": lock_stats,
                }
            except Exception as e:
                health["components"]["lock_manager"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["overall_status"] = "degraded"

            # Check NotificationService health
            health["components"]["notification_service"] = {
                "status": "healthy",
                "bot_available": self.bot_client is not None,
                "channels_supported": ["discord_dm", "email"],
            }

            # Get event system statistics
            health["statistics"]["event_system"] = {
                "preference_change_subscribers": self.event_system.get_subscriber_count(
                    "preference_changed"
                ),
            }

            return health

        except Exception as e:
            self.logger.error("Failed to get system health", error=str(e))
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "components": {},
                "statistics": {},
            }

    async def cleanup_system_resources(self) -> Dict:
        """
        Clean up system resources and expired data.

        Returns:
            Dict: Cleanup results across all components
        """
        try:
            self.logger.info("Starting system resource cleanup")

            cleanup_results = {
                "overall_success": True,
                "components": {},
            }

            # Cleanup expired locks
            try:
                expired_locks = await self.lock_manager.cleanup_expired_locks()
                cleanup_results["components"]["lock_manager"] = {
                    "success": True,
                    "expired_locks_cleaned": expired_locks,
                }
            except Exception as e:
                cleanup_results["components"]["lock_manager"] = {
                    "success": False,
                    "error": str(e),
                }
                cleanup_results["overall_success"] = False

            # Cleanup expired scheduler jobs
            if self.dynamic_scheduler:
                try:
                    expired_jobs = await self.dynamic_scheduler.cleanup_expired_jobs()
                    cleanup_results["components"]["dynamic_scheduler"] = {
                        "success": True,
                        "expired_jobs_cleaned": expired_jobs,
                    }
                except Exception as e:
                    cleanup_results["components"]["dynamic_scheduler"] = {
                        "success": False,
                        "error": str(e),
                    }
                    cleanup_results["overall_success"] = False

            self.logger.info(
                "System resource cleanup completed",
                overall_success=cleanup_results["overall_success"],
            )

            return cleanup_results

        except Exception as e:
            self.logger.error("Failed to cleanup system resources", error=str(e))
            return {
                "overall_success": False,
                "error": str(e),
                "components": {},
            }

    async def _handle_preference_change(self, event: PreferenceChangeEvent) -> None:
        """
        Handle preference change events for scheduler coordination.

        This method is called automatically when preferences change and ensures
        the scheduler is updated accordingly.

        Args:
            event: Preference change event data
        """
        try:
            self.logger.info(
                "Handling preference change event in integration service",
                user_id=str(event.user_id),
                changed_fields=event.changed_fields,
                source=event.source,
            )

            if not self.dynamic_scheduler:
                self.logger.warning(
                    "Dynamic scheduler not available for preference change handling",
                    user_id=str(event.user_id),
                )
                return

            # Check if any scheduling-related fields changed
            scheduling_fields = {
                "frequency",
                "notification_time",
                "timezone",
                "dm_enabled",
                "email_enabled",
            }

            changed_scheduling_fields = [
                field for field in event.changed_fields if field in scheduling_fields
            ]

            if not changed_scheduling_fields:
                self.logger.debug(
                    "No scheduling-related fields changed",
                    user_id=str(event.user_id),
                    changed_fields=event.changed_fields,
                )
                return

            # Update scheduler based on new preferences
            if event.new_preferences.frequency == "disabled":
                await self.dynamic_scheduler.cancel_user_notification(event.user_id)
                self.logger.info(
                    "Cancelled user notifications due to preference change",
                    user_id=str(event.user_id),
                )
            else:
                await self.dynamic_scheduler.reschedule_user_notification(
                    event.user_id, event.new_preferences
                )
                self.logger.info(
                    "Rescheduled user notifications due to preference change",
                    user_id=str(event.user_id),
                    frequency=event.new_preferences.frequency,
                )

        except Exception as e:
            self.logger.error(
                "Error handling preference change event in integration service",
                user_id=str(event.user_id),
                error=str(e),
                changed_fields=event.changed_fields,
                source=event.source,
            )


# Global integration service instance
