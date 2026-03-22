"""
Unit tests for scheduler.py
Covers: weekly_news_job (truncation fix, timezone fix), setup_scheduler
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


# ---------------------------------------------------------------------------
# weekly_news_job — Discord message truncation fix
# ---------------------------------------------------------------------------

class TestWeeklyNewsJobTruncation:
    @pytest.mark.asyncio
    async def test_oversized_draft_is_truncated_to_2000_chars(self):
        """weekly_news_job truncates draft to 2000 chars before sending to Discord."""
        from app.tasks.scheduler import weekly_news_job

        oversized_draft = "A" * 2500
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        mock_notion = MagicMock()
        mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])

        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[make_hardcore_article()])
        mock_llm.generate_weekly_newsletter = AsyncMock(return_value=oversized_draft)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        mock_view = MagicMock()

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert len(content_sent) <= 2000, (
            f"Scheduler sent {len(content_sent)}-char message, exceeds Discord 2000-char limit"
        )

    @pytest.mark.asyncio
    async def test_short_draft_sent_unmodified(self):
        """weekly_news_job sends drafts <= 2000 chars without modification."""
        from app.tasks.scheduler import weekly_news_job

        short_draft = "Short newsletter content"
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        mock_notion = MagicMock()
        mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])

        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[make_hardcore_article()])
        mock_llm.generate_weekly_newsletter = AsyncMock(return_value=short_draft)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        mock_view = MagicMock()

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=mock_view), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert content_sent == short_draft

    @pytest.mark.asyncio
    async def test_truncated_draft_ends_with_ellipsis(self):
        """weekly_news_job appends '...' when truncating an oversized draft."""
        from app.tasks.scheduler import weekly_news_job

        oversized_draft = "B" * 2001
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        mock_notion = MagicMock()
        mock_notion.get_active_feeds = AsyncMock(return_value=["feed1"])
        mock_rss = MagicMock()
        mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=[make_hardcore_article()])
        mock_llm.generate_weekly_newsletter = AsyncMock(return_value=oversized_draft)
        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             patch("app.tasks.scheduler.bot", mock_bot), \
             patch("app.tasks.scheduler.ReadLaterView", return_value=MagicMock()), \
             patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.discord_channel_id = 123456789
            mock_settings.timezone = "Asia/Taipei"
            await weekly_news_job()

        call_kwargs = mock_channel.send.call_args
        content_sent = call_kwargs.kwargs.get("content") or call_kwargs.args[0]
        assert content_sent.endswith("...")

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
