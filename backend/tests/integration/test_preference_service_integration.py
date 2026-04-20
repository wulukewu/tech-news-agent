"""
Integration tests for PreferenceService

Tests the PreferenceService with actual repository integration to verify
the complete CRUD workflow and database operations.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
"""

from datetime import time
from uuid import uuid4

import pytest

from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
)
from app.services.preference_service import PreferenceService


@pytest.mark.integration
class TestPreferenceServiceIntegration:
    """Integration test cases for PreferenceService."""

    @pytest.fixture
    def preferences_repo(self, supabase_client):
        """UserNotificationPreferencesRepository instance with real database client."""
        return UserNotificationPreferencesRepository(supabase_client)

    @pytest.fixture
    def preference_service(self, preferences_repo):
        """PreferenceService instance with real repository."""
        return PreferenceService(preferences_repo=preferences_repo)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_create_and_get_default_preferences(self, preference_service, sample_user_id):
        """Test creating default preferences and retrieving them."""
        # Act - Create default preferences
        created_preferences = await preference_service.create_default_preferences(sample_user_id)

        # Assert - Verify default values
        assert created_preferences.user_id == sample_user_id
        assert created_preferences.frequency == "weekly"
        assert created_preferences.notification_time == time(18, 0)
        assert created_preferences.timezone == "Asia/Taipei"
        assert created_preferences.dm_enabled is True
        assert created_preferences.email_enabled is False

        # Act - Get preferences
        retrieved_preferences = await preference_service.get_user_preferences(sample_user_id)

        # Assert - Should return the same preferences
        assert retrieved_preferences.id == created_preferences.id
        assert retrieved_preferences.user_id == sample_user_id
        assert retrieved_preferences.frequency == "weekly"

        # Cleanup
        await preference_service.delete_user_preferences(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_preferences_workflow(self, preference_service, sample_user_id):
        """Test the complete update preferences workflow."""
        # Arrange - Create default preferences first
        await preference_service.create_default_preferences(sample_user_id)

        # Act - Update preferences
        updates = UpdateUserNotificationPreferencesRequest(
            frequency="daily",
            notification_time="09:30",
            timezone="America/New_York",
            dm_enabled=False,
            email_enabled=True,
        )

        updated_preferences = await preference_service.update_preferences(sample_user_id, updates)

        # Assert - Verify updates were applied
        assert updated_preferences.user_id == sample_user_id
        assert updated_preferences.frequency == "daily"
        assert updated_preferences.notification_time == time(9, 30)
        assert updated_preferences.timezone == "America/New_York"
        assert updated_preferences.dm_enabled is False
        assert updated_preferences.email_enabled is True

        # Act - Get preferences to verify persistence
        retrieved_preferences = await preference_service.get_user_preferences(sample_user_id)

        # Assert - Should have the updated values
        assert retrieved_preferences.frequency == "daily"
        assert retrieved_preferences.notification_time == time(9, 30)
        assert retrieved_preferences.timezone == "America/New_York"
        assert retrieved_preferences.dm_enabled is False
        assert retrieved_preferences.email_enabled is True

        # Cleanup
        await preference_service.delete_user_preferences(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_preferences_creates_default_when_none_exist(
        self, preference_service, sample_user_id
    ):
        """Test that getting preferences creates default when none exist."""
        # Act - Get preferences for user with no existing preferences
        preferences = await preference_service.get_user_preferences(sample_user_id)

        # Assert - Should have created default preferences
        assert preferences.user_id == sample_user_id
        assert preferences.frequency == "weekly"
        assert preferences.notification_time == time(18, 0)
        assert preferences.timezone == "Asia/Taipei"
        assert preferences.dm_enabled is True
        assert preferences.email_enabled is False

        # Cleanup
        await preference_service.delete_user_preferences(sample_user_id)

    @pytest.mark.asyncio
    async def test_validation_with_real_data(self, preference_service):
        """Test validation with various real data scenarios."""
        # Test valid preferences
        valid_updates = UpdateUserNotificationPreferencesRequest(
            frequency="monthly",
            notification_time="14:45",
            timezone="Europe/London",
            dm_enabled=True,
            email_enabled=False,
        )

        validation_result = preference_service.validate_preferences(valid_updates)
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0

        # Test edge case times
        edge_case_updates = UpdateUserNotificationPreferencesRequest(
            notification_time="00:00",  # Midnight
        )

        validation_result = preference_service.validate_preferences(edge_case_updates)
        assert validation_result.is_valid is True

        edge_case_updates = UpdateUserNotificationPreferencesRequest(
            notification_time="23:59",  # Just before midnight
        )

        validation_result = preference_service.validate_preferences(edge_case_updates)
        assert validation_result.is_valid is True

    @pytest.mark.asyncio
    async def test_partial_updates(self, preference_service, sample_user_id):
        """Test partial updates only modify specified fields."""
        # Arrange - Create default preferences
        await preference_service.create_default_preferences(sample_user_id)

        # Act - Update only frequency
        frequency_update = UpdateUserNotificationPreferencesRequest(frequency="daily")
        updated_preferences = await preference_service.update_preferences(
            sample_user_id, frequency_update
        )

        # Assert - Only frequency should change, others remain default
        assert updated_preferences.frequency == "daily"
        assert updated_preferences.notification_time == time(18, 0)  # Default
        assert updated_preferences.timezone == "Asia/Taipei"  # Default
        assert updated_preferences.dm_enabled is True  # Default
        assert updated_preferences.email_enabled is False  # Default

        # Act - Update only notification time
        time_update = UpdateUserNotificationPreferencesRequest(notification_time="12:00")
        updated_preferences = await preference_service.update_preferences(
            sample_user_id, time_update
        )

        # Assert - Frequency should remain "daily", time should be updated
        assert updated_preferences.frequency == "daily"  # From previous update
        assert updated_preferences.notification_time == time(12, 0)  # New value
        assert updated_preferences.timezone == "Asia/Taipei"  # Default
        assert updated_preferences.dm_enabled is True  # Default
        assert updated_preferences.email_enabled is False  # Default

        # Cleanup
        await preference_service.delete_user_preferences(sample_user_id)

    @pytest.mark.asyncio
    async def test_delete_preferences(self, preference_service, sample_user_id):
        """Test deleting user preferences."""
        # Arrange - Create preferences
        await preference_service.create_default_preferences(sample_user_id)

        # Verify preferences exist
        preferences = await preference_service.get_user_preferences(sample_user_id)
        assert preferences.user_id == sample_user_id

        # Act - Delete preferences
        await preference_service.delete_user_preferences(sample_user_id)

        # Assert - Getting preferences should create new defaults
        new_preferences = await preference_service.get_user_preferences(sample_user_id)
        assert new_preferences.user_id == sample_user_id
        # Should be a new record (different ID)
        assert new_preferences.id != preferences.id

        # Cleanup
        await preference_service.delete_user_preferences(sample_user_id)
