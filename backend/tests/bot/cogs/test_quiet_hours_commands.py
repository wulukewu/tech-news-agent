"""
Unit tests for Discord quiet hours commands

Tests the Discord slash commands for managing quiet hours settings.
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import discord
import pytest

from app.bot.cogs.quiet_hours_settings import QuietHoursSettings as QuietHoursSettingsCog
from app.services.quiet_hours_service import QuietHoursSettings

# pytestmark = pytest.mark.skip(
#     reason="NotificationSettings does not have set_quiet_hours (moved to QuietHoursSettings)"
# )


class TestQuietHoursCommands:
    """Test Discord quiet hours commands."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock Discord bot."""
        return Mock(spec=discord.ext.commands.Bot)

    @pytest.fixture
    def mock_supabase_service(self):
        """Create mock SupabaseService."""
        mock_service = AsyncMock()
        mock_service.get_or_create_user = AsyncMock(return_value=uuid4())
        return mock_service

    @pytest.fixture
    def cog(self, mock_bot, mock_supabase_service):
        """Create QuietHoursSettings cog with mocked dependencies."""
        return QuietHoursSettingsCog(mock_bot, mock_supabase_service)

    @pytest.fixture
    def mock_interaction(self):
        """Create mock Discord interaction."""
        interaction = Mock(spec=discord.Interaction)
        interaction.user = Mock()
        interaction.user.id = 123456789
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()
        return interaction

    @pytest.fixture
    def sample_quiet_hours(self):
        """Sample quiet hours settings."""
        return QuietHoursSettings(
            id=uuid4(),
            user_id=uuid4(),
            start_time=time(22, 0),
            end_time=time(8, 0),
            timezone="Asia/Taipei",
            weekdays=[1, 2, 3, 4, 5, 6, 7],
            enabled=True,
        )

    @pytest.mark.asyncio
    async def test_quiet_hours_command_with_existing_settings(
        self, cog, mock_interaction, sample_quiet_hours
    ):
        """Test /quiet-hours command with existing settings."""
        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(return_value=sample_quiet_hours)
            mock_service.is_in_quiet_hours = AsyncMock(return_value=(False, sample_quiet_hours))
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.quiet_hours.callback(cog, mock_interaction)

            # Verify interaction
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_interaction.followup.send.assert_called_once()

            # Verify service calls
            mock_service.get_quiet_hours.assert_called_once()
            mock_service.is_in_quiet_hours.assert_called_once()

            # Check embed content
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]
            assert embed.title == "🌙 勿擾時段設定"
            assert "目前不在勿擾時段內" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_quiet_hours_command_no_existing_settings(self, cog, mock_interaction):
        """Test /quiet-hours command with no existing settings."""
        default_quiet_hours = QuietHoursSettings(
            id=uuid4(),
            user_id=uuid4(),
            start_time=time(22, 0),
            end_time=time(8, 0),
            timezone="UTC",
            weekdays=[1, 2, 3, 4, 5, 6, 7],
            enabled=False,
        )

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(return_value=None)
            mock_service.create_default_quiet_hours = AsyncMock(return_value=default_quiet_hours)
            mock_service.is_in_quiet_hours = AsyncMock(return_value=(False, default_quiet_hours))
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.quiet_hours.callback(cog, mock_interaction)

            # Verify service calls
            mock_service.get_quiet_hours.assert_called_once()
            mock_service.create_default_quiet_hours.assert_called_once()
            mock_service.is_in_quiet_hours.assert_called_once()

            # Verify response
            mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_quiet_hours_command_modal(self, cog, mock_interaction):
        """Test /set-quiet-hours command sends the modal."""
        mock_interaction.response.send_modal = AsyncMock()
        await cog.set_quiet_hours.callback(cog, mock_interaction)
        mock_interaction.response.send_modal.assert_called_once()
        modal = mock_interaction.response.send_modal.call_args[0][0]
        from app.bot.ui.modals import SetQuietHoursModal

        assert isinstance(modal, SetQuietHoursModal)

    @pytest.mark.asyncio
    async def test_set_quiet_hours_modal_validation_errors(self, mock_supabase_service):
        """Test modal validation for invalid inputs."""
        from app.bot.ui.modals import SetQuietHoursModal

        modal = SetQuietHoursModal(mock_supabase_service)

        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_interaction.user.id = 123456789
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()

        # Test invalid start time format
        modal.start_time = MagicMock(value="25:00")
        modal.end_time = MagicMock(value="08:00")
        modal.enabled = MagicMock(value="yes")
        await modal.on_submit(mock_interaction)
        mock_interaction.followup.send.assert_called_once_with(
            "❌ 開始時間格式錯誤，請使用 HH:MM（例如 22:00）", ephemeral=True
        )

        # Test invalid end time format
        mock_interaction.followup.send.reset_mock()
        modal.start_time = MagicMock(value="22:00")
        modal.end_time = MagicMock(value="invalid")
        modal.enabled = MagicMock(value="yes")
        await modal.on_submit(mock_interaction)
        mock_interaction.followup.send.assert_called_once_with(
            "❌ 結束時間格式錯誤，請使用 HH:MM（例如 08:00）", ephemeral=True
        )

        # Test invalid enabled format
        mock_interaction.followup.send.reset_mock()
        modal.start_time = MagicMock(value="22:00")
        modal.end_time = MagicMock(value="08:00")
        modal.enabled = MagicMock(value="invalid")
        await modal.on_submit(mock_interaction)
        mock_interaction.followup.send.assert_called_once_with("❌ 啟用欄位請填 yes 或 no", ephemeral=True)

    @pytest.mark.asyncio
    async def test_set_quiet_hours_modal_submit_success(
        self, mock_supabase_service, sample_quiet_hours
    ):
        """Test modal submit success with valid inputs."""
        from app.bot.ui.modals import SetQuietHoursModal

        modal = SetQuietHoursModal(mock_supabase_service)

        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_interaction.user.id = 123456789
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()

        modal.start_time = MagicMock(value="22:00")
        modal.end_time = MagicMock(value="08:00")
        modal.enabled = MagicMock(value="yes")

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_quiet_hours.return_value = sample_quiet_hours
            mock_service_class.return_value = mock_service

            await modal.on_submit(mock_interaction)

            mock_service.update_quiet_hours.assert_called_once_with(
                user_id=mock_supabase_service.get_or_create_user.return_value,
                start_time=time(22, 0),
                end_time=time(8, 0),
                enabled=True,
            )
            mock_interaction.followup.send.assert_called_once()
            embed = mock_interaction.followup.send.call_args[1]["embed"]
            assert embed.title == "🌙 勿擾時段已更新"

    @pytest.mark.asyncio
    async def test_set_quiet_hours_modal_submit_error(self, mock_supabase_service):
        """Test modal submit service error handling."""
        from app.bot.ui.modals import SetQuietHoursModal

        modal = SetQuietHoursModal(mock_supabase_service)

        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_interaction.user.id = 123456789
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()

        modal.start_time = MagicMock(value="22:00")
        modal.end_time = MagicMock(value="08:00")
        modal.enabled = MagicMock(value="yes")

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_quiet_hours.side_effect = Exception("Service error")
            mock_service_class.return_value = mock_service

            await modal.on_submit(mock_interaction)

            mock_interaction.followup.send.assert_called_once_with("❌ 設定失敗，請稍後再試。", ephemeral=True)

    @pytest.mark.asyncio
    async def test_toggle_quiet_hours_command_enable(
        self, cog, mock_interaction, sample_quiet_hours
    ):
        """Test /toggle-quiet-hours command to enable quiet hours."""
        # Start with disabled quiet hours
        disabled_quiet_hours = QuietHoursSettings(
            id=sample_quiet_hours.id,
            user_id=sample_quiet_hours.user_id,
            start_time=sample_quiet_hours.start_time,
            end_time=sample_quiet_hours.end_time,
            timezone=sample_quiet_hours.timezone,
            weekdays=sample_quiet_hours.weekdays,
            enabled=False,
        )

        # After toggle, enabled
        enabled_quiet_hours = QuietHoursSettings(
            id=sample_quiet_hours.id,
            user_id=sample_quiet_hours.user_id,
            start_time=sample_quiet_hours.start_time,
            end_time=sample_quiet_hours.end_time,
            timezone=sample_quiet_hours.timezone,
            weekdays=sample_quiet_hours.weekdays,
            enabled=True,
        )

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(return_value=disabled_quiet_hours)
            mock_service.update_quiet_hours = AsyncMock(return_value=enabled_quiet_hours)
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.toggle_quiet_hours.callback(cog, mock_interaction)

            # Verify service calls
            mock_service.get_quiet_hours.assert_called_once()
            mock_service.update_quiet_hours.assert_called_once()

            # Verify update call with enabled=True
            call_args = mock_service.update_quiet_hours.call_args
            assert call_args[1]["enabled"] is True

            # Verify response
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]
            assert embed.title == "🌙 勿擾時段狀態已切換"
            assert "✅ 已啟用" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_toggle_quiet_hours_command_disable(
        self, cog, mock_interaction, sample_quiet_hours
    ):
        """Test /toggle-quiet-hours command to disable quiet hours."""
        # After toggle, disabled
        disabled_quiet_hours = QuietHoursSettings(
            id=sample_quiet_hours.id,
            user_id=sample_quiet_hours.user_id,
            start_time=sample_quiet_hours.start_time,
            end_time=sample_quiet_hours.end_time,
            timezone=sample_quiet_hours.timezone,
            weekdays=sample_quiet_hours.weekdays,
            enabled=False,
        )

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(
                return_value=sample_quiet_hours
            )  # Initially enabled
            mock_service.update_quiet_hours = AsyncMock(return_value=disabled_quiet_hours)
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.toggle_quiet_hours.callback(cog, mock_interaction)

            # Verify update call with enabled=False
            call_args = mock_service.update_quiet_hours.call_args
            assert call_args[1]["enabled"] is False

            # Verify response
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]["embed"]
            assert "❌ 已停用" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_toggle_quiet_hours_command_no_existing_settings(self, cog, mock_interaction):
        """Test /toggle-quiet-hours command with no existing settings."""
        default_quiet_hours = QuietHoursSettings(
            id=uuid4(),
            user_id=uuid4(),
            start_time=time(22, 0),
            end_time=time(8, 0),
            timezone="UTC",
            weekdays=[1, 2, 3, 4, 5, 6, 7],
            enabled=False,
        )

        enabled_quiet_hours = QuietHoursSettings(
            id=default_quiet_hours.id,
            user_id=default_quiet_hours.user_id,
            start_time=default_quiet_hours.start_time,
            end_time=default_quiet_hours.end_time,
            timezone=default_quiet_hours.timezone,
            weekdays=default_quiet_hours.weekdays,
            enabled=True,
        )

        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(return_value=None)
            mock_service.create_default_quiet_hours = AsyncMock(return_value=default_quiet_hours)
            mock_service.update_quiet_hours = AsyncMock(return_value=enabled_quiet_hours)
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.toggle_quiet_hours.callback(cog, mock_interaction)

            # Verify service calls
            mock_service.get_quiet_hours.assert_called_once()
            mock_service.create_default_quiet_hours.assert_called_once()
            mock_service.update_quiet_hours.assert_called_once()

    @pytest.mark.asyncio
    async def test_quiet_hours_command_error_handling(self, cog, mock_interaction):
        """Test error handling in quiet hours commands."""
        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service to raise exception
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(side_effect=Exception("Database error"))
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.quiet_hours.callback(cog, mock_interaction)

            # Verify error response
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args
            assert "❌ 載入勿擾時段設定時發生錯誤" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_toggle_quiet_hours_command_service_error(self, cog, mock_interaction):
        """Test error handling in toggle-quiet-hours command."""
        with patch("app.services.quiet_hours_service.QuietHoursService") as mock_service_class:
            # Setup mock service to raise exception
            mock_service = AsyncMock()
            mock_service.get_quiet_hours = AsyncMock(side_effect=Exception("Service error"))
            mock_service_class.return_value = mock_service

            # Execute command
            await cog.toggle_quiet_hours.callback(cog, mock_interaction)

            # Verify error response
            call_args = mock_interaction.followup.send.call_args
            assert "❌ 切換勿擾時段狀態時發生錯誤" in call_args[0][0]
