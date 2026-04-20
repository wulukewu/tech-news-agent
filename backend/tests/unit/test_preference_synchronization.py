"""
Unit tests for preference synchronization mechanism.

Tests the event system and synchronization service for preference changes.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.repositories.user_notification_preferences import UserNotificationPreferences
from app.services.preference_event_system import (
    PreferenceChangeEvent,
    PreferenceEventSystem,
)
from app.services.preference_synchronization_service import PreferenceSynchronizationService


class TestPreferenceEventSystem:
    """Test the preference event system."""

    def test_subscribe_and_unsubscribe(self):
        """Test subscribing and unsubscribing from events."""
        event_system = PreferenceEventSystem()

        def test_callback(event):
            pass

        # Test subscribe
        event_system.subscribe("preference_changed", test_callback)
        assert event_system.get_subscriber_count("preference_changed") == 1

        # Test unsubscribe
        event_system.unsubscribe("preference_changed", test_callback)
        assert event_system.get_subscriber_count("preference_changed") == 0

    @pytest.mark.asyncio
    async def test_publish_event_with_async_callback(self):
        """Test publishing events with async callbacks."""
        event_system = PreferenceEventSystem()
        callback_called = False
        received_event = None

        async def async_callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event

        event_system.subscribe("preference_changed", async_callback)

        # Create test event
        user_id = uuid4()
        preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=None,
            new_preferences=preferences,
            changed_fields=["frequency"],
            source="test",
        )

        # Publish event
        await event_system.publish("preference_changed", event)

        # Verify callback was called
        assert callback_called
        assert received_event == event

    @pytest.mark.asyncio
    async def test_publish_event_with_sync_callback(self):
        """Test publishing events with sync callbacks."""
        event_system = PreferenceEventSystem()
        callback_called = False
        received_event = None

        def sync_callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event

        event_system.subscribe("preference_changed", sync_callback)

        # Create test event
        user_id = uuid4()
        preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=None,
            new_preferences=preferences,
            changed_fields=["frequency"],
            source="test",
        )

        # Publish event
        await event_system.publish("preference_changed", event)

        # Verify callback was called
        assert callback_called
        assert received_event == event

    @pytest.mark.asyncio
    async def test_publish_event_handles_callback_exceptions(self):
        """Test that publishing events handles callback exceptions gracefully."""
        event_system = PreferenceEventSystem()

        async def failing_callback(event):
            raise Exception("Test exception")

        async def working_callback(event):
            pass

        event_system.subscribe("preference_changed", failing_callback)
        event_system.subscribe("preference_changed", working_callback)

        # Create test event
        user_id = uuid4()
        preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=None,
            new_preferences=preferences,
            changed_fields=["frequency"],
            source="test",
        )

        # Should not raise exception even though one callback fails
        await event_system.publish("preference_changed", event)


class TestPreferenceSynchronizationService:
    """Test the preference synchronization service."""

    @pytest.mark.asyncio
    async def test_scheduler_update_on_frequency_change(self):
        """Test that scheduler is updated when frequency changes."""
        mock_scheduler = AsyncMock()
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Create test event with frequency change
        user_id = uuid4()
        old_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="daily",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )
        new_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=old_preferences,
            new_preferences=new_preferences,
            changed_fields=["frequency"],
            source="web",
        )

        # Handle the event
        await sync_service._handle_preference_change(event)

        # Verify scheduler was called
        mock_scheduler.reschedule_user_notification.assert_called_once_with(
            user_id, new_preferences
        )

    @pytest.mark.asyncio
    async def test_scheduler_cancel_on_disabled_frequency(self):
        """Test that scheduler cancels notifications when frequency is disabled."""
        mock_scheduler = AsyncMock()
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Create test event with disabled frequency
        user_id = uuid4()
        old_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )
        new_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="disabled",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=old_preferences,
            new_preferences=new_preferences,
            changed_fields=["frequency"],
            source="discord",
        )

        # Handle the event
        await sync_service._handle_preference_change(event)

        # Verify scheduler was called to cancel
        mock_scheduler.cancel_user_notification.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_no_scheduler_update_on_non_scheduling_change(self):
        """Test that scheduler is not updated for non-scheduling field changes."""
        mock_scheduler = AsyncMock()
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Create test event with non-scheduling field change
        user_id = uuid4()
        old_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )
        new_preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=old_preferences,
            new_preferences=new_preferences,
            changed_fields=["some_other_field"],  # Non-scheduling field
            source="web",
        )

        # Handle the event
        await sync_service._handle_preference_change(event)

        # Verify scheduler was not called
        mock_scheduler.reschedule_user_notification.assert_not_called()
        mock_scheduler.cancel_user_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_missing_scheduler_gracefully(self):
        """Test that service handles missing scheduler gracefully."""
        sync_service = PreferenceSynchronizationService(None)

        # Create test event
        user_id = uuid4()
        preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=None,
            new_preferences=preferences,
            changed_fields=["frequency"],
            source="web",
        )

        # Should not raise exception
        await sync_service._handle_preference_change(event)

    @pytest.mark.asyncio
    async def test_manual_sync_trigger(self):
        """Test manual synchronization trigger."""
        mock_scheduler = AsyncMock()
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        user_id = uuid4()

        # Should not raise exception
        await sync_service.trigger_manual_sync(user_id)


class TestPreferenceChangeEvent:
    """Test the preference change event data structure."""

    def test_event_creation(self):
        """Test creating a preference change event."""
        user_id = uuid4()
        preferences = UserNotificationPreferences(
            id=1,
            user_id=user_id,
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=None,
            new_preferences=preferences,
            changed_fields=["frequency", "dm_enabled"],
            source="web",
        )

        assert event.user_id == user_id
        assert event.old_preferences is None
        assert event.new_preferences == preferences
        assert event.changed_fields == ["frequency", "dm_enabled"]
        assert event.source == "web"
        assert event.timestamp > 0
