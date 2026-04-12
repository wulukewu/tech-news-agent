"""
Unit tests for /add_feed command (Task 2.2).
Tests the add_feed command in SubscriptionCommands cog.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.core.exceptions import SupabaseServiceError


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    return Mock()


@pytest.fixture
def subscription_cog(mock_bot):
    """Create a SubscriptionCommands cog instance."""
    return SubscriptionCommands(mock_bot)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = Mock()
    interaction.user.id = 123456789
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_add_feed_new_feed_new_subscription(subscription_cog, mock_interaction):
    """
    Test /add_feed with a new feed and new subscription.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4
    """
    # Arrange
    user_uuid = uuid4()
    feed_id = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock feed doesn't exist
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )

        # Mock feed creation
        mock_service.client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{"id": str(feed_id)}]
        )

        # Mock subscription
        mock_service.subscribe_to_feed = AsyncMock()

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
        mock_ensure_user.assert_called_once_with(mock_interaction)
        mock_service._validate_url.assert_called_once_with("https://example.com/feed.xml")
        mock_service.subscribe_to_feed.assert_called_once_with("123456789", feed_id)

        # Verify confirmation message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "Test Feed" in call_args[0][0]
        assert "AI" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_existing_feed_new_subscription(subscription_cog, mock_interaction):
    """
    Test /add_feed with an existing feed and new subscription.

    Validates: Requirements 2.2, 2.3, 2.4
    """
    # Arrange
    user_uuid = uuid4()
    feed_id = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock feed exists
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": str(feed_id)}]
        )

        # Mock subscription
        mock_service.subscribe_to_feed = AsyncMock()

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Existing Feed",
            url="https://example.com/feed.xml",
            category="Web",
        )

        # Assert
        mock_service.subscribe_to_feed.assert_called_once_with("123456789", feed_id)

        # Verify confirmation message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "Existing Feed" in call_args[0][0]


@pytest.mark.asyncio
async def test_add_feed_invalid_url(subscription_cog, mock_interaction):
    """
    Test /add_feed with invalid URL format.

    Validates: Requirements 2.7
    """
    # Arrange
    user_uuid = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(side_effect=ValueError("Invalid URL format"))

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog, mock_interaction, name="Test Feed", url="invalid-url", category="AI"
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "URL 格式無效" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_duplicate_subscription(subscription_cog, mock_interaction):
    """
    Test /add_feed with duplicate subscription (user already subscribed).

    Validates: Requirements 2.5
    """
    # Arrange
    user_uuid = uuid4()
    feed_id = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock feed exists
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": str(feed_id)}]
        )

        # Mock duplicate subscription error
        mock_service.subscribe_to_feed = AsyncMock(
            side_effect=SupabaseServiceError("Duplicate entry: already exists")
        )

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "ℹ️" in call_args[0][0]
        assert "已經訂閱過" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_database_error(subscription_cog, mock_interaction):
    """
    Test /add_feed with database error.

    Validates: Requirements 2.8
    """
    # Arrange
    user_uuid = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock database error
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.side_effect = SupabaseServiceError(
            "Database connection failed"
        )

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "訂閱失敗" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_user_registration_error(subscription_cog, mock_interaction):
    """
    Test /add_feed when user registration fails.

    Validates: Requirements 2.1
    """
    # Arrange
    with patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user:
        mock_ensure_user.side_effect = SupabaseServiceError("User registration failed")

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_feed_creation_failure(subscription_cog, mock_interaction):
    """
    Test /add_feed when feed creation fails (no data returned).

    Validates: Requirements 2.3
    """
    # Arrange
    user_uuid = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock feed doesn't exist
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )

        # Mock feed creation failure (no data returned)
        mock_service.client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[]
        )

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_validates_url_before_database_operations(
    subscription_cog, mock_interaction
):
    """
    Test /add_feed validates URL before performing database operations.

    Validates: Requirements 2.7
    """
    # Arrange
    user_uuid = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(side_effect=ValueError("Invalid URL"))

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog, mock_interaction, name="Test Feed", url="not-a-url", category="AI"
        )

        # Assert
        # Verify URL validation was called
        mock_service._validate_url.assert_called_once_with("not-a-url")

        # Verify no database operations were performed
        mock_service.client.table.assert_not_called()


@pytest.mark.asyncio
async def test_add_feed_sends_confirmation_with_feed_details(subscription_cog, mock_interaction):
    """
    Test /add_feed sends confirmation message with feed details.

    Validates: Requirements 2.8
    """
    # Arrange
    user_uuid = uuid4()
    feed_id = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(return_value="https://example.com/feed.xml")

        # Mock feed exists
        mock_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": str(feed_id)}]
        )

        mock_service.subscribe_to_feed = AsyncMock()

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Tech News",
            url="https://example.com/feed.xml",
            category="Technology",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]

        # Verify message contains all required details
        assert "✅" in message
        assert "Tech News" in message
        assert "Technology" in message
        assert "https://example.com/feed.xml" in message
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_add_feed_unexpected_error(subscription_cog, mock_interaction):
    """
    Test /add_feed handles unexpected errors gracefully.

    Validates: Requirements 2.8
    """
    # Arrange
    user_uuid = uuid4()

    with (
        patch("app.bot.cogs.subscription_commands.ensure_user_registered") as mock_ensure_user,
        patch("app.bot.cogs.subscription_commands.SupabaseService") as MockSupabaseService,
    ):
        mock_ensure_user.return_value = user_uuid

        mock_service = MockSupabaseService.return_value
        mock_service._validate_url = Mock(side_effect=RuntimeError("Unexpected error"))

        # Act
        await subscription_cog.add_feed.callback(
            subscription_cog,
            mock_interaction,
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="AI",
        )

        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "未預期的錯誤" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
