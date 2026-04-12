"""
Property-Based Tests for Feed Subscription Status Accuracy

Feature: web-api-oauth-authentication
Property 8: Feed Subscription Status Accuracy

Tests that the list_feeds endpoint correctly marks is_subscribed for feeds.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.api.feeds import list_feeds


# Mock data classes
class MockFeed:
    def __init__(self, id, name, url, category):
        self.id = id
        self.name = name
        self.url = url
        self.category = category


class MockSubscription:
    def __init__(self, feed_id):
        self.feed_id = feed_id


# Strategies for generating test data
feed_ids = st.lists(st.uuids(), min_size=1, max_size=20, unique=True)
subscription_indices = st.lists(st.integers(min_value=0, max_value=19), unique=True)


class TestFeedSubscriptionStatusAccuracy:
    """Test that subscription status is accurately reflected in feed list"""

    @given(
        num_feeds=st.integers(min_value=1, max_value=20),
        subscription_ratio=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_subscription_status_accuracy(self, num_feeds, subscription_ratio):
        """
        Property 8: For any user and set of feeds, the list_feeds endpoint
        should correctly mark is_subscribed=True for feeds in the user's
        subscriptions and is_subscribed=False for all others.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Generate mock feeds
        mock_feeds = []
        feed_ids_list = []
        for i in range(num_feeds):
            feed_id = uuid4()
            feed_ids_list.append(feed_id)
            mock_feeds.append(
                MockFeed(
                    id=feed_id,
                    name=f"Feed {i}",
                    url=f"https://example{i}.com/feed",
                    category=f"Category {i % 3}",
                )
            )

        # Determine which feeds are subscribed
        num_subscribed = int(num_feeds * subscription_ratio)
        subscribed_indices = set(range(num_subscribed))
        subscribed_feed_ids = {feed_ids_list[i] for i in subscribed_indices}

        # Generate mock subscriptions
        mock_subscriptions = [
            MockSubscription(feed_id=feed_ids_list[i]) for i in subscribed_indices
        ]

        # Mock current user
        current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

        # Mock SupabaseService
        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = mock_feeds
            mock_service.get_user_subscriptions.return_value = mock_subscriptions
            MockSupabaseService.return_value = mock_service

            # Call the endpoint
            result = await list_feeds(current_user=current_user)

            # Verify the result
            assert len(result) == num_feeds

            # Check each feed's subscription status
            for feed_response in result:
                if feed_response.id in subscribed_feed_ids:
                    assert (
                        feed_response.is_subscribed is True
                    ), f"Feed {feed_response.id} should be marked as subscribed"
                else:
                    assert (
                        feed_response.is_subscribed is False
                    ), f"Feed {feed_response.id} should be marked as not subscribed"

            # Verify all subscribed feeds are marked correctly
            subscribed_in_response = {f.id for f in result if f.is_subscribed}
            assert (
                subscribed_in_response == subscribed_feed_ids
            ), "Subscribed feeds in response should match actual subscriptions"

    @pytest.mark.asyncio
    async def test_no_subscriptions_all_false(self):
        """
        Property 8: When a user has no subscriptions, all feeds should
        have is_subscribed=False.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Generate mock feeds
        mock_feeds = [
            MockFeed(
                id=uuid4(), name=f"Feed {i}", url=f"https://example{i}.com/feed", category="Tech"
            )
            for i in range(5)
        ]

        # No subscriptions
        mock_subscriptions = []

        current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = mock_feeds
            mock_service.get_user_subscriptions.return_value = mock_subscriptions
            MockSupabaseService.return_value = mock_service

            result = await list_feeds(current_user=current_user)

            # All feeds should be marked as not subscribed
            assert all(
                not f.is_subscribed for f in result
            ), "All feeds should be marked as not subscribed when user has no subscriptions"

    @pytest.mark.asyncio
    async def test_all_subscriptions_all_true(self):
        """
        Property 8: When a user is subscribed to all feeds, all feeds
        should have is_subscribed=True.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Generate mock feeds
        feed_ids_list = [uuid4() for _ in range(5)]
        mock_feeds = [
            MockFeed(
                id=feed_id, name=f"Feed {i}", url=f"https://example{i}.com/feed", category="Tech"
            )
            for i, feed_id in enumerate(feed_ids_list)
        ]

        # Subscribe to all feeds
        mock_subscriptions = [MockSubscription(feed_id=feed_id) for feed_id in feed_ids_list]

        current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = mock_feeds
            mock_service.get_user_subscriptions.return_value = mock_subscriptions
            MockSupabaseService.return_value = mock_service

            result = await list_feeds(current_user=current_user)

            # All feeds should be marked as subscribed
            assert all(
                f.is_subscribed for f in result
            ), "All feeds should be marked as subscribed when user is subscribed to all"

    @pytest.mark.asyncio
    async def test_subscription_status_consistency(self):
        """
        Property 8: The subscription status should be consistent - a feed
        cannot be both subscribed and not subscribed.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        feed_id = uuid4()
        mock_feeds = [
            MockFeed(id=feed_id, name="Test Feed", url="https://example.com/feed", category="Tech")
        ]

        # Subscribe to the feed
        mock_subscriptions = [MockSubscription(feed_id=feed_id)]

        current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = mock_feeds
            mock_service.get_user_subscriptions.return_value = mock_subscriptions
            MockSupabaseService.return_value = mock_service

            result = await list_feeds(current_user=current_user)

            # The feed should be marked as subscribed
            assert len(result) == 1
            assert result[0].is_subscribed is True

            # Now test with no subscription
            mock_service.get_user_subscriptions.return_value = []

            result = await list_feeds(current_user=current_user)

            # The feed should be marked as not subscribed
            assert len(result) == 1
            assert result[0].is_subscribed is False

    @pytest.mark.asyncio
    async def test_feeds_sorted_by_category_and_name(self):
        """
        Property 8: Feeds should be sorted by category ascending, then name ascending.

        **Validates: Requirements 6.7**
        """
        mock_feeds = [
            MockFeed(id=uuid4(), name="Zebra", url="https://z.com/feed", category="Tech"),
            MockFeed(id=uuid4(), name="Apple", url="https://a.com/feed", category="News"),
            MockFeed(id=uuid4(), name="Beta", url="https://b.com/feed", category="Tech"),
            MockFeed(id=uuid4(), name="Charlie", url="https://c.com/feed", category="News"),
        ]

        current_user = {"user_id": uuid4(), "discord_id": "test_discord_id"}

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = mock_feeds
            mock_service.get_user_subscriptions.return_value = []
            MockSupabaseService.return_value = mock_service

            result = await list_feeds(current_user=current_user)

            # Verify sorting: News (Apple, Charlie), Tech (Beta, Zebra)
            assert result[0].name == "Apple"
            assert result[0].category == "News"
            assert result[1].name == "Charlie"
            assert result[1].category == "News"
            assert result[2].name == "Beta"
            assert result[2].category == "Tech"
            assert result[3].name == "Zebra"
            assert result[3].category == "Tech"
