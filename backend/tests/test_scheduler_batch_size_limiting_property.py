"""
Property-based tests for Scheduler batch size limiting
Task 4.12: 撰寫 Scheduler 的屬性測試

Property 14: Batch Size Limiting
Validates Requirements: 12.1, 12.5

This test verifies that the scheduler correctly splits large article lists into batches:
- Lists over 50 articles are split into batches
- Each batch has at most 50 articles
- Lists over 100 articles create multiple batches
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
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


# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(num_articles=st.integers(min_value=51, max_value=200))
@pytest.mark.asyncio
async def test_property_14_batch_size_limiting_over_50(num_articles):
    """
    Property 14: Batch Size Limiting (Over 50 Articles)

    For any list of articles with count > 50, the scheduler should split them
    into batches where each batch has at most 50 articles.

    Validates: Requirements 12.1, 12.5
    """
    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-batch-{uuid4().hex[:8]}.com/article-{i}"
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

    # Track batch sizes
    batch_sizes = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure batch size settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = "UTC"
        mock_settings.scheduler_cron = "0 */6 * * *"
        mock_settings.scheduler_timezone = "UTC"

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

        # Mock evaluate_batch to track batch sizes
        async def mock_evaluate_batch(batch_articles):
            batch_sizes.append(len(batch_articles))
            result = []
            for article in batch_articles:
                # Populate LLM analysis
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return success
        async def mock_insert_articles(articles_dict_list):
            return BatchResult(
                inserted_count=len(articles_dict_list),
                updated_count=0,
                failed_count=0,
                failed_articles=[],
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify batch size limiting properties

    # Property 1: At least one batch should be created
    assert len(batch_sizes) > 0, "At least one batch should be created"

    # Property 2: Each batch should have at most 50 articles
    for i, batch_size in enumerate(batch_sizes):
        assert (
            batch_size <= 50
        ), f"Batch {i + 1} has {batch_size} articles, which exceeds the limit of 50"

    # Property 3: All batches except possibly the last should have exactly 50 articles
    for i, batch_size in enumerate(batch_sizes[:-1]):  # All except last
        assert (
            batch_size == 50
        ), f"Batch {i + 1} (not the last batch) has {batch_size} articles, expected 50"

    # Property 4: The last batch should have the remaining articles
    expected_last_batch_size = num_articles % 50
    if expected_last_batch_size == 0:
        expected_last_batch_size = 50

    assert (
        batch_sizes[-1] == expected_last_batch_size
    ), f"Last batch has {batch_sizes[-1]} articles, expected {expected_last_batch_size}"

    # Property 5: Total articles across all batches should equal input
    total_processed = sum(batch_sizes)
    assert (
        total_processed == num_articles
    ), f"Total articles processed ({total_processed}) should equal input ({num_articles})"

    # Property 6: Number of batches should be correct (ceiling division)
    expected_num_batches = (num_articles + 49) // 50  # Ceiling division
    assert (
        len(batch_sizes) == expected_num_batches
    ), f"Expected {expected_num_batches} batches, but got {len(batch_sizes)}"


# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting (Over 100 Articles)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=101, max_value=300))
@pytest.mark.asyncio
async def test_property_14_batch_size_limiting_over_100(num_articles):
    """
    Property 14: Batch Size Limiting (Over 100 Articles)

    For any list of articles with count > 100, the scheduler should create
    multiple batches, with each batch having at most 50 articles.

    Validates: Requirements 12.1, 12.5
    """
    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-multi-{uuid4().hex[:8]}.com/article-{i}"
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

    # Track batch information
    batch_sizes = []
    batch_calls = 0

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure batch size settings
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

        # Mock evaluate_batch to track batch sizes
        async def mock_evaluate_batch(batch_articles):
            nonlocal batch_calls
            batch_calls += 1
            batch_sizes.append(len(batch_articles))

            result = []
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles
        async def mock_insert_articles(articles_dict_list):
            return BatchResult(
                inserted_count=len(articles_dict_list),
                updated_count=0,
                failed_count=0,
                failed_articles=[],
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify multiple batch creation

    # Property 1: Multiple batches should be created for > 100 articles
    assert (
        len(batch_sizes) >= 3
    ), f"For {num_articles} articles (> 100), expected at least 3 batches, got {len(batch_sizes)}"

    # Property 2: Each batch should have at most 50 articles
    for i, batch_size in enumerate(batch_sizes):
        assert batch_size <= 50, f"Batch {i + 1} has {batch_size} articles, exceeds limit of 50"

    # Property 3: All batches except the last should have exactly 50 articles
    for i, batch_size in enumerate(batch_sizes[:-1]):
        assert batch_size == 50, f"Batch {i + 1} (not last) has {batch_size} articles, expected 50"

    # Property 4: Total articles processed should equal input
    total_processed = sum(batch_sizes)
    assert (
        total_processed == num_articles
    ), f"Total processed ({total_processed}) should equal input ({num_articles})"

    # Property 5: Number of batches should match expected count
    expected_num_batches = (num_articles + 49) // 50
    assert (
        len(batch_sizes) == expected_num_batches
    ), f"Expected {expected_num_batches} batches, got {len(batch_sizes)}"

    # Property 6: evaluate_batch should be called once per batch
    assert batch_calls == len(
        batch_sizes
    ), f"evaluate_batch should be called {len(batch_sizes)} times, was called {batch_calls} times"


# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting (Exactly 50 Articles)
@pytest.mark.asyncio
async def test_property_14_batch_size_limiting_exactly_50():
    """
    Property 14: Batch Size Limiting (Exactly 50 Articles)

    When exactly 50 articles are provided, they should be processed in a single batch.

    Validates: Requirements 12.1
    """
    num_articles = 50

    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-exact50-{uuid4().hex[:8]}.com/article-{i}"
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

    # Track batch sizes
    batch_sizes = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = "UTC"
        mock_settings.scheduler_cron = "0 */6 * * *"
        mock_settings.scheduler_timezone = "UTC"

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
            batch_sizes.append(len(batch_articles))
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=num_articles, updated_count=0, failed_count=0, failed_articles=[]
        )

        # Act
        await background_fetch_job()

    # Assert
    # Property 1: Exactly one batch should be created
    assert (
        len(batch_sizes) == 1
    ), f"For exactly 50 articles, expected 1 batch, got {len(batch_sizes)}"

    # Property 2: The batch should contain all 50 articles
    assert (
        batch_sizes[0] == 50
    ), f"The single batch should contain 50 articles, got {batch_sizes[0]}"


# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting (Exactly 100 Articles)
@pytest.mark.asyncio
async def test_property_14_batch_size_limiting_exactly_100():
    """
    Property 14: Batch Size Limiting (Exactly 100 Articles)

    When exactly 100 articles are provided, they should be split into 2 batches
    of 50 articles each.

    Validates: Requirements 12.1, 12.5
    """
    num_articles = 100

    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-exact100-{uuid4().hex[:8]}.com/article-{i}"
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

    # Track batch sizes
    batch_sizes = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = "UTC"
        mock_settings.scheduler_cron = "0 */6 * * *"
        mock_settings.scheduler_timezone = "UTC"

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
            batch_sizes.append(len(batch_articles))
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=50, updated_count=0, failed_count=0, failed_articles=[]
        )

        # Act
        await background_fetch_job()

    # Assert
    # Property 1: Exactly 2 batches should be created
    assert (
        len(batch_sizes) == 2
    ), f"For exactly 100 articles, expected 2 batches, got {len(batch_sizes)}"

    # Property 2: Each batch should contain exactly 50 articles
    assert batch_sizes[0] == 50, f"First batch should contain 50 articles, got {batch_sizes[0]}"
    assert batch_sizes[1] == 50, f"Second batch should contain 50 articles, got {batch_sizes[1]}"

    # Property 3: Total should equal 100
    assert sum(batch_sizes) == 100, f"Total articles should be 100, got {sum(batch_sizes)}"


# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting (Edge Case: 51 Articles)
@pytest.mark.asyncio
async def test_property_14_batch_size_limiting_51_articles():
    """
    Property 14: Batch Size Limiting (Edge Case: 51 Articles)

    When 51 articles are provided (just over the limit), they should be split
    into 2 batches: one with 50 articles and one with 1 article.

    Validates: Requirements 12.1, 12.5
    """
    num_articles = 51

    # Arrange: Create test articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-51-{uuid4().hex[:8]}.com/article-{i}"
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

    # Track batch sizes
    batch_sizes = []

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.settings") as mock_settings,
    ):
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = "UTC"
        mock_settings.scheduler_cron = "0 */6 * * *"
        mock_settings.scheduler_timezone = "UTC"

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
            batch_sizes.append(len(batch_articles))
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=len(articles), updated_count=0, failed_count=0, failed_articles=[]
        )

        # Act
        await background_fetch_job()

    # Assert
    # Property 1: Exactly 2 batches should be created
    assert len(batch_sizes) == 2, f"For 51 articles, expected 2 batches, got {len(batch_sizes)}"

    # Property 2: First batch should have 50 articles
    assert batch_sizes[0] == 50, f"First batch should contain 50 articles, got {batch_sizes[0]}"

    # Property 3: Second batch should have 1 article
    assert batch_sizes[1] == 1, f"Second batch should contain 1 article, got {batch_sizes[1]}"

    # Property 4: Total should equal 51
    assert sum(batch_sizes) == 51, f"Total articles should be 51, got {sum(batch_sizes)}"
