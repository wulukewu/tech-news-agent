"""
Unit tests for SupabaseService.check_article_exists method
Task 1.1: 實作 check_article_exists 方法

Tests cover:
- Requirements 2.2: Query articles table to check if URL exists
- Requirements 2.3: Return True if exists, False if not exists
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


class TestCheckArticleExists:
    """測試 check_article_exists 方法"""

    @pytest.mark.asyncio
    async def test_returns_true_for_existing_article(self):
        """
        測試當文章存在時返回 True
        Requirements: 2.2, 2.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{'id': 'some-uuid'}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('https://example.com/article')
        
        # Assert
        assert result is True
        mock_client.table.assert_called_once_with('articles')
        mock_client.table.return_value.select.assert_called_once_with('id')
        mock_client.table.return_value.select.return_value.eq.assert_called_once_with('url', 'https://example.com/article')

    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent_article(self):
        """
        測試當文章不存在時返回 False
        Requirements: 2.2, 2.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('https://example.com/new-article')
        
        # Assert
        assert result is False
        mock_client.table.assert_called_once_with('articles')

    @pytest.mark.asyncio
    async def test_returns_false_when_data_is_none(self):
        """
        測試當查詢返回 None 時返回 False
        Requirements: 2.2, 2.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('https://example.com/article')
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_validates_url_format(self):
        """
        測試驗證 URL 格式
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act & Assert - 無效的 URL 應該拋出 ValueError
        with pytest.raises(ValueError) as exc_info:
            await service.check_article_exists('invalid-url')
        
        assert "Invalid URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validates_empty_url(self):
        """
        測試驗證空 URL
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.check_article_exists('')
        
        assert "Invalid URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handles_database_error(self):
        """
        測試處理資料庫錯誤
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            await service.check_article_exists('https://example.com/article')
        
        assert "Database operation failed" in str(exc_info.value)
        assert exc_info.value.context["url"] == 'https://example.com/article'
        assert exc_info.value.context["operation"] == "check_article_exists"

    @pytest.mark.asyncio
    async def test_uses_efficient_query(self):
        """
        測試使用高效查詢（只選擇 id 欄位）
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{'id': 'some-uuid'}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        await service.check_article_exists('https://example.com/article')
        
        # Assert - 驗證只選擇 id 欄位
        mock_client.table.return_value.select.assert_called_once_with('id')

    @pytest.mark.asyncio
    async def test_accepts_http_url(self):
        """
        測試接受 http:// URL
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('http://example.com/article')
        
        # Assert
        assert result is False
        mock_client.table.return_value.select.return_value.eq.assert_called_once_with('url', 'http://example.com/article')

    @pytest.mark.asyncio
    async def test_accepts_https_url(self):
        """
        測試接受 https:// URL
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('https://example.com/article')
        
        # Assert
        assert result is False
        mock_client.table.return_value.select.return_value.eq.assert_called_once_with('url', 'https://example.com/article')

    @pytest.mark.asyncio
    async def test_strips_whitespace_from_url(self):
        """
        測試自動去除 URL 前後空白
        Requirements: 2.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Act
        result = await service.check_article_exists('  https://example.com/article  ')
        
        # Assert
        assert result is False
        # 驗證傳遞給資料庫的 URL 已去除空白
        mock_client.table.return_value.select.return_value.eq.assert_called_once_with('url', 'https://example.com/article')
