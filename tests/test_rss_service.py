"""
Unit tests for RSSService
Covers: _parse_date, _fetch_feed_content, _process_single_feed, fetch_all_feeds
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.rss_service import RSSService
from app.schemas.article import RSSSource


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
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_falls_back_to_updated_parsed(self):
        """_parse_date falls back to updated_parsed when published_parsed is absent."""
        service = RSSService()
        entry = {
            "updated": "Wed, 15 May 2024 08:30:00 +0000",
            "updated_parsed": (2024, 5, 15, 8, 30, 0, 0, 0, 0),
        }
        result = service._parse_date(entry)
        assert result == datetime(2024, 5, 15, 8, 30, 0, tzinfo=timezone.utc)

    def test_returns_now_when_no_date_fields(self):
        """_parse_date returns a recent datetime when no date fields are present."""
        service = RSSService()
        before = datetime.now(timezone.utc)
        result = service._parse_date({})
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_returns_now_on_malformed_struct(self):
        """_parse_date returns a recent datetime when struct_time is malformed."""
        service = RSSService()
        entry = {"published": "not-a-date", "published_parsed": None}
        before = datetime.now(timezone.utc)
        result = service._parse_date(entry)
        after = datetime.now(timezone.utc)
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

        recent_struct = (datetime.now(timezone.utc) - timedelta(days=1)).timetuple()[:6] + (0, 0, 0)
        old_struct = (datetime.now(timezone.utc) - timedelta(days=10)).timetuple()[:6] + (0, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [
            {"title": "Recent", "link": "https://example.com/1", "summary": "content",
             "published": "recent", "published_parsed": recent_struct},
            {"title": "Old", "link": "https://example.com/2", "summary": "content",
             "published": "old", "published_parsed": old_struct},
        ]

        mock_client = AsyncMock()

        with patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")), \
             patch("app.services.rss_service.feedparser.parse", return_value=mock_feed):
            result = await service._process_single_feed(source, mock_client)

        assert len(result) == 1
        assert result[0].title == "Recent"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_fetch_error(self):
        """_process_single_feed returns [] instead of raising when fetch fails."""
        service = RSSService()
        source = make_source()
        mock_client = AsyncMock()

        with patch.object(service, "_fetch_feed_content", AsyncMock(side_effect=Exception("network error"))):
            result = await service._process_single_feed(source, mock_client)

        assert result == []

    @pytest.mark.asyncio
    async def test_article_has_correct_source_metadata(self):
        """_process_single_feed populates source_category and source_name correctly."""
        service = RSSService(days_to_fetch=7)
        source = make_source(name="MyFeed", category="DevOps")

        recent_struct = datetime.now(timezone.utc).timetuple()[:6] + (0, 0, 0)
        mock_feed = MagicMock()
        mock_feed.entries = [
            {"title": "Article", "link": "https://example.com/a", "summary": "s",
             "published": "now", "published_parsed": recent_struct},
        ]

        with patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")), \
             patch("app.services.rss_service.feedparser.parse", return_value=mock_feed):
            result = await service._process_single_feed(source, AsyncMock())

        assert result[0].source_name == "MyFeed"
        assert result[0].source_category == "DevOps"

    @pytest.mark.asyncio
    async def test_content_preview_truncated_to_800_chars(self):
        """_process_single_feed truncates content_preview to 800 characters."""
        service = RSSService(days_to_fetch=7)
        source = make_source()

        recent_struct = datetime.now(timezone.utc).timetuple()[:6] + (0, 0, 0)
        long_summary = "x" * 2000
        mock_feed = MagicMock()
        mock_feed.entries = [
            {"title": "Article", "link": "https://example.com/a", "summary": long_summary,
             "published": "now", "published_parsed": recent_struct},
        ]

        with patch.object(service, "_fetch_feed_content", AsyncMock(return_value="<xml/>")), \
             patch("app.services.rss_service.feedparser.parse", return_value=mock_feed):
            result = await service._process_single_feed(source, AsyncMock())

        assert len(result[0].content_preview) <= 800


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

        with patch.object(service, "_process_single_feed", side_effect=fake_process), \
             patch("app.services.rss_service.httpx.AsyncClient") as mock_client_cls:
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

        with patch.object(service, "_process_single_feed", side_effect=fake_process), \
             patch("app.services.rss_service.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await service.fetch_all_feeds(sources)

        # The exception is caught by gather(return_exceptions=True), result from good feed is kept
        assert len(result) == 1
