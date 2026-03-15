"""
Preservation Tests (Pre-fix and Post-fix)
==========================================
These tests verify that existing correct behaviours are preserved.
They MUST pass on unfixed code (baseline) and continue to pass after fixes.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from hypothesis import given, settings as h_settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Preservation 1: NotionService.add_to_read_later() calls pages.create correctly
# ---------------------------------------------------------------------------

class TestPreservation1AddToReadLater:
    """
    Preservation: add_to_read_later() correctly calls pages.create with the
    right parent and properties structure.
    Validates: Requirements 3.2
    """

    @pytest.mark.asyncio
    async def test_add_to_read_later_calls_pages_create_once(self):
        """pages.create is called exactly once when add_to_read_later() is invoked."""
        from app.services.notion_service import NotionService
        from app.schemas.article import ArticleSchema

        article = ArticleSchema(
            title="Test Article",
            url="https://example.com/article",
            content_preview="preview text",
            source_category="AI",
            source_name="TestSource",
        )

        mock_client = MagicMock()
        mock_client.pages = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            await service.add_to_read_later(article)

        mock_client.pages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_read_later_parent_is_read_later_db(self):
        """pages.create is called with parent pointing to read_later_db_id."""
        from app.services.notion_service import NotionService
        from app.schemas.article import ArticleSchema

        article = ArticleSchema(
            title="Test Article",
            url="https://example.com/article",
            content_preview="preview text",
            source_category="AI",
            source_name="TestSource",
        )

        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            read_later_db_id = service.read_later_db_id
            await service.add_to_read_later(article)

        _, kwargs = mock_client.pages.create.call_args
        assert kwargs["parent"] == {"database_id": read_later_db_id}

# ---------------------------------------------------------------------------
# Preservation 2: macOS SSL patch executes correctly on darwin
# ---------------------------------------------------------------------------

class TestPreservation2SSLPatchOnMacOS:
    """
    Preservation: SSL_CERT_FILE is set when sys.platform == 'darwin'.
    Validates: Requirements 3.5
    """

    def test_ssl_patch_sets_cert_file_on_darwin(self):
        """SSL_CERT_FILE env var is set when platform is darwin."""
        # Remove cached module to force re-import
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("app.main"):
                del sys.modules[mod_name]

        os.environ.pop("SSL_CERT_FILE", None)
        os.environ.pop("SSL_CERT_DIR", None)

        mock_certifi = MagicMock()
        mock_certifi.where.return_value = "/mock/cacert.pem"

        with patch.dict(sys.modules, {"certifi": mock_certifi}):
            with patch("sys.platform", "darwin"):
                try:
                    import app.main  # noqa: F401
                except Exception:
                    pass

        # On darwin the SSL env var should be set
        assert os.environ.get("SSL_CERT_FILE") == "/mock/cacert.pem", (
            "SSL_CERT_FILE was not set on darwin — macOS SSL patch is broken."
        )


# ---------------------------------------------------------------------------
# Preservation 3: ReadLaterButton.callback calls notion.add_to_read_later()
# ---------------------------------------------------------------------------

class TestPreservation3ReadLaterButtonCallback:
    """
    Preservation: When bot has NOT restarted, ReadLaterButton.callback
    successfully calls notion.add_to_read_later().
    Validates: Requirements 3.3
    """

    @pytest.mark.asyncio
    async def test_callback_calls_add_to_read_later_once(self):
        """callback() calls NotionService.add_to_read_later exactly once."""
        from app.bot.cogs.interactions import ReadLaterButton
        from app.schemas.article import ArticleSchema

        article = ArticleSchema(
            title="Test Article",
            url="https://example.com/article",
            content_preview="preview",
            source_category="AI",
            source_name="TestSource",
        )

        button = ReadLaterButton(article=article, index=0)

        # Mock interaction
        mock_interaction = MagicMock()
        mock_interaction.response = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        mock_interaction.message = AsyncMock()
        mock_interaction.message.edit = AsyncMock()

        # Mock view via the internal _view attribute (discord.py stores it there)
        mock_view = MagicMock()
        button._view = mock_view

        mock_notion_instance = MagicMock()
        mock_notion_instance.add_to_read_later = AsyncMock()

        with patch("app.bot.cogs.interactions.NotionService", return_value=mock_notion_instance):
            await button.callback(mock_interaction)

        mock_notion_instance.add_to_read_later.assert_called_once_with(article)


# ---------------------------------------------------------------------------
# Preservation 4: get_active_feeds() returns [] when results is empty
# ---------------------------------------------------------------------------

class TestPreservation4GetActiveFeedsEmpty:
    """
    Preservation: get_active_feeds() returns an empty list (not an exception)
    when the Notion query returns no results.
    Validates: Requirements 3.6
    """

    @pytest.mark.asyncio
    async def test_get_active_feeds_returns_empty_list_not_exception(self):
        """get_active_feeds() returns [] when client.request returns empty results."""
        from app.services.notion_service import NotionService

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value={"results": []})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            result = await service.get_active_feeds()

        assert result == [], f"Expected [], got {result}"


# ---------------------------------------------------------------------------
# Preservation 5 (PBT): add_to_read_later() parent is always read_later_db_id
# ---------------------------------------------------------------------------

class TestPreservation5PBTAddToReadLater:
    """
    Property-based test: for any valid ArticleSchema, pages.create is always
    called with parent == {"database_id": read_later_db_id}.

    **Validates: Requirements 3.2**
    """

    @pytest.mark.asyncio
    @given(
        title=st.text(min_size=1, max_size=100),
        url=st.from_regex(r"https://[a-z]{3,10}\.[a-z]{2,4}/[a-z]{0,20}", fullmatch=True),
        source_category=st.text(min_size=1, max_size=50),
    )
    @h_settings(max_examples=30)
    async def test_parent_always_read_later_db_id(self, title, url, source_category):
        """pages.create parent is always {"database_id": read_later_db_id} for any article."""
        from app.services.notion_service import NotionService
        from app.schemas.article import ArticleSchema

        article = ArticleSchema(
            title=title,
            url=url,
            content_preview="preview",
            source_category=source_category,
            source_name="TestSource",
        )

        mock_client = MagicMock()
        mock_client.pages.create = AsyncMock(return_value={"id": "page-id"})

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            read_later_db_id = service.read_later_db_id
            await service.add_to_read_later(article)

        _, kwargs = mock_client.pages.create.call_args
        assert kwargs["parent"] == {"database_id": read_later_db_id}, (
            f"Expected parent={{'database_id': '{read_later_db_id}'}}, "
            f"got {kwargs.get('parent')}"
        )
