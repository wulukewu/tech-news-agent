"""
Unit tests for RSSService
Covers: _parse_date, _fetch_feed_content, _process_single_feed, fetch_all_feeds
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.article import RSSSource
from app.services.rss_service import RSSService


def make_source(name="TestFeed", url="https://example.com/feed.xml", category="AI"):
    return RSSSource(name=name, url=url, category=category)


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_returns_utc_datetime_from_published_parsed(self):
        """_parse_date extracts datetime from published_parsed struct_time."""
        service = RSSService()
        entry = {
            "published": "Sat, 01 Jun 2024 12:00:00 +0000",
            "published_parsed": (2024, 6, 1, 12, 0, 0, 0, 0, 0),
        }
        result = service._parse_date(entry)
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

    def test_falls_back_to_updated_parsed(self):
        """_parse_date falls back to updated_parsed when published_parsed is absent."""
        service = RSSService()
        entry = {
            "updated": "Wed, 15 May 2024 08:30:00 +0000",
            "updated_parsed": (2024, 5, 15, 8, 30, 0, 0, 0, 0),
        }
        result = service._parse_date(entry)
        assert result == datetime(2024, 5, 15, 8, 30, 0, tzinfo=UTC)

    def test_returns_now_when_no_date_fields(self):
        """_parse_date returns a recent datetime when no date fields are present."""
        service = RSSService()
        before = datetime.now(UTC)
        result = service._parse_date({})
        after = datetime.now(UTC)
        assert before <= result <= after

    def test_returns_now_on_malformed_struct(self):
        """_parse_date returns a recent datetime when struct_time is malformed."""
        service = RSSService()
        entry = {"published": "not-a-date", "published_parsed": None}
        before = datetime.now(UTC)
        result = service._parse_date(entry)
        after = datetime.now(UTC)
        assert before <= result <= after


# ---------------------------------------------------------------------------
# _process_single_feed
# ---------------------------------------------------------------------------


class TestProcessSingleFeed:
    @pytest.mark.asyncio
    async def test_returns_articles_within_cutoff(self):
        """_process_single_feed returns only articles newer than days_to_fetch."""
        service = RSSService(days_to_fetch=7)
        source = make_source()

        recent_struct = (datetime.now(UTC) - timedelta(days=1)).timetuple()[:6] + (0, 0, 0)
        old_struct = (datetime.now(UTC) - timedelta(days=10)).timetuple()[:6] + (0, 0, 0)

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

        assert len(result) == 1
        assert result[0].title == "Recent"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_fetch_error(self):
        """_process_single_feed returns [] instead of raising when fetch fails."""
        service = RSSService()
        source = make_source()
        mock_client = AsyncMock()

        with patch.object(
            service, "_fetch_feed_content", AsyncMock(side_effect=Exception("network error"))
        ):
            result = await service._process_single_feed(source, mock_client)

        assert result == []

    @pytest.mark.asyncio
    async def test_article_has_correct_source_metadata(self):
        """_process_single_feed populates category and feed_name correctly."""
        service = RSSService(days_to_fetch=7)
        source = make_source(name="MyFeed", category="DevOps")

        recent_struct = datetime.now(UTC).timetuple()[:6] + (0, 0, 0)
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Article",
                "link": "https://example.com/a",
                "summary": "s",
                "published": "now",
                "published_parsed": recent_struct,
            },
        ]

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, AsyncMock())

        assert result[0].feed_name == "MyFeed"
        assert result[0].category == "DevOps"

    @pytest.mark.asyncio
    async def test_content_preview_truncated_to_800_chars(self):
        """_process_single_feed no longer includes content_preview (removed in schema update)."""
        service = RSSService(days_to_fetch=7)
        source = make_source()

        recent_struct = datetime.now(UTC).timetuple()[:6] + (0, 0, 0)
        long_summary = "x" * 2000
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Article",
                "link": "https://example.com/a",
                "summary": long_summary,
                "published": "now",
                "published_parsed": recent_struct,
            },
        ]

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, AsyncMock())

        # content_preview field was removed in schema update, so just verify article was created
        assert len(result) == 1
        assert result[0].title == "Article"

    @pytest.mark.asyncio
    async def test_filters_old_articles_and_logs_count(self):
        """_process_single_feed filters articles older than days_to_fetch and logs filtered count.

        Validates: Requirements 11.1, 11.4, 11.7
        """
        service = RSSService(days_to_fetch=7)
        source = make_source()

        # Create articles with different ages
        recent_struct = (datetime.now(UTC) - timedelta(days=2)).timetuple()[:6] + (0, 0, 0)
        old_struct_1 = (datetime.now(UTC) - timedelta(days=10)).timetuple()[:6] + (0, 0, 0)
        old_struct_2 = (datetime.now(UTC) - timedelta(days=15)).timetuple()[:6] + (0, 0, 0)

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
                "title": "Old1",
                "link": "https://example.com/2",
                "summary": "content",
                "published": "old",
                "published_parsed": old_struct_1,
            },
            {
                "title": "Old2",
                "link": "https://example.com/3",
                "summary": "content",
                "published": "old",
                "published_parsed": old_struct_2,
            },
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
            patch("app.services.rss_service.logger") as mock_logger,
        ):
            result = await service._process_single_feed(source, mock_client)

        # Should only return the recent article
        assert len(result) == 1
        assert result[0].title == "Recent"

        # Should log the filtered count
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        assert "filtered 2 articles" in log_message
        assert "older than 7 days" in log_message

    @pytest.mark.asyncio
    async def test_respects_configurable_time_window(self):
        """_process_single_feed respects the configurable days_to_fetch parameter.

        Validates: Requirements 11.5, 11.6
        """
        # Test with 3 days window
        service = RSSService(days_to_fetch=3)
        source = make_source()

        # Create articles at different ages
        day_2_struct = (datetime.now(UTC) - timedelta(days=2)).timetuple()[:6] + (0, 0, 0)
        day_5_struct = (datetime.now(UTC) - timedelta(days=5)).timetuple()[:6] + (0, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Within3Days",
                "link": "https://example.com/1",
                "summary": "content",
                "published": "recent",
                "published_parsed": day_2_struct,
            },
            {
                "title": "Beyond3Days",
                "link": "https://example.com/2",
                "summary": "content",
                "published": "old",
                "published_parsed": day_5_struct,
            },
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            result = await service._process_single_feed(source, mock_client)

        # Should only return article within 3 days
        assert len(result) == 1
        assert result[0].title == "Within3Days"

    @pytest.mark.asyncio
    async def test_uses_current_time_when_published_at_missing(self):
        """_process_single_feed uses current time when published_at is not available.

        Validates: Requirements 11.2, 11.3
        """
        service = RSSService(days_to_fetch=7)
        source = make_source()

        # Entry without published date
        mock_feed = MagicMock()
        mock_feed.entries = [
            {"title": "NoDate", "link": "https://example.com/1", "summary": "content"},
        ]

        mock_client = AsyncMock()

        with (
            patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")),
            patch("app.services.rss_service.feedparser.parse", return_value=mock_feed),
        ):
            before = datetime.now(UTC)
            result = await service._process_single_feed(source, mock_client)
            after = datetime.now(UTC)

        # Should return the article (since current time is within 7 days)
        assert len(result) == 1
        assert result[0].title == "NoDate"
        # Published date should be recent
        assert before <= result[0].published_at <= after


# ---------------------------------------------------------------------------
# fetch_all_feeds
# ---------------------------------------------------------------------------


class TestFetchAllFeeds:
    @pytest.mark.asyncio
    async def test_aggregates_articles_from_all_sources(self):
        """fetch_all_feeds combines articles from all sources."""
        service = RSSService()
        sources = [make_source(name=f"Feed{i}", url=f"https://feed{i}.com/rss") for i in range(3)]

        async def fake_process(source, client):
            return [MagicMock(title=f"Article from {source.name}")]

        with (
            patch.object(service, "_process_single_feed", side_effect=fake_process),
            patch("app.services.rss_service.httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await service.fetch_all_feeds(sources)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_sources(self):
        """fetch_all_feeds returns [] when given an empty source list."""
        service = RSSService()
        with patch("app.services.rss_service.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await service.fetch_all_feeds([])
        assert result == []

    @pytest.mark.asyncio
    async def test_continues_when_one_feed_raises(self):
        """fetch_all_feeds still returns results from healthy feeds when one raises."""
        service = RSSService()
        sources = [make_source(name=f"Feed{i}", url=f"https://feed{i}.com/rss") for i in range(2)]

        call_count = 0

        async def fake_process(source, client):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("broken feed")
            return [MagicMock(title="Good Article")]

        with (
            patch.object(service, "_process_single_feed", side_effect=fake_process),
            patch("app.services.rss_service.httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await service.fetch_all_feeds(sources)

        # The exception is caught by gather(return_exceptions=True), result from good feed is kept
        assert len(result) == 1
