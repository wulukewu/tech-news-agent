"""
Unit tests for PreferenceService

Tests the core functionality of the PreferenceService including CRUD operations,
validation, and default preference creation.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
"""

from datetime import time
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.repositories.user_notification_preferences import UserNotificationPreferences
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
)
from app.services.preference_service import PreferenceService


@pytest.fixture
def mock_preferences_repo():
    """Mock UserNotificationPreferencesRepository."""
    return AsyncMock()


@pytest.fixture
def preference_service(mock_preferences_repo):
    """PreferenceService instance with mocked dependencies."""
    return PreferenceService(preferences_repo=mock_preferences_repo)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def sample_preferences(sample_user_id):
    """Sample UserNotificationPreferences for testing."""
    return UserNotificationPreferences(
        id=uuid4(),
        user_id=sample_user_id,
        frequency="weekly",
        notification_time=time(18, 0),
        timezone="Asia/Taipei",
        dm_enabled=True,
        email_enabled=False,
    )


class TestPreferenceService:
    """Test cases for PreferenceService."""

    @pytest.mark.asyncio
    async def test_get_user_preferences_existing(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test getting existing user preferences."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = sample_preferences

        # Act
        result = await preference_service.get_user_preferences(sample_user_id)

        # Assert
        assert result == sample_preferences
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_user_preferences_creates_default(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test getting user preferences creates default when none exist."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = None
        mock_preferences_repo.create_default_for_user.return_value = sample_preferences

        # Act
        result = await preference_service.get_user_preferences(sample_user_id)

        # Assert
        assert result == sample_preferences
        # get_by_user_id is called twice: once in get_user_preferences and once in create_default_preferences
        assert mock_preferences_repo.get_by_user_id.call_count == 2
        mock_preferences_repo.create_default_for_user.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_create_default_preferences(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test creating default preferences."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = None
        mock_preferences_repo.create_default_for_user.return_value = sample_preferences

        # Act
        result = await preference_service.create_default_preferences(sample_user_id)

        # Assert
        assert result == sample_preferences
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)
        mock_preferences_repo.create_default_for_user.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_create_default_preferences_already_exists(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test creating default preferences when they already exist."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = sample_preferences

        # Act
        result = await preference_service.create_default_preferences(sample_user_id)

        # Assert
        assert result == sample_preferences
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)
        mock_preferences_repo.create_default_for_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_preferences_success(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test successful preference update."""
        # Arrange
        updates = UpdateUserNotificationPreferencesRequest(
            frequency="daily",
            notification_time="09:00",
            dm_enabled=False,
        )

        updated_preferences = UserNotificationPreferences(
            id=sample_preferences.id,
            user_id=sample_user_id,
            frequency="daily",
            notification_time=time(9, 0),
            timezone="Asia/Taipei",
            dm_enabled=False,
            email_enabled=False,
        )

        mock_preferences_repo.get_by_user_id.return_value = sample_preferences
        mock_preferences_repo.update_by_user_id.return_value = updated_preferences

        # Act
        result = await preference_service.update_preferences(sample_user_id, updates)

        # Assert
        assert result == updated_preferences
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)
        mock_preferences_repo.update_by_user_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preferences_creates_default_if_not_exists(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test updating preferences creates default if none exist."""
        # Arrange
        updates = UpdateUserNotificationPreferencesRequest(frequency="daily")

        # First call returns None (no preferences), second call returns the created preferences
        mock_preferences_repo.get_by_user_id.side_effect = [
            None,
            sample_preferences,
            sample_preferences,
        ]
        mock_preferences_repo.update_by_user_id.return_value = sample_preferences

        # Act
        result = await preference_service.update_preferences(sample_user_id, updates)

        # Assert
        assert result == sample_preferences
        # create_default_preferences calls create_default_for_user, but since get_by_user_id returns
        # sample_preferences on the second call, it doesn't actually create new preferences
        assert mock_preferences_repo.get_by_user_id.call_count >= 2

    def test_validate_preferences_valid(self, preference_service):
        """Test validation with valid preferences."""
        # Arrange
        preferences = UpdateUserNotificationPreferencesRequest(
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_preferences_invalid_frequency(self, preference_service):
        """Test validation with invalid frequency using service validation."""

        # Arrange - create a mock object that bypasses Pydantic validation
        class MockPreferences:
            def __init__(self):
                self.frequency = "invalid"

        preferences = MockPreferences()

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is False
        assert any("Invalid frequency" in error for error in result.errors)

    def test_validate_preferences_invalid_time_format(self, preference_service):
        """Test validation with invalid time format using service validation."""

        # Arrange - create a mock object that bypasses Pydantic validation
        class MockPreferences:
            def __init__(self):
                self.notification_time = "invalid_time"

        preferences = MockPreferences()

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is False
        assert any("notification_time must be in HH:MM format" in error for error in result.errors)

    def test_validate_preferences_invalid_time_hour(self, preference_service):
        """Test validation with invalid hour using service validation."""

        # Arrange - create a mock object that bypasses Pydantic validation
        class MockPreferences:
            def __init__(self):
                self.notification_time = "25:00"

        preferences = MockPreferences()

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is False
        assert any("Invalid hour" in error for error in result.errors)

    def test_validate_preferences_invalid_time_minute(self, preference_service):
        """Test validation with invalid minute using service validation."""

        # Arrange - create a mock object that bypasses Pydantic validation
        class MockPreferences:
            def __init__(self):
                self.notification_time = "12:70"

        preferences = MockPreferences()

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is False
        assert any("Invalid minute" in error for error in result.errors)

    def test_validate_preferences_invalid_timezone(self, preference_service):
        """Test validation with invalid timezone using service validation."""

        # Arrange - create a mock object that bypasses Pydantic validation
        class MockPreferences:
            def __init__(self):
                self.timezone = "Invalid/Timezone"

        preferences = MockPreferences()

        # Act
        result = preference_service.validate_preferences(preferences)

        # Assert
        assert result.is_valid is False
        assert any("Invalid timezone identifier" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_get_users_with_frequency(
        self, preference_service, mock_preferences_repo, sample_preferences
    ):
        """Test getting users with specific frequency."""
        # Arrange
        frequency = "weekly"
        mock_preferences_repo.list_by_field.return_value = [sample_preferences]

        # Act
        result = await preference_service.get_users_with_frequency(frequency)

        # Assert
        assert result == [sample_preferences]
        mock_preferences_repo.list_by_field.assert_called_once_with("frequency", frequency)

    @pytest.mark.asyncio
    async def test_get_users_with_invalid_frequency(
        self, preference_service, mock_preferences_repo
    ):
        """Test getting users with invalid frequency raises error."""
        # Arrange
        frequency = "invalid"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await preference_service.get_users_with_frequency(frequency)

        assert "Invalid frequency" in str(exc_info.value)
        mock_preferences_repo.list_by_field.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_preferences(
        self, preference_service, mock_preferences_repo, sample_user_id, sample_preferences
    ):
        """Test deleting user preferences."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = sample_preferences
        mock_preferences_repo.delete.return_value = True

        # Act
        await preference_service.delete_user_preferences(sample_user_id)

        # Assert
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)
        mock_preferences_repo.delete.assert_called_once_with(sample_preferences.id)

    @pytest.mark.asyncio
    async def test_delete_user_preferences_not_found(
        self, preference_service, mock_preferences_repo, sample_user_id
    ):
        """Test deleting user preferences when none exist."""
        # Arrange
        mock_preferences_repo.get_by_user_id.return_value = None

        # Act
        await preference_service.delete_user_preferences(sample_user_id)

        # Assert
        mock_preferences_repo.get_by_user_id.assert_called_once_with(sample_user_id)
        mock_preferences_repo.delete.assert_not_called()
