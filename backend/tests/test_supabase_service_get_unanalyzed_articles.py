"""
Unit tests for SupabaseService.get_unanalyzed_articles method
Task 1.2: 實作 get_unanalyzed_articles 方法

Tests cover:
- Requirements 13.1: Query articles where ai_summary IS NULL
- Requirements 13.2: Query articles where tinkering_index IS NULL
- Requirements 13.7: Support limit parameter to restrict result count
"""
import pytest
from unittest.mock import MagicMock
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


class TestGetUnanalyzedArticles:
    """測試 get_unanalyzed_articles 方法"""

    @pytest.mark.asyncio
    async def test_returns_articles_with_null_ai_summary(self):
        """
        測試返回 ai_summary 為 NULL 的文章
        Requirements: 13.1
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'article-1',
                'url': 'https://example.com/article1',
                'title': 'Article 1',
                'feed_id': 'feed-1'
            },
            {
                'id': 'article-2',
                'url': 'https://example.com/article2',
                'title': 'Article 2',
                'feed_id': 'feed-2'
            }
        ]
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles()
        
        # Assert
        assert len(result) == 2
        assert result[0]['id'] == 'article-1'
        assert result[0]['url'] == 'https://example.com/article1'
        assert result[0]['title'] == 'Article 1'
        assert result[0]['feed_id'] == 'feed-1'
        mock_client.table.assert_called_once_with('articles')
        mock_client.table.return_value.select.assert_called_once_with('id, url, title, feed_id')

    @pytest.mark.asyncio
    async def test_returns_articles_with_null_tinkering_index(self):
        """
        測試返回 tinkering_index 為 NULL 的文章
        Requirements: 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'article-3',
                'url': 'https://example.com/article3',
                'title': 'Article 3',
                'feed_id': 'feed-3'
            }
        ]
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles()
        
        # Assert
        assert len(result) == 1
        assert result[0]['id'] == 'article-3'

    @pytest.mark.asyncio
    async def test_uses_or_condition_for_null_checks(self):
        """
        測試使用 OR 條件查詢 ai_summary IS NULL 或 tinkering_index IS NULL
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.get_unanalyzed_articles()
        
        # Assert
        mock_client.table.return_value.select.return_value.or_.assert_called_once_with('ai_summary.is.null,tinkering_index.is.null')

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self):
        """
        測試支援 limit 參數限制返回數量
        Requirements: 13.7
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.get_unanalyzed_articles(limit=50)
        
        # Assert
        mock_client.table.return_value.select.return_value.or_.return_value.limit.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_defaults_to_100_limit(self):
        """
        測試預設 limit 為 100
        Requirements: 13.7
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.get_unanalyzed_articles()
        
        # Assert
        mock_client.table.return_value.select.return_value.or_.return_value.limit.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_articles(self):
        """
        測試當沒有未分析文章時返回空列表
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles()
        
        # Assert
        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_data_is_none(self):
        """
        測試當查詢返回 None 時返回空列表
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles()
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_handles_database_error(self):
        """
        測試處理資料庫錯誤
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.side_effect = Exception("Database connection failed")
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            await service.get_unanalyzed_articles()
        
        assert "Database operation failed" in str(exc_info.value)
        assert exc_info.value.context["limit"] == 100
        assert exc_info.value.context["operation"] == "get_unanalyzed_articles"

    @pytest.mark.asyncio
    async def test_selects_only_required_fields(self):
        """
        測試只選擇必要的欄位（id, url, title, feed_id）
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.get_unanalyzed_articles()
        
        # Assert
        mock_client.table.return_value.select.assert_called_once_with('id, url, title, feed_id')

    @pytest.mark.asyncio
    async def test_returns_correct_structure(self):
        """
        測試返回正確的資料結構
        Requirements: 13.1, 13.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'test-id',
                'url': 'https://test.com/article',
                'title': 'Test Article',
                'feed_id': 'test-feed-id'
            }
        ]
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles()
        
        # Assert
        assert len(result) == 1
        article = result[0]
        assert 'id' in article
        assert 'url' in article
        assert 'title' in article
        assert 'feed_id' in article
        assert article['id'] == 'test-id'
        assert article['url'] == 'https://test.com/article'
        assert article['title'] == 'Test Article'
        assert article['feed_id'] == 'test-feed-id'

    @pytest.mark.asyncio
    async def test_accepts_custom_limit(self):
        """
        測試接受自訂 limit 參數
        Requirements: 13.7
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.get_unanalyzed_articles(limit=200)
        
        # Assert
        mock_client.table.return_value.select.return_value.or_.return_value.limit.assert_called_once_with(200)

    @pytest.mark.asyncio
    async def test_handles_large_result_set(self):
        """
        測試處理大量結果集
        Requirements: 13.7
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        # 模擬返回 100 筆文章
        mock_response.data = [
            {
                'id': f'article-{i}',
                'url': f'https://example.com/article{i}',
                'title': f'Article {i}',
                'feed_id': f'feed-{i % 10}'
            }
            for i in range(100)
        ]
        mock_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.get_unanalyzed_articles(limit=100)
        
        # Assert
        assert len(result) == 100
        assert all('id' in article for article in result)
        assert all('url' in article for article in result)
        assert all('title' in article for article in result)
        assert all('feed_id' in article for article in result)
