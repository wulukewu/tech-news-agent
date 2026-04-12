"""
Integration tests for weekly_news_job with article page creation.
Tests complete flow, single article failure handling, and Discord notification.
Requirements: 2.1, 2.4, 3.1, 4.1
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotionServiceError
from app.schemas.article import AIAnalysis, ArticleSchema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_hardcore_article(title="Article", tinkering_index=3, category="AI"):
    article = ArticleSchema(
        title=title,
        url="https://example.com/article",
        content_preview="preview",
        source_category=category,
        source_name="TestSource",
    )
    article.ai_analysis = AIAnalysis(
        is_hardcore=True,
        reason="reason",
        actionable_takeaway="takeaway",
        tinkering_index=tinkering_index,
    )
    return article


def make_mock_services(
    hardcore_articles=None,
    create_page_results=None,
    create_page_raises_for=None,
    discord_raises=None,
):
    """Build a set of mocked services for weekly_news_job tests."""
    if hardcore_articles is None:
        hardcore_articles = [
            make_hardcore_article(f"Article {i}", tinkering_index=i, category="AI")
            for i in range(1, 4)
        ]

    if create_page_results is None:
        create_page_results = [
            (f"page-id-{i}", f"https://notion.so/page-{i}") for i in range(len(hardcore_articles))
        ]

    if create_page_raises_for is None:
        create_page_raises_for = set()

    mock_notion = MagicMock()
    mock_notion.get_active_feeds = AsyncMock(return_value=[MagicMock()])

    # Mock create_article_page to fail for specific indices
    call_count = [0]

    async def mock_create_article_page(article, published_week):
        idx = call_count[0]
        call_count[0] += 1

        if idx in create_page_raises_for:
            raise NotionServiceError(f"Failed to create page for article {idx}")

        return create_page_results[idx]

    mock_notion.create_article_page = mock_create_article_page
    mock_notion.build_article_list_notification = MagicMock(return_value="test notification")

    mock_rss = MagicMock()
    mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

    mock_llm = MagicMock()
    mock_llm.evaluate_batch = AsyncMock(return_value=hardcore_articles)

    mock_channel = AsyncMock()
    if discord_raises:
        mock_channel.send = AsyncMock(side_effect=discord_raises)
    else:
        mock_channel.send = AsyncMock()

    mock_bot = MagicMock()
    mock_bot.get_channel = MagicMock(return_value=mock_channel)

    mock_view = MagicMock()

    return mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view


# ---------------------------------------------------------------------------
# Test: Complete flow with all articles succeeding
# ---------------------------------------------------------------------------


class TestCompleteFlow:
    @pytest.mark.asyncio
    async def test_complete_flow_all_articles_succeed(self):
        """Test complete flow when all articles are successfully created.
        Requirements: 2.1, 3.1, 4.1
        """
        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Article 2", 4, "DevOps"),
            make_hardcore_article("Article 3", 3, "Security"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify build_article_list_notification was called with 3 successful pages
        mock_notion.build_article_list_notification.assert_called_once()
        call_args = mock_notion.build_article_list_notification.call_args
        article_pages_arg = call_args[0][0]
        assert len(article_pages_arg) == 3

        # Verify Discord send was called
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_discord_notification_contains_correct_article_links(self):
        """Test that Discord notification contains correct article links.
        Requirements: 3.1
        """
        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Test Article", 5, "AI"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles,
            create_page_results=[("page-123", "https://notion.so/test-page-123")],
        )

        # Use real build_article_list_notification
        from app.services.notion_service import NotionService

        mock_notion.build_article_list_notification = NotionService.build_article_list_notification

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify Discord send was called with correct content
        mock_channel.send.assert_called_once()
        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "https://notion.so/test-page-123" in content_sent
        assert "Test Article" in content_sent

    @pytest.mark.asyncio
    async def test_mark_read_view_correctly_attached(self):
        """Test that MarkReadView is correctly attached to Discord message.
        Requirements: 4.1
        """
        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Article 2", 4, "DevOps"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view) as mock_view_class,
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify MarkReadView was instantiated with article pages
        mock_view_class.assert_called_once()
        call_args = mock_view_class.call_args
        article_pages_arg = call_args[0][0]
        assert len(article_pages_arg) == 2

        # Verify view was attached to Discord message
        call_kwargs = mock_channel.send.call_args
        view_sent = call_kwargs.kwargs.get("view")
        assert view_sent is mock_view


# ---------------------------------------------------------------------------
# Test: Single article failure doesn't affect others
# ---------------------------------------------------------------------------


class TestSingleArticleFailure:
    @pytest.mark.asyncio
    async def test_single_article_failure_does_not_affect_others(self):
        """Test that single article failure doesn't stop other articles from being created.
        Requirements: 2.4
        """
        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Article 2", 4, "DevOps"),  # This will fail
            make_hardcore_article("Article 3", 3, "Security"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles, create_page_raises_for={1}  # Article 2 fails
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify build_article_list_notification was called with 2 successful pages
        mock_notion.build_article_list_notification.assert_called_once()
        call_args = mock_notion.build_article_list_notification.call_args
        article_pages_arg = call_args[0][0]
        assert len(article_pages_arg) == 2

        # Verify Discord send was still called
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_article_failure_logs_error(self, caplog):
        """Test that single article failure logs an ERROR.
        Requirements: 2.4
        """
        import logging

        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Failing Article", 4, "DevOps"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles, create_page_raises_for={1}
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
            caplog.at_level(logging.ERROR, logger="app.tasks.scheduler"),
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify error was logged
        assert any(
            "Failed to create page for 'Failing Article'" in record.message
            for record in caplog.records
            if record.levelno >= logging.ERROR
        )


# ---------------------------------------------------------------------------
# Test: All articles fail - skip Discord notification
# ---------------------------------------------------------------------------


class TestAllArticlesFailure:
    @pytest.mark.asyncio
    async def test_all_articles_failure_skips_discord_notification(self):
        """Test that when all articles fail, Discord notification is skipped.
        Requirements: 2.4
        """
        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Article 2", 4, "DevOps"),
            make_hardcore_article("Article 3", 3, "Security"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles,
            create_page_raises_for={0, 1, 2},  # All articles fail
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify build_article_list_notification was NOT called
        mock_notion.build_article_list_notification.assert_not_called()

        # Verify Discord send was NOT called
        mock_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_articles_failure_logs_error(self, caplog):
        """Test that when all articles fail, an ERROR is logged.
        Requirements: 2.4
        """
        import logging

        from app.tasks.scheduler import weekly_news_job

        hardcore_articles = [
            make_hardcore_article("Article 1", 5, "AI"),
            make_hardcore_article("Article 2", 4, "DevOps"),
        ]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles, create_page_raises_for={0, 1}
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view),
            patch("app.tasks.scheduler.settings") as mock_settings,
            caplog.at_level(logging.ERROR, logger="app.tasks.scheduler"),
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify error was logged
        assert any(
            "All article pages failed to create" in record.message
            for record in caplog.records
            if record.levelno >= logging.ERROR
        )


# ---------------------------------------------------------------------------
# Test: MarkReadView button limit (25 buttons max)
# ---------------------------------------------------------------------------


class TestMarkReadViewButtonLimit:
    @pytest.mark.asyncio
    async def test_mark_read_view_limited_to_25_buttons(self):
        """Test that MarkReadView is limited to 25 buttons even with more articles.
        Requirements: 4.1
        """
        from app.tasks.scheduler import weekly_news_job

        # Create 30 articles
        hardcore_articles = [make_hardcore_article(f"Article {i}", 5, "AI") for i in range(30)]

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            hardcore_articles=hardcore_articles,
            create_page_results=[(f"page-{i}", f"https://notion.so/page-{i}") for i in range(30)],
        )

        with (
            patch("app.tasks.scheduler.NotionService", return_value=mock_notion),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            patch("app.tasks.scheduler.bot", mock_bot),
            patch("app.tasks.scheduler.MarkReadView", return_value=mock_view) as mock_view_class,
            patch("app.tasks.scheduler.settings") as mock_settings,
        ):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"

            await weekly_news_job()

        # Verify MarkReadView was instantiated with only 25 article pages
        mock_view_class.assert_called_once()
        call_args = mock_view_class.call_args
        article_pages_arg = call_args[0][0]
        assert len(article_pages_arg) == 25
