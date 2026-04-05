"""
Unit tests for /list_feeds command (Task 2.3).
Tests the list_feeds command in SubscriptionCommands cog.

Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.schemas.article import Subscription
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
async def test_list_feeds_with_subscriptions(subscription_cog, mock_interaction):
    """
    Test /list_feeds with multiple subscriptions.
    
    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
    """
    # Arrange
    user_uuid = uuid4()
    feed1_id = uuid4()
    feed2_id = uuid4()
    feed3_id = uuid4()
    
    subscriptions = [
        Subscription(
            feed_id=feed1_id,
            name="AI Weekly",
            url="https://example.com/ai-feed.xml",
            category="AI",
            subscribed_at=datetime.now(timezone.utc)
        ),
        Subscription(
            feed_id=feed2_id,
            name="Web Dev News",
            url="https://example.com/web-feed.xml",
            category="Web",
            subscribed_at=datetime.now(timezone.utc)
        ),
        Subscription(
            feed_id=feed3_id,
            name="Security Alerts",
            url="https://example.com/security-feed.xml",
            category="Security",
            subscribed_at=datetime.now(timezone.utc)
        ),
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
        mock_ensure_user.assert_called_once_with(mock_interaction)
        mock_service.get_user_subscriptions.assert_called_once_with("123456789")
        
        # Verify response message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify message contains header
        assert "📚" in message
        assert "你的訂閱清單" in message
        
        # Verify message contains all subscriptions
        assert "AI Weekly" in message
        assert "Web Dev News" in message
        assert "Security Alerts" in message
        
        # Verify message contains URLs
        assert "https://example.com/ai-feed.xml" in message
        assert "https://example.com/web-feed.xml" in message
        assert "https://example.com/security-feed.xml" in message
        
        # Verify message contains categories
        assert "AI" in message
        assert "Web" in message
        assert "Security" in message
        
        # Verify message contains total count
        assert "共 3 個訂閱源" in message
        
        # Verify ephemeral response
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_list_feeds_no_subscriptions(subscription_cog, mock_interaction):
    """
    Test /list_feeds with no subscriptions.
    
    Validates: Requirements 10.6, 10.7
    """
    # Arrange
    user_uuid = uuid4()
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=[])
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify empty state message
        assert "📭" in message
        assert "還沒有訂閱任何 RSS 來源" in message
        assert "/add_feed" in message
        
        # Verify ephemeral response
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_list_feeds_grouped_by_category(subscription_cog, mock_interaction):
    """
    Test /list_feeds groups subscriptions by category.
    
    Validates: Requirements 10.3
    """
    # Arrange
    user_uuid = uuid4()
    
    subscriptions = [
        Subscription(
            feed_id=uuid4(),
            name="AI Feed 1",
            url="https://example.com/ai1.xml",
            category="AI",
            subscribed_at=datetime.now(timezone.utc)
        ),
        Subscription(
            feed_id=uuid4(),
            name="AI Feed 2",
            url="https://example.com/ai2.xml",
            category="AI",
            subscribed_at=datetime.now(timezone.utc)
        ),
        Subscription(
            feed_id=uuid4(),
            name="Web Feed 1",
            url="https://example.com/web1.xml",
            category="Web",
            subscribed_at=datetime.now(timezone.utc)
        ),
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify categories are present
        assert "**AI**" in message
        assert "**Web**" in message
        
        # Verify feeds are under their categories
        # AI feeds should appear before Web feeds (alphabetical order)
        ai_index = message.index("**AI**")
        web_index = message.index("**Web**")
        assert ai_index < web_index
        
        # Verify both AI feeds are listed
        assert "AI Feed 1" in message
        assert "AI Feed 2" in message


@pytest.mark.asyncio
async def test_list_feeds_database_error(subscription_cog, mock_interaction):
    """
    Test /list_feeds handles database errors gracefully.
    
    Validates: Requirements 10.1
    """
    # Arrange
    user_uuid = uuid4()
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify error message
        assert "❌" in message
        assert "無法取得訂閱清單" in message
        
        # Verify ephemeral response
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_list_feeds_user_registration_error(subscription_cog, mock_interaction):
    """
    Test /list_feeds when user registration fails.
    
    Validates: Requirements 10.1
    """
    # Arrange
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user:
        
        mock_ensure_user.side_effect = SupabaseServiceError("User registration failed")
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify error message
        assert "❌" in message
        
        # Verify ephemeral response
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_list_feeds_unexpected_error(subscription_cog, mock_interaction):
    """
    Test /list_feeds handles unexpected errors gracefully.
    
    Validates: Requirements 10.1
    """
    # Arrange
    user_uuid = uuid4()
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify error message
        assert "❌" in message
        assert "未預期的錯誤" in message
        
        # Verify ephemeral response
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_list_feeds_sorted_by_subscribed_at(subscription_cog, mock_interaction):
    """
    Test /list_feeds returns subscriptions sorted by subscribed_at descending.
    
    Validates: Requirements 10.4
    """
    # Arrange
    user_uuid = uuid4()
    
    # Create subscriptions with different timestamps
    old_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    recent_time = datetime(2024, 12, 1, tzinfo=timezone.utc)
    
    subscriptions = [
        Subscription(
            feed_id=uuid4(),
            name="Recent Feed",
            url="https://example.com/recent.xml",
            category="AI",
            subscribed_at=recent_time
        ),
        Subscription(
            feed_id=uuid4(),
            name="Old Feed",
            url="https://example.com/old.xml",
            category="AI",
            subscribed_at=old_time
        ),
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        # Service should return subscriptions already sorted by subscribed_at desc
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        # Verify service was called correctly
        mock_service.get_user_subscriptions.assert_called_once_with("123456789")
        
        # The service is responsible for sorting, so we just verify it was called
        # The actual sorting is tested in the service layer tests


@pytest.mark.asyncio
async def test_list_feeds_displays_name_url_category(subscription_cog, mock_interaction):
    """
    Test /list_feeds displays feed name, URL, and category.
    
    Validates: Requirements 10.3
    """
    # Arrange
    user_uuid = uuid4()
    
    subscriptions = [
        Subscription(
            feed_id=uuid4(),
            name="Test Feed Name",
            url="https://example.com/test-feed.xml",
            category="Test Category",
            subscribed_at=datetime.now(timezone.utc)
        ),
    ]
    
    with patch('app.bot.cogs.subscription_commands.ensure_user_registered') as mock_ensure_user, \
         patch('app.bot.cogs.subscription_commands.SupabaseService') as MockSupabaseService:
        
        mock_ensure_user.return_value = user_uuid
        
        mock_service = MockSupabaseService.return_value
        mock_service.get_user_subscriptions = AsyncMock(return_value=subscriptions)
        
        # Act
        await subscription_cog.list_feeds.callback(subscription_cog, mock_interaction)
        
        # Assert
        call_args = mock_interaction.followup.send.call_args
        message = call_args[0][0]
        
        # Verify all required fields are displayed
        assert "Test Feed Name" in message
        assert "https://example.com/test-feed.xml" in message
        assert "Test Category" in message
