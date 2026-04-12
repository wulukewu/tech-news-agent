"""
Property-based tests for Scheduler robustness
Task 4.11: 撰寫 Scheduler 的屬性測試

Property 11: Scheduler Robustness
Validates Requirements: 9.5

This test verifies that the scheduler correctly handles database errors:
- Scheduler doesn't crash when database errors occur
- Errors are logged with appropriate context
- Scheduler continues to next scheduled execution
- System remains operational after failures
"""

import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema, BatchResult, RSSSource
from app.tasks.scheduler import background_fetch_job

# Hypothesis strategies for generating test data


def database_error_strategy():
    """Generate various database error scenarios"""
    return st.sampled_from(
        [
            "Connection timeout",
            "Connection refused",
            "Database unavailable",
            "Network error",
            "SSL connection error",
            "Authentication failed",
            "Too many connections",
            "Database locked",
            "Query timeout",
            "Connection reset by peer",
        ]
    )


def error_stage_strategy():
    """Generate different stages where database errors can occur"""
    return st.sampled_from(["get_active_feeds", "insert_articles", "both"])


# Feature: background-scheduler-ai-pipeline, Property 11: Scheduler Robustness
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(error_message=database_error_strategy(), error_stage=error_stage_strategy())
@pytest.mark.asyncio
async def test_property_11_scheduler_robustness_database_errors(error_message, error_stage, caplog):
    """
    Property 11: Scheduler Robustness

    For any database error during scheduler execution, the scheduler should:
    - Not crash (no unhandled exceptions)
    - Log the error with full context
    - Continue to next scheduled execution
    - Remain operational

    Validates: Requirements 9.5
    """
    # Arrange: Setup test data
    test_articles = [
        ArticleSchema(
            title=f"Test Article {i}",
            url=f"https://test-robustness-{uuid4().hex[:8]}.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        for i in range(3)
    ]

    test_feeds = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Track if job completed without crashing
    job_completed = False
    exception_raised = None

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Configure database errors based on error_stage
        if error_stage == "get_active_feeds":
            # Error during feed loading
            mock_supabase.get_active_feeds.side_effect = SupabaseServiceError(
                f"Database error during feed loading: {error_message}"
            )
            # insert_articles won't be called, but set it up anyway
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0, updated_count=0, failed_count=0, failed_articles=[]
            )
        elif error_stage == "insert_articles":
            # Error during article insertion
            mock_supabase.get_active_feeds.return_value = test_feeds
            mock_supabase.insert_articles.side_effect = SupabaseServiceError(
                f"Database error during article insertion: {error_message}"
            )
        else:  # both
            # Errors at both stages
            mock_supabase.get_active_feeds.side_effect = SupabaseServiceError(
                f"Database error during feed loading: {error_message}"
            )
            mock_supabase.insert_articles.side_effect = SupabaseServiceError(
                f"Database error during article insertion: {error_message}"
            )

        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = test_articles

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Act: Run the background job with logging capture
        with caplog.at_level(logging.INFO):  # Capture INFO level to see completion message
            try:
                await background_fetch_job()
                job_completed = True
            except Exception as e:
                exception_raised = e
                job_completed = False

    # Assert: Verify scheduler robustness properties

    # Property 1: Scheduler should not crash (no unhandled exceptions)
    assert (
        job_completed
    ), f"Scheduler should not crash on database errors, but raised: {exception_raised}"

    # Property 2: Error should be logged
    # Check that error was logged at ERROR or CRITICAL level
    error_logged = any(record.levelname in ["ERROR", "CRITICAL"] for record in caplog.records)

    assert error_logged, (
        f"Database error should be logged at ERROR or CRITICAL level. "
        f"Captured logs: {[r.message for r in caplog.records]}"
    )

    # Property 3: Error log should contain context about the failure
    # Look for database-related error messages
    database_error_logged = any(
        "database" in record.message.lower()
        or "supabase" in record.message.lower()
        or "error" in record.message.lower()
        for record in caplog.records
        if record.levelname in ["ERROR", "CRITICAL"]
    )

    assert database_error_logged, (
        f"Error log should contain database/error context. "
        f"Error logs: {[r.message for r in caplog.records if r.levelname in ['ERROR', 'CRITICAL']]}"
    )

    # Property 4: Job completion message should be logged (indicating scheduler continues)
    completion_logged = any(
        "execution completed" in record.message.lower()
        and "scheduler will continue" in record.message.lower()
        for record in caplog.records
        if record.levelname == "INFO"
    )

    assert completion_logged, (
        f"Job completion should be logged to indicate scheduler continues. "
        f"Info logs: {[r.message for r in caplog.records if r.levelname == 'INFO']}"
    )


# Feature: background-scheduler-ai-pipeline, Property 11: Scheduler Robustness (Retry Exhaustion)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(error_message=database_error_strategy())
@pytest.mark.asyncio
async def test_property_11_scheduler_robustness_retry_exhaustion(error_message, caplog):
    """
    Property 11: Scheduler Robustness (Retry Exhaustion)

    When all database retry attempts are exhausted, the scheduler should:
    - Not crash
    - Log critical error
    - Skip current execution
    - Continue to next scheduled execution

    Validates: Requirements 9.5
    """
    # Arrange: Setup test data
    test_feeds = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Track retry attempts
    get_feeds_attempts = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds to fail all retry attempts
        async def mock_get_active_feeds():
            get_feeds_attempts.append(1)
            raise SupabaseServiceError(f"Database connection failed: {error_message}")

        mock_supabase.get_active_feeds.side_effect = mock_get_active_feeds

        # Setup RSS mock (won't be called due to early failure)
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        # Setup LLM mock (won't be called due to early failure)
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Act: Run the background job
        job_completed = False
        exception_raised = None

        with caplog.at_level(logging.ERROR):
            try:
                await background_fetch_job()
                job_completed = True
            except Exception as e:
                exception_raised = e
                job_completed = False

    # Assert: Verify retry exhaustion handling

    # Property 1: Scheduler should not crash after retry exhaustion
    assert (
        job_completed
    ), f"Scheduler should not crash after retry exhaustion, but raised: {exception_raised}"

    # Property 2: Should attempt retries (3 attempts total)
    assert (
        len(get_feeds_attempts) == 3
    ), f"Should attempt 3 retries, but attempted {len(get_feeds_attempts)} times"

    # Property 3: Critical error should be logged
    critical_logged = any(record.levelname == "CRITICAL" for record in caplog.records)

    assert critical_logged, (
        f"Critical error should be logged after retry exhaustion. "
        f"Log levels: {[r.levelname for r in caplog.records]}"
    )

    # Property 4: Error message should mention retry failure
    retry_failure_logged = any(
        "retry" in record.message.lower() or "failed" in record.message.lower()
        for record in caplog.records
        if record.levelname == "CRITICAL"
    )

    assert retry_failure_logged, (
        f"Critical log should mention retry failure. "
        f"Critical logs: {[r.message for r in caplog.records if r.levelname == 'CRITICAL']}"
    )

    # Property 5: Sleep should be called for exponential backoff (2 times for 3 attempts)
    assert (
        mock_sleep.call_count == 2
    ), f"Sleep should be called 2 times for exponential backoff, but called {mock_sleep.call_count} times"


# Feature: background-scheduler-ai-pipeline, Property 11: Scheduler Robustness (Partial Retry Success)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    success_on_attempt=st.integers(min_value=1, max_value=3),
    error_message=database_error_strategy(),
)
@pytest.mark.asyncio
async def test_property_11_scheduler_robustness_partial_retry_success(
    success_on_attempt, error_message, caplog
):
    """
    Property 11: Scheduler Robustness (Partial Retry Success)

    When database operations succeed after retries, the scheduler should:
    - Continue normal operation
    - Complete the job successfully
    - Log retry attempts
    - Process all stages normally

    Validates: Requirements 9.5
    """
    # Arrange: Setup test data
    test_articles = [
        ArticleSchema(
            title=f"Test Article {i}",
            url=f"https://test-retry-{uuid4().hex[:8]}.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        for i in range(2)
    ]

    test_feeds = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Track attempts
    get_feeds_attempts = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds to fail then succeed
        async def mock_get_active_feeds():
            attempt_num = len(get_feeds_attempts) + 1
            get_feeds_attempts.append(attempt_num)

            if attempt_num < success_on_attempt:
                # Fail on early attempts
                raise SupabaseServiceError(
                    f"Database connection failed (attempt {attempt_num}): {error_message}"
                )
            else:
                # Succeed on specified attempt
                return test_feeds

        mock_supabase.get_active_feeds.side_effect = mock_get_active_feeds

        # Mock insert_articles to succeed
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=len(test_articles), updated_count=0, failed_count=0, failed_articles=[]
        )

        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = test_articles

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Act: Run the background job
        job_completed = False
        exception_raised = None

        with caplog.at_level(logging.INFO):
            try:
                await background_fetch_job()
                job_completed = True
            except Exception as e:
                exception_raised = e
                job_completed = False

    # Assert: Verify partial retry success handling

    # Property 1: Scheduler should complete successfully after retry success
    assert (
        job_completed
    ), f"Scheduler should complete after retry success, but raised: {exception_raised}"

    # Property 2: Should attempt exactly success_on_attempt times
    assert (
        len(get_feeds_attempts) == success_on_attempt
    ), f"Should attempt {success_on_attempt} times, but attempted {len(get_feeds_attempts)} times"

    # Property 3: Sleep should be called for retries (success_on_attempt - 1 times)
    expected_sleep_calls = success_on_attempt - 1
    assert (
        mock_sleep.call_count == expected_sleep_calls
    ), f"Sleep should be called {expected_sleep_calls} times, but called {mock_sleep.call_count} times"

    # Property 4: Job should complete successfully (success message logged)
    success_logged = any(
        "completed successfully" in record.message.lower()
        for record in caplog.records
        if record.levelname == "INFO"
    )

    assert success_logged, (
        f"Job completion success should be logged. "
        f"Info logs: {[r.message for r in caplog.records if r.levelname == 'INFO']}"
    )

    # Property 5: All pipeline stages should execute
    assert (
        mock_rss.fetch_new_articles.call_count > 0
    ), "RSS service should be called after successful retry"
    assert (
        mock_llm.evaluate_batch.call_count > 0
    ), "LLM service should be called after successful retry"
    assert (
        mock_supabase.insert_articles.call_count > 0
    ), "Database insertion should be called after successful retry"


# Feature: background-scheduler-ai-pipeline, Property 11: Scheduler Robustness (Unexpected Exceptions)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    exception_type=st.sampled_from(
        [
            ValueError("Invalid configuration"),
            RuntimeError("Unexpected runtime error"),
            TypeError("Type mismatch"),
            KeyError("Missing key"),
            AttributeError("Missing attribute"),
        ]
    )
)
@pytest.mark.asyncio
async def test_property_11_scheduler_robustness_unexpected_exceptions(exception_type, caplog):
    """
    Property 11: Scheduler Robustness (Unexpected Exceptions)

    When unexpected exceptions occur (non-database errors), the scheduler should:
    - Not crash
    - Log the exception with full stack trace
    - Continue to next scheduled execution
    - Remain operational

    Validates: Requirements 9.5
    """
    # Arrange: Setup to raise unexpected exception
    test_feeds = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        mock_supabase.get_active_feeds.return_value = test_feeds

        # Setup RSS mock to raise unexpected exception
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.side_effect = exception_type

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Act: Run the background job
        job_completed = False
        exception_raised = None

        with caplog.at_level(logging.INFO):  # Capture INFO level to see completion message
            try:
                await background_fetch_job()
                job_completed = True
            except Exception as e:
                exception_raised = e
                job_completed = False

    # Assert: Verify unexpected exception handling

    # Property 1: Scheduler should not crash on unexpected exceptions
    assert (
        job_completed
    ), f"Scheduler should not crash on unexpected exceptions, but raised: {exception_raised}"

    # Property 2: Exception should be logged at CRITICAL level
    critical_logged = any(record.levelname == "CRITICAL" for record in caplog.records)

    assert critical_logged, (
        f"Unexpected exception should be logged at CRITICAL level. "
        f"Log levels: {[r.levelname for r in caplog.records]}"
    )

    # Property 3: Exception message should be in logs
    exception_message = str(exception_type)
    exception_in_logs = any(
        exception_message in record.message or type(exception_type).__name__ in record.message
        for record in caplog.records
        if record.levelname == "CRITICAL"
    )

    assert exception_in_logs, (
        f"Exception message should be in logs. "
        f"Expected: {exception_message}, "
        f"Critical logs: {[r.message for r in caplog.records if r.levelname == 'CRITICAL']}"
    )

    # Property 4: Job completion message should be logged
    completion_logged = any(
        "execution completed" in record.message.lower()
        and "scheduler will continue" in record.message.lower()
        for record in caplog.records
        if record.levelname == "INFO"
    )

    assert completion_logged, (
        f"Job completion should be logged to indicate scheduler continues. "
        f"Info logs: {[r.message for r in caplog.records if r.levelname == 'INFO']}"
    )
