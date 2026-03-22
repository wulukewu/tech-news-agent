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


# ---------------------------------------------------------------------------
# Preservation 6 (PBT): Short drafts are sent unmodified
# ---------------------------------------------------------------------------

class TestPreservation6DiscordShortDraft:
    """
    Property 2: Preservation - Short Draft Sent Unmodified

    For all draft strings where len(draft) <= 2000 (isBugCondition = False),
    the news_now handler SHALL send the content unmodified in a single
    followup.send call.

    Observation on unfixed code:
      - followup.send(content=draft, view=view) is called with the exact draft string
      - No modification occurs when len(draft) <= 2000

    **Validates: Requirements 3.1, 3.2**
    """

    @pytest.mark.asyncio
    @given(draft=st.text(min_size=0, max_size=2000))
    @h_settings(max_examples=50)
    async def test_short_draft_sent_unmodified(self, draft):
        """
        Property 2: Preservation - for any draft where len(draft) <= 2000,
        followup.send is called exactly once with the content unchanged.
        """
        from app.bot.cogs.news_commands import NewsCommands

        mock_bot = MagicMock()
        cog = NewsCommands(mock_bot)

        mock_interaction = MagicMock()
        mock_interaction.response = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        mock_interaction.user = MagicMock()

        mock_notion = MagicMock()
        mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])

        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[MagicMock(ai_analysis=MagicMock(tinkering_index=3))])
        mock_llm.generate_weekly_newsletter = AsyncMock(return_value=draft)

        mock_filter_view = MagicMock()
        mock_filter_view.children = []
        mock_deep_dive_view = MagicMock()
        mock_deep_dive_view.children = []

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion), \
             patch("app.bot.cogs.news_commands.RSSService", return_value=mock_rss), \
             patch("app.bot.cogs.news_commands.LLMService", return_value=mock_llm), \
             patch("app.bot.cogs.interactions.FilterView", return_value=mock_filter_view), \
             patch("app.bot.cogs.interactions.DeepDiveView", return_value=mock_deep_dive_view):
            await cog.news_now.callback(cog, mock_interaction)

        mock_interaction.followup.send.assert_called_once()
        call_kwargs = mock_interaction.followup.send.call_args
        content_sent = call_kwargs.kwargs.get("content", call_kwargs.args[0] if call_kwargs.args else "")
        assert content_sent == draft, (
            f"Preservation broken: draft of len {len(draft)} was modified. "
            f"Expected content == draft, got len={len(content_sent)}"
        )
        # view must always be attached
        view_sent = call_kwargs.kwargs.get("view")
        assert view_sent is not None, "Preservation broken: view not attached to followup.send"


# ---------------------------------------------------------------------------
# Helpers for combined_view property tests
# ---------------------------------------------------------------------------

def article_strategy():
    """Hypothesis strategy that generates valid ArticleSchema instances."""
    from app.schemas.article import ArticleSchema
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=80),
        url=st.from_regex(r"https://[a-z]{3,10}\.[a-z]{2,4}/[a-z]{0,20}", fullmatch=True),
        content_preview=st.text(min_size=0, max_size=200),
        source_category=st.text(min_size=1, max_size=40),
        source_name=st.text(min_size=1, max_size=40),
        published_date=st.none(),
        ai_analysis=st.none(),
        raw_data=st.none(),
    )


def build_combined_view_fixed(articles):
    """Replicate the FIXED combined_view assembly logic (MAX_READ_LATER = 15)."""
    from app.bot.cogs.interactions import FilterView, DeepDiveView, ReadLaterView
    combined_view = FilterView(articles=articles)
    for item in DeepDiveView(articles=articles[:5]).children:
        combined_view.add_item(item)
    MAX_READ_LATER = 15
    read_later_view = ReadLaterView(articles=articles[:MAX_READ_LATER])
    for item in read_later_view.children:
        combined_view.add_item(item)
    return combined_view


# ---------------------------------------------------------------------------
# Preservation 7 (PBT): FilterSelect always present and first
# ---------------------------------------------------------------------------

class TestPreservation7FilterSelectAlwaysFirst:
    """
    Property 2: Preservation — FilterSelect is always present and is the
    first element in combined_view.children for any non-empty article list.

    **Validates: Requirements 3.1, 3.4**
    """

    @given(st.lists(article_strategy(), min_size=1, max_size=50))
    @h_settings(max_examples=50)
    def test_filter_select_present_and_first(self, articles):
        """FilterSelect is present in combined_view.children and is the first element."""
        from app.bot.cogs.interactions import FilterSelect

        combined_view = build_combined_view_fixed(articles)

        types = [type(c) for c in combined_view.children]
        assert FilterSelect in types, (
            f"FilterSelect not found in combined_view.children: {types}"
        )
        assert isinstance(combined_view.children[0], FilterSelect), (
            f"First element is {type(combined_view.children[0])}, expected FilterSelect"
        )


# ---------------------------------------------------------------------------
# Preservation 8 (PBT): DeepDiveButton count = min(5, len(articles))
# ---------------------------------------------------------------------------

class TestPreservation8DeepDiveButtonCount:
    """
    Property 2: Preservation — DeepDiveButton count equals min(5, len(articles))
    for any article list.

    **Validates: Requirements 3.1, 3.4**
    """

    @given(st.lists(article_strategy(), min_size=0, max_size=50))
    @h_settings(max_examples=50)
    def test_deep_dive_button_count(self, articles):
        """DeepDiveButton count equals min(5, len(articles)) in combined_view."""
        from app.bot.cogs.interactions import DeepDiveButton

        combined_view = build_combined_view_fixed(articles)

        count = sum(1 for c in combined_view.children if isinstance(c, DeepDiveButton))
        expected = min(5, len(articles))
        assert count == expected, (
            f"Expected {expected} DeepDiveButton(s) for {len(articles)} articles, got {count}"
        )


# ---------------------------------------------------------------------------
# Preservation 9 (PBT): ReadLaterButton count = min(len(articles), 15)
# ---------------------------------------------------------------------------

class TestPreservation9ReadLaterButtonCount:
    """
    Property 1: Bug condition fix — ReadLaterButton count equals
    min(len(articles), 15) for any article list.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    @given(st.lists(article_strategy(), min_size=0, max_size=50))
    @h_settings(max_examples=50)
    def test_read_later_button_count(self, articles):
        """ReadLaterButton count equals min(len(articles), 15) in combined_view."""
        from app.bot.cogs.interactions import ReadLaterButton

        combined_view = build_combined_view_fixed(articles)

        count = sum(1 for c in combined_view.children if isinstance(c, ReadLaterButton))
        expected = min(len(articles), 15)
        assert count == expected, (
            f"Expected {expected} ReadLaterButton(s) for {len(articles)} articles, got {count}"
        )
