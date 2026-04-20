"""
Integration tests for preference synchronization mechanism.

Tests the complete flow from preference updates to scheduler synchronization.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.schemas.user_notification_preferences import UpdateUserNotificationPreferencesRequest
from app.services.preference_service import PreferenceService
from app.services.preference_synchronization_service import PreferenceSynchronizationService


class TestPreferenceSynchronizationIntegration:
    """Integration tests for preference synchronization."""

    @pytest.mark.asyncio
    async def test_preference_update_triggers_scheduler_sync(self):
        """Test that updating preferences through PreferenceService triggers scheduler sync."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)
        mock_scheduler = AsyncMock()

        # Create test preferences
        user_id = uuid4()
        old_preferences = AsyncMock()
        old_preferences.frequency = "daily"
        old_preferences.notification_time = "18:00"
        old_preferences.timezone = "Asia/Taipei"
        old_preferences.dm_enabled = True
        old_preferences.email_enabled = False

        new_preferences = AsyncMock()
        new_preferences.frequency = "weekly"
        new_preferences.notification_time = "18:00"
        new_preferences.timezone = "Asia/Taipei"
        new_preferences.dm_enabled = True
        new_preferences.email_enabled = False

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = old_preferences
        mock_repo.update_by_user_id.return_value = new_preferences

        # Initialize services
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Update preferences
        updates = UpdateUserNotificationPreferencesRequest(frequency="weekly")
        result = await preference_service.update_preferences(user_id, updates, source="web")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify scheduler was called
        mock_scheduler.reschedule_user_notification.assert_called_once_with(
            user_id, new_preferences
        )

        assert result == new_preferences

    @pytest.mark.asyncio
    async def test_preference_disable_triggers_scheduler_cancel(self):
        """Test that disabling preferences triggers scheduler cancellation."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)
        mock_scheduler = AsyncMock()

        # Create test preferences
        user_id = uuid4()
        old_preferences = AsyncMock()
        old_preferences.frequency = "weekly"
        old_preferences.notification_time = "18:00"
        old_preferences.timezone = "Asia/Taipei"
        old_preferences.dm_enabled = True
        old_preferences.email_enabled = False

        new_preferences = AsyncMock()
        new_preferences.frequency = "disabled"
        new_preferences.notification_time = "18:00"
        new_preferences.timezone = "Asia/Taipei"
        new_preferences.dm_enabled = True
        new_preferences.email_enabled = False

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = old_preferences
        mock_repo.update_by_user_id.return_value = new_preferences

        # Initialize services
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Update preferences to disabled
        updates = UpdateUserNotificationPreferencesRequest(frequency="disabled")
        result = await preference_service.update_preferences(user_id, updates, source="discord")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify scheduler was called to cancel
        mock_scheduler.cancel_user_notification.assert_called_once_with(user_id)

        assert result == new_preferences

    @pytest.mark.asyncio
    async def test_multiple_preference_changes_sync_correctly(self):
        """Test that multiple preference changes are synchronized correctly."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)
        mock_scheduler = AsyncMock()

        # Create test preferences
        user_id = uuid4()
        old_preferences = AsyncMock()
        old_preferences.frequency = "daily"
        old_preferences.notification_time = "18:00"
        old_preferences.timezone = "Asia/Taipei"
        old_preferences.dm_enabled = True
        old_preferences.email_enabled = False

        new_preferences = AsyncMock()
        new_preferences.frequency = "weekly"
        new_preferences.notification_time = "20:00"
        new_preferences.timezone = "America/New_York"
        new_preferences.dm_enabled = True
        new_preferences.email_enabled = True

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = old_preferences
        mock_repo.update_by_user_id.return_value = new_preferences

        # Initialize services
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Update multiple preferences
        updates = UpdateUserNotificationPreferencesRequest(
            frequency="weekly",
            notification_time="20:00",
            timezone="America/New_York",
            email_enabled=True,
        )
        result = await preference_service.update_preferences(user_id, updates, source="web")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify scheduler was called once (not multiple times)
        mock_scheduler.reschedule_user_notification.assert_called_once_with(
            user_id, new_preferences
        )

        assert result == new_preferences

    @pytest.mark.asyncio
    async def test_create_default_preferences_triggers_sync(self):
        """Test that creating default preferences triggers synchronization."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)
        mock_scheduler = AsyncMock()

        # Create test preferences
        user_id = uuid4()
        default_preferences = AsyncMock()
        default_preferences.frequency = "weekly"
        default_preferences.notification_time = "18:00"
        default_preferences.timezone = "Asia/Taipei"
        default_preferences.dm_enabled = True
        default_preferences.email_enabled = False

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = None  # No existing preferences
        mock_repo.create_default_for_user.return_value = default_preferences

        # Initialize services
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Create default preferences
        result = await preference_service.create_default_preferences(user_id, source="system")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify scheduler was called for new preferences
        mock_scheduler.reschedule_user_notification.assert_called_once_with(
            user_id, default_preferences
        )

        assert result == default_preferences

    @pytest.mark.asyncio
    async def test_synchronization_works_without_scheduler(self):
        """Test that synchronization works gracefully without a scheduler."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)

        # Create test preferences
        user_id = uuid4()
        old_preferences = AsyncMock()
        old_preferences.frequency = "daily"

        new_preferences = AsyncMock()
        new_preferences.frequency = "weekly"

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = old_preferences
        mock_repo.update_by_user_id.return_value = new_preferences

        # Initialize services without scheduler
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(None)  # No scheduler

        # Update preferences - should not raise exception
        updates = UpdateUserNotificationPreferencesRequest(frequency="weekly")
        result = await preference_service.update_preferences(user_id, updates, source="web")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Should complete without error
        assert result == new_preferences

    @pytest.mark.asyncio
    async def test_source_tracking_in_events(self):
        """Test that the source of preference changes is tracked correctly."""
        # Mock dependencies
        mock_repo = AsyncMock(spec=UserNotificationPreferencesRepository)
        mock_scheduler = AsyncMock()

        # Create test preferences
        user_id = uuid4()
        old_preferences = AsyncMock()
        new_preferences = AsyncMock()
        new_preferences.frequency = "weekly"

        # Setup mock repository
        mock_repo.get_by_user_id.return_value = old_preferences
        mock_repo.update_by_user_id.return_value = new_preferences

        # Initialize services
        preference_service = PreferenceService(mock_repo)
        sync_service = PreferenceSynchronizationService(mock_scheduler)

        # Track events
        received_events = []

        async def event_tracker(event):
            received_events.append(event)

        preference_service.event_system.subscribe("preference_changed", event_tracker)

        # Update preferences from different sources
        updates = UpdateUserNotificationPreferencesRequest(frequency="weekly")

        # Web source
        await preference_service.update_preferences(user_id, updates, source="web")

        # Discord source
        await preference_service.update_preferences(user_id, updates, source="discord")

        # Give event system time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify events were tracked with correct sources
        assert len(received_events) == 2
        assert received_events[0].source == "web"
        assert received_events[1].source == "discord"
