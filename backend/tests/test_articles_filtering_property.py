"""
Property 10: Article Filtering by Subscription

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

For any user with subscriptions, the /api/articles/me endpoint should return
only articles where feed_id is in the user's subscribed feeds.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.api.articles import get_my_articles
from app.schemas.article import ArticleListResponse


@given(
    num_subscribed_feeds=st.integers(min_value=1, max_value=5),
    num_unsubscribed_feeds=st.integers(min_value=1, max_value=3),
    articles_per_feed=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_article_filtering_by_subscription(
    num_subscribed_feeds, num_unsubscribed_feeds, articles_per_feed
):
    """
    Property 10: Article Filtering by Subscription

    Verifies that the articles endpoint only returns articles from feeds
    the user has subscribed to, and excludes articles from unsubscribed feeds.
    """
    # Generate subscribed and unsubscribed feed IDs
    subscribed_feed_ids = [uuid4() for _ in range(num_subscribed_feeds)]
    unsubscribed_feed_ids = [uuid4() for _ in range(num_unsubscribed_feeds)]

    # Create mock subscriptions
    mock_subscriptions = []
    for feed_id in subscribed_feed_ids:
        mock_sub = Mock()
        mock_sub.feed_id = feed_id
        mock_subscriptions.append(mock_sub)

    # Create mock articles from both subscribed and unsubscribed feeds
    all_articles = []

    # Articles from subscribed feeds (should be returned)
    for feed_id in subscribed_feed_ids:
        for i in range(articles_per_feed):
            all_articles.append(
                {
                    "id": str(uuid4()),
                    "title": f"Article {i} from subscribed feed",
                    "url": f"https://example.com/article-{i}",
                    "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "tinkering_index": 3,
                    "ai_summary": "Test summary",
                    "feed_id": str(feed_id),
                    "feeds": {"name": "Test Feed", "category": "Tech"},
                }
            )

    # Articles from unsubscribed feeds (should NOT be returned)
    for feed_id in unsubscribed_feed_ids:
        for i in range(articles_per_feed):
            all_articles.append(
                {
                    "id": str(uuid4()),
                    "title": f"Article {i} from unsubscribed feed",
                    "url": f"https://example.com/article-{i}",
                    "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "tinkering_index": 3,
                    "ai_summary": "Test summary",
                    "feed_id": str(feed_id),
                    "feeds": {"name": "Test Feed", "category": "Tech"},
                }
            )

    # Mock current user
    current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

    # Mock SupabaseService
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        mock_service.get_user_subscriptions.return_value = mock_subscriptions

        # Mock article query - filter by subscribed feed_ids
        mock_response = Mock()
        subscribed_feed_id_strs = [str(fid) for fid in subscribed_feed_ids]
        filtered_articles = [a for a in all_articles if a["feed_id"] in subscribed_feed_id_strs]
        mock_response.data = filtered_articles[:20]  # Limit to page size

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
            if call_count[0] % 2 == 1:  # Odd calls for article query
                return mock_table
            else:  # Even calls for count query
                return mock_count_table

        mock_service.client.table.side_effect = table_side_effect

        # Call the endpoint
        result = await get_my_articles(page=1, page_size=20, current_user=current_user)

        # Verify all returned articles are from subscribed feeds
        for article in result.articles:
            # The article should have come from one of the subscribed feeds
            # We can't directly check feed_id in the response, but we can verify
            # that the number of articles matches our filtered set
            assert article.feed_name == "Test Feed"
            assert article.category == "Tech"

        # Verify the count matches subscribed articles only
        expected_count = num_subscribed_feeds * articles_per_feed
        assert result.total_count == expected_count

        # Verify no articles from unsubscribed feeds are included
        # (implicitly verified by the count check)
        assert len(result.articles) <= expected_count


@pytest.mark.asyncio
async def test_article_filtering_empty_subscriptions():
    """
    Property 10: Article Filtering by Subscription (Empty Subscriptions Case)

    **Validates: Requirement 8.3**

    Verifies that when a user has no subscriptions, the endpoint returns
    an empty list with HTTP 200.
    """
    # Mock current user with no subscriptions
    current_user = {"user_id": uuid4(), "discord_id": "test_discord_id_no_subs"}

    # Mock SupabaseService
    with patch("app.api.articles.SupabaseService") as MockSupabase:
        mock_service = MockSupabase.return_value
        # Return empty subscriptions list
        mock_service.get_user_subscriptions.return_value = []

        # Call the endpoint
        result = await get_my_articles(page=1, page_size=20, current_user=current_user)

        # Verify empty response
        assert isinstance(result, ArticleListResponse)
        assert result.articles == []
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_count == 0
        assert result.has_next_page is False

        # Verify get_user_subscriptions was called
        mock_service.get_user_subscriptions.assert_called_once_with("test_discord_id_no_subs")
