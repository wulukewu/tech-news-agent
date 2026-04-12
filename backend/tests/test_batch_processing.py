"""
Tests for batch processing logic in scheduler.

Validates: Requirements 12.1, 12.4, 12.5, 12.6, 12.7
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.article import ArticleSchema, BatchResult
from app.tasks.scheduler import background_fetch_job


@pytest.mark.asyncio
async def test_batch_processing_splits_large_article_sets():
    """
    Test that articles are split into batches when count exceeds threshold.

    Validates: Requirements 12.1, 12.5
    """
    # Create 120 mock articles (should split into 3 batches of 50)
    mock_articles = []
    for i in range(120):
        article = ArticleSchema(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
            embedding=None,
        )
        mock_articles.append(article)

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup mocks
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            {"id": str(uuid4()), "name": "Test Feed", "url": "https://example.com/feed"}
        ]

        # Mock fetch_new_articles to return 120 articles
        mock_rss.fetch_new_articles.return_value = mock_articles

        # Mock evaluate_batch to return articles with analysis
        def mock_evaluate_batch(articles):
            for article in articles:
                article.tinkering_index = 3
                article.ai_summary = "Test summary"
            return articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return success
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=50, updated_count=0, failed_count=0, failed_articles=[]
        )

        # Run the background job
        await background_fetch_job()

        # Verify that evaluate_batch was called 3 times (3 batches)
        assert mock_llm.evaluate_batch.call_count == 3

        # Verify batch sizes
        call_args_list = mock_llm.evaluate_batch.call_args_list
        assert len(call_args_list[0][0][0]) == 50  # First batch: 50 articles
        assert len(call_args_list[1][0][0]) == 50  # Second batch: 50 articles
        assert len(call_args_list[2][0][0]) == 20  # Third batch: 20 articles

        # Verify insert_articles was called 3 times
        assert mock_supabase.insert_articles.call_count == 3


@pytest.mark.asyncio
async def test_batch_processing_handles_small_article_sets():
    """
    Test that small article sets (< batch_size) are processed in a single batch.

    Validates: Requirements 12.1
    """
    # Create 30 mock articles (should be processed in 1 batch)
    mock_articles = []
    for i in range(30):
        article = ArticleSchema(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
            embedding=None,
        )
        mock_articles.append(article)

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
    ):
        # Setup mocks
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            {"id": str(uuid4()), "name": "Test Feed", "url": "https://example.com/feed"}
        ]

        # Mock fetch_new_articles to return 30 articles
        mock_rss.fetch_new_articles.return_value = mock_articles

        # Mock evaluate_batch to return articles with analysis
        def mock_evaluate_batch(articles):
            for article in articles:
                article.tinkering_index = 3
                article.ai_summary = "Test summary"
            return articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return success
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=30, updated_count=0, failed_count=0, failed_articles=[]
        )

        # Run the background job
        await background_fetch_job()

        # Verify that evaluate_batch was called only once
        assert mock_llm.evaluate_batch.call_count == 1

        # Verify batch size
        call_args_list = mock_llm.evaluate_batch.call_args_list
        assert len(call_args_list[0][0][0]) == 30  # Single batch: 30 articles

        # Verify insert_articles was called once
        assert mock_supabase.insert_articles.call_count == 1


@pytest.mark.asyncio
async def test_batch_processing_aggregates_results():
    """
    Test that batch results are correctly aggregated across multiple batches.

    Validates: Requirements 12.6, 12.7
    """
    # Create 100 mock articles (should split into 2 batches of 50)
    mock_articles = []
    for i in range(100):
        article = ArticleSchema(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
            embedding=None,
        )
        mock_articles.append(article)

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.logger") as mock_logger,
    ):
        # Setup mocks
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            {"id": str(uuid4()), "name": "Test Feed", "url": "https://example.com/feed"}
        ]

        # Mock fetch_new_articles to return 100 articles
        mock_rss.fetch_new_articles.return_value = mock_articles

        # Mock evaluate_batch to return articles with analysis
        def mock_evaluate_batch(articles):
            for article in articles:
                article.tinkering_index = 3
                article.ai_summary = "Test summary"
            return articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return different results for each batch
        batch_results = [
            BatchResult(inserted_count=40, updated_count=8, failed_count=2, failed_articles=[]),
            BatchResult(inserted_count=35, updated_count=10, failed_count=5, failed_articles=[]),
        ]
        mock_supabase.insert_articles.side_effect = batch_results

        # Run the background job
        await background_fetch_job()

        # Verify that the final log contains aggregated results
        # Find the final completion log call
        final_log_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Background fetch job completed successfully" in str(call)
        ]

        assert len(final_log_calls) > 0
        final_log = str(final_log_calls[0])

        # Verify aggregated counts
        assert "Inserted: 75" in final_log  # 40 + 35
        assert "Updated: 18" in final_log  # 8 + 10
        assert "Failed: 7" in final_log  # 2 + 5
        assert "Batches: 2" in final_log


@pytest.mark.asyncio
async def test_batch_processing_logs_timing():
    """
    Test that batch processing logs timing information for each batch.

    Validates: Requirements 12.6, 12.7
    """
    # Create 60 mock articles (should split into 2 batches)
    mock_articles = []
    for i in range(60):
        article = ArticleSchema(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
            embedding=None,
        )
        mock_articles.append(article)

    # Mock dependencies
    with (
        patch("app.tasks.scheduler.SupabaseService") as mock_supabase_class,
        patch("app.tasks.scheduler.RSSService") as mock_rss_class,
        patch("app.tasks.scheduler.LLMService") as mock_llm_class,
        patch("app.tasks.scheduler.logger") as mock_logger,
    ):
        # Setup mocks
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase

        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss

        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Mock get_active_feeds to return one feed
        mock_supabase.get_active_feeds.return_value = [
            {"id": str(uuid4()), "name": "Test Feed", "url": "https://example.com/feed"}
        ]

        # Mock fetch_new_articles to return 60 articles
        mock_rss.fetch_new_articles.return_value = mock_articles

        # Mock evaluate_batch to return articles with analysis
        def mock_evaluate_batch(articles):
            for article in articles:
                article.tinkering_index = 3
                article.ai_summary = "Test summary"
            return articles

        mock_llm.evaluate_batch.side_effect = mock_evaluate_batch

        # Mock insert_articles to return success
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=50, updated_count=0, failed_count=0, failed_articles=[]
        )

        # Run the background job
        await background_fetch_job()

        # Verify that batch timing logs were created
        batch_timing_logs = [
            call
            for call in mock_logger.info.call_args_list
            if "completed in" in str(call) and "Batch" in str(call)
        ]

        # Should have 2 batch timing logs (one for each batch)
        assert len(batch_timing_logs) == 2

        # Verify total duration log exists
        total_duration_logs = [
            call for call in mock_logger.info.call_args_list if "Total duration:" in str(call)
        ]

        assert len(total_duration_logs) > 0
