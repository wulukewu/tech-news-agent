"""
Unit tests for NotificationSettingsService

Tests the core functionality of the NotificationSettingsService including:
- Getting notification settings
- Updating notification settings
- Sending test notifications
- Error handling
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.schemas.notification import (
    NotificationSettings,
    QuietHours,
    UpdateNotificationSettingsRequest,
)
from app.services.notification_settings_service import NotificationSettingsService
from app.services.supabase_service import SupabaseService


@pytest.fixture
def mock_supabase_service():
    """Create a mock SupabaseService"""
    return AsyncMock(spec=SupabaseService)


@pytest.fixture
def notification_service(mock_supabase_service):
    """Create a NotificationSettingsService instance with mock dependencies"""
    return NotificationSettingsService(mock_supabase_service)


@pytest.fixture
def sample_user_id():
    """Sample user UUID for testing"""
    return uuid4()


class TestNotificationSettingsService:
    """Test cases for NotificationSettingsService"""

    @pytest.mark.asyncio
    async def test_get_notification_settings_success(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test successful retrieval of notification settings"""
        # Mock user data and DM settings
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )
        mock_supabase_service.get_notification_settings.return_value = True

        result = await notification_service.get_notification_settings(sample_user_id)

        assert isinstance(result, NotificationSettings)
        assert result.enabled is True
        assert result.dm_enabled is True
        assert result.email_enabled is False
        assert result.frequency == "immediate"
        assert result.min_tinkering_index == 3
        assert "dm" in result.channels
        assert "in-app" in result.channels

    @pytest.mark.asyncio
    async def test_get_notification_settings_user_not_found(
        self, notification_service, sample_user_id
    ):
        """Test getting settings when user not found returns defaults"""
        # Mock user not found
        notification_service._get_user_data = AsyncMock(return_value={})

        result = await notification_service.get_notification_settings(sample_user_id)

        assert isinstance(result, NotificationSettings)
        assert result.enabled is True
        assert result.dm_enabled is True
        assert result.frequency == "immediate"

    @pytest.mark.asyncio
    async def test_get_notification_settings_dm_disabled(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test getting settings when DM notifications are disabled"""
        # Mock user data with DM disabled
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )
        mock_supabase_service.get_notification_settings.return_value = False

        result = await notification_service.get_notification_settings(sample_user_id)

        assert result.enabled is False
        assert result.dm_enabled is False
        assert "dm" not in result.channels
        assert "in-app" in result.channels

    @pytest.mark.asyncio
    async def test_update_notification_settings_success(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test successful update of notification settings"""
        # Mock user data
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )
        mock_supabase_service.update_notification_settings.return_value = None
        mock_supabase_service.get_notification_settings.return_value = True

        updates = UpdateNotificationSettingsRequest(dm_enabled=True)
        result = await notification_service.update_notification_settings(sample_user_id, updates)

        assert isinstance(result, NotificationSettings)
        assert result.dm_enabled is True
        mock_supabase_service.update_notification_settings.assert_called_once_with(
            "discord_123", True
        )

    @pytest.mark.asyncio
    async def test_update_notification_settings_user_not_found(
        self, notification_service, sample_user_id
    ):
        """Test updating settings when user not found"""
        # Mock user not found
        notification_service._get_user_data = AsyncMock(return_value={})

        updates = UpdateNotificationSettingsRequest(dm_enabled=True)

        with pytest.raises(ValidationError) as exc_info:
            await notification_service.update_notification_settings(sample_user_id, updates)

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_test_notification_success(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test successful sending of test notification"""
        # Mock user data and enabled DM
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )
        mock_supabase_service.get_notification_settings.return_value = True

        # Should not raise any exception
        await notification_service.send_test_notification(sample_user_id)

    @pytest.mark.asyncio
    async def test_send_test_notification_user_not_found(
        self, notification_service, sample_user_id
    ):
        """Test sending test notification when user not found"""
        # Mock user not found
        notification_service._get_user_data = AsyncMock(return_value={})

        with pytest.raises(ValidationError) as exc_info:
            await notification_service.send_test_notification(sample_user_id)

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_test_notification_dm_disabled(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test sending test notification when DM is disabled"""
        # Mock user data with DM disabled
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )
        mock_supabase_service.get_notification_settings.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            await notification_service.send_test_notification(sample_user_id)

        assert "DM notifications are disabled" in str(exc_info.value)

    def test_get_default_settings(self, notification_service):
        """Test getting default notification settings"""
        settings = notification_service._get_default_settings()

        assert isinstance(settings, NotificationSettings)
        assert settings.enabled is True
        assert settings.dm_enabled is True
        assert settings.email_enabled is False
        assert settings.frequency == "immediate"
        assert settings.min_tinkering_index == 3
        assert isinstance(settings.quiet_hours, QuietHours)
        assert settings.quiet_hours.enabled is False
        assert settings.quiet_hours.start == "22:00"
        assert settings.quiet_hours.end == "08:00"
        assert settings.channels == ["dm", "in-app"]

    @pytest.mark.asyncio
    async def test_get_user_data_placeholder(self, notification_service, sample_user_id):
        """Test the placeholder _get_user_data method"""
        result = await notification_service._get_user_data(sample_user_id)

        assert isinstance(result, dict)
        assert result["id"] == str(sample_user_id)
        assert result["discord_id"] == f"discord_{sample_user_id}"

    @pytest.mark.asyncio
    async def test_error_handling(
        self, notification_service, mock_supabase_service, sample_user_id
    ):
        """Test error handling in service methods"""
        # Mock service error
        mock_supabase_service.get_notification_settings.side_effect = Exception("Database error")
        notification_service._get_user_data = AsyncMock(
            return_value={"id": str(sample_user_id), "discord_id": "discord_123"}
        )

        with pytest.raises(Exception):  # Should raise some exception, not necessarily ServiceError
            await notification_service.get_notification_settings(sample_user_id)
