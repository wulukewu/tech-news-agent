"""
Unit tests for scheduler re-processing logic
Task 5.1: 實作未分析文章的重新處理

Tests cover:
- Querying unanalyzed articles
- Re-processing articles with NULL ai_summary
- Re-processing articles with NULL tinkering_index but non-NULL ai_summary
- Updating updated_at timestamp during re-processing
- Logging re-processed article counts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.tasks.scheduler import background_fetch_job
from app.schemas.article import ArticleSchema, RSSSource, BatchResult


class TestSchedulerReprocessing:
    """測試排程器重新處理邏輯"""

    @pytest.mark.asyncio
    async def test_reprocessing_queries_unanalyzed_articles(self):
        """測試排程器查詢未分析的文章"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock unanalyzed articles
            mock_supabase.get_unanalyzed_articles.return_value = [
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article1',
                    'title': 'Test Article 1',
                    'feed_id': str(uuid4())
                }
            ]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            mock_llm.evaluate_batch.return_value = []
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=1,
                failed_count=0
            )
            
            # Act
            await background_fetch_job()
            
            # Assert
            mock_supabase.get_unanalyzed_articles.assert_called_once_with(limit=100)

    @pytest.mark.asyncio
    async def test_reprocessing_calls_llm_for_unanalyzed_articles(self):
        """測試排程器對未分析文章呼叫 LLM"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock unanalyzed articles
            feed_id = uuid4()
            mock_supabase.get_unanalyzed_articles.return_value = [
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article1',
                    'title': 'Test Article 1',
                    'feed_id': str(feed_id)
                },
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article2',
                    'title': 'Test Article 2',
                    'feed_id': str(feed_id)
                }
            ]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Mock LLM evaluation to return articles with analysis
            def mock_evaluate_batch(articles):
                for article in articles:
                    article.tinkering_index = 3
                    article.ai_summary = "Test summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=2,
                failed_count=0
            )
            
            # Act
            await background_fetch_job()
            
            # Assert
            mock_llm.evaluate_batch.assert_called()
            call_args = mock_llm.evaluate_batch.call_args[0][0]
            assert len(call_args) == 2

    @pytest.mark.asyncio
    async def test_reprocessing_updates_articles_in_database(self):
        """測試重新處理後更新資料庫"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock unanalyzed articles
            feed_id = uuid4()
            mock_supabase.get_unanalyzed_articles.return_value = [
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article1',
                    'title': 'Test Article 1',
                    'feed_id': str(feed_id)
                }
            ]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Mock LLM evaluation
            def mock_evaluate_batch(articles):
                for article in articles:
                    article.tinkering_index = 4
                    article.ai_summary = "Detailed summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=1,
                failed_count=0
            )
            
            # Act
            await background_fetch_job()
            
            # Assert
            # Verify insert_articles was called for re-processing
            assert mock_supabase.insert_articles.call_count >= 1
            
            # Get the call for re-processing (should be the first call if no new articles)
            reprocess_call = mock_supabase.insert_articles.call_args_list[0]
            articles_updated = reprocess_call[0][0]
            
            assert len(articles_updated) == 1
            assert articles_updated[0]['url'] == 'https://example.com/article1'
            assert articles_updated[0]['tinkering_index'] == 4
            assert articles_updated[0]['ai_summary'] == "Detailed summary"

    @pytest.mark.asyncio
    async def test_reprocessing_logs_count(self, caplog):
        """測試重新處理記錄文章數量"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock unanalyzed articles
            feed_id = uuid4()
            mock_supabase.get_unanalyzed_articles.return_value = [
                {
                    'id': str(uuid4()),
                    'url': f'https://example.com/article{i}',
                    'title': f'Test Article {i}',
                    'feed_id': str(feed_id)
                }
                for i in range(5)
            ]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            def mock_evaluate_batch(articles):
                for article in articles:
                    article.tinkering_index = 3
                    article.ai_summary = "Summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=5,
                failed_count=0
            )
            
            # Act
            with caplog.at_level('INFO'):
                await background_fetch_job()
            
            # Assert
            # Check that re-processing count is logged
            assert any('Found 5 unanalyzed articles' in record.message for record in caplog.records)
            assert any('Re-processing 5 unanalyzed articles' in record.message for record in caplog.records)
            assert any('5 articles updated' in record.message for record in caplog.records)
            assert any('Articles re-processed: 5' in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_reprocessing_handles_no_unanalyzed_articles(self, caplog):
        """測試沒有未分析文章時的處理"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock no unanalyzed articles
            mock_supabase.get_unanalyzed_articles.return_value = []
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Act
            with caplog.at_level('INFO'):
                await background_fetch_job()
            
            # Assert
            assert any('No unanalyzed articles found' in record.message for record in caplog.records)
            mock_llm.evaluate_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_reprocessing_continues_on_parse_failure(self, caplog):
        """測試解析失敗時繼續處理其他文章"""
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock unanalyzed articles with one invalid entry
            feed_id = uuid4()
            mock_supabase.get_unanalyzed_articles.return_value = [
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article1',
                    'title': 'Valid Article',
                    'feed_id': str(feed_id)
                },
                {
                    # Missing required fields - will cause parse error
                    'id': str(uuid4()),
                    'title': 'Invalid Article'
                },
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article3',
                    'title': 'Another Valid Article',
                    'feed_id': str(feed_id)
                }
            ]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            def mock_evaluate_batch(articles):
                for article in articles:
                    article.tinkering_index = 3
                    article.ai_summary = "Summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=2,
                failed_count=0
            )
            
            # Act
            with caplog.at_level('WARNING'):
                await background_fetch_job()
            
            # Assert
            # Should log warning about failed parse
            assert any('Failed to parse unanalyzed article' in record.message for record in caplog.records)
            
            # Should still process the valid articles
            mock_llm.evaluate_batch.assert_called()
            call_args = mock_llm.evaluate_batch.call_args[0][0]
            assert len(call_args) == 2  # Only 2 valid articles


class TestReprocessingEdgeCases:
    """Task 5.3: 撰寫重新處理邏輯的單元測試 - Edge Cases"""

    @pytest.mark.asyncio
    async def test_reprocess_when_ai_summary_is_null(self):
        """測試 ai_summary IS NULL 時重新處理
        
        Validates: Requirements 13.4, 13.6
        """
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock article with NULL ai_summary
            feed_id = uuid4()
            article_with_null_summary = {
                'id': str(uuid4()),
                'url': 'https://example.com/article-null-summary',
                'title': 'Article with NULL summary',
                'feed_id': str(feed_id),
                'ai_summary': None,  # NULL - should trigger re-processing
                'tinkering_index': 3  # Has index but missing summary
            }
            
            mock_supabase.get_unanalyzed_articles.return_value = [article_with_null_summary]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            processed_articles = []
            
            def mock_evaluate_batch(articles):
                for article in articles:
                    processed_articles.append(article)
                    article.tinkering_index = 4
                    article.ai_summary = "Newly generated summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=1,
                failed_count=0
            )
            
            # Act
            await background_fetch_job()
            
            # Assert
            # Verify LLM was called for re-processing
            mock_llm.evaluate_batch.assert_called_once()
            
            # Verify the article was processed
            assert len(processed_articles) == 1
            assert str(processed_articles[0].url) == article_with_null_summary['url']
            assert processed_articles[0].ai_summary == "Newly generated summary"

    @pytest.mark.asyncio
    async def test_skip_when_ai_summary_is_not_null(self):
        """測試 ai_summary IS NOT NULL 時跳過處理
        
        Validates: Requirements 13.4, 13.6
        """
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock no unanalyzed articles (all have ai_summary)
            # In real implementation, get_unanalyzed_articles filters these out
            mock_supabase.get_unanalyzed_articles.return_value = []
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Act
            await background_fetch_job()
            
            # Assert
            # Verify LLM was NOT called for re-processing
            mock_llm.evaluate_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_selective_reprocessing_partial_null_fields(self):
        """測試部分欄位 NULL 時的選擇性重新處理
        
        Validates: Requirements 13.4, 13.6
        """
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock articles with partial NULL fields
            feed_id = uuid4()
            articles_with_partial_nulls = [
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article1',
                    'title': 'Article with NULL tinkering_index',
                    'feed_id': str(feed_id),
                    'ai_summary': 'Existing summary',
                    'tinkering_index': None  # NULL - needs re-processing
                },
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article2',
                    'title': 'Article with NULL ai_summary',
                    'feed_id': str(feed_id),
                    'ai_summary': None,  # NULL - needs re-processing
                    'tinkering_index': 4
                },
                {
                    'id': str(uuid4()),
                    'url': 'https://example.com/article3',
                    'title': 'Article with both NULL',
                    'feed_id': str(feed_id),
                    'ai_summary': None,
                    'tinkering_index': None
                }
            ]
            
            mock_supabase.get_unanalyzed_articles.return_value = articles_with_partial_nulls
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            processed_articles = []
            
            def mock_evaluate_batch(articles):
                for article in articles:
                    processed_articles.append(article)
                    article.tinkering_index = 3
                    article.ai_summary = "Re-processed summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Mock insert_articles
            mock_supabase.insert_articles.return_value = BatchResult(
                inserted_count=0,
                updated_count=3,
                failed_count=0
            )
            
            # Act
            await background_fetch_job()
            
            # Assert
            # Verify all articles with any NULL field were re-processed
            mock_llm.evaluate_batch.assert_called_once()
            assert len(processed_articles) == 3
            
            # Verify all processed articles now have both fields populated
            for article in processed_articles:
                assert article.ai_summary is not None
                assert article.tinkering_index is not None

    @pytest.mark.asyncio
    async def test_updated_at_timestamp_update(self):
        """測試 updated_at 時間戳更新
        
        Validates: Requirements 13.4, 13.6
        """
        # Arrange
        with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
             patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
             patch('app.tasks.scheduler.LLMService') as mock_llm_class:
            
            mock_supabase = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Mock active feeds
            mock_supabase.get_active_feeds.return_value = [
                RSSSource(name="Test Feed", url="https://example.com/feed", category="Tech")
            ]
            
            # Mock no new articles
            mock_rss = AsyncMock()
            mock_rss_class.return_value = mock_rss
            mock_rss.fetch_new_articles.return_value = []
            
            # Mock article needing re-processing
            feed_id = uuid4()
            article_to_reprocess = {
                'id': str(uuid4()),
                'url': 'https://example.com/article-timestamp',
                'title': 'Article for timestamp test',
                'feed_id': str(feed_id),
                'ai_summary': None,
                'tinkering_index': None
            }
            
            mock_supabase.get_unanalyzed_articles.return_value = [article_to_reprocess]
            
            # Mock LLM service
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            def mock_evaluate_batch(articles):
                for article in articles:
                    article.tinkering_index = 3
                    article.ai_summary = "Summary"
                return articles
            
            mock_llm.evaluate_batch.side_effect = mock_evaluate_batch
            
            # Track what was inserted
            inserted_articles = []
            
            async def mock_insert_articles(articles_dict_list):
                inserted_articles.extend(articles_dict_list)
                return BatchResult(
                    inserted_count=0,
                    updated_count=len(articles_dict_list),
                    failed_count=0
                )
            
            mock_supabase.insert_articles.side_effect = mock_insert_articles
            
            # Act
            await background_fetch_job()
            
            # Assert
            # Verify insert_articles was called (which triggers UPSERT with updated_at)
            assert len(inserted_articles) == 1
            
            # Verify the article has the required fields for UPSERT
            updated_article = inserted_articles[0]
            assert updated_article['url'] == article_to_reprocess['url']
            assert updated_article['ai_summary'] == "Summary"
            assert updated_article['tinkering_index'] == 3
            
            # Note: The actual updated_at timestamp is set by the database UPSERT operation
            # This test verifies that the article is passed to insert_articles, which
            # triggers the UPSERT that updates the timestamp
