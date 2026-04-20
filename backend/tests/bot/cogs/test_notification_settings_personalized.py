"""
Tests for personalized notification settings Discord commands.

This module tests the new Discord slash commands for managing
personalized notification preferences.
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import discord
import pytest
from discord.ext import commands

from app.bot.cogs.notification_settings import NotificationSettings
from app.schemas.user_notification_preferences import UserNotificationPreferences


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    bot = MagicMock(spec=commands.Bot)
    return bot


@pytest.fixture
def mock_supabase_service():
    """Create a mock SupabaseService."""
    service = AsyncMock()
    service.get_or_create_user.return_value = str(uuid4())
    return service


@pytest.fixture
def notification_cog(mock_bot, mock_supabase_service):
    """Create a NotificationSettings cog instance."""
    return NotificationSettings(mock_bot, mock_supabase_service)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user.id = 123456789
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def mock_preferences():
    """Create mock user notification preferences."""
    return UserNotificationPreferences(
        id=uuid4(),
        user_id=uuid4(),
        frequency="weekly",
        notification_time=time(18, 0),
        timezone="Asia/Taipei",
        dm_enabled=True,
        email_enabled=False,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


class TestPersonalizedNotificationCommands:
    """Test personalized notification Discord commands."""

    @pytest.mark.asyncio
    async def test_notification_settings_detailed_success(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test /notification-settings command success."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.TimezoneConverter"
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify interaction handling
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify embed was sent
            call_args = mock_interaction.followup.send.call_args
            assert call_args[1]["ephemeral"] is True
            assert "embed" in call_args[1]

    @pytest.mark.asyncio
    async def test_set_notification_frequency_success(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test /set-notification-frequency command success."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ) as mock_scheduler:
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance

            # Create frequency choice
            frequency_choice = MagicMock()
            frequency_choice.value = "daily"

            # Execute command
            await notification_cog.set_notification_frequency.callback(
                notification_cog, mock_interaction, frequency_choice
            )

            # Verify interaction handling
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service calls
            mock_service_instance.update_preferences.assert_called_once()
            mock_scheduler_instance.reschedule_user_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_notification_time_success(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test /set-notification-time command success."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ) as mock_scheduler:
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance

            # Execute command
            await notification_cog.set_notification_time.callback(
                notification_cog, mock_interaction, 20, 30
            )

            # Verify interaction handling
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service calls
            mock_service_instance.update_preferences.assert_called_once()
            update_call_args = mock_service_instance.update_preferences.call_args[0][1]
            assert update_call_args.notification_time == "20:30"

    @pytest.mark.asyncio
    async def test_set_timezone_success(self, notification_cog, mock_interaction, mock_preferences):
        """Test /set-timezone command success."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ) as mock_scheduler, patch(
            "app.bot.cogs.notification_settings.TimezoneConverter"
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance

            # Create timezone choice
            timezone_choice = MagicMock()
            timezone_choice.value = "America/New_York"
            timezone_choice.name = "紐約 (America/New_York)"

            # Execute command
            await notification_cog.set_timezone.callback(
                notification_cog, mock_interaction, timezone_choice
            )

            # Verify interaction handling
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service calls
            mock_service_instance.update_preferences.assert_called_once()
            update_call_args = mock_service_instance.update_preferences.call_args[0][1]
            assert update_call_args.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_toggle_notifications_success(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test /toggle-notifications command success."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ) as mock_scheduler:
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = mock_preferences

            # Create updated preferences with toggled DM setting
            updated_preferences = mock_preferences.model_copy()
            updated_preferences.dm_enabled = False
            mock_service_instance.update_preferences.return_value = updated_preferences

            mock_pref_service.return_value = mock_service_instance

            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance

            # Execute command
            await notification_cog.toggle_notifications.callback(notification_cog, mock_interaction)

            # Verify interaction handling
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service calls
            mock_service_instance.get_user_preferences.assert_called_once()
            mock_service_instance.update_preferences.assert_called_once()

            # Verify DM was toggled to False
            update_call_args = mock_service_instance.update_preferences.call_args[0][1]
            assert update_call_args.dm_enabled is False

    @pytest.mark.asyncio
    async def test_command_error_handling(self, notification_cog, mock_interaction):
        """Test error handling in commands."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service:
            # Setup mock to raise exception
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.side_effect = Exception("Database error")
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify error response
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify error message was sent
            call_args = mock_interaction.followup.send.call_args[0][0]
            assert "❌" in call_args
            assert "錯誤" in call_args

    @pytest.mark.asyncio
    async def test_frequency_choice_validation(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test frequency choice validation."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test each valid frequency choice
            valid_frequencies = ["daily", "weekly", "monthly", "disabled"]

            for freq in valid_frequencies:
                frequency_choice = MagicMock()
                frequency_choice.value = freq

                # Execute command
                await notification_cog.set_notification_frequency.callback(
                    notification_cog, mock_interaction, frequency_choice
                )

                # Verify service was called with correct frequency
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert update_call_args.frequency == freq

    @pytest.mark.asyncio
    async def test_time_range_validation(
        self, notification_cog, mock_interaction, mock_preferences
    ):
        """Test time range validation."""
        with patch(
            "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
        ), patch(
            "app.bot.cogs.notification_settings.PreferenceService"
        ) as mock_pref_service, patch(
            "app.bot.cogs.notification_settings.get_dynamic_scheduler"
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = mock_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test boundary values
            test_cases = [
                (0, 0, "00:00"),  # Minimum values
                (23, 59, "23:59"),  # Maximum values
                (12, 30, "12:30"),  # Middle values
            ]

            for hour, minute, expected_time in test_cases:
                # Execute command
                await notification_cog.set_notification_time.callback(
                    notification_cog, mock_interaction, hour, minute
                )

                # Verify service was called with correct time
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert update_call_args.notification_time == expected_time
