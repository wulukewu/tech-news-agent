"""
Unit tests for NotionService.mark_article_as_read
Covers: mark_article_as_read method
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotionServiceError
from app.services.notion_service import NotionService


class TestMarkArticleAsRead:
    @pytest.mark.asyncio
    async def test_calls_pages_update_with_read_status(self):
        """mark_article_as_read calls pages.update with Status='Read' for the given page_id."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(return_value={})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.mark_article_as_read("article-page-001")

        mock_client.pages.update.assert_called_once()
        _, kwargs = mock_client.pages.update.call_args
        assert kwargs["page_id"] == "article-page-001"
        assert kwargs["properties"]["Status"]["status"]["name"] == "Read"

    @pytest.mark.asyncio
    async def test_raises_notion_service_error_on_api_failure(self):
        """mark_article_as_read raises NotionServiceError when Notion API fails."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(side_effect=Exception("API connection error"))

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError) as exc_info:
                await service.mark_article_as_read("article-page-001")

            assert "Error updating article page status in Notion" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_call_parameters_are_correct(self):
        """mark_article_as_read passes correct parameters to Notion API."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(return_value={"id": "article-page-001"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.mark_article_as_read("article-page-001")

        # Verify the exact structure of the API call
        call_args = mock_client.pages.update.call_args
        assert call_args is not None
        _, kwargs = call_args

        # Verify page_id parameter
        assert kwargs["page_id"] == "article-page-001"

        # Verify properties structure
        assert "properties" in kwargs
        assert "Status" in kwargs["properties"]
        assert kwargs["properties"]["Status"] == {"status": {"name": "Read"}}

    @pytest.mark.asyncio
    async def test_handles_different_page_ids(self):
        """mark_article_as_read works with different page ID formats."""
        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.update = AsyncMock(return_value={})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()

            # Test with UUID format
            await service.mark_article_as_read("123e4567-e89b-12d3-a456-426614174000")

            # Test with short ID
            await service.mark_article_as_read("abc123")

            # Test with hyphenated ID
            await service.mark_article_as_read("page-id-with-hyphens")

        # Verify all three calls were made
        assert mock_client.pages.update.call_count == 3
