"""
Property-Based Tests for Subscription Toggle Idempotence

Feature: web-api-oauth-authentication
Property 9: Subscription Toggle Idempotence

Tests that toggling subscription twice returns to the original state.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.api.feeds import toggle_subscription
from app.schemas.feed import SubscriptionToggleRequest


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


class TestSubscriptionToggleIdempotence:
    """Test that subscription toggle is idempotent"""

    @given(initial_state=st.booleans())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_toggle_twice_returns_to_original_state(self, initial_state):
        """
        Property 9: For any user and feed, toggling subscription twice should
        return to the original state (subscribed → unsubscribed → subscribed,
        or unsubscribed → subscribed → unsubscribed).

        **Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7**
        """
        feed_id = uuid4()
        discord_id = "test_discord_id"
        user_id = uuid4()

        # Mock feed
        mock_feed = MockFeed(
            id=feed_id, name="Test Feed", url="https://example.com/feed", category="Tech"
        )

        current_user = {"user_id": user_id, "discord_id": discord_id}

        request = SubscriptionToggleRequest(feed_id=feed_id)

        # Track subscription state
        subscription_state = initial_state
        subscriptions = [MockSubscription(feed_id=feed_id)] if initial_state else []

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = [mock_feed]

            # First toggle
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()

            async def mock_subscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = True
                subscriptions = [MockSubscription(feed_id=feed_id)]

            async def mock_unsubscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = False
                subscriptions = []

            mock_service.subscribe_to_feed = mock_subscribe
            mock_service.unsubscribe_from_feed = mock_unsubscribe

            MockSupabaseService.return_value = mock_service

            # First toggle
            result1 = await toggle_subscription(request, current_user)
            assert result1.feed_id == feed_id
            assert result1.is_subscribed == (not initial_state)

            # Second toggle
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result2 = await toggle_subscription(request, current_user)
            assert result2.feed_id == feed_id
            assert result2.is_subscribed == initial_state

            # Verify we're back to the original state
            assert subscription_state == initial_state

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe_subscribe_sequence(self):
        """
        Property 9: Starting from unsubscribed, the sequence
        unsubscribed → subscribed → unsubscribed → subscribed
        should work correctly.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7**
        """
        feed_id = uuid4()
        discord_id = "test_discord_id"
        user_id = uuid4()

        mock_feed = MockFeed(
            id=feed_id, name="Test Feed", url="https://example.com/feed", category="Tech"
        )

        current_user = {"user_id": user_id, "discord_id": discord_id}

        request = SubscriptionToggleRequest(feed_id=feed_id)

        # Track subscription state
        subscription_state = False
        subscriptions = []

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = [mock_feed]

            async def mock_subscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = True
                subscriptions = [MockSubscription(feed_id=feed_id)]

            async def mock_unsubscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = False
                subscriptions = []

            mock_service.subscribe_to_feed = mock_subscribe
            mock_service.unsubscribe_from_feed = mock_unsubscribe

            MockSupabaseService.return_value = mock_service

            # Start: unsubscribed
            assert subscription_state is False

            # Toggle 1: unsubscribed → subscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result1 = await toggle_subscription(request, current_user)
            assert result1.is_subscribed is True
            assert subscription_state is True

            # Toggle 2: subscribed → unsubscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result2 = await toggle_subscription(request, current_user)
            assert result2.is_subscribed is False
            assert subscription_state is False

            # Toggle 3: unsubscribed → subscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result3 = await toggle_subscription(request, current_user)
            assert result3.is_subscribed is True
            assert subscription_state is True

    @pytest.mark.asyncio
    async def test_unsubscribe_subscribe_unsubscribe_sequence(self):
        """
        Property 9: Starting from subscribed, the sequence
        subscribed → unsubscribed → subscribed → unsubscribed
        should work correctly.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7**
        """
        feed_id = uuid4()
        discord_id = "test_discord_id"
        user_id = uuid4()

        mock_feed = MockFeed(
            id=feed_id, name="Test Feed", url="https://example.com/feed", category="Tech"
        )

        current_user = {"user_id": user_id, "discord_id": discord_id}

        request = SubscriptionToggleRequest(feed_id=feed_id)

        # Track subscription state - start subscribed
        subscription_state = True
        subscriptions = [MockSubscription(feed_id=feed_id)]

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = [mock_feed]

            async def mock_subscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = True
                subscriptions = [MockSubscription(feed_id=feed_id)]

            async def mock_unsubscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = False
                subscriptions = []

            mock_service.subscribe_to_feed = mock_subscribe
            mock_service.unsubscribe_from_feed = mock_unsubscribe

            MockSupabaseService.return_value = mock_service

            # Start: subscribed
            assert subscription_state is True

            # Toggle 1: subscribed → unsubscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result1 = await toggle_subscription(request, current_user)
            assert result1.is_subscribed is False
            assert subscription_state is False

            # Toggle 2: unsubscribed → subscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result2 = await toggle_subscription(request, current_user)
            assert result2.is_subscribed is True
            assert subscription_state is True

            # Toggle 3: subscribed → unsubscribed
            mock_service.get_user_subscriptions.return_value = subscriptions.copy()
            result3 = await toggle_subscription(request, current_user)
            assert result3.is_subscribed is False
            assert subscription_state is False

    @pytest.mark.asyncio
    async def test_multiple_toggles_maintain_consistency(self):
        """
        Property 9: Multiple toggles should maintain consistency - the state
        should alternate between subscribed and unsubscribed.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7**
        """
        feed_id = uuid4()
        discord_id = "test_discord_id"
        user_id = uuid4()

        mock_feed = MockFeed(
            id=feed_id, name="Test Feed", url="https://example.com/feed", category="Tech"
        )

        current_user = {"user_id": user_id, "discord_id": discord_id}

        request = SubscriptionToggleRequest(feed_id=feed_id)

        # Track subscription state
        subscription_state = False
        subscriptions = []

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            mock_service.get_active_feeds.return_value = [mock_feed]

            async def mock_subscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = True
                subscriptions = [MockSubscription(feed_id=feed_id)]

            async def mock_unsubscribe(discord_id, feed_id):
                nonlocal subscription_state, subscriptions
                subscription_state = False
                subscriptions = []

            mock_service.subscribe_to_feed = mock_subscribe
            mock_service.unsubscribe_from_feed = mock_unsubscribe

            MockSupabaseService.return_value = mock_service

            # Perform 10 toggles and verify alternating state
            expected_state = False
            for i in range(10):
                mock_service.get_user_subscriptions.return_value = subscriptions.copy()
                result = await toggle_subscription(request, current_user)

                expected_state = not expected_state
                assert (
                    result.is_subscribed == expected_state
                ), f"Toggle {i+1}: Expected {expected_state}, got {result.is_subscribed}"
                assert subscription_state == expected_state, f"Toggle {i+1}: State inconsistency"

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_feed_raises_404(self):
        """
        Property 9: Toggling a non-existent feed should raise 404.

        **Validates: Requirements 7.9**
        """
        feed_id = uuid4()
        discord_id = "test_discord_id"
        user_id = uuid4()

        current_user = {"user_id": user_id, "discord_id": discord_id}

        request = SubscriptionToggleRequest(feed_id=feed_id)

        with patch("app.api.feeds.SupabaseService") as MockSupabaseService:
            mock_service = AsyncMock()
            # No feeds exist
            mock_service.get_active_feeds.return_value = []
            MockSupabaseService.return_value = mock_service

            # Should raise 404
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await toggle_subscription(request, current_user)

            assert exc_info.value.status_code == 404
            assert "Feed not found" in exc_info.value.detail
