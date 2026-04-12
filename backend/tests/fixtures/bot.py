"""
Discord bot-related test fixtures.

Provides fixtures for Discord bot testing, including mock Discord clients and contexts.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_discord_bot():
    """Mock Discord bot client for testing."""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 987654321
    bot.user.name = "TestBot"
    bot.get_user = AsyncMock(return_value=None)
    bot.fetch_user = AsyncMock(return_value=None)

    return bot


@pytest.fixture
def mock_discord_context():
    """Mock Discord command context for testing."""
    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 123456789
    ctx.author.name = "testuser"
    ctx.guild = MagicMock()
    ctx.guild.id = 111222333
    ctx.channel = MagicMock()
    ctx.send = AsyncMock()
    ctx.reply = AsyncMock()

    return ctx


@pytest.fixture
def mock_discord_interaction():
    """Mock Discord interaction for testing buttons and modals."""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.user.name = "testuser"
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    return interaction
