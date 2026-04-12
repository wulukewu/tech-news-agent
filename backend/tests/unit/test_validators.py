"""
Unit tests for business rule validators.

Tests the validation logic in app/core/validators.py to ensure
business rules are enforced correctly before data persistence.

Validates: Requirements 14.2, 14.3
"""

from uuid import uuid4

import pytest

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import (
    ArticleValidator,
    BusinessRuleValidator,
    FeedValidator,
    ReadingListValidator,
    UserValidator,
)


class TestBusinessRuleValidator:
    """Test base validator helper methods."""

    def test_validate_required_field_success(self):
        """Required field validation should pass for valid data."""
        data = {"name": "Test"}
        # Should not raise
        BusinessRuleValidator.validate_required_field(data, "name", str)

    def test_validate_required_field_missing(self):
        """Required field validation should fail for missing field."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_required_field(data, "name", str)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD
        assert "name" in exc_info.value.details["field"]

    def test_validate_string_length_success(self):
        """String length validation should pass for valid length."""
        # Should not raise
        BusinessRuleValidator.validate_string_length("test", "field", min_length=1, max_length=10)

    def test_validate_string_length_too_short(self):
        """String length validation should fail for too short string."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_string_length("", "field", min_length=1)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_string_length_too_long(self):
        """String length validation should fail for too long string."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_string_length("toolong", "field", max_length=5)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_integer_range_success(self):
        """Integer range validation should pass for valid range."""
        # Should not raise
        BusinessRuleValidator.validate_integer_range(5, "field", min_value=1, max_value=10)

    def test_validate_integer_range_too_low(self):
        """Integer range validation should fail for too low value."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_integer_range(0, "field", min_value=1)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_integer_range_too_high(self):
        """Integer range validation should fail for too high value."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_integer_range(11, "field", max_value=10)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_enum_value_success(self):
        """Enum validation should pass for valid value."""
        # Should not raise
        BusinessRuleValidator.validate_enum_value("Read", "status", {"Unread", "Read", "Archived"})

    def test_validate_enum_value_invalid(self):
        """Enum validation should fail for invalid value."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessRuleValidator.validate_enum_value(
                "Invalid", "status", {"Unread", "Read", "Archived"}
            )

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT


class TestUserValidator:
    """Test user-specific business rule validation."""

    def test_validate_discord_id_success(self):
        """Valid Discord ID should pass validation."""
        # Should not raise
        UserValidator.validate_discord_id("12345678901234567")  # 17 digits
        UserValidator.validate_discord_id("123456789012345678")  # 18 digits
        UserValidator.validate_discord_id("1234567890123456789")  # 19 digits
        UserValidator.validate_discord_id("12345678901234567890")  # 20 digits

    def test_validate_discord_id_empty(self):
        """Empty Discord ID should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserValidator.validate_discord_id("")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "empty" in exc_info.value.message.lower()

    def test_validate_discord_id_non_numeric(self):
        """Non-numeric Discord ID should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserValidator.validate_discord_id("abc123")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "numeric" in exc_info.value.message.lower()

    def test_validate_discord_id_too_short(self):
        """Too short Discord ID should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserValidator.validate_discord_id("123456")  # Only 6 digits

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "17-20" in exc_info.value.message

    def test_validate_discord_id_too_long(self):
        """Too long Discord ID should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserValidator.validate_discord_id("123456789012345678901")  # 21 digits

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "17-20" in exc_info.value.message

    def test_validate_user_create_success(self):
        """Valid user creation data should pass validation."""
        data = {"discord_id": "12345678901234567", "dm_notifications_enabled": True}
        # Should not raise
        UserValidator.validate_user_create(data)

    def test_validate_user_create_missing_discord_id(self):
        """User creation without discord_id should fail."""
        data = {"dm_notifications_enabled": True}
        with pytest.raises(ValidationError) as exc_info:
            UserValidator.validate_user_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    def test_validate_user_update_success(self):
        """Valid user update data should pass validation."""
        data = {"dm_notifications_enabled": False}
        # Should not raise
        UserValidator.validate_user_update(data)


class TestFeedValidator:
    """Test feed-specific business rule validation."""

    def test_validate_url_format_success(self):
        """Valid URLs should pass validation."""
        # Should not raise
        FeedValidator.validate_url_format("https://example.com/feed.xml")
        FeedValidator.validate_url_format("http://example.com/feed")

    def test_validate_url_format_empty(self):
        """Empty URL should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            FeedValidator.validate_url_format("")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_url_format_no_protocol(self):
        """URL without protocol should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            FeedValidator.validate_url_format("example.com/feed")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "http" in exc_info.value.message.lower()

    def test_validate_url_format_too_long(self):
        """URL exceeding max length should fail validation."""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ValidationError) as exc_info:
            FeedValidator.validate_url_format(long_url)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "2048" in exc_info.value.message

    def test_validate_feed_create_success(self):
        """Valid feed creation data should pass validation."""
        data = {
            "name": "Tech News",
            "url": "https://example.com/feed.xml",
            "category": "Technology",
            "is_active": True,
        }
        # Should not raise
        FeedValidator.validate_feed_create(data)

    def test_validate_feed_create_missing_fields(self):
        """Feed creation without required fields should fail."""
        data = {"name": "Tech News"}
        with pytest.raises(ValidationError) as exc_info:
            FeedValidator.validate_feed_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD


class TestArticleValidator:
    """Test article-specific business rule validation."""

    def test_validate_article_create_success(self):
        """Valid article creation data should pass validation."""
        data = {
            "feed_id": str(uuid4()),
            "title": "New AI Breakthrough",
            "url": "https://example.com/article",
            "tinkering_index": 4,
        }
        # Should not raise
        ArticleValidator.validate_article_create(data)

    def test_validate_article_create_missing_fields(self):
        """Article creation without required fields should fail."""
        data = {"title": "Test"}
        with pytest.raises(ValidationError) as exc_info:
            ArticleValidator.validate_article_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    def test_validate_article_tinkering_index_valid_range(self):
        """Tinkering index in valid range (1-5) should pass."""
        for index in range(1, 6):
            data = {
                "feed_id": str(uuid4()),
                "title": "Test Article",
                "url": "https://example.com/test",
                "tinkering_index": index,
            }
            # Should not raise
            ArticleValidator.validate_article_create(data)

    def test_validate_article_tinkering_index_too_low(self):
        """Tinkering index below 1 should fail."""
        data = {
            "feed_id": str(uuid4()),
            "title": "Test Article",
            "url": "https://example.com/test",
            "tinkering_index": 0,
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticleValidator.validate_article_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_article_tinkering_index_too_high(self):
        """Tinkering index above 5 should fail."""
        data = {
            "feed_id": str(uuid4()),
            "title": "Test Article",
            "url": "https://example.com/test",
            "tinkering_index": 6,
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticleValidator.validate_article_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_article_title_too_long(self):
        """Article title exceeding max length should fail."""
        data = {
            "feed_id": str(uuid4()),
            "title": "a" * 2001,  # Exceeds 2000 char limit
            "url": "https://example.com/test",
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticleValidator.validate_article_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "2000" in exc_info.value.message

    def test_validate_article_ai_summary_too_long(self):
        """AI summary exceeding max length should fail."""
        data = {
            "feed_id": str(uuid4()),
            "title": "Test Article",
            "url": "https://example.com/test",
            "ai_summary": "a" * 5001,  # Exceeds 5000 char limit
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticleValidator.validate_article_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "5000" in exc_info.value.message


class TestReadingListValidator:
    """Test reading list-specific business rule validation."""

    def test_validate_reading_list_create_success(self):
        """Valid reading list creation data should pass validation."""
        data = {
            "user_id": str(uuid4()),
            "article_id": str(uuid4()),
            "status": "Unread",
            "rating": 4,
        }
        # Should not raise
        ReadingListValidator.validate_reading_list_create(data)

    def test_validate_reading_list_create_missing_fields(self):
        """Reading list creation without required fields should fail."""
        data = {"status": "Unread"}
        with pytest.raises(ValidationError) as exc_info:
            ReadingListValidator.validate_reading_list_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    def test_validate_reading_list_status_valid_values(self):
        """Valid status values should pass validation."""
        for status in ["Unread", "Read", "Archived"]:
            data = {"user_id": str(uuid4()), "article_id": str(uuid4()), "status": status}
            # Should not raise
            ReadingListValidator.validate_reading_list_create(data)

    def test_validate_reading_list_status_invalid(self):
        """Invalid status value should fail validation."""
        data = {"user_id": str(uuid4()), "article_id": str(uuid4()), "status": "Invalid"}
        with pytest.raises(ValidationError) as exc_info:
            ReadingListValidator.validate_reading_list_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
        assert "Unread" in exc_info.value.message
        assert "Read" in exc_info.value.message
        assert "Archived" in exc_info.value.message

    def test_validate_reading_list_rating_valid_range(self):
        """Rating in valid range (1-5) should pass."""
        for rating in range(1, 6):
            data = {
                "user_id": str(uuid4()),
                "article_id": str(uuid4()),
                "status": "Read",
                "rating": rating,
            }
            # Should not raise
            ReadingListValidator.validate_reading_list_create(data)

    def test_validate_reading_list_rating_too_low(self):
        """Rating below 1 should fail."""
        data = {"user_id": str(uuid4()), "article_id": str(uuid4()), "status": "Read", "rating": 0}
        with pytest.raises(ValidationError) as exc_info:
            ReadingListValidator.validate_reading_list_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_reading_list_rating_too_high(self):
        """Rating above 5 should fail."""
        data = {"user_id": str(uuid4()), "article_id": str(uuid4()), "status": "Read", "rating": 6}
        with pytest.raises(ValidationError) as exc_info:
            ReadingListValidator.validate_reading_list_create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_INVALID_FORMAT

    def test_validate_reading_list_rating_null_allowed(self):
        """Null rating should be allowed."""
        data = {
            "user_id": str(uuid4()),
            "article_id": str(uuid4()),
            "status": "Unread",
            "rating": None,
        }
        # Should not raise
        ReadingListValidator.validate_reading_list_create(data)

    def test_validate_status_transition_success(self):
        """Valid status transitions should pass."""
        # All transitions are allowed for flexibility
        transitions = [
            ("Unread", "Read"),
            ("Read", "Archived"),
            ("Unread", "Archived"),
            ("Archived", "Unread"),
            ("Read", "Unread"),
        ]
        for current, new in transitions:
            # Should not raise
            ReadingListValidator.validate_status_transition(current, new)
