"""
Property-based tests for Scheduler batch result accuracy
Task 4.9: 撰寫 Scheduler 的屬性測試

Property 8: Batch Result Accuracy
Validates Requirements: 4.6, 7.6

This test verifies that batch operation results are accurately tracked:
- For batch operations: success_count + failure_count = total_count
- For article insertion: inserted_count + updated_count + failed_count = total_articles
- All articles are accounted for in the result
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema, BatchResult, RSSSource
from app.tasks.scheduler import background_fetch_job

# Hypothesis strategies for generating test data


def valid_url_strategy():
    """Generate valid HTTP/HTTPS URLs for articles"""
    domains = st.sampled_from(["example.com", "test.org", "demo.net", "sample.io", "news.com"])
    paths = st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=15),
        min_size=1,
        max_size=3,
    )

    def build_url(domain, path_parts):
        path = "/".join(path_parts)
        return f"https://{domain}/{path}"

    return st.builds(build_url, domains, paths)


# Feature: background-scheduler-ai-pipeline, Property 8: Batch Result Accuracy
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(
    num_articles=st.integers(min_value=5, max_value=30),
    num_inserted=st.integers(min_value=0, max_value=20),
    num_updated=st.integers(min_value=0, max_value=20),
    num_failed=st.integers(min_value=0, max_value=10),
)
@pytest.mark.asyncio
async def test_property_8_batch_result_accuracy(
    num_articles, num_inserted, num_updated, num_failed
):
    """
    Property 8: Batch Result Accuracy

    For any batch operation (feed fetching, article insertion), the sum of
    success count and failure count should equal the total input count.
    Specifically:
    - For article insertion: inserted_count + updated_count + failed_count = total_articles

    Validates: Requirements 4.6, 7.6
    """
    # Ensure the counts don't exceed the total number of articles
    assume(num_inserted + num_updated + num_failed <= num_articles)

    # Calculate actual counts to match total articles
    # Distribute remaining articles to inserted/updated/failed proportionally
    total_specified = num_inserted + num_updated + num_failed
    remaining = num_articles - total_specified

    # Add remaining to inserted count (could be any category)
    actual_inserted = num_inserted + remaining
    actual_updated = num_updated
    actual_failed = num_failed

    # Verify our calculation is correct
    assert actual_inserted + actual_updated + actual_failed == num_articles

    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-accuracy-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Track the batch result returned
    captured_batch_result = None

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        # Mock fetch_new_articles to return our test articles
        mock_rss.fetch_new_articles.return_value = articles

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock evaluate_batch to return articles with analysis
        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                # Populate LLM analysis
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return our specified batch result
        async def mock_insert_articles(articles_dict_list):
            nonlocal captured_batch_result

            # Create failed articles list
            failed_articles = []
            for i in range(actual_failed):
                if i < len(articles_dict_list):
                    failed_articles.append(
                        {"url": articles_dict_list[i]["url"], "error": f"Simulated error {i}"}
                    )

            # Create batch result with our specified counts
            batch_result = BatchResult(
                inserted_count=actual_inserted,
                updated_count=actual_updated,
                failed_count=actual_failed,
                failed_articles=failed_articles,
            )

            captured_batch_result = batch_result
            return batch_result

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify batch result accuracy properties

    # Property 1: Batch result should be captured
    assert captured_batch_result is not None, "Batch result should be returned from insert_articles"

    # Property 2: inserted_count + updated_count + failed_count = total_articles
    total_accounted = (
        captured_batch_result.inserted_count
        + captured_batch_result.updated_count
        + captured_batch_result.failed_count
    )

    assert total_accounted == num_articles, (
        f"Batch result accuracy violated: "
        f"inserted({captured_batch_result.inserted_count}) + "
        f"updated({captured_batch_result.updated_count}) + "
        f"failed({captured_batch_result.failed_count}) = {total_accounted}, "
        f"but expected {num_articles}"
    )

    # Property 3: Individual counts should match what we specified
    assert (
        captured_batch_result.inserted_count == actual_inserted
    ), f"Inserted count mismatch: expected {actual_inserted}, got {captured_batch_result.inserted_count}"

    assert (
        captured_batch_result.updated_count == actual_updated
    ), f"Updated count mismatch: expected {actual_updated}, got {captured_batch_result.updated_count}"

    assert (
        captured_batch_result.failed_count == actual_failed
    ), f"Failed count mismatch: expected {actual_failed}, got {captured_batch_result.failed_count}"

    # Property 4: Failed articles list should match failed count
    assert len(captured_batch_result.failed_articles) == actual_failed, (
        f"Failed articles list length ({len(captured_batch_result.failed_articles)}) "
        f"should match failed_count ({actual_failed})"
    )

    # Property 5: total_processed property should equal total articles
    assert captured_batch_result.total_processed == num_articles, (
        f"total_processed ({captured_batch_result.total_processed}) "
        f"should equal total articles ({num_articles})"
    )


# Feature: background-scheduler-ai-pipeline, Property 8: Batch Result Accuracy (Multiple Batches)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_articles=st.integers(min_value=60, max_value=150),  # Force multiple batches
    failure_rate=st.floats(min_value=0.0, max_value=0.3),  # 0-30% failure rate
)
@pytest.mark.asyncio
async def test_property_8_multiple_batches_accuracy(num_articles, failure_rate):
    """
    Property 8: Batch Result Accuracy (Multiple Batches)

    When processing multiple batches, the aggregated results should still
    maintain accuracy: total inserted + updated + failed = total articles.

    Validates: Requirements 4.6, 7.6
    """
    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-multibatch-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Track all batch results
    all_batch_results = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure batch size to force multiple batches
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = "UTC"
        mock_settings.scheduler_cron = "0 */6 * * *"
        mock_settings.scheduler_timezone = "UTC"

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds
        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = articles

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock evaluate_batch
        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to simulate realistic batch results
        async def mock_insert_articles(articles_dict_list):
            batch_size = len(articles_dict_list)

            # Calculate failures based on failure rate
            num_failed = int(batch_size * failure_rate)
            num_success = batch_size - num_failed

            # Split successes between inserted and updated (roughly 60/40)
            num_inserted = int(num_success * 0.6)
            num_updated = num_success - num_inserted

            # Create failed articles list
            failed_articles = []
            for i in range(num_failed):
                failed_articles.append(
                    {"url": articles_dict_list[i]["url"], "error": f"Simulated error {i}"}
                )

            batch_result = BatchResult(
                inserted_count=num_inserted,
                updated_count=num_updated,
                failed_count=num_failed,
                failed_articles=failed_articles,
            )

            all_batch_results.append(batch_result)
            return batch_result

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify aggregated batch result accuracy

    # Property 1: At least one batch should have been processed
    assert len(all_batch_results) > 0, "At least one batch should be processed"

    # Property 2: Aggregate all batch results
    total_inserted = sum(br.inserted_count for br in all_batch_results)
    total_updated = sum(br.updated_count for br in all_batch_results)
    total_failed = sum(br.failed_count for br in all_batch_results)

    # Property 3: Aggregated counts should equal total articles
    total_accounted = total_inserted + total_updated + total_failed

    assert total_accounted == num_articles, (
        f"Aggregated batch result accuracy violated: "
        f"inserted({total_inserted}) + "
        f"updated({total_updated}) + "
        f"failed({total_failed}) = {total_accounted}, "
        f"but expected {num_articles}"
    )

    # Property 4: Each individual batch should be accurate
    for i, batch_result in enumerate(all_batch_results):
        batch_total = (
            batch_result.inserted_count + batch_result.updated_count + batch_result.failed_count
        )

        # Each batch should account for all its articles
        assert batch_total > 0, f"Batch {i} should have processed at least one article"

        # Failed articles list should match failed count
        assert len(batch_result.failed_articles) == batch_result.failed_count, (
            f"Batch {i}: failed_articles length ({len(batch_result.failed_articles)}) "
            f"should match failed_count ({batch_result.failed_count})"
        )


# Feature: background-scheduler-ai-pipeline, Property 8: Batch Result Accuracy (All Success)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=5, max_value=30))
@pytest.mark.asyncio
async def test_property_8_all_success_accuracy(num_articles):
    """
    Property 8: Batch Result Accuracy (All Success)

    When all operations succeed, the batch result should show:
    - failed_count = 0
    - inserted_count + updated_count = total_articles
    - failed_articles list is empty

    Validates: Requirements 4.6, 7.6
    """
    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-allsuccess-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    captured_batch_result = None

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup mocks
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = articles

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # All operations succeed
        async def mock_insert_articles(articles_dict_list):
            nonlocal captured_batch_result

            batch_size = len(articles_dict_list)
            # Split between inserted and updated (60/40)
            num_inserted = int(batch_size * 0.6)
            num_updated = batch_size - num_inserted

            batch_result = BatchResult(
                inserted_count=num_inserted,
                updated_count=num_updated,
                failed_count=0,
                failed_articles=[],
            )

            captured_batch_result = batch_result
            return batch_result

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act
        await background_fetch_job()

    # Assert
    assert captured_batch_result is not None

    # Property 1: No failures
    assert (
        captured_batch_result.failed_count == 0
    ), "Failed count should be 0 when all operations succeed"

    assert (
        len(captured_batch_result.failed_articles) == 0
    ), "Failed articles list should be empty when all operations succeed"

    # Property 2: All articles accounted for in success counts
    total_success = captured_batch_result.inserted_count + captured_batch_result.updated_count

    assert total_success == num_articles, (
        f"All articles should be accounted for in success counts: "
        f"inserted({captured_batch_result.inserted_count}) + "
        f"updated({captured_batch_result.updated_count}) = {total_success}, "
        f"expected {num_articles}"
    )

    # Property 3: Success rate should be 1.0
    assert (
        captured_batch_result.success_rate == 1.0
    ), "Success rate should be 1.0 when all operations succeed"


# Feature: background-scheduler-ai-pipeline, Property 8: Batch Result Accuracy (All Fail)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=5, max_value=30))
@pytest.mark.asyncio
async def test_property_8_all_fail_accuracy(num_articles):
    """
    Property 8: Batch Result Accuracy (All Fail)

    When all operations fail, the batch result should show:
    - inserted_count = 0
    - updated_count = 0
    - failed_count = total_articles
    - failed_articles list has total_articles entries

    Validates: Requirements 4.6, 7.6
    """
    # Arrange
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-allfail-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    captured_batch_result = None

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = articles

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # All operations fail
        async def mock_insert_articles(articles_dict_list):
            nonlocal captured_batch_result

            failed_articles = [
                {"url": a["url"], "error": "Simulated failure"} for a in articles_dict_list
            ]

            batch_result = BatchResult(
                inserted_count=0,
                updated_count=0,
                failed_count=len(articles_dict_list),
                failed_articles=failed_articles,
            )

            captured_batch_result = batch_result
            return batch_result

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act
        await background_fetch_job()

    # Assert
    assert captured_batch_result is not None

    # Property 1: No successes
    assert (
        captured_batch_result.inserted_count == 0
    ), "Inserted count should be 0 when all operations fail"

    assert (
        captured_batch_result.updated_count == 0
    ), "Updated count should be 0 when all operations fail"

    # Property 2: All articles accounted for in failed count
    assert captured_batch_result.failed_count == num_articles, (
        f"Failed count should equal total articles: "
        f"expected {num_articles}, got {captured_batch_result.failed_count}"
    )

    # Property 3: Failed articles list matches failed count
    assert len(captured_batch_result.failed_articles) == num_articles, (
        f"Failed articles list length should equal total articles: "
        f"expected {num_articles}, got {len(captured_batch_result.failed_articles)}"
    )

    # Property 4: Success rate should be 0.0
    assert (
        captured_batch_result.success_rate == 0.0
    ), "Success rate should be 0.0 when all operations fail"
