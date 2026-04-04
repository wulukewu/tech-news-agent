"""
Integration test for background_fetch_job.
Tests the complete pipeline: load feeds → fetch articles → deduplicate → analyze → insert.

Validates: Requirements 1.1, 1.3, 2.1, 3.1, 4.1, 5.4, 5.5
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.article import ArticleSchema, RSSSource, BatchResult


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
        published_at=datetime.now(timezone.utc),
        tinkering_index=None,
        ai_summary=None
    )


def make_test_feed(name="Test Feed", url="https://example.com/feed", category="AI"):
    """Helper to create a test RSS source."""
    return RSSSource(
        name=name,
        url=url,
        category=category
    )


class TestBackgroundFetchJob:
    @pytest.mark.asyncio
    async def test_complete_pipeline_success(self):
        """Test complete pipeline when all stages succeed.
        
        Validates: Requirements 1.1, 2.1, 3.1, 4.1, 5.4, 5.5
        """
        from app.tasks.scheduler import background_fetch_job
        
        # Setup test data
        test_feeds = [
            make_test_feed("Feed 1", "https://example.com/feed1", "AI"),
            make_test_feed("Feed 2", "https://example.com/feed2", "DevOps")
        ]
        
        test_articles = [
            make_test_article("Article 1", "https://example.com/article1"),
            make_test_article("Article 2", "https://example.com/article2"),
            make_test_article("Article 3", "https://example.com/article3")
        ]
        
        # Add analysis results
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"
        
        batch_result = BatchResult(
            inserted_count=3,
            updated_count=0,
            failed_count=0
        )
        
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)
        
        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)
        
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)
        
        # Execute job with mocks
        with patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm):
            
            await background_fetch_job()
        
        # Verify all stages were called
        mock_supabase.get_active_feeds.assert_called_once()
        mock_rss.fetch_new_articles.assert_called_once()
        mock_llm.evaluate_batch.assert_called_once()
        mock_supabase.insert_articles.assert_called_once()
        
        # Verify correct data flow
        rss_call_args = mock_rss.fetch_new_articles.call_args
        assert rss_call_args[0][0] == test_feeds  # feeds passed to RSS service
        
        llm_call_args = mock_llm.evaluate_batch.call_args
        assert llm_call_args[0][0] == test_articles  # articles passed to LLM service
        
        insert_call_args = mock_supabase.insert_articles.call_args
        articles_to_insert = insert_call_args[0][0]
        assert len(articles_to_insert) == 3
        assert all('feed_id' in article for article in articles_to_insert)
        assert all('tinkering_index' in article for article in articles_to_insert)
    
    @pytest.mark.asyncio
    async def test_no_active_feeds_exits_early(self):
        """Test that job exits early when no active feeds are found.
        
        Validates: Requirement 1.4
        """
        from app.tasks.scheduler import background_fetch_job
        
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=[])
        
        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock()
        
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock()
        
        # Execute job
        with patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm):
            
            await background_fetch_job()
        
        # Verify early exit - RSS and LLM services should not be called
        mock_supabase.get_active_feeds.assert_called_once()
        mock_rss.fetch_new_articles.assert_not_called()
        mock_llm.evaluate_batch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_no_new_articles_exits_early(self):
        """Test that job exits early when no new articles are found.
        
        Validates: Requirement 2.6
        """
        from app.tasks.scheduler import background_fetch_job
        
        test_feeds = [make_test_feed()]
        
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        
        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=[])  # No new articles
        
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock()
        
        # Execute job
        with patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm):
            
            await background_fetch_job()
        
        # Verify early exit - LLM service should not be called
        mock_supabase.get_active_feeds.assert_called_once()
        mock_rss.fetch_new_articles.assert_called_once()
        mock_llm.evaluate_batch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_database_error_is_caught_and_logged(self, caplog):
        """Test that database errors are caught and logged without crashing.
        
        Validates: Requirement 5.5
        """
        import logging
        from app.tasks.scheduler import background_fetch_job
        from app.core.exceptions import SupabaseServiceError
        
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(
            side_effect=SupabaseServiceError("Database connection failed")
        )
        
        # Execute job
        with patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase), \
             caplog.at_level(logging.ERROR, logger="app.tasks.scheduler"):
            
            await background_fetch_job()
        
        # Verify error was logged (either retry errors or critical error)
        assert any("Database connection failed" in record.message
                   for record in caplog.records if record.levelno >= logging.ERROR)
    
    @pytest.mark.asyncio
    async def test_high_failure_rate_logs_warning(self, caplog):
        """Test that high database insertion failure rate logs a warning.
        
        Validates: Requirement 4.7
        """
        import logging
        from app.tasks.scheduler import background_fetch_job
        
        test_feeds = [make_test_feed()]
        test_articles = [make_test_article(f"Article {i}") for i in range(10)]
        
        # Add analysis results
        for article in test_articles:
            article.tinkering_index = 4
            article.ai_summary = "Test summary"
        
        # High failure rate: 4 out of 10 failed (40%)
        batch_result = BatchResult(
            inserted_count=6,
            updated_count=0,
            failed_count=4
        )
        
        # Mock services
        mock_supabase = MagicMock()
        mock_supabase.get_active_feeds = AsyncMock(return_value=test_feeds)
        mock_supabase.insert_articles = AsyncMock(return_value=batch_result)
        
        mock_rss = MagicMock()
        mock_rss.fetch_new_articles = AsyncMock(return_value=test_articles)
        
        mock_llm = MagicMock()
        mock_llm.evaluate_batch = AsyncMock(return_value=test_articles)
        
        # Execute job
        with patch("app.tasks.scheduler.SupabaseService", return_value=mock_supabase), \
             patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
             patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
             caplog.at_level(logging.WARNING, logger="app.tasks.scheduler"):
            
            await background_fetch_job()
        
        # Verify warning was logged
        assert any("High database insertion failure rate" in record.message
                   for record in caplog.records if record.levelno >= logging.WARNING)
    
    @pytest.mark.asyncio
    async def test_no_discord_imports(self):
        """Test that scheduler does not import Discord bot client.
        
        Validates: Requirements 5.1, 5.2
        """
        import app.tasks.scheduler as scheduler_module
        
        # Verify no Discord imports in the module
        module_dict = vars(scheduler_module)
        
        # Check that 'bot' is not imported
        assert 'bot' not in module_dict, "Scheduler should not import Discord bot"
        
        # Check that Discord-related classes are not imported
        assert 'MarkReadView' not in module_dict, "Scheduler should not import MarkReadView"
        assert 'ReadLaterView' not in module_dict, "Scheduler should not import ReadLaterView"
