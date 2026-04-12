"""
Unit tests for batch subscription functionality

Tests the SubscriptionService.batch_subscribe() method with various scenarios
including success, partial failure, and edge cases.

Requirements: 2.6, 2.7
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.subscription_service import SubscriptionService


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    return MagicMock()


@pytest.fixture
def subscription_service(mock_supabase_client):
    """Create a SubscriptionService instance with mock client"""
    return SubscriptionService(mock_supabase_client)


class TestBatchSubscribe:
    """Test suite for batch_subscribe method"""

    @pytest.mark.asyncio
    async def test_batch_subscribe_all_success(self, subscription_service, mock_supabase_client):
        """Test successful subscription to all feeds"""
        user_id = uuid4()
        feed_ids = [uuid4(), uuid4(), uuid4()]

        # Mock feed existence checks - all feeds exist
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": str(feed_ids[0])}
        ]

        # Mock subscription checks - none exist yet
        def mock_subscription_check(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.data = []
            return mock_response

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            # Feed existence checks (3 feeds)
            MagicMock(data=[{"id": str(feed_ids[0])}]),
            MagicMock(data=[]),  # No existing subscription
            MagicMock(data=[{"id": str(feed_ids[1])}]),
            MagicMock(data=[]),  # No existing subscription
            MagicMock(data=[{"id": str(feed_ids[2])}]),
            MagicMock(data=[]),  # No existing subscription
        ]

        # Mock insert operations
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 3
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_all_fail_invalid_feeds(
        self, subscription_service, mock_supabase_client
    ):
        """Test when all feeds are invalid/not found"""
        user_id = uuid4()
        feed_ids = [uuid4(), uuid4()]

        # Mock feed existence checks - no feeds exist
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 0
        assert result.failed_count == 2
        assert len(result.errors) == 2
        assert "not found or inactive" in result.errors[0]

    @pytest.mark.asyncio
    async def test_batch_subscribe_partial_success(
        self, subscription_service, mock_supabase_client
    ):
        """Test partial success - some feeds succeed, some fail"""
        user_id = uuid4()
        feed_ids = [uuid4(), uuid4(), uuid4()]

        # Mock responses: first feed exists, second doesn't, third exists
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(feed_ids[0])}]),  # Feed 1 exists
            MagicMock(data=[]),  # No existing subscription
            MagicMock(data=[]),  # Feed 2 doesn't exist
            MagicMock(data=[{"id": str(feed_ids[2])}]),  # Feed 3 exists
            MagicMock(data=[]),  # No existing subscription
        ]

        # Mock insert operations
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 2
        assert result.failed_count == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_batch_subscribe_duplicate_subscriptions(
        self, subscription_service, mock_supabase_client
    ):
        """Test subscribing to feeds that are already subscribed (idempotent)"""
        user_id = uuid4()
        feed_ids = [uuid4(), uuid4()]

        # Mock responses: feeds exist and already subscribed
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(feed_ids[0])}]),  # Feed 1 exists
            MagicMock(data=[{"id": "sub1"}]),  # Already subscribed
            MagicMock(data=[{"id": str(feed_ids[1])}]),  # Feed 2 exists
            MagicMock(data=[{"id": "sub2"}]),  # Already subscribed
        ]

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Should count as success (idempotent behavior)
        assert result.subscribed_count == 2
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_empty_list(self, subscription_service, mock_supabase_client):
        """Test with empty feed list"""
        user_id = uuid4()
        feed_ids = []

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 0
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_single_feed(self, subscription_service, mock_supabase_client):
        """Test with single feed"""
        user_id = uuid4()
        feed_ids = [uuid4()]

        # Mock successful subscription
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(feed_ids[0])}]),  # Feed exists
            MagicMock(data=[]),  # Not subscribed yet
        ]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 1
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_database_error_on_insert(
        self, subscription_service, mock_supabase_client
    ):
        """Test handling of database errors during insert"""
        user_id = uuid4()
        feed_ids = [uuid4()]

        # Mock feed exists and not subscribed
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(feed_ids[0])}]),  # Feed exists
            MagicMock(data=[]),  # Not subscribed yet
        ]

        # Mock insert failure
        mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "Database error"
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 0
        assert result.failed_count == 1
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_batch_subscribe_mixed_valid_invalid_feeds(
        self, subscription_service, mock_supabase_client
    ):
        """Test with mix of valid and invalid feed IDs"""
        user_id = uuid4()
        valid_feed = uuid4()
        invalid_feed = uuid4()
        feed_ids = [valid_feed, invalid_feed]

        # Mock responses
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(valid_feed)}]),  # Valid feed exists
            MagicMock(data=[]),  # Not subscribed
            MagicMock(data=[]),  # Invalid feed doesn't exist
        ]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 1
        assert result.failed_count == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_batch_subscribe_large_batch(self, subscription_service, mock_supabase_client):
        """Test with large number of feeds (10 feeds)"""
        user_id = uuid4()
        feed_ids = [uuid4() for _ in range(10)]

        # Mock all feeds exist and not subscribed
        responses = []
        for feed_id in feed_ids:
            responses.append(MagicMock(data=[{"id": str(feed_id)}]))  # Feed exists
            responses.append(MagicMock(data=[]))  # Not subscribed

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = (
            responses
        )
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 10
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_inactive_feed(self, subscription_service, mock_supabase_client):
        """Test subscribing to inactive feed (should fail)"""
        user_id = uuid4()
        feed_ids = [uuid4()]

        # Mock feed doesn't exist (filtered by is_active=True)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 0
        assert result.failed_count == 1
        assert "not found or inactive" in result.errors[0]

    @pytest.mark.asyncio
    async def test_batch_subscribe_returns_correct_counts(
        self, subscription_service, mock_supabase_client
    ):
        """Test that counts are accurate for mixed results"""
        user_id = uuid4()
        feed_ids = [uuid4() for _ in range(5)]

        # Mock: 3 succeed, 2 fail
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": str(feed_ids[0])}]),  # Success
            MagicMock(data=[]),
            MagicMock(data=[]),  # Fail
            MagicMock(data=[{"id": str(feed_ids[2])}]),  # Success
            MagicMock(data=[]),
            MagicMock(data=[{"id": str(feed_ids[3])}]),  # Success
            MagicMock(data=[]),
            MagicMock(data=[]),  # Fail
        ]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        assert result.subscribed_count == 3
        assert result.failed_count == 2
        assert result.subscribed_count + result.failed_count == len(feed_ids)
