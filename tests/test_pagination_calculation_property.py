"""
Property 12: Pagination Calculation Correctness

**Validates: Requirements 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.9**

For any valid page and page_size parameters, the pagination calculation should satisfy:
- offset = (page - 1) * page_size
- has_next_page = (page * page_size) < total_count
- When page exceeds range, return empty list (not error)
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.api.articles import get_my_articles
from app.schemas.article import ArticleListResponse


@given(
    page=st.integers(min_value=1, max_value=100),
    page_size=st.integers(min_value=1, max_value=100),
    total_count=st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_pagination_calculation_correctness(page, page_size, total_count):
    """
    Property 12: Pagination Calculation Correctness
    
    Verifies that pagination calculations are mathematically correct:
    1. offset = (page - 1) * page_size
    2. has_next_page = (page * page_size) < total_count
    3. Page parameters are validated (page >= 1, 1 <= page_size <= 100)
    4. When page exceeds range, returns empty list (not error)
    """
    # Calculate expected values
    expected_offset = (page - 1) * page_size
    expected_has_next_page = (page * page_size) < total_count
    
    # Verify offset is non-negative
    assert expected_offset >= 0, "Offset must be non-negative"
    
    # Verify has_next_page logic
    if page * page_size >= total_count:
        assert expected_has_next_page is False, "Should not have next page when at or beyond total"
    else:
        assert expected_has_next_page is True, "Should have next page when more items exist"
    
    # Create mock subscriptions (at least one to avoid early return)
    mock_subscriptions = []
    subscribed_feed_id = uuid4()
    mock_sub = Mock()
    mock_sub.feed_id = subscribed_feed_id
    mock_subscriptions.append(mock_sub)
    
    # Create mock articles based on total_count
    # Calculate how many articles should be on this page
    articles_on_page = min(page_size, max(0, total_count - expected_offset))
    
    mock_articles = []
    for i in range(articles_on_page):
        mock_articles.append({
            "id": str(uuid4()),
            "title": f"Article {i}",
            "url": f"https://example.com/article-{i}",
            "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
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
        mock_service.get_user_subscriptions.return_value = mock_subscriptions
        
        # Mock article query response
        mock_response = Mock()
        mock_response.data = mock_articles
        
        # Mock count query response
        mock_count_response = Mock()
        mock_count_response.count = total_count
        
        # Setup query chain for article query
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
        
        # Setup query chain for count query
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
            if call_count[0] % 2 == 1:  # Odd calls for article query
                return mock_table
            else:  # Even calls for count query
                return mock_count_table
        
        mock_service.client.table.side_effect = table_side_effect
        
        # Call the endpoint
        result = await get_my_articles(
            page=page,
            page_size=page_size,
            current_user=current_user
        )
        
        # Verify the result is an ArticleListResponse
        assert isinstance(result, ArticleListResponse)
        
        # Verify pagination metadata
        assert result.page == page, f"Page should be {page}"
        assert result.page_size == page_size, f"Page size should be {page_size}"
        assert result.total_count == total_count, f"Total count should be {total_count}"
        assert result.has_next_page == expected_has_next_page, \
            f"has_next_page should be {expected_has_next_page}"
        
        # Verify articles count on this page
        assert len(result.articles) == articles_on_page, \
            f"Should have {articles_on_page} articles on this page"
        
        # Verify range() was called with correct offset and limit
        # range(start, end) where end = start + page_size - 1
        expected_range_start = expected_offset
        expected_range_end = expected_offset + page_size - 1
        mock_order2.range.assert_called_once_with(expected_range_start, expected_range_end)


@given(
    page=st.integers(min_value=1, max_value=10),
    page_size=st.integers(min_value=1, max_value=20),
    total_count=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_pagination_boundary_conditions(page, page_size, total_count):
    """
    Property 12: Pagination Calculation Correctness (Boundary Conditions)
    
    **Validates: Requirement 9.9**
    
    Verifies that when page exceeds the available range, the system returns
    an empty list without throwing an error.
    """
    # Only test cases where page is beyond available data
    offset = (page - 1) * page_size
    assume(offset >= total_count and total_count > 0)
    
    # Create mock subscriptions
    mock_subscriptions = []
    subscribed_feed_id = uuid4()
    mock_sub = Mock()
    mock_sub.feed_id = subscribed_feed_id
    mock_subscriptions.append(mock_sub)
    
    # Mock current user
    current_user = {
        "user_id": uuid4(),
        "discord_id": "test_discord_id"
    }
    
    # Mock SupabaseService
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        mock_service.get_user_subscriptions.return_value = mock_subscriptions
        
        # Mock article query response - empty because page is out of range
        mock_response = Mock()
        mock_response.data = []
        
        # Mock count query response
        mock_count_response = Mock()
        mock_count_response.count = total_count
        
        # Setup query chains
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
        
        # Mock client.table
        call_count = [0]
        def table_side_effect(table_name):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return mock_table
            else:
                return mock_count_table
        
        mock_service.client.table.side_effect = table_side_effect
        
        # Call the endpoint - should not raise an error
        result = await get_my_articles(
            page=page,
            page_size=page_size,
            current_user=current_user
        )
        
        # Verify empty result (not an error)
        assert isinstance(result, ArticleListResponse)
        assert result.articles == [], "Should return empty list when page exceeds range"
        assert result.page == page
        assert result.page_size == page_size
        assert result.total_count == total_count
        assert result.has_next_page is False, "Should not have next page when beyond range"


@pytest.mark.asyncio
async def test_pagination_first_page():
    """
    Property 12: Pagination Calculation Correctness (First Page)
    
    **Validates: Requirements 9.1, 9.3**
    
    Verifies that the first page (page=1) has offset=0.
    """
    page = 1
    page_size = 20
    total_count = 50
    
    # Expected values
    expected_offset = 0
    expected_has_next_page = True  # 1 * 20 < 50
    
    # Create mock data
    mock_subscriptions = [Mock(feed_id=uuid4())]
    mock_articles = [
        {
            "id": str(uuid4()),
            "title": f"Article {i}",
            "url": f"https://example.com/article-{i}",
            "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "tinkering_index": 3,
            "ai_summary": "Test summary",
            "feeds": {"name": "Test Feed", "category": "Tech"}
        }
        for i in range(page_size)
    ]
    
    current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}
    
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        mock_service.get_user_subscriptions.return_value = mock_subscriptions
        
        mock_response = Mock()
        mock_response.data = mock_articles
        
        mock_count_response = Mock()
        mock_count_response.count = total_count
        
        # Setup mocks
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
        
        call_count = [0]
        def table_side_effect(table_name):
            call_count[0] += 1
            return mock_table if call_count[0] % 2 == 1 else mock_count_table
        
        mock_service.client.table.side_effect = table_side_effect
        
        result = await get_my_articles(
            page=page,
            page_size=page_size,
            current_user=current_user
        )
        
        # Verify first page calculations
        assert result.page == 1
        assert result.has_next_page is True
        assert len(result.articles) == page_size
        
        # Verify range was called with offset=0
        mock_order2.range.assert_called_once_with(0, 19)  # 0 to page_size-1


@pytest.mark.asyncio
async def test_pagination_last_page():
    """
    Property 12: Pagination Calculation Correctness (Last Page)
    
    **Validates: Requirements 9.6, 9.7**
    
    Verifies that the last page correctly calculates has_next_page=False.
    """
    page = 3
    page_size = 20
    total_count = 50  # Last page has 10 items (50 - 40)
    
    # Expected values
    expected_offset = 40  # (3 - 1) * 20
    expected_has_next_page = False  # 3 * 20 = 60 >= 50
    
    # Create mock data
    mock_subscriptions = [Mock(feed_id=uuid4())]
    mock_articles = [
        {
            "id": str(uuid4()),
            "title": f"Article {i}",
            "url": f"https://example.com/article-{i}",
            "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "tinkering_index": 3,
            "ai_summary": "Test summary",
            "feeds": {"name": "Test Feed", "category": "Tech"}
        }
        for i in range(10)  # Only 10 items on last page
    ]
    
    current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}
    
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        mock_service.get_user_subscriptions.return_value = mock_subscriptions
        
        mock_response = Mock()
        mock_response.data = mock_articles
        
        mock_count_response = Mock()
        mock_count_response.count = total_count
        
        # Setup mocks
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
        
        call_count = [0]
        def table_side_effect(table_name):
            call_count[0] += 1
            return mock_table if call_count[0] % 2 == 1 else mock_count_table
        
        mock_service.client.table.side_effect = table_side_effect
        
        result = await get_my_articles(
            page=page,
            page_size=page_size,
            current_user=current_user
        )
        
        # Verify last page calculations
        assert result.page == 3
        assert result.has_next_page is False, "Last page should not have next page"
        assert len(result.articles) == 10, "Last page should have remaining items"
        assert result.total_count == total_count
        
        # Verify range was called with correct offset
        mock_order2.range.assert_called_once_with(40, 59)  # offset to offset+page_size-1
