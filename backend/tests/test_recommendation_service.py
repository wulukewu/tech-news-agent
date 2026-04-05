"""
Unit tests for RecommendationService

Tests the core functionality of the RecommendationService including:
- Getting recommended feeds sorted by priority
- Getting feeds by category
- Updating recommendation status
- Error handling

Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from app.services.recommendation_service import RecommendationService, RecommendationServiceError
from app.schemas.recommendation import RecommendedFeed, FeedsByCategoryResponse


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    return Mock()


@pytest.fixture
def recommendation_service(mock_supabase_client):
    """Create a RecommendationService instance with mock client"""
    return RecommendationService(mock_supabase_client)


@pytest.fixture
def sample_feed_data():
    """Sample feed data for testing"""
    return [
        {
            'id': str(uuid4()),
            'name': 'Hacker News',
            'url': 'https://news.ycombinator.com/rss',
            'category': 'Tech News',
            'description': '最熱門的科技新聞和討論',
            'is_recommended': True,
            'recommendation_priority': 100
        },
        {
            'id': str(uuid4()),
            'name': 'OpenAI Blog',
            'url': 'https://openai.com/blog/rss',
            'category': 'AI',
            'description': 'OpenAI 官方部落格',
            'is_recommended': True,
            'recommendation_priority': 95
        },
        {
            'id': str(uuid4()),
            'name': 'CSS Tricks',
            'url': 'https://css-tricks.com/feed',
            'category': 'Web Development',
            'description': 'CSS 和前端開發技巧',
            'is_recommended': True,
            'recommendation_priority': 90
        }
    ]


class TestGetRecommendedFeeds:
    """Tests for get_recommended_feeds method"""
    
    @pytest.mark.asyncio
    async def test_get_recommended_feeds_returns_sorted_by_priority(
        self,
        recommendation_service,
        mock_supabase_client,
        sample_feed_data
    ):
        """Test that recommended feeds are returned sorted by priority (highest first)"""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = sample_feed_data
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_recommended_feeds()
        
        # Verify
        assert len(result) == 3
        assert result[0].name == 'Hacker News'
        assert result[0].recommendation_priority == 100
        assert result[1].name == 'OpenAI Blog'
        assert result[1].recommendation_priority == 95
        assert result[2].name == 'CSS Tricks'
        assert result[2].recommendation_priority == 90
        
        # Verify correct query was made
        mock_supabase_client.table.assert_called_once_with('feeds')
        mock_table.eq.assert_called_once_with('is_recommended', True)
        mock_table.order.assert_called_once_with('recommendation_priority', desc=True)
    
    @pytest.mark.asyncio
    async def test_get_recommended_feeds_with_user_subscription_status(
        self,
        recommendation_service,
        mock_supabase_client,
        sample_feed_data
    ):
        """Test that subscription status is included when user_id is provided"""
        user_id = uuid4()
        subscribed_feed_id = UUID(sample_feed_data[0]['id'])
        
        # Setup mock response for feeds
        mock_feeds_response = Mock()
        mock_feeds_response.data = sample_feed_data
        
        # Setup mock response for subscriptions
        mock_subs_response = Mock()
        mock_subs_response.data = [{'feed_id': str(subscribed_feed_id)}]
        
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.order.return_value = mock_table
            
            if table_name == 'feeds':
                mock_table.execute.return_value = mock_feeds_response
            elif table_name == 'user_subscriptions':
                mock_table.execute.return_value = mock_subs_response
            
            return mock_table
        
        mock_supabase_client.table.side_effect = table_side_effect
        
        # Execute
        result = await recommendation_service.get_recommended_feeds(user_id=user_id)
        
        # Verify
        assert len(result) == 3
        assert result[0].is_subscribed is True  # First feed is subscribed
        assert result[1].is_subscribed is False
        assert result[2].is_subscribed is False
    
    @pytest.mark.asyncio
    async def test_get_recommended_feeds_returns_empty_list_when_none_found(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that empty list is returned when no recommended feeds exist"""
        # Setup mock response with no data
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_recommended_feeds()
        
        # Verify
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_recommended_feeds_handles_missing_optional_fields(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that feeds with missing optional fields are handled correctly"""
        # Feed data with missing description and default values
        feed_data = [{
            'id': str(uuid4()),
            'name': 'Test Feed',
            'url': 'https://test.com/rss',
            # Missing category, description
            'is_recommended': True,
            'recommendation_priority': 50
        }]
        
        mock_response = Mock()
        mock_response.data = feed_data
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_recommended_feeds()
        
        # Verify
        assert len(result) == 1
        assert result[0].category == 'Uncategorized'
        assert result[0].description is None
    
    @pytest.mark.asyncio
    async def test_get_recommended_feeds_raises_error_on_database_failure(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that database errors are properly handled"""
        # Setup mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.side_effect = Exception("Database connection failed")
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(RecommendationServiceError) as exc_info:
            await recommendation_service.get_recommended_feeds()
        
        assert "Failed to get recommended feeds" in str(exc_info.value)


class TestGetFeedsByCategory:
    """Tests for get_feeds_by_category method"""
    
    @pytest.mark.asyncio
    async def test_get_feeds_by_category_returns_feeds_in_category(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that feeds are filtered by category and sorted by priority"""
        category = 'AI'
        feed_data = [
            {
                'id': str(uuid4()),
                'name': 'OpenAI Blog',
                'url': 'https://openai.com/blog/rss',
                'category': 'AI',
                'description': 'OpenAI 官方部落格',
                'is_recommended': True,
                'recommendation_priority': 95
            },
            {
                'id': str(uuid4()),
                'name': 'DeepMind Blog',
                'url': 'https://deepmind.com/blog/rss',
                'category': 'AI',
                'description': 'DeepMind 研究部落格',
                'is_recommended': True,
                'recommendation_priority': 90
            }
        ]
        
        mock_response = Mock()
        mock_response.data = feed_data
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_feeds_by_category(category)
        
        # Verify
        assert result.category == 'AI'
        assert result.feed_count == 2
        assert len(result.feeds) == 2
        assert result.feeds[0].name == 'OpenAI Blog'
        assert result.feeds[1].name == 'DeepMind Blog'
        
        # Verify correct query
        mock_table.eq.assert_called_once_with('category', 'AI')
    
    @pytest.mark.asyncio
    async def test_get_feeds_by_category_returns_empty_when_no_feeds(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that empty response is returned when category has no feeds"""
        category = 'NonExistent'
        
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_feeds_by_category(category)
        
        # Verify
        assert result.category == 'NonExistent'
        assert result.feed_count == 0
        assert result.feeds == []
    
    @pytest.mark.asyncio
    async def test_get_feeds_by_category_orders_recommended_first(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that recommended feeds appear before non-recommended feeds"""
        category = 'Web Development'
        feed_data = [
            {
                'id': str(uuid4()),
                'name': 'CSS Tricks',
                'url': 'https://css-tricks.com/feed',
                'category': 'Web Development',
                'is_recommended': True,
                'recommendation_priority': 90
            },
            {
                'id': str(uuid4()),
                'name': 'Random Blog',
                'url': 'https://random.com/feed',
                'category': 'Web Development',
                'is_recommended': False,
                'recommendation_priority': 0
            }
        ]
        
        mock_response = Mock()
        mock_response.data = feed_data
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service.get_feeds_by_category(category)
        
        # Verify ordering
        assert result.feeds[0].is_recommended is True
        assert result.feeds[1].is_recommended is False
        
        # Verify order calls (is_recommended DESC, then priority DESC)
        assert mock_table.order.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_feeds_by_category_raises_error_on_database_failure(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that database errors are properly handled"""
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.side_effect = Exception("Database error")
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(RecommendationServiceError) as exc_info:
            await recommendation_service.get_feeds_by_category('AI')
        
        assert "Failed to get feeds by category" in str(exc_info.value)


class TestUpdateRecommendationStatus:
    """Tests for update_recommendation_status method"""
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status_updates_feed(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that recommendation status is updated correctly"""
        feed_id = uuid4()
        is_recommended = True
        priority = 100
        
        mock_response = Mock()
        mock_response.data = [{'id': str(feed_id)}]
        
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await recommendation_service.update_recommendation_status(
            feed_id=feed_id,
            is_recommended=is_recommended,
            priority=priority
        )
        
        # Verify update was called with correct data
        update_call = mock_table.update.call_args[0][0]
        assert update_call['is_recommended'] is True
        assert update_call['recommendation_priority'] == 100
        assert 'updated_at' in update_call
        
        # Verify correct feed was targeted
        mock_table.eq.assert_called_once_with('id', str(feed_id))
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status_can_unrecommend_feed(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that a feed can be marked as not recommended"""
        feed_id = uuid4()
        
        mock_response = Mock()
        mock_response.data = [{'id': str(feed_id)}]
        
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await recommendation_service.update_recommendation_status(
            feed_id=feed_id,
            is_recommended=False,
            priority=0
        )
        
        # Verify
        update_call = mock_table.update.call_args[0][0]
        assert update_call['is_recommended'] is False
        assert update_call['recommendation_priority'] == 0
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status_raises_error_for_negative_priority(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that negative priority values are rejected"""
        feed_id = uuid4()
        
        # Execute and verify exception
        with pytest.raises(RecommendationServiceError) as exc_info:
            await recommendation_service.update_recommendation_status(
                feed_id=feed_id,
                is_recommended=True,
                priority=-10
            )
        
        assert "Priority must be non-negative" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status_raises_error_when_feed_not_found(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that error is raised when feed doesn't exist"""
        feed_id = uuid4()
        
        mock_response = Mock()
        mock_response.data = []  # No feed found
        
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(RecommendationServiceError) as exc_info:
            await recommendation_service.update_recommendation_status(
                feed_id=feed_id,
                is_recommended=True,
                priority=100
            )
        
        assert "Feed not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status_raises_error_on_database_failure(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that database errors are properly handled"""
        feed_id = uuid4()
        
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = Exception("Database error")
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(RecommendationServiceError) as exc_info:
            await recommendation_service.update_recommendation_status(
                feed_id=feed_id,
                is_recommended=True,
                priority=100
            )
        
        assert "Failed to update recommendation status" in str(exc_info.value)


class TestPrivateHelperMethods:
    """Tests for private helper methods"""
    
    @pytest.mark.asyncio
    async def test_get_user_subscribed_feed_ids_returns_set_of_uuids(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that user subscriptions are returned as a set of UUIDs"""
        user_id = uuid4()
        feed_id_1 = uuid4()
        feed_id_2 = uuid4()
        
        mock_response = Mock()
        mock_response.data = [
            {'feed_id': str(feed_id_1)},
            {'feed_id': str(feed_id_2)}
        ]
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service._get_user_subscribed_feed_ids(user_id)
        
        # Verify
        assert isinstance(result, set)
        assert len(result) == 2
        assert feed_id_1 in result
        assert feed_id_2 in result
    
    @pytest.mark.asyncio
    async def test_get_user_subscribed_feed_ids_returns_empty_set_when_no_subscriptions(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that empty set is returned when user has no subscriptions"""
        user_id = uuid4()
        
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await recommendation_service._get_user_subscribed_feed_ids(user_id)
        
        # Verify
        assert result == set()
    
    @pytest.mark.asyncio
    async def test_get_user_subscribed_feed_ids_handles_errors_gracefully(
        self,
        recommendation_service,
        mock_supabase_client
    ):
        """Test that errors in getting subscriptions don't crash the service"""
        user_id = uuid4()
        
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = Exception("Database error")
        
        mock_supabase_client.table.return_value = mock_table
        
        # Execute - should not raise exception
        result = await recommendation_service._get_user_subscribed_feed_ids(user_id)
        
        # Verify - returns empty set on error
        assert result == set()
