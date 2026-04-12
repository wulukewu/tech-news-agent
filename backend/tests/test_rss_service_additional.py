"""
Additional unit tests for RSSService to ensure complete coverage
Task 2.5: 撰寫 RSS Service 的單元測試

These tests complement existing tests in test_rss_service.py and
test_rss_service_fetch_new_articles.py to ensure complete coverage of:
- Default 7-day time window (Requirement 11.6)
- Individual feed failure handling in fetch_new_articles context (Requirement 2.7)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService


def make_source(name="TestFeed", url="https://example.com/feed.xml", category="AI"):
    """Helper to create a test RSSSource"""
    return RSSSource(name=name, url=url, category=category)


class TestRSSServiceDefaults:
    """Test default configuration values"""

    def test_default_days_to_fetch_is_7(self):
        """RSSService should default to 7 days when days_to_fetch is not specified.

        Validates: Requirements 11.6
        """
        # Arrange & Act
        service = RSSService()

        # Assert
        assert service.days_to_fetch == 7

    @pytest.mark.asyncio
    async def test_default_time_window_filters_correctly(self):
        """RSSService with default configuration should filter articles older than 7 days.

        Validates: Requirements 11.1, 11.6
        """
        # Arrange
        service = RSSService()  # Use default days_to_fetch
        source = make_source()

        # Create articles: one within 7 days, one older than 7 days
        recent_struct = (datetime.now(UTC) - timedelta(days=5)).timetuple()[:6] + (0, 0, 0)
        old_struct = (datetime.now(UTC) - timedelta(days=8)).timetuple()[:6] + (0, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Recent",
                "link": "https://example.com/1",
                "summary": "content",
                "published": "recent",
                "published_parsed": recent_struct,
            },
            {
                "title": "Old",
                "link": "https://example.com/2",
                "summary": "content",
                "published": "old",
                "published_parsed": old_struct,
            },
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, mock_client)

        # Assert - should only return the recent article (within default 7 days)
        assert len(result) == 1
        assert result[0].title == "Recent"


class TestFetchNewArticlesErrorHandling:
    """Test error handling in fetch_new_articles method"""

    @pytest.mark.asyncio
    async def test_fetch_all_feeds_failure_propagates(self):
        """fetch_new_articles should handle fetch_all_feeds failures gracefully.

        Validates: Requirements 2.7, 7.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]
        mock_supabase = AsyncMock()

        # Mock fetch_all_feeds to raise an exception
        with patch.object(
            service, "fetch_all_feeds", AsyncMock(side_effect=Exception("Network error"))
        ):
            # Act & Assert - should raise the exception
            with pytest.raises(Exception, match="Network error"):
                await service.fetch_new_articles(sources, mock_supabase)

    @pytest.mark.asyncio
    async def test_logs_error_on_check_failure(self):
        """fetch_new_articles should log errors when check_article_exists fails.

        Validates: Requirements 2.7
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        from uuid import uuid4

        article1 = ArticleSchema(
            title="Article 1",
            url="https://example.com/article1",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
        )

        # Mock fetch_all_feeds to return one article
        with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=[article1])):
            # Mock supabase service to fail
            mock_supabase = AsyncMock()
            mock_supabase.check_article_exists = AsyncMock(side_effect=Exception("Database error"))

            # Act
            with patch("app.services.rss_service.logger") as mock_logger:
                result = await service.fetch_new_articles(sources, mock_supabase)

            # Assert - should log the error
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "Failed to check existence" in error_call
            assert "article1" in error_call

            # Should still return the article (assumes new on error)
            assert len(result) == 1
            assert result[0] == article1


class TestTimeWindowConfiguration:
    """Test configurable time window behavior"""

    @pytest.mark.asyncio
    async def test_custom_time_window_1_day(self):
        """RSSService should respect custom time window of 1 day.

        Validates: Requirements 11.5
        """
        # Arrange
        service = RSSService(days_to_fetch=1)
        source = make_source()

        # Create articles at different ages
        hours_12_struct = (datetime.now(UTC) - timedelta(hours=12)).timetuple()[:6] + (
            0,
            0,
            0,
        )
        days_2_struct = (datetime.now(UTC) - timedelta(days=2)).timetuple()[:6] + (0, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Within1Day",
                "link": "https://example.com/1",
                "summary": "content",
                "published": "recent",
                "published_parsed": hours_12_struct,
            },
            {
                "title": "Beyond1Day",
                "link": "https://example.com/2",
                "summary": "content",
                "published": "old",
                "published_parsed": days_2_struct,
            },
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, mock_client)

        # Assert - should only return article within 1 day
        assert len(result) == 1
        assert result[0].title == "Within1Day"

    @pytest.mark.asyncio
    async def test_custom_time_window_30_days(self):
        """RSSService should respect custom time window of 30 days.

        Validates: Requirements 11.5
        """
        # Arrange
        service = RSSService(days_to_fetch=30)
        source = make_source()

        # Create articles at different ages
        days_20_struct = (datetime.now(UTC) - timedelta(days=20)).timetuple()[:6] + (
            0,
            0,
            0,
        )
        days_35_struct = (datetime.now(UTC) - timedelta(days=35)).timetuple()[:6] + (
            0,
            0,
            0,
        )

        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Within30Days",
                "link": "https://example.com/1",
                "summary": "content",
                "published": "recent",
                "published_parsed": days_20_struct,
            },
            {
                "title": "Beyond30Days",
                "link": "https://example.com/2",
                "summary": "content",
                "published": "old",
                "published_parsed": days_35_struct,
            },
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, mock_client)

        # Assert - should only return article within 30 days
        assert len(result) == 1
        assert result[0].title == "Within30Days"


class TestPublishedAtHandling:
    """Test published_at timestamp handling edge cases"""

    @pytest.mark.asyncio
    async def test_missing_all_date_fields(self):
        """_parse_date should use current time when all date fields are missing.

        Validates: Requirements 11.2, 11.3
        """
        # Arrange
        service = RSSService()
        entry = {}  # No date fields at all

        # Act
        before = datetime.now(UTC)
        result = service._parse_date(entry)
        after = datetime.now(UTC)

        # Assert
        assert before <= result <= after
        assert result.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_malformed_date_string(self):
        """_parse_date should use current time when date string is malformed.

        Validates: Requirements 11.2, 11.3
        """
        # Arrange
        service = RSSService()
        entry = {"published": "not-a-valid-date", "published_parsed": None}

        # Act
        before = datetime.now(UTC)
        result = service._parse_date(entry)
        after = datetime.now(UTC)

        # Assert
        assert before <= result <= after
        assert result.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_article_with_missing_published_at_is_included(self):
        """Articles with missing published_at should be included (using current time).

        Validates: Requirements 11.2, 11.3
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        source = make_source()

        # Entry without any date fields
        mock_feed = MagicMock()
        mock_feed.entries = [
            {"title": "NoDate", "link": "https://example.com/1", "summary": "content"},
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, mock_client)

        # Assert - should include the article (current time is within 7 days)
        assert len(result) == 1
        assert result[0].title == "NoDate"
        # Verify published_at is recent
        assert (datetime.now(UTC) - result[0].published_at).total_seconds() < 5
