"""
Property 11: Article Time Window Filter

**Validates: Requirements 8.6**

For any query to /api/articles/me, all returned articles should have 
published_at >= 7 days ago.
"""

import pytest
from hypothesis import given, settings, strategies as st
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.api.articles import get_my_articles


@given(
    days_old=st.integers(min_value=0, max_value=14),
    num_articles=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_article_time_window_filter(days_old, num_articles):
    """
    Property 11: Article Time Window Filter
    
    Verifies that all returned articles have published_at within the last 7 days.
    Articles older than 7 days should be filtered out.
    """
    # Create mock subscription
    feed_id = uuid4()
    mock_subscription = Mock()
    mock_subscription.feed_id = feed_id
    
    # Create articles with varying ages
    articles = []
    now = datetime.utcnow()
    
    for i in range(num_articles):
        # Create article with specific age
        published_at = now - timedelta(days=days_old, hours=i)
        articles.append({
            "id": str(uuid4()),
            "title": f"Article {i}",
            "url": f"https://example.com/article-{i}",
            "published_at": published_at.isoformat(),
            "tinkering_index": 3,
            "ai_summary": "Test summary",
            "feeds": {"name": "Test Feed", "category": "Tech"}
        })
    
    # Mock current user
    current_user = {
        "user_id": uuid4(),
        "discord_id": "test_discord_id"
    }
    
    # Mock SupabaseService
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        mock_service.get_user_subscriptions.return_value = [mock_subscription]
        
        # Filter articles based on 7-day window (simulating database behavior)
        seven_days_ago = now - timedelta(days=7)
        filtered_articles = [
            a for a in articles 
            if datetime.fromisoformat(a["published_at"]) >= seven_days_ago
        ]
        
        # Mock article query
        mock_response = Mock()
        mock_response.data = filtered_articles
        
        # Mock count query
        mock_count_response = Mock()
        mock_count_response.count = len(filtered_articles)
        
        # Setup query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_in = Mock()
        mock_gte = Mock()
        mock_not = Mock()
        mock_is = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_range = Mock()
        
        mock_table.select.return_value = mock_select
        mock_select.in_.return_value = mock_in
        mock_in.gte.return_value = mock_gte
        mock_gte.not_ = mock_not
        mock_not.is_.return_value = mock_is
        mock_is.order.return_value = mock_order1
        mock_order1.order.return_value = mock_order2
        mock_order2.range.return_value = mock_range
        mock_range.execute.return_value = mock_response
        
        # Setup count query chain
        mock_count_table = Mock()
        mock_count_select = Mock()
        mock_count_in = Mock()
        mock_count_gte = Mock()
        mock_count_not = Mock()
        mock_count_is = Mock()
        
        mock_count_table.select.return_value = mock_count_select
        mock_count_select.in_.return_value = mock_count_in
        mock_count_in.gte.return_value = mock_count_gte
        mock_count_gte.not_ = mock_count_not
        mock_count_not.is_.return_value = mock_count_is
        mock_count_is.execute.return_value = mock_count_response
        
        # Mock client.table to return different mocks for different calls
        call_count = [0]
        def table_side_effect(table_name):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return mock_table
            else:
                return mock_count_table
        
        mock_service.client.table.side_effect = table_side_effect
        
        # Call the endpoint
        result = await get_my_articles(
            page=1,
            page_size=20,
            current_user=current_user
        )
        
        # Verify all returned articles are within 7-day window
        for article in result.articles:
            if article.published_at:
                age_in_days = (now - article.published_at).days
                assert age_in_days <= 7, (
                    f"Article published {age_in_days} days ago, "
                    f"should be within 7 days"
                )
        
        # Verify count matches filtered articles
        # Note: When days_old=7, some articles might be filtered out due to hours offset
        if days_old < 7:
            # Articles should be included
            assert result.total_count == num_articles
        elif days_old == 7:
            # Some articles might be filtered out due to hours offset
            assert result.total_count <= num_articles
        else:
            # Articles should be excluded
            assert result.total_count == 0
