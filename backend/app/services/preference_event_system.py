"""
Preference Event System

This module provides an event system for preference changes to ensure immediate
synchronization between web and Discord interfaces and trigger scheduler updates.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.repositories.user_notification_preferences import UserNotificationPreferences

logger = get_logger(__name__)


class PreferenceChangeEvent:
    """
    Event data for preference changes.

    Contains information about what changed and the new values.
    """

    def __init__(
        self,
        user_id: UUID,
        old_preferences: Optional[UserNotificationPreferences],
        new_preferences: UserNotificationPreferences,
        changed_fields: List[str],
        source: str = "unknown",
    ):
        """
        Initialize preference change event.

        Args:
            user_id: UUID of the user whose preferences changed
            old_preferences: Previous preferences (None if creating new)
            new_preferences: New preferences after change
            changed_fields: List of field names that changed
            source: Source of the change (web, discord, system)
        """
        self.user_id = user_id
        self.old_preferences = old_preferences
        self.new_preferences = new_preferences
        self.changed_fields = changed_fields
        self.source = source
        self.timestamp = asyncio.get_event_loop().time()


class PreferenceEventSystem:
    """
    Event system for preference changes.

    Provides publish/subscribe mechanism for preference change events to enable
    immediate synchronization between interfaces and trigger scheduler updates.

    Requirements: 8.1, 8.2, 8.3, 8.4
    """

    def __init__(self):
        """Initialize the event system."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self.logger = get_logger(f"{__name__}.PreferenceEventSystem")

    def subscribe(self, event_type: str, callback: Callable[[PreferenceChangeEvent], Any]) -> None:
        """
        Subscribe to preference change events.

        Args:
            event_type: Type of event to subscribe to ('preference_changed')
            callback: Async callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        self.logger.info(
            "Subscribed to preference events",
            event_type=event_type,
            callback=callback.__name__,
            total_subscribers=len(self._subscribers[event_type]),
        )

    def unsubscribe(
        self, event_type: str, callback: Callable[[PreferenceChangeEvent], Any]
    ) -> None:
        """
        Unsubscribe from preference change events.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            self.logger.info(
                "Unsubscribed from preference events",
                event_type=event_type,
                callback=callback.__name__,
                remaining_subscribers=len(self._subscribers[event_type]),
            )

    async def publish(self, event_type: str, event: PreferenceChangeEvent) -> None:
        """
        Publish a preference change event to all subscribers.

        Args:
            event_type: Type of event to publish
            event: Event data to publish
        """
        if event_type not in self._subscribers:
            self.logger.debug("No subscribers for event type", event_type=event_type)
            return

        subscribers = self._subscribers[event_type]
        self.logger.info(
            "Publishing preference change event",
            event_type=event_type,
            user_id=str(event.user_id),
            changed_fields=event.changed_fields,
            source=event.source,
            subscriber_count=len(subscribers),
        )

        # Execute all callbacks concurrently
        tasks = []
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    # Handle sync callbacks by running in executor
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, event))
            except Exception as e:
                self.logger.error(
                    "Error preparing callback for execution",
                    callback=callback.__name__,
                    error=str(e),
                    user_id=str(event.user_id),
                )

        if tasks:
            # Wait for all callbacks to complete, but don't fail if some do
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions that occurred
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    callback_name = subscribers[i].__name__ if i < len(subscribers) else "unknown"
                    self.logger.error(
                        "Error in preference change event callback",
                        callback=callback_name,
                        error=str(result),
                        user_id=str(event.user_id),
                    )

    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))


# Global event system instance
preference_event_system = PreferenceEventSystem()


def get_preference_event_system() -> PreferenceEventSystem:
    """
    Get the global preference event system instance.

    Returns:
        PreferenceEventSystem: Global event system instance
    """
    return preference_event_system
