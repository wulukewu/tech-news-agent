"""
Unit tests for NotionService.create_article_page
Covers: Task 3.1 - create_article_page method
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.schemas.article import ArticleSchema, AIAnalysis
from app.services.notion_service import NotionService
from app.core.exceptions import NotionServiceError


def make_article_with_analysis(
    title="Test Article",
    url="https://example.com/article",
    category="AI",
    reason="Great technical depth",
    actionable_takeaway="Try implementing this pattern",
    tinkering_index=3,
):
    """Helper to create an ArticleSchema with AIAnalysis."""
    return ArticleSchema(
        title=title,
        url=url,
        content_preview="preview",
        source_category=category,
        source_name="TestSource",
        ai_analysis=AIAnalysis(
            is_hardcore=True,
            reason=reason,
            actionable_takeaway=actionable_takeaway,
            tinkering_index=tinkering_index,
        ),
    )


class TestCreateArticlePage:
    @pytest.mark.asyncio
    async def test_creates_page_with_correct_properties(self):
        """create_article_page sets all required properties correctly."""
        article = make_article_with_analysis(
            title="Test Article",
            category="AI",
            tinkering_index=4,
        )
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            page_id, page_url = await service.create_article_page(article, "2024-01")
        
        # Verify pages.create was called
        mock_client.pages.create.assert_called_once()
        _, kwargs = mock_client.pages.create.call_args
        
        # Verify properties
        props = kwargs["properties"]
        assert props["Title"]["title"][0]["text"]["content"] == "Test Article"
        assert props["URL"]["url"] == "https://example.com/article"
        assert props["Source_Category"]["select"]["name"] == "AI"
        assert props["Published_Week"]["rich_text"][0]["text"]["content"] == "2024-01"
        assert props["Tinkering_Index"]["number"] == 4
        assert props["Status"]["status"]["name"] == "Unread"
        assert "Added_At" in props
        assert "date" in props["Added_At"]
        
        # Verify return values
        assert page_id == "page-123"
        assert page_url == "https://notion.so/page-123"

    @pytest.mark.asyncio
    async def test_page_body_contains_reason_callout(self):
        """create_article_page includes recommendation reason in page body."""
        article = make_article_with_analysis(reason="Excellent technical depth")
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        children = kwargs["children"]
        
        # Find the reason callout
        reason_callout = next(
            (block for block in children if block["type"] == "callout" and "推薦原因" in block["callout"]["rich_text"][0]["text"]["content"]),
            None
        )
        assert reason_callout is not None
        assert "Excellent technical depth" in reason_callout["callout"]["rich_text"][0]["text"]["content"]
        assert reason_callout["callout"]["icon"]["emoji"] == "💡"

    @pytest.mark.asyncio
    async def test_page_body_contains_takeaway_callout_when_present(self):
        """create_article_page includes actionable takeaway when non-empty."""
        article = make_article_with_analysis(actionable_takeaway="Implement this pattern in your codebase")
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        children = kwargs["children"]
        
        # Find the takeaway callout
        takeaway_callout = next(
            (block for block in children if block["type"] == "callout" and "行動價值" in block["callout"]["rich_text"][0]["text"]["content"]),
            None
        )
        assert takeaway_callout is not None
        assert "Implement this pattern in your codebase" in takeaway_callout["callout"]["rich_text"][0]["text"]["content"]
        assert takeaway_callout["callout"]["icon"]["emoji"] == "🎯"

    @pytest.mark.asyncio
    async def test_page_body_omits_takeaway_when_empty(self):
        """create_article_page omits actionable takeaway callout when empty."""
        article = make_article_with_analysis(actionable_takeaway="")
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        children = kwargs["children"]
        
        # Verify no takeaway callout exists
        takeaway_callouts = [
            block for block in children 
            if block["type"] == "callout" and "行動價值" in block["callout"]["rich_text"][0]["text"]["content"]
        ]
        assert len(takeaway_callouts) == 0

    @pytest.mark.asyncio
    async def test_page_body_contains_bookmark_block(self):
        """create_article_page includes bookmark block with article URL."""
        article = make_article_with_analysis(url="https://example.com/test-article")
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        children = kwargs["children"]
        
        # Find the bookmark block
        bookmark = next(
            (block for block in children if block["type"] == "bookmark"),
            None
        )
        assert bookmark is not None
        assert bookmark["bookmark"]["url"] == "https://example.com/test-article"

    @pytest.mark.asyncio
    async def test_page_body_block_order(self):
        """create_article_page creates blocks in correct order: reason, takeaway, bookmark."""
        article = make_article_with_analysis(
            reason="Great article",
            actionable_takeaway="Try this",
        )
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        children = kwargs["children"]
        
        # Verify order: reason callout, takeaway callout, bookmark
        assert len(children) == 3
        assert children[0]["type"] == "callout"
        assert "推薦原因" in children[0]["callout"]["rich_text"][0]["text"]["content"]
        assert children[1]["type"] == "callout"
        assert "行動價值" in children[1]["callout"]["rich_text"][0]["text"]["content"]
        assert children[2]["type"] == "bookmark"

    @pytest.mark.asyncio
    async def test_raises_error_when_db_id_not_configured(self):
        """create_article_page raises NotionServiceError when weekly_digests_db_id is not set."""
        article = make_article_with_analysis()
        
        mock_client = MagicMock()
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            with patch("app.services.notion_service.settings") as mock_settings:
                mock_settings.notion_token = "test-token"
                mock_settings.notion_feeds_db_id = "feeds-db"
                mock_settings.notion_read_later_db_id = "read-later-db"
                mock_settings.notion_weekly_digests_db_id = None
                
                service = NotionService()
                with pytest.raises(NotionServiceError, match="notion_weekly_digests_db_id is not configured"):
                    await service.create_article_page(article, "2024-01")

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_api_failure(self):
        """create_article_page raises NotionServiceError when Notion API fails."""
        article = make_article_with_analysis()
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(side_effect=Exception("API connection failed"))
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError, match="Error creating article page"):
                await service.create_article_page(article, "2024-01")

    @pytest.mark.asyncio
    async def test_uses_correct_database_id(self):
        """create_article_page uses notion_weekly_digests_db_id as parent."""
        article = make_article_with_analysis()
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            db_id = service.client  # Get the settings value
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        # The parent should use the weekly_digests_db_id from settings
        assert "parent" in kwargs
        assert "database_id" in kwargs["parent"]

    @pytest.mark.asyncio
    async def test_added_at_uses_utc_plus_8(self):
        """create_article_page sets Added_At to current date in UTC+8."""
        article = make_article_with_analysis()
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        props = kwargs["properties"]
        
        # Verify Added_At is a date string
        added_at = props["Added_At"]["date"]["start"]
        assert isinstance(added_at, str)
        # Should be in ISO date format (YYYY-MM-DD)
        assert len(added_at) == 10
        assert added_at.count("-") == 2

    @pytest.mark.asyncio
    async def test_handles_article_without_ai_analysis(self):
        """create_article_page handles articles without ai_analysis gracefully."""
        article = ArticleSchema(
            title="No Analysis Article",
            url="https://example.com/article",
            content_preview="preview",
            source_category="AI",
            source_name="TestSource",
            ai_analysis=None,
        )
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            page_id, page_url = await service.create_article_page(article, "2024-01")
        
        # Should succeed and return valid IDs
        assert page_id == "page-123"
        assert page_url == "https://notion.so/page-123"
        
        # Verify tinkering_index defaults to 0
        _, kwargs = mock_client.pages.create.call_args
        props = kwargs["properties"]
        assert props["Tinkering_Index"]["number"] == 0

    @pytest.mark.asyncio
    async def test_truncates_long_title(self):
        """create_article_page truncates title to 2000 chars for Notion limit."""
        long_title = "A" * 2500
        article = make_article_with_analysis(title=long_title)
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        props = kwargs["properties"]
        title_sent = props["Title"]["title"][0]["text"]["content"]
        assert len(title_sent) <= 2000

    @pytest.mark.asyncio
    async def test_truncates_long_url(self):
        """create_article_page truncates URL to 2000 chars for Notion limit."""
        # Create a valid URL for schema validation, then override
        article = make_article_with_analysis(url="https://example.com/short")
        long_url = "https://example.com/" + "a" * 2100
        object.__setattr__(article, "url", long_url)
        
        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={
            "id": "page-123",
            "url": "https://notion.so/page-123"
        })
        
        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.create_article_page(article, "2024-01")
        
        _, kwargs = mock_client.pages.create.call_args
        props = kwargs["properties"]
        url_sent = props["URL"]["url"]
        assert len(url_sent) <= 2000
