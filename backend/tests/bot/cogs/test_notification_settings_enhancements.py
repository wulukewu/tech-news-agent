from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import discord
import pytest

from app.bot.client import TechNewsBot
from app.bot.cogs.thread_qa_listener import ThreadQAListener
from app.bot.ui.modals import SetNotificationTimeModal


@pytest.mark.asyncio
async def test_set_notification_time_modal_validation():
    """Test modal validation for invalid time format."""
    mock_supabase = AsyncMock()
    modal = SetNotificationTimeModal(mock_supabase)

    mock_interaction = AsyncMock(spec=discord.Interaction)
    mock_interaction.user.id = 123456789
    mock_interaction.response.send_message = AsyncMock()

    # Test invalid time format
    modal.notification_time = MagicMock(value="99:99")
    await modal.on_submit(mock_interaction)

    mock_interaction.response.send_message.assert_called_once_with(
        "❌ 通知時間格式錯誤，請使用 HH:MM（例如 09:30）", ephemeral=True
    )


@pytest.mark.asyncio
async def test_set_notification_time_modal_submit():
    """Test modal submit with valid time format."""
    mock_supabase = AsyncMock()
    mock_supabase.get_or_create_user.return_value = uuid4()

    modal = SetNotificationTimeModal(mock_supabase)
    modal.notification_time = MagicMock(value="08:30")

    mock_interaction = AsyncMock(spec=discord.Interaction)
    mock_interaction.user.id = 123456789
    mock_interaction.response.send_message = AsyncMock()
    mock_interaction.followup.send = AsyncMock()

    with (
        patch(
            "app.repositories.user_notification_preferences.UserNotificationPreferencesRepository"
        ) as mock_repo_class,
        patch("app.services.preference_service.PreferenceService") as mock_service_class,
        patch(
            "app.bot.cogs.notification_settings.NotificationSettingsControlView"
        ) as mock_view_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = AsyncMock()
        mock_service.update_preferences.return_value = AsyncMock()
        mock_service.get_user_preferences.return_value = MagicMock(dm_enabled=True)
        mock_service_class.return_value = mock_service

        mock_view = AsyncMock()
        mock_view_class.return_value = mock_view

        await modal.on_submit(mock_interaction)

        # Verify preferences updated
        mock_service.update_preferences.assert_called_once()

        # Verify success message sent
        mock_interaction.followup.send.assert_called_once()

        # Verify dashboard refreshed
        mock_view._refresh_dashboard.assert_called_once()


@pytest.mark.asyncio
async def test_client_dev_guild_isolation_local():
    """Test local dev bot ignores interactions outside dev_guild_id."""
    bot = TechNewsBot()

    mock_settings = MagicMock()
    mock_settings.enable_dm_listener = False
    mock_settings.dev_guild_id = 9999

    mock_interaction = AsyncMock(spec=discord.Interaction)
    mock_interaction.guild_id = 1111  # Different guild
    mock_interaction.type = discord.InteractionType.component

    with patch("app.core.config.get_settings", return_value=mock_settings):
        # We need to mock super().on_interaction to verify if it was called
        with patch(
            "discord.Client.on_interaction", create=True, new_callable=AsyncMock
        ) as mock_super_on_interaction:
            await bot.on_interaction(mock_interaction)
            mock_super_on_interaction.assert_not_called()


@pytest.mark.asyncio
async def test_client_dev_guild_isolation_production():
    """Test production bot ignores interactions from dev_guild_id."""
    bot = TechNewsBot()

    mock_settings = MagicMock()
    mock_settings.enable_dm_listener = True
    mock_settings.dev_guild_id = 9999

    mock_interaction = AsyncMock(spec=discord.Interaction)
    mock_interaction.guild_id = 9999  # Dev guild
    mock_interaction.type = discord.InteractionType.component

    with patch("app.core.config.get_settings", return_value=mock_settings):
        with patch(
            "discord.Client.on_interaction", create=True, new_callable=AsyncMock
        ) as mock_super_on_interaction:
            await bot.on_interaction(mock_interaction)
            mock_super_on_interaction.assert_not_called()


@pytest.mark.asyncio
async def test_thread_qa_listener_isolation():
    """Test ThreadQAListener ignores thread messages in dev guild in production."""
    bot = MagicMock()
    with patch("app.services.thread_memory_service.LLMService") as mock_llm:
        listener = ThreadQAListener(bot)

    mock_settings = MagicMock()
    mock_settings.dev_guild_id = 9999

    mock_message = MagicMock(spec=discord.Message)
    mock_message.author.bot = False
    mock_message.channel = MagicMock(spec=discord.Thread)
    mock_message.guild.id = 9999  # Dev guild
    mock_message.content = "How does this work?"

    with patch("app.core.config.get_settings", return_value=mock_settings):
        # If it returns early, it won't query database or do anything
        with patch.object(
            listener.supabase_service, "get_user_by_discord_id", new_callable=AsyncMock
        ) as mock_get_user:
            await listener.on_message(mock_message)
            mock_get_user.assert_not_called()
