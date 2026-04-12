"""
Unit tests for scheduler logging requirements.

Tests comprehensive logging in the scheduler module:
- Task start time at INFO level
- Task end time and total duration at INFO level
- Count of feeds processed at INFO level
- Count of new articles found at INFO level
- Count of articles analyzed by LLM at INFO level
- Count of articles inserted into database at INFO level
- All errors at ERROR level with full stack traces
- Warnings at WARNING level when failure rates exceed thresholds

Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8
"""

import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema, BatchResult, RSSSource


def make_test_article(title="Test Article", url="https://example.com/test", feed_id=None):
    """Helper to create a test article."""
    if feed_id is None:
        feed_id = uuid4()

    return ArticleSchema(
        title=title,
        url=url,
        feed_id=feed_id,
        feed_name="Test Feed",
        category="AI",
        published_at=datetime.now(UTC),
        tinkering_index=None,
        ai_summary=None,
    )


def make_test_feed(name="Test Feed", url="https://example.com/feed", category="AI"):
    """Helper to create a test RSS source."""
    return RSSSource(name=name, url=url, category=category)


class TestSchedulerLogging:
    """Test suite for scheduler logging requirements."""

    @pytest.mark.asyncio
    async def test_logs_task_start_time_at_info_level(self, caplog):
        """Test that scheduler logs task start time at INFO level.

        Validates: Requirement 14.1
        """
        from app.tasks.scheduler import background_fetch_job

        # Mock services to return empty data for quick exit
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=[])

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify start time is logged at INFO level
        start_logs = [
            record
            for record in caplog.records
            if "Starting background_fetch_job" in record.message and record.levelno == logging.INFO
        ]

        assert len(start_logs) >= 1, "Should log task start time at INFO level"
        assert "at" in start_logs[0].message, "Should include timestamp in start log"

    @pytest.mark.asyncio
    async def test_logs_task_end_time_and_duration_at_info_level(self, caplog):
        """Test that scheduler logs task end time and total duration at INFO level.

        Validates: Requirement 14.2
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data
        test_feeds = [make_test_feed()]
        test_articles = [make_test_article()]
        test_articles[0].tinkering_index = 4
        test_articles[0].ai_summary = "Test summary"

        batch_result = BatchResult(inserted_count=1, updated_count=0, failed_count=0)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify end time and duration are logged at INFO level
        completion_logs = [
            record
            for record in caplog.records
            if "Background fetch job completed successfully" in record.message
            and record.levelno == logging.INFO
        ]

        assert len(completion_logs) >= 1, "Should log task completion at INFO level"
        assert "Total duration:" in completion_logs[0].message, "Should include total duration"
        assert "s" in completion_logs[0].message, "Duration should be in seconds"

    @pytest.mark.asyncio
    async def test_logs_count_of_feeds_processed_at_info_level(self, caplog):
        """Test that scheduler logs count of feeds processed at INFO level.

        Validates: Requirement 14.3
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data with 3 feeds
        test_feeds = [
            make_test_feed("Feed 1", "https://example.com/feed1"),
            make_test_feed("Feed 2", "https://example.com/feed2"),
            make_test_feed("Feed 3", "https://example.com/feed3"),
        ]
        test_articles = [make_test_article()]
        test_articles[0].tinkering_index = 4
        test_articles[0].ai_summary = "Test summary"

        batch_result = BatchResult(inserted_count=1, updated_count=0, failed_count=0)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify feeds count is logged at INFO level
        feed_logs = [
            record
            for record in caplog.records
            if ("Loaded 3 active feeds" in record.message or "Feeds processed: 3" in record.message)
            and record.levelno == logging.INFO
        ]

        assert len(feed_logs) >= 1, "Should log count of feeds processed at INFO level"

    @pytest.mark.asyncio
    async def test_logs_count_of_new_articles_found_at_info_level(self, caplog):
        """Test that scheduler logs count of new articles found at INFO level.

        Validates: Requirement 14.4
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data with 5 new articles
        test_feeds = [make_test_feed()]
        test_articles = [
            make_test_article(f"Article {i}", f"https://example.com/article{i}") for i in range(5)
        ]
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"

        batch_result = BatchResult(inserted_count=5, updated_count=0, failed_count=0)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify new articles count is logged at INFO level
        article_logs = [
            record
            for record in caplog.records
            if (
                "Found 5 new articles" in record.message
                or "New articles found: 5" in record.message
            )
            and record.levelno == logging.INFO
        ]

        assert len(article_logs) >= 1, "Should log count of new articles found at INFO level"

    @pytest.mark.asyncio
    async def test_logs_count_of_articles_analyzed_by_llm_at_info_level(self, caplog):
        """Test that scheduler logs count of articles analyzed by LLM at INFO level.

        Validates: Requirement 14.5
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data with 7 articles
        test_feeds = [make_test_feed()]
        test_articles = [
            make_test_article(f"Article {i}", f"https://example.com/article{i}") for i in range(7)
        ]
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"

        batch_result = BatchResult(inserted_count=7, updated_count=0, failed_count=0)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify articles analyzed count is logged at INFO level
        # The scheduler logs "Articles processed: X" which includes LLM analysis
        analysis_logs = [
            record
            for record in caplog.records
            if "Articles processed: 7" in record.message and record.levelno == logging.INFO
        ]

        assert len(analysis_logs) >= 1, "Should log count of articles analyzed by LLM at INFO level"

    @pytest.mark.asyncio
    async def test_logs_count_of_articles_inserted_into_database_at_info_level(self, caplog):
        """Test that scheduler logs count of articles inserted into database at INFO level.

        Validates: Requirement 14.6
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data
        test_feeds = [make_test_feed()]
        test_articles = [
            make_test_article(f"Article {i}", f"https://example.com/article{i}") for i in range(10)
        ]
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"

        # 8 inserted, 2 updated
        batch_result = BatchResult(inserted_count=8, updated_count=2, failed_count=0)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.INFO, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify database insertion counts are logged at INFO level
        db_logs = [
            record
            for record in caplog.records
            if "Inserted: 8" in record.message
            and "Updated: 2" in record.message
            and record.levelno == logging.INFO
        ]

        assert (
            len(db_logs) >= 1
        ), "Should log count of articles inserted into database at INFO level"

    @pytest.mark.asyncio
    async def test_logs_all_errors_at_error_level_with_stack_traces(self, caplog):
        """Test that scheduler logs all errors at ERROR level with full stack traces.

        Validates: Requirement 14.7
        """
        from app.tasks.scheduler import background_fetch_job

        # Mock services to raise an error
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            caplog.at_level(logging.ERROR, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify error is logged at ERROR level with stack trace
        error_logs = [
            record
            for record in caplog.records
            if record.levelno >= logging.ERROR and "Database connection failed" in record.message
        ]

        assert len(error_logs) >= 1, "Should log errors at ERROR level"

        # Verify stack trace is included (exc_info=True adds stack trace)
        assert any(
            record.exc_info is not None for record in error_logs
        ), "Should include full stack traces with errors"

    @pytest.mark.asyncio
    async def test_logs_warnings_when_failure_rates_exceed_thresholds(self, caplog):
        """Test that scheduler logs warnings at WARNING level when failure rates exceed thresholds.

        Validates: Requirement 14.8
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data with high failure rate (40% > 30% threshold)
        test_feeds = [make_test_feed()]
        test_articles = [
            make_test_article(f"Article {i}", f"https://example.com/article{i}") for i in range(10)
        ]
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"

        # 6 inserted, 0 updated, 4 failed (40% failure rate)
        batch_result = BatchResult(inserted_count=6, updated_count=0, failed_count=4)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.WARNING, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify warning is logged when failure rate exceeds threshold
        warning_logs = [
            record
            for record in caplog.records
            if record.levelno == logging.WARNING
            and "High database insertion failure rate" in record.message
        ]

        assert len(warning_logs) >= 1, "Should log warning when failure rate exceeds threshold"
        assert "4/10" in warning_logs[0].message, "Should include failure count in warning"
        assert "40" in warning_logs[0].message, "Should include failure percentage in warning"

    @pytest.mark.asyncio
    async def test_no_warning_when_failure_rate_below_threshold(self, caplog):
        """Test that scheduler does not log warning when failure rate is below threshold.

        Validates: Requirement 14.8 (negative case)
        """
        from app.tasks.scheduler import background_fetch_job

        # Setup test data with low failure rate (20% < 30% threshold)
        test_feeds = [make_test_feed()]
        test_articles = [
            make_test_article(f"Article {i}", f"https://example.com/article{i}") for i in range(10)
        ]
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"

        # 8 inserted, 0 updated, 2 failed (20% failure rate)
        batch_result = BatchResult(inserted_count=8, updated_count=0, failed_count=2)

        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)

        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)

        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)

        # Execute job
        with (
            patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase),
            patch("app.tasks.scheduler.RSSService", return_value=mock_rss),
            patch("app.tasks.scheduler.LLMService", return_value=mock_llm),
            caplog.at_level(logging.WARNING, logger="app.tasks.scheduler"),
        ):
            await background_fetch_job()

        # Verify no warning is logged when failure rate is below threshold
        warning_logs = [
            record
            for record in caplog.records
            if record.levelno == logging.WARNING
            and "High database insertion failure rate" in record.message
        ]

        assert len(warning_logs) == 0, "Should not log warning when failure rate is below threshold"
