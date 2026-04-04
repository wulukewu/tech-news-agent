"""
Tests for /unsubscribe_feed command.

Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.schemas.article import Subscription
from app.core.exceptions import SupabaseServiceError


@pytest.fixture
def subscription_cog():
    """Create a SubscriptionCommands cog instance for testing."""
    bot = MagicMock()
    return SubscriptionCommands(bot)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock()
    interaction.user.id = "123456789"
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_unsubscribe_feed_by_name(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed with feed name.
    
    Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6
    """
    # Arrange
    feed_id = uuid4()
    subscriptions = [
        Subscription(
            feed_id=feed_id,
            name="Tech News",
            url="https://example.com/feed",
            category="Technology",
            subscribed_at=datetime.now(timezone.utc)
        )
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        mock_service.unsubscribe_from_feed = AsyncMock()
        
        # Act
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            "Tech News"
        )
        
        # Assert
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
        mock_ensure_user.assert_called_once_with(mock_interaction)
        mock_service.get_user_subscriptions.assert_called_once_with("123456789")
        mock_service.unsubscribe_from_feed.assert_called_once_with("123456789", feed_id)
        
        # Verify confirmation message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "Tech News" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_unsubscribe_feed_by_uuid(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed with feed UUID.
    
    Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6
    """
    # Arrange
    feed_id = uuid4()
    subscriptions = [
        Subscription(
            feed_id=feed_id,
            name="Tech News",
            url="https://example.com/feed",
            category="Technology",
            subscribed_at=datetime.now(timezone.utc)
        )
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        mock_service.unsubscribe_from_feed = AsyncMock()
        
        # Act
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            str(feed_id)
        )
        
        # Assert
        mock_service.unsubscribe_from_feed.assert_called_once_with("123456789", feed_id)
        
        # Verify confirmation message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "Tech News" in call_args[0][0]


@pytest.mark.asyncio
async def test_unsubscribe_feed_not_found(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed with non-existent feed.
    
    Validates: Requirements 11.4
    """
    # Arrange
    subscriptions = [
        Subscription(
            feed_id=uuid4(),
            name="Tech News",
            url="https://example.com/feed",
            category="Technology",
            subscribed_at=datetime.now(timezone.utc)
        )
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        mock_service.unsubscribe_from_feed = AsyncMock()
        
        # Act
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            "Non-existent Feed"
        )
        
        # Assert
        mock_service.unsubscribe_from_feed.assert_not_called()
        
        # Verify error message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "找不到訂閱源" in call_args[0][0]
        assert "Non-existent Feed" in call_args[0][0]


@pytest.mark.asyncio
async def test_unsubscribe_feed_no_subscriptions(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed when user has no subscriptions.
    
    Validates: Requirements 11.4
    """
    # Arrange
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=[])
        mock_service.unsubscribe_from_feed = AsyncMock()
        
        # Act
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            "Tech News"
        )
        
        # Assert
        mock_service.unsubscribe_from_feed.assert_not_called()
        
        # Verify message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "📭" in call_args[0][0]
        assert "還沒有訂閱" in call_args[0][0]


@pytest.mark.asyncio
async def test_unsubscribe_feed_database_error(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed handles database errors gracefully.
    
    Validates: Requirements 11.5
    """
    # Arrange
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )
        
        # Act
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            "Tech News"
        )
        
        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "取消訂閱失敗" in call_args[0][0]


@pytest.mark.asyncio
async def test_unsubscribe_feed_case_insensitive(subscription_cog, mock_interaction):
    """
    Test /unsubscribe_feed matches feed name case-insensitively.
    
    Validates: Requirements 11.2
    """
    # Arrange
    feed_id = uuid4()
    subscriptions = [
        Subscription(
            feed_id=feed_id,
            name="Tech News",
            url="https://example.com/feed",
            category="Technology",
            subscribed_at=datetime.now(timezone.utc)
        )
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered', new_callable=AsyncMock) as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = uuid4()
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        mock_service.unsubscribe_from_feed = AsyncMock()
        
        # Act - use different case
        await subscription_cog.unsubscribe_feed.callback(
            subscription_cog,
            mock_interaction,
            "TECH NEWS"
        )
        
        # Assert
        mock_service.unsubscribe_from_feed.assert_called_once_with("123456789", feed_id)
        
        # Verify confirmation message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
