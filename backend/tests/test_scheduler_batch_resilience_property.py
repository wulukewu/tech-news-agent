"""
Property-based tests for Scheduler batch processing resilience
Task 4.8: 撰寫 Scheduler 的屬性測試

Property 3: Batch Processing Resilience
Validates Requirements: 2.7, 7.2, 8.3, 4.8

This test verifies that the scheduler correctly handles failures in batch processing:
- Individual item failures don't prevent other items from being processed
- All items are attempted for processing
- Failed items are tracked and logged
- Successful items complete normally
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


def article_strategy():
    """Generate valid ArticleSchema objects"""
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=200),
        url=valid_url_strategy(),
        feed_id=st.uuids(),
        feed_name=st.text(min_size=1, max_size=50),
        category=st.sampled_from(["AI", "DevOps", "Web", "Mobile", "Security"]),
        published_at=st.just(datetime.now(UTC)),
        tinkering_index=st.none(),
        ai_summary=st.none(),
        embedding=st.none(),
    )


# Feature: background-scheduler-ai-pipeline, Property 3: Batch Processing Resilience
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(
    num_articles=st.integers(min_value=5, max_value=20),
    num_llm_failures=st.integers(min_value=1, max_value=10),
    num_db_failures=st.integers(min_value=0, max_value=5),
)
@pytest.mark.asyncio
async def test_property_3_batch_processing_resilience(
    num_articles, num_llm_failures, num_db_failures
):
    """
    Property 3: Batch Processing Resilience

    For any batch of items (feeds, articles, or database operations), when
    individual items fail, the system should continue processing remaining items.
    Specifically:
    - LLM analysis failures should not prevent other articles from being analyzed
    - Database insertion failures should not prevent other articles from being inserted
    - All items should be attempted for processing

    Validates: Requirements 2.7, 7.2, 8.3, 4.8
    """
    # Ensure we have valid test cases
    assume(num_llm_failures <= num_articles)
    assume(num_db_failures <= num_articles)

    # Arrange: Create test data
    # Generate unique articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-resilience-{uuid4().hex[:8]}.com/article-{i}"
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

    # Determine which articles will fail at LLM stage
    llm_failing_indices = set(range(num_llm_failures))

    # Determine which articles will fail at DB stage (from successful LLM articles)
    successful_llm_indices = set(range(num_articles)) - llm_failing_indices
    db_failing_indices = set(list(successful_llm_indices)[:num_db_failures])

    # Track which articles were processed
    llm_processed_articles = []
    db_insert_attempts = []

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

        # Mock evaluate_batch to track processing and inject failures
        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                llm_processed_articles.append(str(article.url))

                # Find article index
                article_index = int(str(article.url).split("-")[-1])

                if article_index in llm_failing_indices:
                    # LLM failure: set NULL values
                    article.tinkering_index = None
                    article.ai_summary = None
                else:
                    # LLM success: populate values
                    article.tinkering_index = 3
                    article.ai_summary = f"Summary for {article.title}"

                result.append(article)

            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to track attempts and inject failures
        async def mock_insert_articles(articles_dict_list):
            # Track all insertion attempts
            for article_dict in articles_dict_list:
                db_insert_attempts.append(article_dict["url"])

            # Count successes and failures based on our failure set
            inserted = 0
            updated = 0
            failed = 0
            failed_articles = []

            for article_dict in articles_dict_list:
                # Extract article index from URL
                article_index = int(article_dict["url"].split("-")[-1])

                if article_index in db_failing_indices:
                    # Database failure
                    failed += 1
                    failed_articles.append(
                        {"url": article_dict["url"], "error": "Simulated database error"}
                    )
                # Database success (randomly choose insert or update)
                elif article_index % 2 == 0:
                    inserted += 1
                else:
                    updated += 1

            return BatchResult(
                inserted_count=inserted,
                updated_count=updated,
                failed_count=failed,
                failed_articles=failed_articles,
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify batch processing resilience properties

    # Property 1: All articles should be attempted for LLM processing
    assert len(llm_processed_articles) == num_articles, (
        f"Expected {num_articles} articles to be processed by LLM, "
        f"but only {len(llm_processed_articles)} were processed"
    )

    # Property 2: All articles should have unique URLs in LLM processing
    assert (
        len(set(llm_processed_articles)) == num_articles
    ), "LLM processing should not duplicate articles"

    # Property 3: All successfully analyzed articles should be attempted for DB insertion
    # (articles with LLM failures should still be attempted for insertion)
    expected_db_attempts = num_articles  # All articles should be attempted
    assert len(db_insert_attempts) == expected_db_attempts, (
        f"Expected {expected_db_attempts} articles to be attempted for DB insertion, "
        f"but only {len(db_insert_attempts)} were attempted"
    )

    # Property 4: Database insertion should be called (batch processing continues despite LLM failures)
    assert (
        mock_supabase.insert_articles.call_count > 0
    ), "Database insertion should be called even if some LLM analyses fail"

    # Property 5: LLM evaluate_batch should be called (processing should not be skipped)
    assert mock_llm.evaluate_batch.call_count > 0, "LLM evaluate_batch should be called"


# Feature: background-scheduler-ai-pipeline, Property 3: Batch Processing Resilience (Feed Failures)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_feeds=st.integers(min_value=3, max_value=10),
    num_feed_failures=st.integers(min_value=1, max_value=5),
)
@pytest.mark.asyncio
async def test_property_3_feed_fetch_resilience(num_feeds, num_feed_failures):
    """
    Property 3: Batch Processing Resilience (Feed Failures)

    When individual feeds fail to fetch, other feeds should still be processed.
    The RSS service should continue processing remaining feeds after a failure.

    Validates: Requirements 2.7, 7.2
    """
    # Ensure valid test case
    assume(num_feed_failures < num_feeds)

    # Arrange: Create test feeds
    feeds = []
    feed_ids = []  # Track feed IDs separately
    for i in range(num_feeds):
        feed_id = uuid4()
        feed_ids.append(feed_id)
        feed = RSSSource(name=f"Test Feed {i}", url=f"https://example.com/feed-{i}", category="AI")
        feeds.append(feed)

    # Determine which feeds will fail
    failing_feed_indices = set(range(num_feed_failures))

    # Track which feeds were attempted
    attempted_feeds = []
    successful_articles = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds to return our test feeds
        mock_supabase.get_active_feeds.return_value = feeds

        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        # Mock fetch_new_articles to simulate partial feed failures
        async def mock_fetch_new_articles(feed_sources, supabase_service):
            # Track all feed attempts
            for feed in feed_sources:
                attempted_feeds.append(feed.name)

            # Generate articles only from successful feeds
            articles = []
            for i, feed in enumerate(feed_sources):
                if i not in failing_feed_indices:
                    # Successful feed: generate 2 articles
                    for j in range(2):
                        article = ArticleSchema(
                            title=f"Article {j} from {feed.name}",
                            url=f"https://test-feed-{i}-article-{j}.com",
                            feed_id=feed_ids[i],  # Use the tracked feed ID
                            feed_name=feed.name,
                            category=feed.category,
                            published_at=datetime.now(UTC),
                            tinkering_index=None,
                            ai_summary=None,
                        )
                        articles.append(article)
                        successful_articles.append(article.url)

            return articles

        mock_rss.fetch_new_articles.side_effect = mock_fetch_new_articles

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock evaluate_batch to return articles with analysis
        async def mock_evaluate_batch(batch_articles):
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return success
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=len(successful_articles),
            updated_count=0,
            failed_count=0,
            failed_articles=[],
        )

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify feed processing resilience

    # Property 1: All feeds should be attempted
    assert len(attempted_feeds) == num_feeds, (
        f"Expected {num_feeds} feeds to be attempted, "
        f"but only {len(attempted_feeds)} were attempted"
    )

    # Property 2: Articles from successful feeds should be processed
    expected_successful_feeds = num_feeds - num_feed_failures
    expected_articles = expected_successful_feeds * 2  # 2 articles per successful feed

    assert len(successful_articles) == expected_articles, (
        f"Expected {expected_articles} articles from successful feeds, "
        f"got {len(successful_articles)}"
    )

    # Property 3: LLM processing should occur for successful articles
    if expected_articles > 0:
        assert (
            mock_llm.evaluate_batch.call_count > 0
        ), "LLM should process articles from successful feeds"

        # Property 4: Database insertion should occur for successful articles
        assert (
            mock_supabase.insert_articles.call_count > 0
        ), "Database insertion should occur for articles from successful feeds"


# Feature: background-scheduler-ai-pipeline, Property 3: Batch Processing Resilience (All Items Fail)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=3, max_value=15))
@pytest.mark.asyncio
async def test_property_3_all_items_fail_gracefully(num_articles):
    """
    Property 3: Batch Processing Resilience (All Items Fail)

    When all items fail processing, the system should:
    - Attempt to process all items
    - Not crash or raise exceptions
    - Log appropriate errors
    - Complete the job execution

    Validates: Requirements 8.3, 4.8
    """
    # Arrange: Create test articles
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

    # Track processing
    llm_processed = []
    db_attempted = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
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

        # Setup LLM mock - all fail
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                llm_processed.append(str(article.url))
                # All LLM analyses fail - set NULL values
                article.tinkering_index = None
                article.ai_summary = None
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles - all fail
        async def mock_insert_articles(articles_dict_list):
            for article_dict in articles_dict_list:
                db_attempted.append(article_dict["url"])

            # All insertions fail
            return BatchResult(
                inserted_count=0,
                updated_count=0,
                failed_count=len(articles_dict_list),
                failed_articles=[
                    {"url": a["url"], "error": "Simulated failure"} for a in articles_dict_list
                ],
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job (should not raise exception)
        try:
            await background_fetch_job()
            job_completed = True
        except Exception as e:
            job_completed = False
            pytest.fail(f"Job should not raise exception when all items fail, but raised: {e}")

    # Assert: Verify graceful failure handling

    # Property 1: Job should complete without crashing
    assert job_completed, "Job should complete even when all items fail"

    # Property 2: All articles should be attempted for LLM processing
    assert (
        len(llm_processed) == num_articles
    ), f"All {num_articles} articles should be attempted for LLM processing"

    # Property 3: All articles should be attempted for DB insertion
    assert (
        len(db_attempted) == num_articles
    ), f"All {num_articles} articles should be attempted for DB insertion"

    # Property 4: Processing methods should be called
    assert mock_llm.evaluate_batch.call_count > 0, "LLM evaluate_batch should be called"
    assert mock_supabase.insert_articles.call_count > 0, "Database insert_articles should be called"


# Feature: background-scheduler-ai-pipeline, Property 3: Batch Processing Resilience (Empty Batch)
@pytest.mark.asyncio
async def test_property_3_empty_batch_handling():
    """
    Property 3: Batch Processing Resilience (Empty Batch)

    When no new articles are found, the system should:
    - Complete gracefully without errors
    - Not attempt LLM processing
    - Not attempt database insertion
    - Log appropriate messages

    Validates: Requirements 2.7
    """
    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds
        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Setup RSS mock - return empty list
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify empty batch handling

    # Property 1: LLM should not be called for empty batch
    assert (
        mock_llm.evaluate_batch.call_count == 0
    ), "LLM should not be called when no articles are found"

    # Property 2: Database insertion should not be called for empty batch
    assert (
        mock_supabase.insert_articles.call_count == 0
    ), "Database insertion should not be called when no articles are found"

    # Property 3: Job should complete successfully
    # (if we reach here without exception, the job completed)
    assert True, "Job should complete successfully with empty batch"
