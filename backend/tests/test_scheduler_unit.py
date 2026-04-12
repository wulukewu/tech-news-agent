"""
Unit tests for scheduler module (Task 4.13).

This test file consolidates unit tests for scheduler functionality:
- Valid CRON expression scheduler initialization
- Invalid CRON expression scheduler initialization
- Empty feed list handling
- Database connection failure handling
- Scheduler doesn't import Discord client
- Scheduler doesn't call Discord API
- Default schedule is 6 hours
- Health check returns 200 when healthy
- Health check returns 503 when stale
- Health check returns 503 when high failure rate

Validates: Requirements 6.3, 9.5, 10.5, 10.6, 10.7
"""

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import RSSSource
from app.tasks.scheduler import (
    _scheduler_health,
    background_fetch_job,
    get_scheduler_health,
    scheduler,
    setup_scheduler,
)


class TestSchedulerInitialization:
    """Unit tests for scheduler initialization."""

    def test_setup_scheduler_with_valid_cron_expression(self):
        """
        Test that setup_scheduler successfully initializes with valid CRON expression.

        Validates: Requirement 6.3
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 */6 * * *"
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler should not raise
            setup_scheduler()

            # Verify job was added
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "background_fetch"
            assert jobs[0].name == "Background Article Fetch and Analysis"

    def test_setup_scheduler_with_invalid_cron_expression_raises_error(self):
        """
        Test that setup_scheduler raises ValueError for invalid CRON expression.

        Validates: Requirement 6.3
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "invalid_cron_expression"
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                setup_scheduler()

            # Verify error message contains relevant information
            assert "Invalid CRON expression" in str(exc_info.value)
            assert "invalid_cron_expression" in str(exc_info.value)

    def test_default_schedule_is_6_hours(self):
        """
        Test that the default scheduler CRON expression is every 6 hours.

        Validates: Requirement 6.3
        """
        from app.core.config import Settings

        # Create settings without SCHEDULER_CRON environment variable
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "http://test.com",
                "SUPABASE_KEY": "test_key",
                "DISCORD_TOKEN": "test_token",
                "DISCORD_CHANNEL_ID": "123456",
                "GROQ_API_KEY": "test_groq_key",
            },
            clear=True,
        ):
            settings = Settings()

            # Verify default is every 6 hours
            assert settings.scheduler_cron == "0 */6 * * *"


class TestSchedulerEmptyFeedHandling:
    """Unit tests for empty feed list handling."""

    @pytest.mark.asyncio
    async def test_empty_feed_list_handling(self, caplog):
        """
        Test that scheduler handles empty feed list gracefully.

        Validates: Requirement 9.5
        """
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=[])

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock()

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock()

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.WARNING),
        ):
            await background_fetch_job()

        # Verify early exit - RSS and LLM services should not be called
        mock_supabase.get_active_feeds.assert_called_once()
        mock_rss.fetch_new_articles.assert_not_called()
        mock_llm.evaluate_batch.assert_not_called()

        # Verify warning was logged
        assert any(
            "No active feeds found" in record.message
            for record in caplog.records
            if record.levelno == logging.WARNING
        )


class TestSchedulerDatabaseFailureHandling:
    """Unit tests for database connection failure handling."""

    @pytest.mark.asyncio
    async def test_database_connection_failure_handling(self, caplog):
        """
        Test that scheduler handles database connection failures gracefully.

        Validates: Requirement 9.5
        """
        # Mock services to raise database error
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.ERROR),
        ):
            # Job should not crash
            await background_fetch_job()

        # Verify error was logged
        assert any(
            "Database connection failed" in record.message
            for record in caplog.records
            if record.levelno >= logging.ERROR
        )

    @pytest.mark.asyncio
    async def test_scheduler_continues_after_database_failure(self, caplog):
        """
        Test that scheduler continues to next execution after database failure.

        Validates: Requirement 9.5
        """
        # Mock services to raise database error
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.INFO),
        ):
            await background_fetch_job()

        # Verify completion message indicating scheduler will continue
        assert any(
            "execution completed" in record.message.lower()
            and "scheduler will continue" in record.message.lower()
            for record in caplog.records
            if record.levelno == logging.INFO
        )


class TestSchedulerDiscordDecoupling:
    """Unit tests for Discord decoupling."""

    def test_scheduler_does_not_import_discord_client(self):
        """
        Test that scheduler module does not import Discord bot client.

        Validates: Requirements 5.1, 5.2
        """
        import app.tasks.scheduler as scheduler_module

        # Verify no Discord imports in the module
        module_dict = vars(scheduler_module)

        # Check that 'bot' is not imported
        assert "bot" not in module_dict, "Scheduler should not import Discord bot"

        # Check that Discord-related classes are not imported
        assert "MarkReadView" not in module_dict, "Scheduler should not import MarkReadView"
        assert "ReadLaterView" not in module_dict, "Scheduler should not import ReadLaterView"

        # Check that discord module is not imported
        assert "discord" not in module_dict, "Scheduler should not import discord module"

    @pytest.mark.asyncio
    async def test_scheduler_does_not_call_discord_api(self):
        """
        Test that scheduler does not call Discord API during execution.

        Validates: Requirements 5.3, 5.4
        """
        # Setup test data
        test_feeds = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

        test_articles = []  # Empty to exit early

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        # Create a mock Discord client to verify it's never called
        mock_discord_client = MagicMock()
        mock_discord_channel = MagicMock()
        mock_discord_channel.send = AsyncMock()
        mock_discord_client.get_channel = MagicMock(return_value=mock_discord_channel)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
        ):
            # Even if Discord client exists, it should not be used
            with patch.dict("sys.modules", {"app.bot.client": MagicMock(bot=mock_discord_client)}):
                await background_fetch_job()

        # Verify Discord API was never called
        mock_discord_client.get_channel.assert_not_called()
        mock_discord_channel.send.assert_not_called()


class TestSchedulerHealthCheck:
    """Unit tests for scheduler health check."""

    @pytest.fixture(autouse=True)
    def reset_health_state(self):
        """Reset health state before each test."""
        _scheduler_health["last_execution_time"] = None
        _scheduler_health["last_articles_processed"] = 0
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 0
        yield

    @pytest.mark.asyncio
    async def test_health_check_returns_200_when_healthy(self):
        """
        Test that health check returns HTTP 200 when scheduler is healthy.

        Validates: Requirement 10.5
        """
        # Set up healthy state (recent execution, low failure rate)
        _scheduler_health["last_execution_time"] = datetime.now(UTC)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 2
        _scheduler_health["last_total_operations"] = 20

        # Get health status
        health = await get_scheduler_health()

        # Verify healthy status
        assert health["status_code"] == 200
        assert health["is_healthy"] is True
        assert len(health["issues"]) == 0

    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_stale(self):
        """
        Test that health check returns HTTP 503 when scheduler is stale (>12 hours).

        Validates: Requirement 10.6
        """
        # Set up stale state (last execution > 12 hours ago)
        stale_time = datetime.now(UTC) - timedelta(hours=13)
        _scheduler_health["last_execution_time"] = stale_time
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10

        # Get health status
        health = await get_scheduler_health()

        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert len(health["issues"]) > 0
        assert any("has not run in" in issue for issue in health["issues"])

    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_high_failure_rate(self):
        """
        Test that health check returns HTTP 503 when failure rate exceeds 50%.

        Validates: Requirement 10.7
        """
        # Set up high failure rate state (>50% failures)
        _scheduler_health["last_execution_time"] = datetime.now(UTC)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 15
        _scheduler_health["last_total_operations"] = 20

        # Get health status
        health = await get_scheduler_health()

        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert len(health["issues"]) > 0
        assert any("failure rate" in issue for issue in health["issues"])

    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_never_executed(self):
        """
        Test that health check returns HTTP 503 when scheduler has never executed.

        Validates: Requirement 10.6
        """
        # Health state is already reset (never executed)

        # Get health status
        health = await get_scheduler_health()

        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert health["last_execution_time"] is None
        assert len(health["issues"]) > 0
        assert any("never executed" in issue for issue in health["issues"])


class TestSchedulerRobustness:
    """Additional unit tests for scheduler robustness."""

    @pytest.mark.asyncio
    async def test_scheduler_does_not_crash_on_unexpected_exception(self, caplog):
        """
        Test that scheduler does not crash on unexpected exceptions.

        Validates: Requirement 9.5
        """
        # Mock services to raise unexpected exception
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.CRITICAL),
        ):
            # Job should not crash
            await background_fetch_job()

        # Verify error was logged at CRITICAL level
        assert any(
            "Unexpected error" in record.message
            for record in caplog.records
            if record.levelno == logging.CRITICAL
        )

    @pytest.mark.asyncio
    async def test_scheduler_logs_full_stack_trace_on_error(self, caplog):
        """
        Test that scheduler logs full stack trace when errors occur.

        Validates: Requirement 9.5
        """
        # Mock services to raise error
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(side_effect=SupabaseServiceError("Test error"))

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.ERROR),
        ):
            await background_fetch_job()

        # Verify error was logged with stack trace (exc_info=True)
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_records) > 0

        # Check that at least one error record has exc_info (stack trace)
        assert any(
            record.exc_info is not None for record in error_records
        ), "Error logs should include full stack traces"
