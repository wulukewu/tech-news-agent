"""
Unit tests for /news_now command.

Tests cover:
- No subscriptions prompt
- No articles prompt
- Normal query and display
- Articles sorted by tinkering_index
- Article limit (20)
- Time window filter (7 days)
- No RSS fetching
- No LLM analysis
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord import app_commands

from app.bot.cogs.news_commands import NewsCommands, ensure_user_registered
from app.schemas.article import Subscription


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    bot = MagicMock(spec=discord.ext.commands.Bot)
    return bot


@pytest.fixture
def news_cog(mock_bot):
    """Create NewsCommands cog instance."""
    return NewsCommands(mock_bot)


@pytest.fixture
def sample_subscriptions():
    """Create sample subscription data."""
    feed_id = uuid4()
    return [
        Subscription(
            feed_id=feed_id,
            name="Test Feed",
            url="https://example.com/feed",
            category="AI",
            subscribed_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def sample_articles():
    """Create sample article data from database."""
    feed_id = uuid4()
    now = datetime.now(timezone.utc)
    
    return [
        {
            'id': str(uuid4()),
            'title': f'Article {i}',
            'url': f'https://example.com/article{i}',
            'category': 'AI' if i % 2 == 0 else 'Backend',
            'tinkering_index': 5 - (i % 5),  # Varying scores
            'ai_summary': f'Summary {i}',
            'published_at': (now - timedelta(days=i)).isoformat(),
            'feed_id': str(feed_id)
        }
        for i in range(25)  # More than 20 to test limit
    ]


class TestEnsureUserRegistered:
    """Tests for ensure_user_registered function."""
    
    @pytest.mark.asyncio
    async def test_registers_new_user(self, mock_interaction):
        """Test that new users are registered."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            
            result = await ensure_user_registered(mock_interaction)
            
            assert result == user_uuid
            mock_supabase.get_or_create_user.assert_called_once_with('123456789')
    
    @pytest.mark.asyncio
    async def test_returns_existing_user_uuid(self, mock_interaction):
        """Test that existing users return their UUID."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            
            # Call twice
            result1 = await ensure_user_registered(mock_interaction)
            result2 = await ensure_user_registered(mock_interaction)
            
            assert result1 == result2 == user_uuid


class TestNewsNowCommand:
    """Tests for /news_now command."""
    
    @pytest.mark.asyncio
    async def test_no_subscriptions_prompt(self, news_cog, mock_interaction):
        """Test that users with no subscriptions get prompted to subscribe."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=[])
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify defer was called
            mock_interaction.response.defer.assert_called_once_with(thinking=True)
            
            # Verify prompt message
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args[0][0]
            assert "還沒有訂閱任何 RSS 來源" in call_args
            assert "/add_feed" in call_args
    
    @pytest.mark.asyncio
    async def test_no_articles_prompt(self, news_cog, mock_interaction, sample_subscriptions):
        """Test that users with subscriptions but no articles get informed."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            # Mock empty article query result
            mock_response = MagicMock()
            mock_response.data = []
            mock_supabase.client.table.return_value.select.return_value.in_.return_value\
                .gte.return_value.not_.is_.return_value.order.return_value.limit.return_value\
                .execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify prompt message
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args[0][0]
            assert "最近 7 天沒有新文章" in call_args
            assert "背景排程器" in call_args
    
    @pytest.mark.asyncio
    async def test_normal_query_and_display(self, news_cog, mock_interaction, sample_subscriptions, sample_articles):
        """Test normal article query and display."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            # Mock article query result (limit to 20)
            mock_response = MagicMock()
            mock_response.data = sample_articles[:20]
            mock_supabase.client.table.return_value.select.return_value.in_.return_value\
                .gte.return_value.not_.is_.return_value.order.return_value.limit.return_value\
                .execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify followup was called with content and view
            mock_interaction.followup.send.assert_called_once()
            call_kwargs = mock_interaction.followup.send.call_args[1]
            
            # Check content
            content = call_kwargs['content']
            assert "個人化技術新聞" in content
            assert "找到 20 篇精選文章" in content
            
            # Check view was provided
            assert 'view' in call_kwargs
    
    @pytest.mark.asyncio
    async def test_articles_sorted_by_tinkering_index(self, news_cog, mock_interaction, sample_subscriptions):
        """Test that articles are sorted by tinkering_index descending."""
        user_uuid = uuid4()
        feed_id = uuid4()
        now = datetime.now(timezone.utc)
        
        # Create articles with specific tinkering_index values
        unsorted_articles = [
            {
                'id': str(uuid4()),
                'title': 'Low Priority',
                'url': 'https://example.com/low',
                'category': 'AI',
                'tinkering_index': 1,
                'ai_summary': 'Summary',
                'published_at': now.isoformat(),
                'feed_id': str(feed_id)
            },
            {
                'id': str(uuid4()),
                'title': 'High Priority',
                'url': 'https://example.com/high',
                'category': 'AI',
                'tinkering_index': 5,
                'ai_summary': 'Summary',
                'published_at': now.isoformat(),
                'feed_id': str(feed_id)
            },
            {
                'id': str(uuid4()),
                'title': 'Medium Priority',
                'url': 'https://example.com/medium',
                'category': 'AI',
                'tinkering_index': 3,
                'ai_summary': 'Summary',
                'published_at': now.isoformat(),
                'feed_id': str(feed_id)
            }
        ]
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            # Mock the query to return unsorted articles
            # In reality, database would sort, but we're testing the query construction
            mock_response = MagicMock()
            mock_response.data = unsorted_articles
            
            mock_table = mock_supabase.client.table.return_value
            mock_select = mock_table.select.return_value
            mock_in = mock_select.in_.return_value
            mock_gte = mock_in.gte.return_value
            mock_not = mock_gte.not_
            mock_is = mock_not.is_.return_value
            mock_order = mock_is.order.return_value
            mock_limit = mock_order.limit.return_value
            mock_limit.execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify order was called with correct parameters
            mock_is.order.assert_called_once_with('tinkering_index', desc=True)
    
    @pytest.mark.asyncio
    async def test_article_limit_20(self, news_cog, mock_interaction, sample_subscriptions, sample_articles):
        """Test that only 20 articles are returned."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            # Mock article query result
            mock_response = MagicMock()
            mock_response.data = sample_articles[:20]  # Database limits to 20
            
            mock_table = mock_supabase.client.table.return_value
            mock_select = mock_table.select.return_value
            mock_in = mock_select.in_.return_value
            mock_gte = mock_in.gte.return_value
            mock_not = mock_gte.not_
            mock_is = mock_not.is_.return_value
            mock_order = mock_is.order.return_value
            mock_limit = mock_order.limit.return_value
            mock_limit.execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify limit was called with 20
            mock_order.limit.assert_called_once_with(20)
            
            # Verify message shows 20 articles
            call_kwargs = mock_interaction.followup.send.call_args[1]
            content = call_kwargs['content']
            assert "20 篇" in content
    
    @pytest.mark.asyncio
    async def test_time_window_filter_7_days(self, news_cog, mock_interaction, sample_subscriptions):
        """Test that articles are filtered to last 7 days."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            mock_response = MagicMock()
            mock_response.data = []
            
            mock_table = mock_supabase.client.table.return_value
            mock_select = mock_table.select.return_value
            mock_in = mock_select.in_.return_value
            mock_gte = mock_in.gte.return_value
            mock_not = mock_gte.not_
            mock_is = mock_not.is_.return_value
            mock_order = mock_is.order.return_value
            mock_limit = mock_order.limit.return_value
            mock_limit.execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify gte was called with a timestamp from 7 days ago
            call_args = mock_in.gte.call_args
            assert call_args[0][0] == 'published_at'
            
            # The timestamp should be approximately 7 days ago
            timestamp_str = call_args[0][1]
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            seven_days_ago = now - timedelta(days=7)
            
            # Allow 1 minute tolerance for test execution time
            time_diff = abs((timestamp - seven_days_ago).total_seconds())
            assert time_diff < 60, f"Timestamp {timestamp} is not within 7 days ago"
    
    @pytest.mark.asyncio
    async def test_no_rss_fetching(self, news_cog, mock_interaction, sample_subscriptions, sample_articles):
        """Test that /news_now does NOT trigger RSS fetching."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase, \
             patch('app.bot.cogs.news_commands.RSSService') as MockRSS:
            
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            mock_response = MagicMock()
            mock_response.data = sample_articles[:20]
            mock_supabase.client.table.return_value.select.return_value.in_.return_value\
                .gte.return_value.not_.is_.return_value.order.return_value.limit.return_value\
                .execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify RSSService was never instantiated or called
            MockRSS.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_no_llm_analysis(self, news_cog, mock_interaction, sample_subscriptions, sample_articles):
        """Test that /news_now does NOT trigger LLM analysis."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase, \
             patch('app.bot.cogs.news_commands.LLMService') as MockLLM:
            
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            mock_response = MagicMock()
            mock_response.data = sample_articles[:20]
            mock_supabase.client.table.return_value.select.return_value.in_.return_value\
                .gte.return_value.not_.is_.return_value.order.return_value.limit.return_value\
                .execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify LLMService was never instantiated or called
            # (except for interactive components which may use it)
            # The command itself should not call LLM for batch analysis
            assert MockLLM.call_count == 0 or all(
                'evaluate_batch' not in str(call) for call in MockLLM.mock_calls
            )
    
    @pytest.mark.asyncio
    async def test_error_handling(self, news_cog, mock_interaction):
        """Test that errors are handled gracefully."""
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(side_effect=Exception("Database error"))
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify error message was sent
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args[0][0]
            assert "發生錯誤" in call_args
    
    @pytest.mark.asyncio
    async def test_filters_null_tinkering_index(self, news_cog, mock_interaction, sample_subscriptions):
        """Test that articles with NULL tinkering_index are filtered out."""
        user_uuid = uuid4()
        
        with patch('app.bot.cogs.news_commands.SupabaseService') as MockSupabase:
            mock_supabase = MockSupabase.return_value
            mock_supabase.get_or_create_user = AsyncMock(return_value=user_uuid)
            mock_supabase.get_user_subscriptions = AsyncMock(return_value=sample_subscriptions)
            
            mock_response = MagicMock()
            mock_response.data = []
            
            mock_table = mock_supabase.client.table.return_value
            mock_select = mock_table.select.return_value
            mock_in = mock_select.in_.return_value
            mock_gte = mock_in.gte.return_value
            mock_not = mock_gte.not_
            mock_is = mock_not.is_.return_value
            mock_order = mock_is.order.return_value
            mock_limit = mock_order.limit.return_value
            mock_limit.execute.return_value = mock_response
            
            await news_cog.news_now.callback(news_cog, mock_interaction)
            
            # Verify not_.is_ was called to filter NULL tinkering_index
            mock_not.is_.assert_called_once_with('tinkering_index', 'null')
