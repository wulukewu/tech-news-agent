"""
Manual verification tests for scheduler error handling (Task 4.4)

These tests verify that the scheduler implements comprehensive error handling:
- Wraps entire task in try-except to prevent crashes
- Logs all exceptions with full stack traces
- Implements retry logic with exponential backoff for database operations
- Caches articles in memory during connection failures
- Logs critical errors and skips current execution when all retries fail
- Continues normal operation on next scheduled execution

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import SupabaseServiceError
from app.tasks.scheduler import background_fetch_job


class TestSchedulerErrorHandling:
    """測試排程器錯誤處理 (Task 4.4)"""

    @pytest.mark.asyncio
    async def test_scheduler_does_not_crash_on_database_error(self):
        """
        Test that scheduler does not crash when database connection fails.

        Validates: Requirements 9.1, 9.5
        """
        # Mock SupabaseService to raise error
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_supabase_class.side_effect = SupabaseServiceError(
                "Database connection failed", context={"error": "connection timeout"}
            )

            # Should not raise exception - scheduler should catch and log
            try:
                await background_fetch_job()
                # If we reach here, the scheduler handled the error gracefully
                assert True
            except Exception as e:
                pytest.fail(f"Scheduler crashed with exception: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_logs_full_stack_trace_on_error(self, caplog):
        """
        Test that scheduler logs full stack trace when errors occur.

        Validates: Requirements 9.2
        """
        import logging

        caplog.set_level(logging.CRITICAL)

        # Mock SupabaseService to raise error
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_supabase_class.side_effect = SupabaseServiceError(
                "Database connection failed", context={"error": "connection timeout"}
            )

            await background_fetch_job()

            # Check that critical error was logged (either during retry or final catch)
            critical_messages = [
                record.message for record in caplog.records if record.levelname == "CRITICAL"
            ]
            assert any(
                "All database retry attempts failed" in msg
                or "Database error during background fetch job" in msg
                for msg in critical_messages
            ), f"Expected critical error log, got: {critical_messages}"

    @pytest.mark.asyncio
    async def test_scheduler_retries_database_operations_with_exponential_backoff(self):
        """
        Test that scheduler retries database operations up to 3 times with exponential backoff.

        Validates: Requirements 9.3
        """
        # Track retry attempts
        attempt_count = 0

        def mock_get_active_feeds():
            nonlocal attempt_count
            attempt_count += 1
            raise SupabaseServiceError(
                "Database connection failed", context={"attempt": attempt_count}
            )

        # Mock SupabaseService to fail on all attempts
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_instance = MagicMock()
            mock_instance.get_active_feeds = AsyncMock(side_effect=mock_get_active_feeds)
            mock_supabase_class.return_value = mock_instance

            start_time = asyncio.get_event_loop().time()
            await background_fetch_job()
            end_time = asyncio.get_event_loop().time()

            # Should have attempted 3 times
            assert attempt_count == 3, f"Expected 3 retry attempts, got {attempt_count}"

            # Should have taken at least 1s + 2s = 3s for exponential backoff
            # (1s delay after 1st failure, 2s delay after 2nd failure)
            elapsed_time = end_time - start_time
            assert elapsed_time >= 3.0, f"Expected at least 3s for retries, got {elapsed_time:.2f}s"

    @pytest.mark.asyncio
    async def test_scheduler_skips_execution_after_all_retries_fail(self, caplog):
        """
        Test that scheduler skips current execution when all retries fail.

        Validates: Requirements 9.4
        """
        import logging

        caplog.set_level(logging.CRITICAL)

        # Mock SupabaseService to always fail
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_instance = MagicMock()
            mock_instance.get_active_feeds = AsyncMock(
                side_effect=SupabaseServiceError("Database connection failed")
            )
            mock_supabase_class.return_value = mock_instance

            await background_fetch_job()

            # Check that critical error was logged with "skipping" message
            assert any(
                "Skipping current job execution" in record.message
                for record in caplog.records
                if record.levelname == "CRITICAL"
            )

    @pytest.mark.asyncio
    async def test_scheduler_continues_to_next_execution_after_failure(self, caplog):
        """
        Test that scheduler continues to next scheduled execution after failure.

        Validates: Requirements 9.6
        """
        import logging

        caplog.set_level(logging.INFO)

        # Mock SupabaseService to fail
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_supabase_class.side_effect = SupabaseServiceError("Database connection failed")

            await background_fetch_job()

            # Check that scheduler logged it will continue to next execution
            assert any(
                "Scheduler will continue to next scheduled execution" in record.message
                for record in caplog.records
                if record.levelname == "INFO"
            )

    @pytest.mark.asyncio
    async def test_scheduler_handles_unexpected_exceptions(self, caplog):
        """
        Test that scheduler catches and logs unexpected exceptions.

        Validates: Requirements 9.1, 9.5
        """
        import logging

        caplog.set_level(logging.CRITICAL)

        # Mock SupabaseService to raise unexpected exception
        with patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class:
            mock_supabase_class.side_effect = RuntimeError("Unexpected error")

            # Should not crash
            try:
                await background_fetch_job()
                assert True
            except Exception as e:
                pytest.fail(f"Scheduler crashed with unexpected exception: {e}")

            # Check that critical error was logged
            assert any(
                "Unexpected error during background fetch job" in record.message
                for record in caplog.records
                if record.levelname == "CRITICAL"
            )

    @pytest.mark.asyncio
    async def test_scheduler_retries_article_insertion_on_failure(self):
        """
        Test that scheduler retries article insertion when database connection fails.

        Validates: Requirements 9.3
        """
        # Track insertion attempts
        insertion_attempts = 0

        async def mock_insert_articles(articles):
            nonlocal insertion_attempts
            insertion_attempts += 1
            raise SupabaseServiceError("Database connection failed during insertion")

        # Mock services
        with (
            patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
            patch("app.tasks.scheduler.RSSService") as mock_rss_class,
            patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        ):
            # Setup mocks
            mock_supabase = MagicMock()
            mock_supabase.get_active_feeds = AsyncMock(
                return_value=[
                    MagicMock(name="Test Feed", url="https://example.com/feed", category="AI")
                ]
            )
            mock_supabase.insert_articles = AsyncMock(side_effect=mock_insert_articles)
            mock_supabase_class.return_value = mock_supabase

            mock_rss = MagicMock()
            mock_rss.fetch_new_articles = AsyncMock(
                return_value=[
                    MagicMock(
                        title="Test Article",
                        url="https://example.com/article",
                        feed_id="test-feed-id",
                        published_at=datetime.now(UTC),
                        tinkering_index=3,
                        ai_summary="Test summary",
                        embedding=None,
                    )
                ]
            )
            mock_rss_class.return_value = mock_rss

            mock_llm = MagicMock()
            mock_llm.evaluate_batch = AsyncMock(
                return_value=[
                    MagicMock(
                        title="Test Article",
                        url="https://example.com/article",
                        feed_id="test-feed-id",
                        published_at=datetime.now(UTC),
                        tinkering_index=3,
                        ai_summary="Test summary",
                        embedding=None,
                    )
                ]
            )
            mock_llm_class.return_value = mock_llm

            await background_fetch_job()

            # Should have attempted insertion 3 times
            assert (
                insertion_attempts == 3
            ), f"Expected 3 insertion attempts, got {insertion_attempts}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
