"""
Tests for Discord bot admin commands.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.name = "test_user"
    interaction.user.id = 123456789
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
class TestAdminCommands:
    """Test admin commands for scheduler management."""

    @patch("app.bot.cogs.admin_commands.background_fetch_job")
    async def test_trigger_fetch_command_success(self, mock_job, mock_interaction):
        """Test successful manual trigger via Discord command."""
        from discord.ext import commands

        from app.bot.cogs.admin_commands import AdminCommands

        # Create bot and cog
        bot = MagicMock(spec=commands.Bot)
        admin_cog = AdminCommands(bot)

        # Mock the background job
        mock_job.return_value = AsyncMock()

        # Execute command - call the callback directly
        await admin_cog.trigger_fetch.callback(admin_cog, mock_interaction)

        # Verify interaction was deferred
        mock_interaction.response.defer.assert_called_once()

        # Verify followup message was sent
        mock_interaction.followup.send.assert_called_once()

        # Verify embed was created with success message
        call_args = mock_interaction.followup.send.call_args
        embed = call_args.kwargs["embed"]
        assert "✅" in embed.title or "成功" in embed.title

    @patch("app.bot.cogs.admin_commands.get_scheduler_health")
    async def test_scheduler_status_command_healthy(self, mock_health, mock_interaction):
        """Test scheduler status command when scheduler is healthy."""
        from discord.ext import commands

        from app.bot.cogs.admin_commands import AdminCommands

        # Create bot and cog
        bot = MagicMock(spec=commands.Bot)
        admin_cog = AdminCommands(bot)

        # Mock healthy scheduler status
        mock_health.return_value = {
            "last_execution_time": "2024-01-01T12:00:00Z",
            "articles_processed": 25,
            "failed_operations": 2,
            "total_operations": 27,
            "is_healthy": True,
            "issues": [],
        }

        # Execute command - call the callback directly
        await admin_cog.scheduler_status.callback(admin_cog, mock_interaction)

        # Verify interaction was deferred
        mock_interaction.response.defer.assert_called_once()

        # Verify followup message was sent
        mock_interaction.followup.send.assert_called_once()

        # Verify embed shows healthy status
        call_args = mock_interaction.followup.send.call_args
        embed = call_args.kwargs["embed"]
        assert "✅" in embed.title or "正常" in embed.title

    @patch("app.bot.cogs.admin_commands.get_scheduler_health")
    async def test_scheduler_status_command_unhealthy(self, mock_health, mock_interaction):
        """Test scheduler status command when scheduler is unhealthy."""
        from discord.ext import commands

        from app.bot.cogs.admin_commands import AdminCommands

        # Create bot and cog
        bot = MagicMock(spec=commands.Bot)
        admin_cog = AdminCommands(bot)

        # Mock unhealthy scheduler status
        mock_health.return_value = {
            "last_execution_time": None,
            "articles_processed": 0,
            "failed_operations": 0,
            "total_operations": 0,
            "is_healthy": False,
            "issues": ["Scheduler has never executed"],
        }

        # Execute command - call the callback directly
        await admin_cog.scheduler_status.callback(admin_cog, mock_interaction)

        # Verify interaction was deferred
        mock_interaction.response.defer.assert_called_once()

        # Verify followup message was sent
        mock_interaction.followup.send.assert_called_once()

        # Verify embed shows unhealthy status
        call_args = mock_interaction.followup.send.call_args
        embed = call_args.kwargs["embed"]
        assert "⚠️" in embed.title or "異常" in embed.title
