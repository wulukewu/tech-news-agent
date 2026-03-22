"""
Unit tests for NotionService
Covers: get_active_feeds, add_to_read_later, add_feed
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.article import ArticleSchema, RSSSource
from app.services.notion_service import NotionService
from app.core.exceptions import NotionServiceError


def make_article(title="Test Article", url="https://example.com/article", category="AI"):
    return ArticleSchema(
        title=title,
        url=url,
        content_preview="preview",
        source_category=category,
        source_name="TestSource",
    )


def make_notion_page(name="Feed Name", url="https://example.com/feed.xml", category="AI", active=True):
    return {
        "properties": {
            "Name": {"title": [{"plain_text": name}]},
            "URL": {"url": url},
            "Category": {"select": {"name": category}},
            "Active": {"checkbox": active},
        }
    }


# ---------------------------------------------------------------------------
# get_active_feeds
# ---------------------------------------------------------------------------

class TestGetActiveFeeds:
    @pytest.mark.asyncio
    async def test_returns_rss_sources_from_notion(self):
        """get_active_feeds parses Notion pages into RSSSource objects."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value={
            "results": [make_notion_page(name="HN", url="https://hn.com/rss", category="Tech")]
        })

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_active_feeds()

        assert len(result) == 1
        assert isinstance(result[0], RSSSource)
        assert result[0].name == "HN"
        assert result[0].category == "Tech"

    @pytest.mark.asyncio
    async def test_skips_pages_with_missing_url(self):
        """get_active_feeds skips Notion pages that have no URL property."""
        page_no_url = {
            "properties": {
                "Name": {"title": [{"plain_text": "No URL Feed"}]},
                "URL": {"url": None},
                "Category": {"select": {"name": "AI"}},
            }
        }
        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value={"results": [page_no_url]})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_active_feeds()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_results(self):
        """get_active_feeds returns [] when Notion returns empty results."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_active_feeds()

        assert result == []

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_exception(self):
        """get_active_feeds wraps exceptions as NotionServiceError."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=Exception("connection refused"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.get_active_feeds()

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_attribute_error(self):
        """get_active_feeds wraps AttributeError (e.g. SDK changes) as NotionServiceError."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=AttributeError("no attribute 'request'"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.get_active_feeds()

    @pytest.mark.asyncio
    async def test_uses_category_uncategorized_when_select_is_none(self):
        """get_active_feeds defaults category to 'Uncategorized' when select is null."""
        page = {
            "properties": {
                "Name": {"title": [{"plain_text": "Feed"}]},
                "URL": {"url": "https://example.com/rss"},
                "Category": {"select": None},
            }
        }
        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value={"results": [page]})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_active_feeds()

        assert result[0].category == "Uncategorized"


# ---------------------------------------------------------------------------
# add_to_read_later
# ---------------------------------------------------------------------------

class TestAddToReadLater:
    @pytest.mark.asyncio
    async def test_calls_pages_create_once(self):
        """add_to_read_later calls pages.create exactly once."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.add_to_read_later(make_article())

        mock_client.pages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_parent_is_read_later_db_id(self):
        """add_to_read_later uses read_later_db_id as the parent database."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            db_id = service.read_later_db_id
            await service.add_to_read_later(make_article())

        _, kwargs = mock_client.pages.create.call_args
        assert kwargs["parent"] == {"database_id": db_id}

    @pytest.mark.asyncio
    async def test_url_is_truncated_to_2000_chars(self):
        """add_to_read_later truncates URL to 2000 chars for Notion's limit."""
        long_url = "https://example.com/" + "a" * 2100
        article = make_article(url="https://example.com/short")  # valid URL for schema
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        # Manually override url after construction to simulate edge case
        object.__setattr__(article, "url", long_url)

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.add_to_read_later(article)

        _, kwargs = mock_client.pages.create.call_args
        url_sent = kwargs["properties"]["URL"]["url"]
        assert len(url_sent) <= 2000

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """add_to_read_later raises NotionServiceError when pages.create fails."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.add_to_read_later(make_article())


# ---------------------------------------------------------------------------
# add_feed
# ---------------------------------------------------------------------------

class TestAddFeed:
    @pytest.mark.asyncio
    async def test_calls_pages_create_with_correct_properties(self):
        """add_feed creates a Notion page with Name, URL, Category, and Active=True."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.add_feed("HN", "https://news.ycombinator.com/rss", "Tech")

        _, kwargs = mock_client.pages.create.call_args
        props = kwargs["properties"]
        assert props["Active"]["checkbox"] is True
        assert props["Category"]["select"]["name"] == "Tech"
        assert props["URL"]["url"] == "https://news.ycombinator.com/rss"

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """add_feed raises NotionServiceError when pages.create fails."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.add_feed("Feed", "https://example.com/rss", "AI")

    @pytest.mark.asyncio
    async def test_parent_is_feeds_db_id(self):
        """add_feed uses feeds_db_id as the parent database."""
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            feeds_db_id = service.feeds_db_id
            await service.add_feed("Feed", "https://example.com/rss", "AI")

        _, kwargs = mock_client.pages.create.call_args
        assert kwargs["parent"] == {"database_id": feeds_db_id}


# ---------------------------------------------------------------------------
# Helpers for ReadingListItem tests
# ---------------------------------------------------------------------------

def make_notion_reading_page(
    page_id="page-001",
    title="Test Article",
    url="https://example.com/article",
    status="Unread",
    category="AI",
    added_at="2024-01-01T00:00:00+00:00",
    rating=None,
):
    rating_prop = {"number": rating} if rating is not None else {"number": None}
    return {
        "id": page_id,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "URL": {"url": url},
            "Status": {"status": {"name": status}},
            "Source_Category": {"select": {"name": category}},
            "Added_At": {"date": {"start": added_at}},
            "Rating": rating_prop,
        }
    }


# ---------------------------------------------------------------------------
# get_reading_list
# ---------------------------------------------------------------------------

class TestGetReadingList:
    @pytest.mark.asyncio
    async def test_returns_reading_list_items(self):
        """get_reading_list returns a list of ReadingListItem for Unread pages."""
        from app.schemas.article import ReadingListItem
        page = make_notion_reading_page()
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": [page]})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_reading_list()

        assert len(result) == 1
        assert isinstance(result[0], ReadingListItem)
        assert result[0].page_id == "page-001"
        assert result[0].title == "Test Article"

    @pytest.mark.asyncio
    async def test_filters_by_unread_status(self):
        """get_reading_list passes the correct Unread filter to Notion."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.get_reading_list()

        _, kwargs = mock_client.databases.query.call_args
        assert kwargs["filter"]["property"] == "Status"
        assert kwargs["filter"]["status"]["equals"] == "Unread"

    @pytest.mark.asyncio
    async def test_rating_is_none_when_not_set(self):
        """get_reading_list sets rating=None when Notion Rating field is null."""
        page = make_notion_reading_page(rating=None)
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": [page]})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_reading_list()

        assert result[0].rating is None

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_results(self):
        """get_reading_list returns [] when Notion returns no pages."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_reading_list()

        assert result == []

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """get_reading_list raises NotionServiceError on API failure."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.get_reading_list()


# ---------------------------------------------------------------------------
# mark_as_read
# ---------------------------------------------------------------------------

class TestMarkAsRead:
    @pytest.mark.asyncio
    async def test_calls_pages_update_with_read_status(self):
        """mark_as_read calls pages.update with Status='Read' for the given page_id."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(return_value={})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.mark_as_read("page-001")

        mock_client.pages.update.assert_called_once()
        _, kwargs = mock_client.pages.update.call_args
        assert kwargs["page_id"] == "page-001"
        assert kwargs["properties"]["Status"]["status"]["name"] == "Read"

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """mark_as_read raises NotionServiceError on API failure."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.mark_as_read("page-001")


# ---------------------------------------------------------------------------
# rate_article
# ---------------------------------------------------------------------------

class TestRateArticle:
    @pytest.mark.asyncio
    async def test_calls_pages_update_with_rating(self):
        """rate_article calls pages.update with the correct Rating number."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(return_value={})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.rate_article("page-001", 4)

        mock_client.pages.update.assert_called_once()
        _, kwargs = mock_client.pages.update.call_args
        assert kwargs["page_id"] == "page-001"
        assert kwargs["properties"]["Rating"]["number"] == 4

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """rate_article raises NotionServiceError on API failure."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.rate_article("page-001", 3)


# ---------------------------------------------------------------------------
# get_highly_rated_articles
# ---------------------------------------------------------------------------

class TestGetHighlyRatedArticles:
    @pytest.mark.asyncio
    async def test_returns_articles_above_threshold(self):
        """get_highly_rated_articles returns articles with rating >= threshold."""
        page = make_notion_reading_page(rating=5)
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": [page]})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_highly_rated_articles(threshold=4)

        assert len(result) == 1
        assert result[0].rating == 5

    @pytest.mark.asyncio
    async def test_uses_correct_filter(self):
        """get_highly_rated_articles passes the correct number filter to Notion."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.get_highly_rated_articles(threshold=4)

        _, kwargs = mock_client.databases.query.call_args
        assert kwargs["filter"]["property"] == "Rating"
        assert kwargs["filter"]["number"]["greater_than_or_equal_to"] == 4

    @pytest.mark.asyncio
    async def test_default_threshold_is_4(self):
        """get_highly_rated_articles defaults threshold to 4."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.get_highly_rated_articles()

        _, kwargs = mock_client.databases.query.call_args
        assert kwargs["filter"]["number"]["greater_than_or_equal_to"] == 4

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_failure(self):
        """get_highly_rated_articles raises NotionServiceError on API failure."""
        mock_client = MagicMock()
        mock_client.databases = MagicMock()
        mock_client.databases.query = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError):
                await service.get_highly_rated_articles()
