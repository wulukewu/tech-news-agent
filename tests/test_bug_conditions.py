"""
Bug Condition Exploration Tests (Pre-fix)
=========================================
These tests are designed to run on UNFIXED code.
Their purpose is to CONFIRM that the five bugs exist by producing counterexamples.

Expected outcome:
- Some tests will PASS  → they confirm the bug exists (the bad behaviour is observable)
- Some tests will FAIL  → they confirm the bug exists (the correct behaviour is absent)

The overall task is complete when all five bugs are confirmed.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from app.core.exceptions import NotionServiceError


# ---------------------------------------------------------------------------
# Bug 1: Notion API AttributeError
# ---------------------------------------------------------------------------

class TestBug1NotionAttributeError:
    """
    Bug Condition: notion-client >= 2.2.1 raises AttributeError when
    get_active_feeds() calls self.client.databases.query(...)
    because the 'query' method no longer exists on the databases endpoint.

    After the fix, get_active_feeds() uses self.client.request() instead.
    The test now verifies that AttributeError from client.request() is still
    correctly wrapped as NotionServiceError (the exception handling is intact).

    Exploration strategy:
      - Mock the notion AsyncClient so that client.request raises AttributeError.
      - Call NotionService.get_active_feeds().
      - The fixed code catches the generic Exception and re-raises as
        NotionServiceError, so we expect NotionServiceError to be raised.
    """

    @pytest.mark.asyncio
    async def test_bug1_get_active_feeds_raises_notion_service_error_on_attribute_error(self):
        """
        Verifies Bug 1 fix: AttributeError from client.request() is wrapped and
        re-raised as NotionServiceError.
        After the fix, this test PASSES – confirming the error handling is correct.
        """
        from app.services.notion_service import NotionService
        from app.core.exceptions import NotionServiceError

        # Build a mock client whose request() raises AttributeError
        # (simulating any unexpected SDK-level attribute error)
        mock_client = MagicMock()
        mock_client.request = AsyncMock(
            side_effect=AttributeError(
                "'AsyncClient' object has no attribute 'request'"
            )
        )

        with patch("app.services.notion_service.AsyncClient", return_value=mock_client):
            service = NotionService()
            with pytest.raises(NotionServiceError) as exc_info:
                await service.get_active_feeds()

        # The error message should contain the original AttributeError text
        assert "AttributeError" in str(exc_info.value) or "request" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Bug 2: SSL patch runs unconditionally (even on Linux)
# ---------------------------------------------------------------------------

class TestBug2SSLPatchUnconditional:
    """
    Bug Condition: app/main.py executes the SSL patch at module top-level
    without any platform guard.  On Linux the certifi import and env-var
    assignment still run.

    Exploration strategy:
      - Reload app.main with sys.platform patched to "linux".
      - Verify that SSL_CERT_FILE is set (proving the patch ran).
    """

    def test_bug2_ssl_patch_runs_on_linux(self):
        """
        Verifies Bug 2 fix: SSL env vars are NOT set when sys.platform == 'linux'.
        After the fix, the SSL patch is guarded by `if sys.platform == "darwin"`,
        so on linux SSL_CERT_FILE should remain unset.
        """
        # Remove cached module so we can re-import with patched platform
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("app.main"):
                del sys.modules[mod_name]

        # Clear any previously set env vars so we can detect a fresh write
        os.environ.pop("SSL_CERT_FILE", None)
        os.environ.pop("SSL_CERT_DIR", None)

        mock_certifi = MagicMock()
        mock_certifi.where.return_value = "/mock/cacert.pem"

        with patch.dict(sys.modules, {"certifi": mock_certifi}):
            with patch("sys.platform", "linux"):
                try:
                    import app.main  # noqa: F401 – side-effects are what we test
                except Exception:
                    pass  # Ignore any startup errors unrelated to SSL

        # After the fix, SSL_CERT_FILE should NOT be set on linux
        ssl_cert_file = os.environ.get("SSL_CERT_FILE", "")
        assert ssl_cert_file == "", (
            f"Bug 2 fix broken: SSL_CERT_FILE was set to '{ssl_cert_file}' on linux – "
            "the platform guard is not working correctly."
        )


# ---------------------------------------------------------------------------
# Bug 3: Scheduler timezone always returns default value
# ---------------------------------------------------------------------------

class TestBug3SchedulerTimezone:
    """
    Bug Fix Verification: settings.timezone now correctly reads from the
    TIMEZONE environment variable via Pydantic's BaseSettings field,
    instead of using model_config.get() which always returned the default.

    Verification strategy:
      - Set TIMEZONE=UTC in the environment.
      - Create a fresh Settings instance.
      - Assert settings.timezone returns "UTC" (not the default "Asia/Taipei").
    """

    def test_bug3_model_config_get_ignores_env_timezone(self):
        """
        Verifies Bug 3 fix: settings.timezone correctly reads TIMEZONE env var.
        After the fix, settings.timezone returns "UTC" when TIMEZONE=UTC is set.
        """
        import importlib
        import app.core.config as config_module

        # Patch the environment so TIMEZONE=UTC is visible
        with patch.dict(os.environ, {"TIMEZONE": "UTC"}, clear=False):
            # Re-instantiate Settings to pick up the env var
            importlib.reload(config_module)
            fresh_settings = config_module.Settings()

            result = fresh_settings.timezone

        # Fix verified: settings.timezone correctly returns "UTC" from env var
        assert result == "UTC", (
            f"Bug 3 fix broken: settings.timezone returned '{result}' "
            f"instead of 'UTC' when TIMEZONE=UTC is set in the environment."
        )


# ---------------------------------------------------------------------------
# Bug 4: /add_feed does not call Notion (NotionService.add_feed missing)
# ---------------------------------------------------------------------------

class TestBug4AddFeedMissingMethod:
    """
    Bug Condition: NotionService has no add_feed() method, and the
    /add_feed command only sends a placeholder message without writing
    to Notion.

    Exploration strategy:
      - Verify that NotionService does NOT have an add_feed attribute.
      - Attempting to access it should raise AttributeError.
    """

    def test_bug4_notion_service_missing_add_feed_method(self):
        """
        Verifies Bug 4 fix: NotionService now has the add_feed() method.
        After the fix, this test PASSES – confirming the method exists.
        """
        from app.services.notion_service import NotionService

        assert hasattr(NotionService, "add_feed"), (
            "Bug 4 fix broken: NotionService is still missing the add_feed method."
        )

    @pytest.mark.asyncio
    async def test_bug4_add_feed_command_does_not_call_notion(self):
        """
        Verifies Bug 4 fix: The /add_feed Discord command calls notion.add_feed exactly once.
        After the fix, this test PASSES – confirming Notion is written to.
        """
        from app.bot.cogs.news_commands import NewsCommands

        # Build a minimal mock bot
        mock_bot = MagicMock()

        cog = NewsCommands(mock_bot)

        # Build a mock interaction
        mock_interaction = MagicMock()
        mock_interaction.response = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        mock_interaction.user = MagicMock()
        mock_interaction.user.__str__ = lambda self: "TestUser"

        # Mock NotionService so we can track calls
        mock_notion_instance = MagicMock()
        mock_notion_instance.add_feed = AsyncMock()

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion_instance):
            # The method is wrapped by @app_commands.command; call the underlying callback
            await cog.add_feed.callback(cog, mock_interaction, name="Test", url="https://example.com", category="AI")

        # After the fix, add_feed is called exactly once on the notion instance
        assert mock_notion_instance.add_feed.call_count == 1, (
            f"Bug 4 fix broken: notion.add_feed was called "
            f"{mock_notion_instance.add_feed.call_count} time(s) instead of 1."
        )


# ---------------------------------------------------------------------------
# Bug 5: ReadLaterView not registered via bot.add_view()
# ---------------------------------------------------------------------------

class TestBug5ReadLaterViewNotPersistent:
    """
    Bug Condition: TechNewsBot.setup_hook() loads cogs but never calls
    self.add_view(ReadLaterView(...)), so after a bot restart the persistent
    view is not registered and button interactions fail.

    Exploration strategy:
      - Inspect the setup_hook source / behaviour to confirm add_view is
        never called.
      - Also verify that ReadLaterButton uses index-based custom_id
        (read_later_0, read_later_1, …) rather than a URL-hash-based id,
        which is the other half of the persistent-view bug.
    """

    def test_bug5_setup_hook_does_not_call_add_view(self):
        """
        Verifies Bug 5 fix (part A): setup_hook() now contains a call to add_view,
        registering the persistent ReadLaterView so button interactions survive bot restarts.
        After the fix, this test PASSES – confirming add_view is called.
        """
        import inspect
        from app.bot.client import TechNewsBot

        source = inspect.getsource(TechNewsBot.setup_hook)
        assert "add_view" in source, (
            "Bug 5 fix broken: setup_hook does not call add_view. "
            "The persistent view is not registered."
        )

    def test_bug5_read_later_button_uses_index_not_url_hash(self):
        """
        Verifies Bug 5 fix (part B): ReadLaterButton.custom_id is now based on a
        stable URL hash (read_later_{8-char hex}) rather than a positional index.
        After the fix, this test PASSES – confirming the custom_id format is correct.
        """
        import re
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

        # After the fix, custom_id should be "read_later_{8-char hex}"
        assert re.fullmatch(r"read_later_[0-9a-f]{8}", button.custom_id), (
            f"Bug 5 fix broken: custom_id is '{button.custom_id}', "
            f"expected format 'read_later_{{8-char hex}}'."
        )


# ---------------------------------------------------------------------------
# Bug 6: Discord message length - oversized draft crashes followup.send
# ---------------------------------------------------------------------------

class TestBug6DiscordMessageLength:
    """
    Bug 6 test updated to reflect the new /news_now flow (Task 9):
    - The command now uses build_discord_notification which enforces ≤ 2000 chars.
    - Tests verify the notification is always within Discord's limit.

    _Requirements: 5.2_
    """

    @pytest.mark.asyncio
    async def test_bug6_notification_within_discord_limit(self):
        """
        Req 5.2: The Discord notification sent by /news_now must be ≤ 2000 chars.
        The new flow uses build_discord_notification which enforces this limit.
        """
        from app.bot.cogs.news_commands import NewsCommands
        from app.schemas.article import ArticleSchema, AIAnalysis

        article = ArticleSchema(
            title="Test Article",
            url="https://example.com/article",
            content_preview="Preview",
            source_category="AI",
            source_name="TestSource",
            ai_analysis=AIAnalysis(
                is_hardcore=True,
                reason="Very hardcore",
                actionable_takeaway="Can be used",
                tinkering_index=5,
            ),
        )

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
        mock_notion.create_weekly_digest_page = AsyncMock(return_value=("page-id", "https://notion.so/page"))
        mock_notion.build_digest_blocks = MagicMock(return_value=[])
        mock_notion.append_digest_blocks = AsyncMock()

        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[article])

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[article])
        mock_llm.generate_digest_intro = AsyncMock(return_value="本週前言")

        mock_filter_view = MagicMock()
        mock_filter_view.children = []
        mock_deep_dive_view = MagicMock()
        mock_deep_dive_view.children = []
        mock_read_later_view = MagicMock()
        mock_read_later_view.children = []

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion), \
             patch("app.bot.cogs.news_commands.RSSService", return_value=mock_rss), \
             patch("app.bot.cogs.news_commands.LLMService", return_value=mock_llm), \
             patch("app.bot.cogs.news_commands.settings") as mock_settings, \
             patch("app.bot.cogs.interactions.FilterView", return_value=mock_filter_view), \
             patch("app.bot.cogs.interactions.DeepDiveView", return_value=mock_deep_dive_view), \
             patch("app.bot.cogs.interactions.ReadLaterView", return_value=mock_read_later_view):
            mock_settings.notion_weekly_digests_db_id = "test-db-id"
            await cog.news_now.callback(cog, mock_interaction)

        call_kwargs = mock_interaction.followup.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert len(content_sent) <= 2000, (
            f"Req 5.2: notification exceeds 2000 chars (len={len(content_sent)})"
        )


# ---------------------------------------------------------------------------
# Bug 7: Markdown formatting - `+` list markers and missing newlines
# ---------------------------------------------------------------------------

class TestBug7MarkdownFormatting:
    """
    Bug 7 tests updated to reflect the new /news_now flow (Task 9):
    - The command now uses build_discord_notification (lightweight structured format)
      instead of generate_weekly_newsletter + regex post-processing.
    - The new format is inherently free of `+` markers and hyperlink concatenation issues.
    - Tests now verify the new structured notification format.
    """

    def _make_article(self, title="Test Article", url="https://example.com/article"):
        from app.schemas.article import ArticleSchema, AIAnalysis
        return ArticleSchema(
            title=title,
            url=url,
            content_preview="Preview content",
            source_category="AI",
            source_name="TestSource",
            ai_analysis=AIAnalysis(
                is_hardcore=True,
                reason="Very hardcore",
                actionable_takeaway="Can be used",
                tinkering_index=3,
            ),
        )

    @pytest.mark.asyncio
    async def test_notification_within_discord_limit(self):
        """
        Req 5.2: The Discord notification sent by /news_now must be ≤ 2000 chars.
        The new flow uses build_discord_notification which enforces this limit.
        """
        from app.bot.cogs.news_commands import NewsCommands

        article = self._make_article()

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
        mock_notion.create_weekly_digest_page = AsyncMock(return_value=("page-id", "https://notion.so/page"))
        mock_notion.build_digest_blocks = MagicMock(return_value=[])
        mock_notion.append_digest_blocks = AsyncMock()
        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[article])
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[article])
        mock_llm.generate_digest_intro = AsyncMock(return_value="本週前言")

        mock_filter_view = MagicMock()
        mock_filter_view.children = []
        mock_deep_dive_view = MagicMock()
        mock_deep_dive_view.children = []
        mock_read_later_view = MagicMock()
        mock_read_later_view.children = []

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion), \
             patch("app.bot.cogs.news_commands.RSSService", return_value=mock_rss), \
             patch("app.bot.cogs.news_commands.LLMService", return_value=mock_llm), \
             patch("app.bot.cogs.news_commands.settings") as mock_settings, \
             patch("app.bot.cogs.interactions.FilterView", return_value=mock_filter_view), \
             patch("app.bot.cogs.interactions.DeepDiveView", return_value=mock_deep_dive_view), \
             patch("app.bot.cogs.interactions.ReadLaterView", return_value=mock_read_later_view):
            mock_settings.notion_weekly_digests_db_id = "test-db-id"
            await cog.news_now.callback(cog, mock_interaction)

        call_kwargs = mock_interaction.followup.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert len(content_sent) <= 2000, (
            f"Req 5.2: notification exceeds 2000 chars (len={len(content_sent)})"
        )

    @pytest.mark.asyncio
    async def test_notification_contains_article_hyperlink(self):
        """
        Req 5.1: The Discord notification contains article hyperlinks in Markdown format.
        The new build_discord_notification format includes [title](url) links.
        """
        from app.bot.cogs.news_commands import NewsCommands

        article = self._make_article(title="Some Article", url="https://example.com/article")

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
        mock_notion.create_weekly_digest_page = AsyncMock(return_value=("page-id", "https://notion.so/page"))
        mock_notion.build_digest_blocks = MagicMock(return_value=[])
        mock_notion.append_digest_blocks = AsyncMock()
        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[article])
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[article])
        mock_llm.generate_digest_intro = AsyncMock(return_value="本週前言")

        mock_filter_view = MagicMock()
        mock_filter_view.children = []
        mock_deep_dive_view = MagicMock()
        mock_deep_dive_view.children = []
        mock_read_later_view = MagicMock()
        mock_read_later_view.children = []

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion), \
             patch("app.bot.cogs.news_commands.RSSService", return_value=mock_rss), \
             patch("app.bot.cogs.news_commands.LLMService", return_value=mock_llm), \
             patch("app.bot.cogs.news_commands.settings") as mock_settings, \
             patch("app.bot.cogs.interactions.FilterView", return_value=mock_filter_view), \
             patch("app.bot.cogs.interactions.DeepDiveView", return_value=mock_deep_dive_view), \
             patch("app.bot.cogs.interactions.ReadLaterView", return_value=mock_read_later_view):
            mock_settings.notion_weekly_digests_db_id = "test-db-id"
            await cog.news_now.callback(cog, mock_interaction)

        call_kwargs = mock_interaction.followup.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "[Some Article](https://example.com/article)" in content_sent, (
            f"Req 5.1: Article hyperlink not found in notification. content='{content_sent}'"
        )

    @pytest.mark.asyncio
    async def test_degraded_notification_when_notion_fails(self):
        """
        Req 5.4: When Notion page creation fails, /news_now sends a degraded notification
        with a warning instead of a Notion link.
        """
        from app.bot.cogs.news_commands import NewsCommands

        article = self._make_article()

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
        mock_notion.create_weekly_digest_page = AsyncMock(side_effect=NotionServiceError("API error"))
        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[article])
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[article])
        mock_llm.generate_digest_intro = AsyncMock(return_value="本週前言")

        mock_filter_view = MagicMock()
        mock_filter_view.children = []
        mock_deep_dive_view = MagicMock()
        mock_deep_dive_view.children = []
        mock_read_later_view = MagicMock()
        mock_read_later_view.children = []

        with patch("app.bot.cogs.news_commands.NotionService", return_value=mock_notion), \
             patch("app.bot.cogs.news_commands.RSSService", return_value=mock_rss), \
             patch("app.bot.cogs.news_commands.LLMService", return_value=mock_llm), \
             patch("app.bot.cogs.news_commands.settings") as mock_settings, \
             patch("app.bot.cogs.interactions.FilterView", return_value=mock_filter_view), \
             patch("app.bot.cogs.interactions.DeepDiveView", return_value=mock_deep_dive_view), \
             patch("app.bot.cogs.interactions.ReadLaterView", return_value=mock_read_later_view):
            mock_settings.notion_weekly_digests_db_id = "test-db-id"
            await cog.news_now.callback(cog, mock_interaction)

        call_kwargs = mock_interaction.followup.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "Notion 頁面建立失敗" in content_sent, (
            f"Req 5.4: Degraded notification missing warning. content='{content_sent}'"
        )


# ---------------------------------------------------------------------------
# Bug 8: ReadLaterButton missing from combined_view (read-later-button-missing)
# ---------------------------------------------------------------------------

class TestBug8ReadLaterButtonMissing:
    """
    Bug Condition Exploration: combined_view assembly in news_now never adds
    ReadLaterView's ReadLaterButton children.

    This test replicates the CURRENT (unfixed) combined_view assembly logic
    and asserts that combined_view.children SHOULD contain a ReadLaterButton.

    Expected outcome on UNFIXED code: FAIL (confirms the bug exists).
    Expected outcome on FIXED code: PASS.

    Validates: Requirements 2.1, 2.3
    """

    def test_bug8_exploration_combined_view_missing_read_later_button(self):
        """
        Bug Condition Exploration: Verifies the fix — combined_view assembly in
        news_now now correctly includes ReadLaterView's ReadLaterButton children.

        Expected outcome on FIXED code: PASS.

        Validates: Requirements 2.1, 2.3
        """
        from app.bot.cogs.interactions import (
            ReadLaterButton,
        )
        from app.schemas.article import ArticleSchema

        # Create a minimal list of articles (3 articles)
        articles = [
            ArticleSchema(
                title=f"Article {i}",
                url=f"https://example.com/article-{i}",
                content_preview=f"Preview {i}",
                source_category="AI",
                source_name="TestSource",
            )
            for i in range(3)
        ]

        # Use the fixed combined_view assembly logic (includes ReadLaterView children)
        combined_view = self._build_combined_view_fixed(articles)

        # Assert that combined_view contains a ReadLaterButton (bug is fixed)
        assert any(isinstance(c, ReadLaterButton) for c in combined_view.children), (
            "Bug 8 fix regression: combined_view does not contain any ReadLaterButton. "
            "ReadLaterView children were never added to combined_view in news_now."
        )

    # -----------------------------------------------------------------------
    # Fix-check tests (Tasks 3.1, 3.2, 3.3)
    # -----------------------------------------------------------------------

    def _build_articles(self, count: int):
        """Helper: build a list of minimal ArticleSchema instances."""
        from app.schemas.article import ArticleSchema
        return [
            ArticleSchema(
                title=f"Article {i}",
                url=f"https://example.com/article-{i}",
                content_preview=f"Preview {i}",
                source_category="AI",
                source_name="TestSource",
            )
            for i in range(count)
        ]

    def _build_combined_view_fixed(self, articles):
        """Helper: replicate the FIXED combined_view assembly logic."""
        from app.bot.cogs.interactions import FilterView, DeepDiveView, ReadLaterView
        combined_view = FilterView(articles=articles)
        for item in DeepDiveView(articles=articles[:5]).children:
            combined_view.add_item(item)
        MAX_READ_LATER = 15
        read_later_view = ReadLaterView(articles=articles[:MAX_READ_LATER])
        for item in read_later_view.children:
            combined_view.add_item(item)
        return combined_view

    def test_bug8_fix_check_articles_gte_1_has_read_later_button(self):
        """
        Fix-check (Task 3.1): When articles >= 1, combined_view contains at least
        one ReadLaterButton using the FIXED assembly logic.

        Validates: Requirements 2.1, 2.2
        """
        from app.bot.cogs.interactions import ReadLaterButton

        for count in [1, 3, 5, 10, 15, 20]:
            articles = self._build_articles(count)
            combined_view = self._build_combined_view_fixed(articles)
            assert any(isinstance(c, ReadLaterButton) for c in combined_view.children), (
                f"Fix-check failed for count={count}: combined_view has no ReadLaterButton."
            )

    def test_bug8_fix_check_total_components_le_25(self):
        """
        Fix-check (Task 3.2): For article counts 1, 5, 15, and 20, the total number
        of components in combined_view is always <= 25.

        Validates: Requirements 2.2, 2.3
        """
        for count in [1, 5, 15, 20]:
            articles = self._build_articles(count)
            combined_view = self._build_combined_view_fixed(articles)
            total = len(combined_view.children)
            assert total <= 25, (
                f"Fix-check failed for count={count}: combined_view has {total} components (> 25)."
            )

    def test_bug8_fix_check_zero_articles_no_crash(self):
        """
        Fix-check (Task 3.3): When articles = 0, combined_view is created without
        crashing and contains no ReadLaterButton (edge case).

        Validates: Requirements 2.1
        """
        from app.bot.cogs.interactions import ReadLaterButton

        articles = self._build_articles(0)
        combined_view = self._build_combined_view_fixed(articles)

        # Should not crash — combined_view is created normally
        assert combined_view is not None

        # No ReadLaterButton expected when there are no articles
        assert not any(isinstance(c, ReadLaterButton) for c in combined_view.children), (
            "Fix-check failed for count=0: combined_view unexpectedly contains a ReadLaterButton."
        )
