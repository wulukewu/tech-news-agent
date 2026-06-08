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


@pytest.mark.asyncio
async def test_qa_commands_ask_in_dm_channel():
    """Test /ask command when executed in a DM channel (no name attribute)."""
    from app.bot.cogs.qa_commands import QACommands

    bot = MagicMock()
    cog = QACommands(bot)

    mock_interaction = AsyncMock(spec=discord.Interaction)
    mock_interaction.user.id = 123456789
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.followup.send = AsyncMock()

    # Mock DM Channel
    mock_dm_channel = AsyncMock(spec=discord.DMChannel)
    mock_dm_channel.id = 987654321
    mock_dm_channel.send = AsyncMock()
    # Ensure DMChannel does NOT have a 'name' attribute
    if hasattr(mock_dm_channel, "name"):
        delattr(mock_dm_channel, "name")

    user_uuid = uuid4()

    with (
        patch(
            "app.bot.cogs.qa_commands.ensure_user_registered", return_value=user_uuid
        ) as mock_register,
        patch(
            "app.bot.cogs.qa_commands.ensure_discussion_thread",
            return_value=(mock_dm_channel, False),
        ) as mock_ensure_thread,
        patch("app.bot.cogs.qa_commands.ThreadMemoryService") as mock_memory_service_class,
    ):
        mock_memory_service = AsyncMock()
        mock_memory_service.process_thread_query.return_value = {
            "answer": "This is a test answer from AI assistant."
        }
        mock_memory_service_class.return_value = mock_memory_service

        await cog.ask.callback(cog, mock_interaction, "hello")

        # Verify registration and thread utilities were called
        mock_register.assert_called_once_with(mock_interaction)
        mock_ensure_thread.assert_called_once_with(
            interaction=mock_interaction,
            thread_name="ask-hello",
        )

        # Verify thread.send was called
        mock_dm_channel.send.assert_any_call("❓ **問題**：hello")
        mock_dm_channel.send.assert_any_call("This is a test answer from AI assistant.")

        # Verify followup.send was called
        mock_interaction.followup.send.assert_called_once_with("✅ 已在此討論串處理你的問題。", ephemeral=True)

        # Verify process_thread_query was called with correct title fallback (Ask hello)
        mock_memory_service.process_thread_query.assert_called_once_with(
            user_id=str(user_uuid),
            thread_id=str(mock_dm_channel.id),
            query="hello",
            title="Ask hello",
        )
