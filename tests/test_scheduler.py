"""
Unit tests for scheduler.py
Covers: weekly_news_job (Discord notification, timezone fix), setup_scheduler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.article import ArticleSchema, AIAnalysis


def make_hardcore_article(title="Article", tinkering_index=3):
    article = ArticleSchema(
        title=title,
        url="https://example.com/article",
        content_preview="preview",
        source_category="AI",
        source_name="TestSource",
    )
    article.ai_analysis = AIAnalysis(
        is_hardcore=True,
        reason="reason",
        actionable_takeaway="takeaway",
        tinkering_index=tinkering_index,
    )
    return article


def _make_base_mocks(hardcore_articles=None):
    """Return a set of base mocks for weekly_news_job tests."""
    if hardcore_articles is None:
        hardcore_articles = [make_hardcore_article()]

    mock_notion = MagicMock()
    mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])
    mock_notion.create_weekly_digest_page = AsyncMock(
        return_value=("page-id", "https://notion.so/page-id")
    )
    mock_notion.build_digest_blocks = MagicMock(return_value=[])
    mock_notion.append_digest_blocks = AsyncMock(return_value=None)

    mock_rss = MagicMock()
    mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

    mock_llm = MagicMock()
    mock_llm.evaluate_batch = AsyncMock(return_value=hardcore_articles)
    mock_llm.generate_digest_intro = AsyncMock(return_value="intro text")

    mock_channel = AsyncMock()
    mock_channel.send = AsyncMock()

    mock_bot = MagicMock()
    mock_bot.get_channel = MagicMock(return_value=mock_channel)

    return mock_notion, mock_rss, mock_llm, mock_channel, mock_bot


# ---------------------------------------------------------------------------
# weekly_news_job — Discord notification (new Notion-based flow)
# ---------------------------------------------------------------------------

class TestWeeklyNewsJobTruncation:
    @pytest.mark.asyncio
    async def test_discord_message_within_2000_chars(self):
        """weekly_news_job sends a Discord message within the 2000-char limit."""
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot = _make_base_mocks()

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=MagicMock()), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert len(content_sent) <= 2000, (
            f"Scheduler sent {len(content_sent)}-char message, exceeds Discord 2000-char limit"
        )

    @pytest.mark.asyncio
    async def test_discord_message_contains_stats(self):
        """weekly_news_job Discord notification contains article stats."""
        from app.tasks.scheduler import weekly_news_job

        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot = _make_base_mocks(
            hardcore_articles=[make_hardcore_article(f"Article {i}") for i in range(3)]
        )
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()] * 10)

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=MagicMock()), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        # Should contain stats numbers
        assert "10" in content_sent or "3" in content_sent

    @pytest.mark.asyncio
    async def test_discord_message_contains_notion_url(self):
        """weekly_news_job Discord notification contains the Notion page URL."""
        from app.tasks.scheduler import weekly_news_job

        page_url = "https://notion.so/test-page-xyz"
        mock_notion, mock_rss, mock_llm, mock_channel, mock_bot = _make_base_mocks()
        mock_notion.create_weekly_digest_page = AsyncMock(
            return_value=("page-xyz", page_url)
        )

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=MagicMock()), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            mock_settings.notion_weekly_digests_db_id = "some-db-id"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert page_url in content_sent

    @pytest.mark.asyncio
    async def test_returns_early_when_no_channel(self):
        """weekly_news_job exits gracefully when Discord channel is not found."""
        from app.tasks.scheduler import weekly_news_job

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=None)

        with patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 999
            mock_settings.timezone = "Asia/Taipei"
            # Should not raise
            await weekly_news_job()

        mock_bot.get_channel.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_returns_early_when_no_feeds(self):
        """weekly_news_job exits gracefully when Notion returns no active feeds."""
        from app.tasks.scheduler import weekly_news_job

        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()
        mock_notion = MagicMock()
        mock_notion.get_active_feeds = AsyncMock(return_value=[])
        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123
            mock_settings.timezone = "Asia/Taipei"
            await weekly_news_job()

        mock_channel.send.assert_not_called()


# ---------------------------------------------------------------------------
# setup_scheduler — timezone fix
# ---------------------------------------------------------------------------

class TestSetupScheduler:
    def test_cron_trigger_uses_settings_timezone(self):
        """setup_scheduler uses settings.timezone for the CronTrigger, not a hardcoded value."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.tasks.scheduler import setup_scheduler

        test_timezone = "UTC"
        mock_scheduler = MagicMock(spec=AsyncIOScheduler)

        with patch("app.tasks.scheduler.scheduler", mock_scheduler), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.timezone = test_timezone
            setup_scheduler()

        mock_scheduler.add_job.assert_called_once()
        _, kwargs = mock_scheduler.add_job.call_args
        trigger = kwargs["trigger"]
        # CronTrigger stores timezone as a tzinfo object; check its zone name
        assert str(trigger.timezone) == test_timezone, (
            f"CronTrigger timezone is '{trigger.timezone}', expected '{test_timezone}'"
        )

    def test_setup_scheduler_registers_weekly_news_job(self):
        """setup_scheduler registers a job with id='weekly_news'."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.tasks.scheduler import setup_scheduler

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)

        with patch("app.tasks.scheduler.scheduler", mock_scheduler), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.timezone = "Asia/Taipei"
            setup_scheduler()

        _, kwargs = mock_scheduler.add_job.call_args
        assert kwargs["id"] == "weekly_news"
        assert kwargs["replace_existing"] is True
