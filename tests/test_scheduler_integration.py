"""
Integration tests for weekly_news_job scheduler task.
Mocks all external services (LLMService, NotionService, Discord channel).
Requirements: 7.2, 7.3, 5.4
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.article import ArticleSchema, AIAnalysis
from app.core.exceptions import NotionServiceError


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
    notion_page_result=("page-id-123", "https://notion.so/page-id-123"),
    notion_raises=None,
    discord_raises=None,
    intro_text="本週精選技術文章，請展開各項目查看詳情。",
):
    """Build a set of mocked services for weekly_news_job tests."""
    if hardcore_articles is None:
        hardcore_articles = [make_hardcore_article(f"Article {i}", tinkering_index=i) for i in range(1, 4)]

    mock_notion = MagicMock()
    mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])
    if notion_raises:
        mock_notion.create_weekly_digest_page = AsyncMock(side_effect=notion_raises)
    else:
        mock_notion.create_weekly_digest_page = AsyncMock(return_value=notion_page_result)
    mock_notion.build_digest_blocks = MagicMock(return_value=[{"type": "paragraph"}])
    mock_notion.append_digest_blocks = AsyncMock(return_value=None)

    mock_rss = MagicMock()
    mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

    mock_llm = MagicMock()
    mock_llm.evaluate_batch = AsyncMock(return_value=hardcore_articles)
    mock_llm.generate_digest_intro = AsyncMock(return_value=intro_text)

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
# Test: Notion fails → Discord still sends degraded notification (Req 7.2, 5.4)
# ---------------------------------------------------------------------------

class TestNotionFailureDegradedNotification:
    @pytest.mark.asyncio
    async def test_notion_failure_discord_sends_degraded_notification(self):
        """When Notion page creation fails, Discord still sends a degraded notification.
        Requirements: 7.2, 5.4
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            notion_raises=NotionServiceError("Notion API error")
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        # Discord should still have been called
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_notion_failure_discord_notification_contains_warning(self):
        """Degraded notification contains the warning marker.
        Requirements: 5.4
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            notion_raises=NotionServiceError("Notion API error")
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "（Notion 頁面建立失敗，請查看日誌）" in content_sent, (
            f"Expected degraded warning in message, got: {content_sent!r}"
        )

    @pytest.mark.asyncio
    async def test_empty_notion_db_id_discord_sends_degraded_notification(self):
        """When notion_weekly_digests_db_id is empty, Discord sends degraded notification.
        Requirements: 1.3, 5.4
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services()

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = ""  # empty
            await weekly_news_job()

        mock_channel.send.assert_called_once()
        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "（Notion 頁面建立失敗，請查看日誌）" in content_sent


# ---------------------------------------------------------------------------
# Test: Discord fails → Notion page already created, not affected (Req 7.3)
# ---------------------------------------------------------------------------

class TestDiscordFailureNotionUnaffected:
    @pytest.mark.asyncio
    async def test_discord_failure_does_not_affect_notion_page(self):
        """When Discord send fails, the Notion page was already created and is unaffected.
        Requirements: 7.3
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            discord_raises=Exception("Discord API error")
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            # Should not raise even though Discord fails
            await weekly_news_job()

        # Notion page creation was called and succeeded
        mock_notion.create_weekly_digest_page.assert_called_once()
        # Blocks were appended
        mock_notion.append_digest_blocks.assert_called_once()

    @pytest.mark.asyncio
    async def test_discord_failure_logs_error(self, caplog):
        """When Discord send fails, an ERROR is logged.
        Requirements: 7.3
        """
        import logging
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            discord_raises=Exception("Discord API error")
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings, \
             caplog.at_level(logging.ERROR, logger="app.tasks.scheduler"):
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        assert any("Discord" in record.message or "discord" in record.message.lower()
                   for record in caplog.records if record.levelno >= logging.ERROR), (
            "Expected an ERROR log about Discord failure"
        )


# ---------------------------------------------------------------------------
# Test: Degraded notification contains warning marker (Req 5.4)
# ---------------------------------------------------------------------------

class TestDegradedNotificationContent:
    @pytest.mark.asyncio
    async def test_degraded_notification_contains_warning_marker(self):
        """Degraded notification contains '（Notion 頁面建立失敗，請查看日誌）'.
        Requirements: 5.4
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            notion_raises=NotionServiceError("Notion failed")
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert "（Notion 頁面建立失敗，請查看日誌）" in content_sent

    @pytest.mark.asyncio
    async def test_normal_notification_contains_notion_url(self):
        """Normal notification (Notion success) contains the Notion page URL.
        Requirements: 5.1
        """
        from app.tasks.scheduler import weekly_news_job

        page_url = "https://notion.so/test-page-abc123"
        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services(
            notion_page_result=("page-abc123", page_url)
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert page_url in content_sent, (
            f"Expected Notion page URL '{page_url}' in notification, got: {content_sent!r}"
        )

    @pytest.mark.asyncio
    async def test_read_later_view_attached_to_notification(self):
        """ReadLaterView is attached to the Discord notification.
        Requirements: 5.5
        """
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot, mock_view = make_mock_services()

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        view_sent = call_kwargs.kwargs.get("view")
        assert view_sent is mock_view, "Expected ReadLaterView to be attached to Discord message"
