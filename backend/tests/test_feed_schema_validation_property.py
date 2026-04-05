"""
Property-Based Tests for Feed Schema Validation

Feature: web-api-oauth-authentication
Property 17: Pydantic Schema Validation

Tests that Pydantic models correctly validate and reject invalid data.
"""

import pytest
from hypothesis import given, strategies as st, settings
from pydantic import ValidationError
from uuid import UUID, uuid4

from app.schemas.feed import (
    FeedResponse,
    SubscriptionToggleRequest,
    SubscriptionToggleResponse
)


# Strategies for generating test data
valid_uuids = st.uuids()
valid_names = st.text(min_size=1, max_size=200)
valid_urls = st.from_regex(r"https?://[a-z0-9\-\.]+\.[a-z]{2,}(/.*)?", fullmatch=True)
valid_categories = st.text(min_size=1, max_size=100)
valid_booleans = st.booleans()


class TestFeedResponseValidation:
    """Test FeedResponse schema validation"""

    @given(
        feed_id=valid_uuids,
        name=valid_names,
        url=valid_urls,
        category=valid_categories,
        is_subscribed=valid_booleans
    )
    @settings(max_examples=100)
    def test_valid_feed_response_accepts_valid_data(
        self, feed_id, name, url, category, is_subscribed
    ):
        """
        Property 17: For any valid feed data, FeedResponse should accept it.
        **Validates: Requirements 17.1, 17.8**
        """
        feed = FeedResponse(
            id=feed_id,
            name=name,
            url=url,
            category=category,
            is_subscribed=is_subscribed
        )
        
        assert feed.id == feed_id
        assert feed.name == name
        # HttpUrl normalizes and encodes URLs, so just verify it's a valid URL
        assert str(feed.url).startswith('http')
        assert feed.category == category
        assert feed.is_subscribed == is_subscribed

    def test_feed_response_rejects_missing_required_fields(self):
        """
        Property 17: FeedResponse should reject data with missing required fields.
        **Validates: Requirements 17.1, 17.8**
        """
        # Missing id
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                name="Test Feed",
                url="https://example.com/feed",
                category="Tech",
                is_subscribed=True
            )
        assert "id" in str(exc_info.value)

        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=uuid4(),
                url="https://example.com/feed",
                category="Tech",
                is_subscribed=True
            )
        assert "name" in str(exc_info.value)

        # Missing url
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=uuid4(),
                name="Test Feed",
                category="Tech",
                is_subscribed=True
            )
        assert "url" in str(exc_info.value)

    @given(invalid_url=st.text().filter(lambda x: not x.startswith("http")))
    @settings(max_examples=50)
    def test_feed_response_rejects_invalid_url(self, invalid_url):
        """
        Property 17: FeedResponse should reject invalid URLs.
        **Validates: Requirements 17.1, 17.8**
        """
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=uuid4(),
                name="Test Feed",
                url=invalid_url,
                category="Tech",
                is_subscribed=True
            )
        assert "url" in str(exc_info.value).lower()

    @given(invalid_id=st.text().filter(lambda x: x != ""))
    @settings(max_examples=50)
    def test_feed_response_rejects_invalid_uuid(self, invalid_id):
        """
        Property 17: FeedResponse should reject invalid UUIDs.
        **Validates: Requirements 17.1, 17.8**
        """
        try:
            UUID(invalid_id)
            # If it's a valid UUID string, skip this test case
            return
        except (ValueError, AttributeError):
            pass

        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=invalid_id,
                name="Test Feed",
                url="https://example.com/feed",
                category="Tech",
                is_subscribed=True
            )
        assert "id" in str(exc_info.value).lower()

    def test_feed_response_rejects_invalid_boolean(self):
        """
        Property 17: FeedResponse should reject invalid boolean values.
        **Validates: Requirements 17.1, 17.8**
        
        Note: Pydantic is lenient with boolean conversion, accepting many string values.
        This test verifies that truly invalid types (like lists or dicts) are rejected.
        """
        # Test with a list (definitely not a boolean)
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=uuid4(),
                name="Test Feed",
                url="https://example.com/feed",
                category="Tech",
                is_subscribed=["not", "a", "bool"]
            )
        assert "is_subscribed" in str(exc_info.value).lower()
        
        # Test with a dict (definitely not a boolean)
        with pytest.raises(ValidationError) as exc_info:
            FeedResponse(
                id=uuid4(),
                name="Test Feed",
                url="https://example.com/feed",
                category="Tech",
                is_subscribed={"not": "a bool"}
            )
        assert "is_subscribed" in str(exc_info.value).lower()


class TestSubscriptionToggleRequestValidation:
    """Test SubscriptionToggleRequest schema validation"""

    @given(feed_id=valid_uuids)
    @settings(max_examples=100)
    def test_valid_subscription_toggle_request_accepts_valid_data(self, feed_id):
        """
        Property 17: For any valid UUID, SubscriptionToggleRequest should accept it.
        **Validates: Requirements 17.2, 17.8**
        """
        request = SubscriptionToggleRequest(feed_id=feed_id)
        assert request.feed_id == feed_id

    def test_subscription_toggle_request_rejects_missing_feed_id(self):
        """
        Property 17: SubscriptionToggleRequest should reject missing feed_id.
        **Validates: Requirements 17.2, 17.8**
        """
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionToggleRequest()
        assert "feed_id" in str(exc_info.value)

    @given(invalid_id=st.text().filter(lambda x: x != ""))
    @settings(max_examples=50)
    def test_subscription_toggle_request_rejects_invalid_uuid(self, invalid_id):
        """
        Property 17: SubscriptionToggleRequest should reject invalid UUIDs.
        **Validates: Requirements 17.2, 17.8**
        """
        try:
            UUID(invalid_id)
            # If it's a valid UUID string, skip this test case
            return
        except (ValueError, AttributeError):
            pass

        with pytest.raises(ValidationError) as exc_info:
            SubscriptionToggleRequest(feed_id=invalid_id)
        assert "feed_id" in str(exc_info.value).lower()


class TestSubscriptionToggleResponseValidation:
    """Test SubscriptionToggleResponse schema validation"""

    @given(
        feed_id=valid_uuids,
        is_subscribed=valid_booleans
    )
    @settings(max_examples=100)
    def test_valid_subscription_toggle_response_accepts_valid_data(
        self, feed_id, is_subscribed
    ):
        """
        Property 17: For any valid data, SubscriptionToggleResponse should accept it.
        **Validates: Requirements 17.3, 17.8**
        """
        response = SubscriptionToggleResponse(
            feed_id=feed_id,
            is_subscribed=is_subscribed
        )
        
        assert response.feed_id == feed_id
        assert response.is_subscribed == is_subscribed

    def test_subscription_toggle_response_rejects_missing_fields(self):
        """
        Property 17: SubscriptionToggleResponse should reject missing required fields.
        **Validates: Requirements 17.3, 17.8**
        """
        # Missing feed_id
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionToggleResponse(is_subscribed=True)
        assert "feed_id" in str(exc_info.value)

        # Missing is_subscribed
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionToggleResponse(feed_id=uuid4())
        assert "is_subscribed" in str(exc_info.value)


class TestSchemaIntegrity:
    """Test overall schema integrity and edge cases"""

    def test_feed_response_with_empty_strings(self):
        """
        Property 17: FeedResponse should handle empty strings appropriately.
        **Validates: Requirements 17.1, 17.8**
        """
        # Empty name should be accepted (validation is minimal)
        feed = FeedResponse(
            id=uuid4(),
            name="",
            url="https://example.com/feed",
            category="",
            is_subscribed=False
        )
        assert feed.name == ""
        assert feed.category == ""

    def test_feed_response_with_very_long_strings(self):
        """
        Property 17: FeedResponse should handle very long strings.
        **Validates: Requirements 17.1, 17.8**
        """
        long_name = "A" * 10000
        long_category = "B" * 10000
        
        feed = FeedResponse(
            id=uuid4(),
            name=long_name,
            url="https://example.com/feed",
            category=long_category,
            is_subscribed=True
        )
        
        assert len(feed.name) == 10000
        assert len(feed.category) == 10000

    def test_feed_response_json_serialization(self):
        """
        Property 17: FeedResponse should be JSON serializable.
        **Validates: Requirements 17.1, 17.8**
        """
        feed = FeedResponse(
            id=uuid4(),
            name="Test Feed",
            url="https://example.com/feed",
            category="Tech",
            is_subscribed=True
        )
        
        json_data = feed.model_dump_json()
        assert isinstance(json_data, str)
        assert "Test Feed" in json_data
        assert "https://example.com/feed" in json_data

    def test_subscription_toggle_request_json_deserialization(self):
        """
        Property 17: SubscriptionToggleRequest should deserialize from JSON.
        **Validates: Requirements 17.2, 17.8**
        """
        feed_id = uuid4()
        json_data = f'{{"feed_id": "{feed_id}"}}'
        
        request = SubscriptionToggleRequest.model_validate_json(json_data)
        assert request.feed_id == feed_id
