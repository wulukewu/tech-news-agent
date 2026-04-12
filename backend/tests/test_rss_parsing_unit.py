"""
Unit tests for RSS feed parsing
Task 7.2: 撰寫 RSS 解析的單元測試

Tests RSS feed entry parsing to ArticleSchema:
- RSS feed entry parsing to ArticleSchema
- published_at timestamp parsing
- Timezone information preservation
- Special characters handling
- NULL value handling

Validates Requirements: 17.1, 17.2, 17.6, 17.7
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService


class TestRSSParsing:
    """Unit tests for RSS feed parsing functionality"""

    def test_parse_rss_entry_to_article_schema(self):
        """
        Test that RSS feed entries are correctly parsed into ArticleSchema objects.

        Validates: Requirements 17.1
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        feed_id = uuid4()

        # Mock RSS entry
        entry = {
            "title": "Test Article Title",
            "link": "https://example.com/article",
            "published": "Mon, 01 Jan 2024 12:00:00 GMT",
            "published_parsed": (2024, 1, 1, 12, 0, 0, 0, 1, 0),
        }

        # Act
        published_date = service._parse_date(entry)

        article = ArticleSchema(
            title=entry["title"],
            url=entry["link"],
            feed_id=feed_id,
            feed_name="Test Feed",
            category="Test",
            published_at=published_date,
        )

        # Assert
        assert article.title == "Test Article Title"
        assert str(article.url) == "https://example.com/article"
        assert article.feed_id == feed_id
        assert article.feed_name == "Test Feed"
        assert article.category == "Test"
        assert article.published_at is not None
        assert isinstance(article.published_at, datetime)

    def test_parse_published_at_timestamp(self):
        """
        Test that published_at timestamps are correctly parsed from RSS entries.

        Validates: Requirements 17.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        # Test various date formats
        test_cases = [
            {
                "entry": {
                    "published": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "published_parsed": (2024, 1, 1, 12, 0, 0, 0, 1, 0),
                },
                "expected_year": 2024,
                "expected_month": 1,
                "expected_day": 1,
            },
            {
                "entry": {
                    "updated": "Tue, 15 Feb 2024 08:30:00 GMT",
                    "updated_parsed": (2024, 2, 15, 8, 30, 0, 1, 46, 0),
                },
                "expected_year": 2024,
                "expected_month": 2,
                "expected_day": 15,
            },
        ]

        for test_case in test_cases:
            # Act
            parsed_date = service._parse_date(test_case["entry"])

            # Assert
            assert parsed_date is not None
            assert isinstance(parsed_date, datetime)
            assert parsed_date.year == test_case["expected_year"]
            assert parsed_date.month == test_case["expected_month"]
            assert parsed_date.day == test_case["expected_day"]

    def test_timezone_information_preserved(self):
        """
        Test that timezone information is preserved when parsing timestamps.

        Validates: Requirements 17.6
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        entry = {
            "published": "Mon, 01 Jan 2024 12:00:00 GMT",
            "published_parsed": (2024, 1, 1, 12, 0, 0, 0, 1, 0),
        }

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        assert parsed_date.tzinfo is not None, "Timezone information should be present"
        assert parsed_date.tzinfo == UTC, "Timezone should be UTC"

    def test_special_characters_in_title(self):
        """
        Test that special characters in article titles are correctly handled.

        Validates: Requirements 17.7
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        feed_id = uuid4()

        # Test titles with special characters
        special_titles = [
            "Article with <HTML> tags",
            "Article with \"quotes\" and 'apostrophes'",
            "Article with & ampersand",
            "Article with émojis 🚀 and ñ",
            "Article with special chars: @#$%^&*()",
        ]

        for title in special_titles:
            # Act
            article = ArticleSchema(
                title=title,
                url="https://example.com/article",
                feed_id=feed_id,
                feed_name="Test Feed",
                category="Test",
            )

            # Assert
            assert (
                article.title == title
            ), f"Special characters should be preserved in title: {title}"

    def test_special_characters_in_url(self):
        """
        Test that special characters in URLs are correctly handled.

        Validates: Requirements 17.7
        """
        # Arrange
        feed_id = uuid4()

        # Test URLs with special characters
        special_urls = [
            "https://example.com/article?param=value&other=123",
            "https://example.com/article%20with%20spaces",
            "https://example.com/article-with-dashes",
            "https://example.com/article_with_underscores",
            "https://example.com/article~with~tildes",
        ]

        for url in special_urls:
            # Act
            article = ArticleSchema(
                title="Test Article",
                url=url,
                feed_id=feed_id,
                feed_name="Test Feed",
                category="Test",
            )

            # Assert
            assert str(article.url) == url, f"Special characters should be preserved in URL: {url}"

    def test_null_published_at_handling(self):
        """
        Test that NULL published_at values are correctly handled.

        Validates: Requirements 17.7
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        # Entry without date information
        entry = {"title": "Article without date", "link": "https://example.com/article"}

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        # When no date is available, should default to current time
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)

        # Should be very recent (within last minute)
        now = datetime.now(UTC)
        time_diff = abs((now - parsed_date).total_seconds())
        assert time_diff < 60, "Default timestamp should be current time"

    def test_null_optional_fields_handling(self):
        """
        Test that NULL values for optional fields are correctly handled.

        Validates: Requirements 17.7
        """
        # Arrange
        feed_id = uuid4()

        # Act - Create article with NULL optional fields
        article = ArticleSchema(
            title="Test Article",
            url="https://example.com/article",
            feed_id=feed_id,
            feed_name="Test Feed",
            category="Test",
            published_at=None,
            tinkering_index=None,
            ai_summary=None,
        )

        # Assert
        assert article.published_at is None
        assert article.tinkering_index is None
        assert article.ai_summary is None

    def test_parse_date_with_published_field(self):
        """
        Test parsing date from 'published' field in RSS entry.

        Validates: Requirements 17.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        entry = {
            "published": "Wed, 20 Mar 2024 15:45:00 GMT",
            "published_parsed": (2024, 3, 20, 15, 45, 0, 2, 80, 0),
        }

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        assert parsed_date.year == 2024
        assert parsed_date.month == 3
        assert parsed_date.day == 20
        assert parsed_date.hour == 15
        assert parsed_date.minute == 45

    def test_parse_date_with_updated_field(self):
        """
        Test parsing date from 'updated' field when 'published' is not available.

        Validates: Requirements 17.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        entry = {
            "updated": "Thu, 21 Mar 2024 10:30:00 GMT",
            "updated_parsed": (2024, 3, 21, 10, 30, 0, 3, 81, 0),
        }

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        assert parsed_date.year == 2024
        assert parsed_date.month == 3
        assert parsed_date.day == 21
        assert parsed_date.hour == 10
        assert parsed_date.minute == 30

    def test_parse_date_fallback_to_current_time(self):
        """
        Test that parsing falls back to current time when no date fields are available.

        Validates: Requirements 17.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        entry = {"title": "Article without any date fields"}

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)

        # Should be current time (within 1 second)
        now = datetime.now(UTC)
        time_diff = abs((now - parsed_date).total_seconds())
        assert time_diff < 1, "Should default to current time"

    def test_parse_date_with_invalid_format(self):
        """
        Test that invalid date formats are handled gracefully.

        Validates: Requirements 17.2
        """
        # Arrange
        service = RSSService(days_to_fetch=7)

        entry = {
            "published": "Invalid date format",
            # No published_parsed field
        }

        # Act
        parsed_date = service._parse_date(entry)

        # Assert
        # Should fall back to current time
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)

        now = datetime.now(UTC)
        time_diff = abs((now - parsed_date).total_seconds())
        assert time_diff < 1, "Should fall back to current time on parse error"

    @pytest.mark.asyncio
    async def test_process_single_feed_creates_article_schemas(self):
        """
        Test that _process_single_feed correctly creates ArticleSchema objects.

        Validates: Requirements 17.1
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        feed_id = uuid4()

        source = RSSSource(name="Test Feed", url="https://example.com/rss", category="Test")

        # Generate recent dates for the articles (within last 7 days)
        from datetime import datetime

        recent_date1 = datetime.now(UTC)
        recent_date2 = datetime.now(UTC)

        # Format dates in RFC 2822 format for RSS
        date1_str = recent_date1.strftime("%a, %d %b %Y %H:%M:%S GMT")
        date2_str = recent_date2.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Mock RSS feed XML with recent dates
        mock_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article 1</title>
                    <link>https://example.com/article1</link>
                    <pubDate>{date1_str}</pubDate>
                </item>
                <item>
                    <title>Test Article 2</title>
                    <link>https://example.com/article2</link>
                    <pubDate>{date2_str}</pubDate>
                </item>
            </channel>
        </rss>
        """

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = mock_xml
        mock_client.get = AsyncMock(return_value=mock_response)

        feed_id_map = {str(source.url): feed_id}

        # Act
        articles = await service._process_single_feed(source, mock_client, feed_id_map)

        # Assert
        assert len(articles) == 2
        assert all(isinstance(article, ArticleSchema) for article in articles)
        assert articles[0].title == "Test Article 1"
        assert str(articles[0].url) == "https://example.com/article1"
        assert articles[1].title == "Test Article 2"
        assert str(articles[1].url) == "https://example.com/article2"

    @pytest.mark.asyncio
    async def test_process_single_feed_handles_special_characters(self):
        """
        Test that RSS parsing correctly handles special characters in feed entries.

        Validates: Requirements 17.7
        """
        # Arrange
        service = RSSService(days_to_fetch=7)
        feed_id = uuid4()

        source = RSSSource(name="Test Feed", url="https://example.com/rss", category="Test")

        # Generate recent date
        from datetime import datetime

        recent_date = datetime.now(UTC)
        date_str = recent_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Mock RSS feed with special characters and recent date
        mock_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article with &lt;HTML&gt; &amp; "quotes"</title>
                    <link>https://example.com/article?param=value&amp;other=123</link>
                    <pubDate>{date_str}</pubDate>
                </item>
            </channel>
        </rss>
        """

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = mock_xml
        mock_client.get = AsyncMock(return_value=mock_response)

        feed_id_map = {str(source.url): feed_id}

        # Act
        articles = await service._process_single_feed(source, mock_client, feed_id_map)

        # Assert
        assert len(articles) == 1
        # feedparser automatically decodes HTML entities
        assert "<HTML>" in articles[0].title or "&lt;HTML&gt;" in articles[0].title
        assert "&" in articles[0].title or "&amp;" in articles[0].title
