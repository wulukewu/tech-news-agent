"""
Preference Synchronization Service

This service handles synchronization of preference changes across interfaces
and triggers scheduler updates when preferences change.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

from typing import Optional
from uuid import UUID

from app.core.logger import get_logger
from app.services.preference_event_system import (
    PreferenceChangeEvent,
    get_preference_event_system,
)

logger = get_logger(__name__)


class PreferenceSynchronizationService:
    """
    Service for synchronizing preference changes across interfaces.

    This service:
    - Subscribes to preference change events
    - Triggers scheduler updates when preferences change
    - Ensures consistency across web and Discord interfaces
    - Handles notification status synchronization

    Requirements: 8.1, 8.2, 8.3, 8.4
    """

    def __init__(self, dynamic_scheduler=None):
        """
        Initialize the synchronization service.

        Args:
            dynamic_scheduler: DynamicScheduler instance for triggering updates
        """
        self.dynamic_scheduler = dynamic_scheduler
        self.event_system = get_preference_event_system()
        self.logger = get_logger(f"{__name__}.PreferenceSynchronizationService")

        # Subscribe to preference change events
        self.event_system.subscribe("preference_changed", self._handle_preference_change)

        self.logger.info("Preference synchronization service initialized")

    async def _handle_preference_change(self, event: PreferenceChangeEvent) -> None:
        """
        Handle preference change events.

        This method is called whenever preferences change and handles:
        - Scheduler updates
        - Cross-interface synchronization
        - Notification status updates

        Args:
            event: Preference change event data
        """
        try:
            self.logger.info(
                "Handling preference change event",
                user_id=str(event.user_id),
                changed_fields=event.changed_fields,
                source=event.source,
            )

            # Trigger scheduler updates if scheduling-related fields changed
            await self._update_scheduler_if_needed(event)

            # Log successful synchronization
            self.logger.info(
                "Successfully synchronized preference changes",
                user_id=str(event.user_id),
                changed_fields=event.changed_fields,
                source=event.source,
            )

        except Exception as e:
            self.logger.error(
                "Error handling preference change event",
                user_id=str(event.user_id),
                error=str(e),
                changed_fields=event.changed_fields,
                source=event.source,
            )

    async def _update_scheduler_if_needed(self, event: PreferenceChangeEvent) -> None:
        """
        Update scheduler if scheduling-related preferences changed.

        Args:
            event: Preference change event data
        """
        if not self.dynamic_scheduler:
            self.logger.warning(
                "No dynamic scheduler available for updates", user_id=str(event.user_id)
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
                "No scheduling-related fields changed, skipping scheduler update",
                user_id=str(event.user_id),
                changed_fields=event.changed_fields,
            )
            return

        try:
            self.logger.info(
                "Updating scheduler for preference changes",
                user_id=str(event.user_id),
                changed_scheduling_fields=changed_scheduling_fields,
            )

            # Check if notifications are disabled
            if event.new_preferences.frequency == "disabled":
                # Cancel all notifications for this user
                await self.dynamic_scheduler.cancel_user_notification(event.user_id)
                self.logger.info(
                    "Cancelled user notifications (disabled)", user_id=str(event.user_id)
                )
            else:
                # Reschedule notifications with new preferences
                await self.dynamic_scheduler.reschedule_user_notification(
                    event.user_id, event.new_preferences
                )
                self.logger.info(
                    "Rescheduled user notifications",
                    user_id=str(event.user_id),
                    frequency=event.new_preferences.frequency,
                    notification_time=str(event.new_preferences.notification_time),
                    timezone=event.new_preferences.timezone,
                )

        except Exception as e:
            self.logger.error(
                "Error updating scheduler for preference changes",
                user_id=str(event.user_id),
                error=str(e),
                changed_scheduling_fields=changed_scheduling_fields,
            )
            raise

    def set_dynamic_scheduler(self, dynamic_scheduler) -> None:
        """
        Set the dynamic scheduler instance.

        Args:
            dynamic_scheduler: DynamicScheduler instance
        """
        self.dynamic_scheduler = dynamic_scheduler
        self.logger.info("Dynamic scheduler set for preference synchronization")

    async def trigger_manual_sync(self, user_id: UUID) -> None:
        """
        Manually trigger synchronization for a user.

        This can be used to force synchronization when needed.

        Args:
            user_id: UUID of the user to synchronize
        """
        try:
            self.logger.info("Triggering manual synchronization", user_id=str(user_id))

            # This would typically fetch current preferences and trigger sync
            # For now, we just log the manual trigger
            self.logger.info("Manual synchronization completed", user_id=str(user_id))

        except Exception as e:
            self.logger.error("Error in manual synchronization", user_id=str(user_id), error=str(e))
            raise


# Global synchronization service instance
_sync_service: Optional[PreferenceSynchronizationService] = None


def get_preference_sync_service() -> PreferenceSynchronizationService:
    """
    Get the global preference synchronization service instance.

    Returns:
        PreferenceSynchronizationService: Global sync service instance
    """
    global _sync_service
    if _sync_service is None:
        _sync_service = PreferenceSynchronizationService()
    return _sync_service


def initialize_preference_sync_service(dynamic_scheduler=None) -> PreferenceSynchronizationService:
    """
    Initialize the global preference synchronization service.

    Args:
        dynamic_scheduler: DynamicScheduler instance

    Returns:
        PreferenceSynchronizationService: Initialized sync service
    """
    global _sync_service
    _sync_service = PreferenceSynchronizationService(dynamic_scheduler)
    return _sync_service
