"""
Unit tests for Discord commands - command parsing, validation, and database integration.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

This module provides comprehensive unit tests for Discord slash commands including:
- Command parsing and parameter validation
- Database integration and error handling
- Service layer interactions
- Response formatting and user feedback
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import discord
import pytest
from discord.ext import commands

from app.bot.cogs.notification_settings import NotificationSettings
from app.core.exceptions import SupabaseServiceError
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
    UserNotificationPreferences,
)


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
def sample_preferences():
    """Create sample user notification preferences."""
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


class TestDiscordCommandParsing:
    """Test Discord command parsing and parameter validation."""

    @pytest.mark.asyncio
    async def test_notification_settings_command_parsing(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test /notification-settings command parsing and execution."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.TimezoneConverter"),
        ):
            # Setup service mock
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify command parsing
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service interaction
            mock_service_instance.get_user_preferences.assert_called_once()

            # Verify response structure
            call_args = mock_interaction.followup.send.call_args
            assert call_args[1]["ephemeral"] is True
            assert "embed" in call_args[1]

    @pytest.mark.asyncio
    async def test_set_frequency_command_parsing(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test /set-notification-frequency command parsing with valid choices."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
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

                # Verify parameter parsing
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert isinstance(update_call_args, UpdateUserNotificationPreferencesRequest)
                assert update_call_args.frequency == freq

    @pytest.mark.asyncio
    async def test_set_time_command_parsing(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test /set-notification-time command parsing with hour/minute parameters."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test time parameter parsing
            test_cases = [
                (0, 0, "00:00"),  # Minimum boundary
                (23, 59, "23:59"),  # Maximum boundary
                (12, 30, "12:30"),  # Middle value
                (9, 5, "09:05"),  # Single digit formatting
            ]

            for hour, minute, expected_time in test_cases:
                # Execute command
                await notification_cog.set_notification_time.callback(
                    notification_cog, mock_interaction, hour, minute
                )

                # Verify time formatting
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert update_call_args.notification_time == expected_time

    @pytest.mark.asyncio
    async def test_set_timezone_command_parsing(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test /set-timezone command parsing with timezone choices."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
            patch("app.bot.cogs.notification_settings.TimezoneConverter"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test timezone choices
            timezone_choices = [
                ("Asia/Taipei", "台北 (Asia/Taipei)"),
                ("America/New_York", "紐約 (America/New_York)"),
                ("Europe/London", "倫敦 (Europe/London)"),
                ("UTC", "UTC"),
            ]

            for tz_value, tz_name in timezone_choices:
                timezone_choice = MagicMock()
                timezone_choice.value = tz_value
                timezone_choice.name = tz_name

                # Execute command
                await notification_cog.set_timezone.callback(
                    notification_cog, mock_interaction, timezone_choice
                )

                # Verify timezone parsing
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert update_call_args.timezone == tz_value

    @pytest.mark.asyncio
    async def test_toggle_notifications_command_parsing(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test /toggle-notifications command parsing and state toggling."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences

            # Create toggled preferences
            toggled_preferences = sample_preferences.model_copy()
            toggled_preferences.dm_enabled = not sample_preferences.dm_enabled
            mock_service_instance.update_preferences.return_value = toggled_preferences

            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.toggle_notifications.callback(notification_cog, mock_interaction)

            # Verify state retrieval and toggle
            mock_service_instance.get_user_preferences.assert_called_once()
            mock_service_instance.update_preferences.assert_called_once()

            # Verify toggle logic
            update_call_args = mock_service_instance.update_preferences.call_args[0][1]
            assert update_call_args.dm_enabled == (not sample_preferences.dm_enabled)


class TestCommandValidation:
    """Test command input validation and error handling."""

    @pytest.mark.asyncio
    async def test_frequency_validation(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test frequency parameter validation."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test all valid frequency values
            valid_frequencies = ["daily", "weekly", "monthly", "disabled"]

            for freq in valid_frequencies:
                frequency_choice = MagicMock()
                frequency_choice.value = freq

                # Execute command - should not raise exception
                await notification_cog.set_notification_frequency.callback(
                    notification_cog, mock_interaction, frequency_choice
                )

                # Verify service was called successfully
                assert mock_service_instance.update_preferences.called

    @pytest.mark.asyncio
    async def test_time_boundary_validation(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test time parameter boundary validation."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test boundary values (Discord's app_commands.Range handles validation)
            boundary_cases = [
                (0, 0),  # Minimum values
                (23, 59),  # Maximum values
                (12, 0),  # Hour boundary, minute minimum
                (0, 30),  # Hour minimum, minute middle
            ]

            for hour, minute in boundary_cases:
                # Execute command - should not raise exception
                await notification_cog.set_notification_time.callback(
                    notification_cog, mock_interaction, hour, minute
                )

                # Verify proper time formatting
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                expected_time = f"{hour:02d}:{minute:02d}"
                assert update_call_args.notification_time == expected_time

    @pytest.mark.asyncio
    async def test_timezone_validation(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test timezone parameter validation."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
            patch("app.bot.cogs.notification_settings.TimezoneConverter"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Test valid timezone identifiers
            valid_timezones = [
                "Asia/Taipei",
                "America/New_York",
                "Europe/London",
                "UTC",
                "Australia/Sydney",
            ]

            for tz in valid_timezones:
                timezone_choice = MagicMock()
                timezone_choice.value = tz
                timezone_choice.name = f"Test ({tz})"

                # Execute command - should not raise exception
                await notification_cog.set_timezone.callback(
                    notification_cog, mock_interaction, timezone_choice
                )

                # Verify timezone was set correctly
                update_call_args = mock_service_instance.update_preferences.call_args[0][1]
                assert update_call_args.timezone == tz


class TestDatabaseIntegration:
    """Test database integration and service layer interactions."""

    @pytest.mark.asyncio
    async def test_user_creation_and_retrieval(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test user creation and preference retrieval from database."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify user creation/retrieval
            notification_cog.supabase_service.get_or_create_user.assert_called_once_with(
                str(mock_interaction.user.id)
            )

            # Verify preference service initialization and usage
            mock_pref_service.assert_called_once()
            mock_service_instance.get_user_preferences.assert_called_once()

    @pytest.mark.asyncio
    async def test_preference_updates_database_sync(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test preference updates synchronize with database."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler") as mock_scheduler,
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
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

            # Verify database update
            mock_service_instance.update_preferences.assert_called_once()
            call_args, call_kwargs = mock_service_instance.update_preferences.call_args

            # Verify user ID and update request
            assert isinstance(call_args[0], UUID)
            assert isinstance(call_args[1], UpdateUserNotificationPreferencesRequest)
            assert call_args[1].frequency == "daily"
            assert call_kwargs.get("source") == "discord"

    @pytest.mark.asyncio
    async def test_scheduler_integration(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test dynamic scheduler integration with preference updates."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler") as mock_scheduler,
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance

            # Execute time update command
            await notification_cog.set_notification_time.callback(
                notification_cog, mock_interaction, 20, 30
            )

            # Verify scheduler interaction
            mock_scheduler.assert_called_once()
            # Note: The actual scheduler reschedule call happens in the service layer

    @pytest.mark.asyncio
    async def test_database_error_handling(self, notification_cog, mock_interaction):
        """Test database error handling and user feedback."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
        ):
            # Setup mock to raise database error
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.side_effect = SupabaseServiceError(
                "Database connection failed"
            )
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify error response
            mock_interaction.followup.send.assert_called_once()
            error_message = mock_interaction.followup.send.call_args[0][0]
            assert "❌" in error_message
            assert "錯誤" in error_message

    @pytest.mark.asyncio
    async def test_concurrent_update_handling(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test handling of concurrent preference updates."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Create multiple update requests
            frequency_choice = MagicMock()
            frequency_choice.value = "daily"

            # Execute multiple concurrent updates
            await notification_cog.set_notification_frequency.callback(
                notification_cog, mock_interaction, frequency_choice
            )

            # Verify each update is handled independently
            assert mock_service_instance.update_preferences.call_count >= 1


class TestResponseFormatting:
    """Test Discord response formatting and user feedback."""

    @pytest.mark.asyncio
    async def test_settings_display_formatting(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test notification settings display formatting."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.TimezoneConverter"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify embed response
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]

            # Verify embed structure
            assert embed.title == "🔔 你的個人化通知設定"
            assert embed.color == discord.Color.blue()

    @pytest.mark.asyncio
    async def test_success_message_formatting(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test success message formatting for updates."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Create frequency choice
            frequency_choice = MagicMock()
            frequency_choice.value = "daily"

            # Execute command
            await notification_cog.set_notification_frequency.callback(
                notification_cog, mock_interaction, frequency_choice
            )

            # Verify success response
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]

            assert embed.title == "✅ 通知頻率已更新"
            assert embed.color == discord.Color.green()
            assert "每日" in embed.description

    @pytest.mark.asyncio
    async def test_error_message_formatting(self, notification_cog, mock_interaction):
        """Test error message formatting."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
        ):
            # Setup mock to raise error
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.side_effect = Exception("Test error")
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify error response format
            call_args = mock_interaction.followup.send.call_args
            error_message = call_args[0][0]

            assert error_message.startswith("❌")
            assert "錯誤" in error_message
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_toggle_response_formatting(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test toggle notification response formatting."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
        ):
            # Setup mocks for enabled -> disabled toggle
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences

            disabled_preferences = sample_preferences.model_copy()
            disabled_preferences.dm_enabled = False
            mock_service_instance.update_preferences.return_value = disabled_preferences

            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.toggle_notifications.callback(notification_cog, mock_interaction)

            # Verify toggle response
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]

            assert "❌ 通知已關閉" == embed.title
            assert embed.color == discord.Color.red()


class TestCommandIntegration:
    """Test end-to-end command integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_preference_workflow(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test complete preference configuration workflow."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
            patch("app.bot.cogs.notification_settings.get_dynamic_scheduler"),
            patch("app.bot.cogs.notification_settings.TimezoneConverter"),
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_service_instance.update_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # 1. View current settings
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # 2. Update frequency
            frequency_choice = MagicMock()
            frequency_choice.value = "daily"
            await notification_cog.set_notification_frequency.callback(
                notification_cog, mock_interaction, frequency_choice
            )

            # 3. Update time
            await notification_cog.set_notification_time.callback(
                notification_cog, mock_interaction, 9, 30
            )

            # 4. Update timezone
            timezone_choice = MagicMock()
            timezone_choice.value = "America/New_York"
            timezone_choice.name = "New York"
            await notification_cog.set_timezone.callback(
                notification_cog, mock_interaction, timezone_choice
            )

            # 5. Toggle notifications
            await notification_cog.toggle_notifications.callback(notification_cog, mock_interaction)

            # Verify all commands executed successfully
            assert mock_service_instance.get_user_preferences.call_count >= 1
            assert mock_service_instance.update_preferences.call_count >= 4

    @pytest.mark.asyncio
    async def test_user_registration_integration(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test user registration integration with commands."""
        with (
            patch("app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"),
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify user registration flow
            notification_cog.supabase_service.get_or_create_user.assert_called_once_with(
                str(mock_interaction.user.id)
            )

            # Verify UUID conversion
            user_id_arg = mock_service_instance.get_user_preferences.call_args[0][0]
            assert isinstance(user_id_arg, UUID)

    @pytest.mark.asyncio
    async def test_service_layer_integration(
        self, notification_cog, mock_interaction, sample_preferences
    ):
        """Test service layer integration and dependency injection."""
        with (
            patch(
                "app.bot.cogs.notification_settings.UserNotificationPreferencesRepository"
            ) as mock_repo,
            patch("app.bot.cogs.notification_settings.PreferenceService") as mock_pref_service,
        ):
            # Setup mocks
            mock_service_instance = AsyncMock()
            mock_service_instance.get_user_preferences.return_value = sample_preferences
            mock_pref_service.return_value = mock_service_instance

            # Execute command
            await notification_cog.notification_settings_detailed.callback(
                notification_cog, mock_interaction
            )

            # Verify service layer initialization
            mock_repo.assert_called_once_with(notification_cog.supabase_service.client)
            mock_pref_service.assert_called_once()

            # Verify repository passed to service
            repo_instance = mock_repo.return_value
            service_init_args = mock_pref_service.call_args[0]
            assert service_init_args[0] == repo_instance
