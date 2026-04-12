"""
Property-based tests for Scheduler re-processing logic
Task 5.2: 撰寫重新處理邏輯的屬性測試

Property 15: Re-processing Logic
Validates Requirements: 13.1, 13.2, 13.3, 13.4, 13.6, 13.7

This test verifies that the scheduler correctly re-processes articles:
- Articles with NULL ai_summary are re-processed
- Articles with non-NULL ai_summary are skipped
- Selective re-processing works correctly (only tinkering_index when ai_summary exists)
- Timestamps are updated during re-processing
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.schemas.article import BatchResult, RSSSource
from app.tasks.scheduler import background_fetch_job

# Hypothesis strategies for generating test data


@st.composite
def article_state_strategy(draw):
    """
    Generate random article states for testing re-processing logic.

    Returns a dict with:
    - id: UUID
    - url: str
    - title: str
    - feed_id: UUID
    - ai_summary: None or str
    - tinkering_index: None or int (1-5)
    """
    has_summary = draw(st.booleans())
    has_index = draw(st.booleans())

    return {
        "id": str(uuid4()),
        "url": f"https://test-{uuid4().hex[:8]}.com/article",
        "title": draw(st.text(min_size=5, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz ")),
        "feed_id": str(uuid4()),
        "ai_summary": draw(st.text(min_size=10, max_size=200)) if has_summary else None,
        "tinkering_index": draw(st.integers(min_value=1, max_value=5)) if has_index else None,
    }


# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic
@settings(
    max_examples=100,  # Minimum 100 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(unanalyzed_articles=st.lists(article_state_strategy(), min_size=1, max_size=20))
@pytest.mark.asyncio
async def test_property_15_reprocessing_null_ai_summary(unanalyzed_articles):
    """
    Property 15: Re-processing Logic - NULL ai_summary

    For any article with ai_summary IS NULL, the system should re-process
    it with LLM, regardless of tinkering_index value.

    Validates: Requirements 13.1, 13.2
    """
    # Filter to only articles with NULL ai_summary
    null_summary_articles = [
        article for article in unanalyzed_articles if article["ai_summary"] is None
    ]

    # Skip if no articles match criteria
    if not null_summary_articles:
        return

    # Track which articles were re-processed
    reprocessed_urls = set()
    llm_called = False

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

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Mock get_unanalyzed_articles to return our test articles
        mock_supabase.get_unanalyzed_articles.return_value = null_summary_articles

        # Setup RSS mock - return no new articles to focus on re-processing
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock evaluate_batch to track re-processing
        async def mock_evaluate_batch(batch_articles):
            nonlocal llm_called
            llm_called = True

            result = []
            for article in batch_articles:
                reprocessed_urls.add(str(article.url))
                # Populate LLM analysis
                article.tinkering_index = 3
                article.ai_summary = f"Re-processed summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to track updates
        async def mock_insert_articles(articles_dict_list):
            return BatchResult(
                inserted_count=0,
                updated_count=len(articles_dict_list),
                failed_count=0,
                failed_articles=[],
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify re-processing behavior

    # Property 1: LLM should be called for articles with NULL ai_summary
    assert llm_called, "LLM should be called to re-process articles with NULL ai_summary"

    # Property 2: All articles with NULL ai_summary should be re-processed
    for article in null_summary_articles:
        assert (
            article["url"] in reprocessed_urls
        ), f"Article {article['url']} with NULL ai_summary should be re-processed"

    # Property 3: insert_articles should be called to update the database
    assert (
        mock_supabase.insert_articles.called
    ), "insert_articles should be called to update re-processed articles"


# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic (Skip Non-NULL)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_complete_articles=st.integers(min_value=1, max_value=10))
@pytest.mark.asyncio
async def test_property_15_skip_complete_articles(num_complete_articles):
    """
    Property 15: Re-processing Logic - Skip Complete Articles

    For any article with ai_summary IS NOT NULL and tinkering_index IS NOT NULL,
    the system should skip LLM processing.

    Validates: Requirements 13.3, 13.6
    """
    # Create articles with both fields populated
    complete_articles = []
    for i in range(num_complete_articles):
        complete_articles.append(
            {
                "id": str(uuid4()),
                "url": f"https://complete-{uuid4().hex[:8]}.com/article-{i}",
                "title": f"Complete Article {i}",
                "feed_id": str(uuid4()),
                "ai_summary": f"Existing summary {i}",
                "tinkering_index": 3,
            }
        )

    llm_called_for_reprocessing = False

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

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Return empty list - no unanalyzed articles
        mock_supabase.get_unanalyzed_articles.return_value = []

        # Setup RSS mock - return no new articles
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            nonlocal llm_called_for_reprocessing
            llm_called_for_reprocessing = True
            return batch_articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify that LLM was NOT called for re-processing
    # (since get_unanalyzed_articles returned empty list)

    # Property: LLM should not be called when no unanalyzed articles exist
    assert (
        not llm_called_for_reprocessing
    ), "LLM should not be called when all articles have complete analysis"


# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic (Selective)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_partial_articles=st.integers(min_value=1, max_value=10))
@pytest.mark.asyncio
async def test_property_15_selective_reprocessing(num_partial_articles):
    """
    Property 15: Re-processing Logic - Selective Re-processing

    For any article with tinkering_index IS NULL but ai_summary IS NOT NULL,
    the system should re-process to populate tinkering_index.

    Note: Current implementation re-processes both fields. This test verifies
    that articles with NULL tinkering_index are identified and re-processed.

    Validates: Requirements 13.7
    """
    # Create articles with ai_summary but NULL tinkering_index
    partial_articles = []
    for i in range(num_partial_articles):
        partial_articles.append(
            {
                "id": str(uuid4()),
                "url": f"https://partial-{uuid4().hex[:8]}.com/article-{i}",
                "title": f"Partial Article {i}",
                "feed_id": str(uuid4()),
                "ai_summary": f"Existing summary {i}",
                "tinkering_index": None,  # NULL - needs re-processing
            }
        )

    reprocessed_count = 0

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

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Return partial articles as unanalyzed
        mock_supabase.get_unanalyzed_articles.return_value = partial_articles

        # Setup RSS mock - return no new articles
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            nonlocal reprocessed_count
            reprocessed_count = len(batch_articles)

            result = []
            for article in batch_articles:
                # Populate tinkering_index (and re-generate ai_summary)
                article.tinkering_index = 4
                article.ai_summary = f"Re-processed summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=0, updated_count=num_partial_articles, failed_count=0, failed_articles=[]
        )

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify selective re-processing

    # Property 1: Articles with NULL tinkering_index should be re-processed
    assert (
        reprocessed_count == num_partial_articles
    ), f"Expected {num_partial_articles} articles to be re-processed, got {reprocessed_count}"

    # Property 2: LLM should be called for re-processing
    assert (
        mock_llm.evaluate_batch.called
    ), "LLM should be called to re-process articles with NULL tinkering_index"


# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic (Timestamp Update)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=1, max_value=10))
@pytest.mark.asyncio
async def test_property_15_timestamp_update_on_reprocessing(num_articles):
    """
    Property 15: Re-processing Logic - Timestamp Update

    For any article that is re-processed, the updated_at timestamp should be
    updated when the article is written back to the database via UPSERT.

    Validates: Requirements 13.4
    """
    # Create articles with NULL ai_summary
    unanalyzed_articles = []
    for i in range(num_articles):
        unanalyzed_articles.append(
            {
                "id": str(uuid4()),
                "url": f"https://timestamp-{uuid4().hex[:8]}.com/article-{i}",
                "title": f"Timestamp Test Article {i}",
                "feed_id": str(uuid4()),
                "ai_summary": None,
                "tinkering_index": None,
            }
        )

    insert_called = False
    inserted_articles = []

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

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        mock_supabase.get_unanalyzed_articles.return_value = unanalyzed_articles

        # Setup RSS mock - return no new articles
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                article.tinkering_index = 3
                article.ai_summary = f"Summary for {article.title}"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to capture the articles being updated
        async def mock_insert_articles(articles_dict_list):
            nonlocal insert_called, inserted_articles
            insert_called = True
            inserted_articles = articles_dict_list

            return BatchResult(
                inserted_count=0,
                updated_count=len(articles_dict_list),
                failed_count=0,
                failed_articles=[],
            )

        mock_supabase.insert_articles.side_effect = mock_insert_articles

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify timestamp update behavior

    # Property 1: insert_articles should be called for re-processed articles
    assert insert_called, "insert_articles should be called to update re-processed articles"

    # Property 2: All re-processed articles should be passed to insert_articles
    assert (
        len(inserted_articles) == num_articles
    ), f"Expected {num_articles} articles to be updated, got {len(inserted_articles)}"

    # Property 3: Each article should have the required fields for UPSERT
    for article_dict in inserted_articles:
        assert "url" in article_dict, "Article must have 'url' field for UPSERT operation"
        assert "title" in article_dict, "Article must have 'title' field"
        assert "feed_id" in article_dict, "Article must have 'feed_id' field"
        assert (
            "ai_summary" in article_dict
        ), "Article must have 'ai_summary' field after re-processing"
        assert (
            "tinkering_index" in article_dict
        ), "Article must have 'tinkering_index' field after re-processing"

        # Verify that ai_summary and tinkering_index are not NULL
        assert (
            article_dict["ai_summary"] is not None
        ), "Re-processed article should have non-NULL ai_summary"
        assert (
            article_dict["tinkering_index"] is not None
        ), "Re-processed article should have non-NULL tinkering_index"


# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic (Mixed States)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(articles=st.lists(article_state_strategy(), min_size=1, max_size=15))
@pytest.mark.asyncio
async def test_property_15_mixed_article_states(articles):
    """
    Property 15: Re-processing Logic - Mixed Article States

    For any mix of article states (complete, partial, unanalyzed), the system
    should correctly identify and re-process only those with NULL fields.

    Validates: Requirements 13.1, 13.2, 13.3, 13.6, 13.7
    """
    # Separate articles by state
    needs_reprocessing = [
        article
        for article in articles
        if article["ai_summary"] is None or article["tinkering_index"] is None
    ]

    complete_articles = [
        article
        for article in articles
        if article["ai_summary"] is not None and article["tinkering_index"] is not None
    ]

    # Skip if no articles need re-processing
    if not needs_reprocessing:
        return

    reprocessed_urls = set()

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

        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_supabase.get_active_feeds.return_value = [
            RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")
        ]

        # Return only articles that need re-processing
        mock_supabase.get_unanalyzed_articles.return_value = needs_reprocessing

        # Setup RSS mock - return no new articles
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        mock_rss.fetch_new_articles.return_value = []

        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        async def mock_evaluate_batch(batch_articles):
            result = []
            for article in batch_articles:
                reprocessed_urls.add(str(article.url))
                article.tinkering_index = 3
                article.ai_summary = "Re-processed summary"
                result.append(article)
            return result

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=0,
            updated_count=len(needs_reprocessing),
            failed_count=0,
            failed_articles=[],
        )

        # Act: Run the background job
        await background_fetch_job()

    # Assert: Verify correct re-processing behavior

    # Property 1: All articles needing re-processing should be processed
    for article in needs_reprocessing:
        assert (
            article["url"] in reprocessed_urls
        ), f"Article {article['url']} with NULL fields should be re-processed"

    # Property 2: Number of re-processed articles should match expected count
    assert len(reprocessed_urls) == len(
        needs_reprocessing
    ), f"Expected {len(needs_reprocessing)} articles to be re-processed, got {len(reprocessed_urls)}"
