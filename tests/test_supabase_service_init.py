"""
Unit tests for SupabaseService initialization
Task 3.1: 建立 SupabaseService 類別與初始化

Tests cover:
- Requirements 14.1: Initialize Supabase client in __init__ method
- Requirements 14.2: Read supabase_url and supabase_key from settings
- Requirements 14.3: Raise configuration error when config is missing
- Requirements 14.4: Validate Supabase connection on initialization
- Requirements 17.1: Accept optional client parameter for dependency injection
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


class TestSupabaseServiceInitialization:
    """測試 SupabaseService 初始化"""

    def test_init_with_provided_client(self):
        """
        測試使用提供的 client 初始化
        Requirements: 17.1
        """
        # Arrange
        mock_client = MagicMock()
        # Mock the validation query
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()
        
        # Act
        service = SupabaseService(client=mock_client)
        
        # Assert
        assert service.client is mock_client

    @patch('app.services.supabase_service.create_client')
    def test_init_with_valid_config(self, mock_create_client):
        """
        測試使用有效配置初始化
        Requirements: 14.1, 14.2
        """
        # Arrange
        mock_client = MagicMock()
        # Mock the validation query
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Act
        service = SupabaseService()
        
        # Assert
        assert service.client is mock_client
        mock_create_client.assert_called_once()

    @patch('app.services.supabase_service.settings')
    def test_init_without_url_raises_error(self, mock_settings):
        """
        測試缺少 supabase_url 時拋出錯誤
        Requirements: 14.3
        """
        # Arrange
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = "test_key"
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(validate_connection=False)
        
        assert "configuration is missing" in str(exc_info.value)
        assert exc_info.value.context["supabase_url_present"] is False
        assert exc_info.value.context["supabase_key_present"] is True

    @patch('app.services.supabase_service.settings')
    def test_init_without_key_raises_error(self, mock_settings):
        """
        測試缺少 supabase_key 時拋出錯誤
        Requirements: 14.3
        """
        # Arrange
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = ""
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(validate_connection=False)
        
        assert "configuration is missing" in str(exc_info.value)
        assert exc_info.value.context["supabase_url_present"] is True
        assert exc_info.value.context["supabase_key_present"] is False

    @patch('app.services.supabase_service.settings')
    def test_init_without_both_config_raises_error(self, mock_settings):
        """
        測試同時缺少 supabase_url 和 supabase_key 時拋出錯誤
        Requirements: 14.3
        """
        # Arrange
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = ""
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(validate_connection=False)
        
        assert "configuration is missing" in str(exc_info.value)
        assert exc_info.value.context["supabase_url_present"] is False
        assert exc_info.value.context["supabase_key_present"] is False
        assert "troubleshooting" in exc_info.value.context

    @patch('app.services.supabase_service.create_client')
    def test_init_connection_failure_raises_error(self, mock_create_client):
        """
        測試連線失敗時拋出錯誤
        Requirements: 14.4
        """
        # Arrange
        mock_create_client.side_effect = Exception("Connection timeout")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(validate_connection=False)
        
        assert "Failed to initialize Supabase client" in str(exc_info.value)
        assert exc_info.value.original_error is not None
        assert "troubleshooting" in exc_info.value.context

    def test_error_message_format(self):
        """
        測試錯誤訊息格式包含所有必要資訊
        Requirements: 14.3
        """
        # Arrange
        error = SupabaseServiceError(
            "Test error",
            original_error=ValueError("Original"),
            context={"key": "value"}
        )
        
        # Act
        error_str = str(error)
        
        # Assert
        assert "Test error" in error_str
        assert "Context:" in error_str
        assert "Original error:" in error_str


class TestConnectionValidation:
    """測試連線驗證功能 (Task 3.2)"""

    def test_skip_validation_with_flag(self):
        """
        測試可以跳過連線驗證
        Requirements: 14.4
        """
        # Arrange
        mock_client = MagicMock()
        
        # Act - 不應該呼叫 table() 方法
        service = SupabaseService(client=mock_client, validate_connection=False)
        
        # Assert
        assert service.client is mock_client
        # 驗證沒有呼叫驗證查詢
        mock_client.table.assert_not_called()

    def test_validation_success(self):
        """
        測試連線驗證成功
        Requirements: 14.4
        """
        # Arrange
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        
        # Act
        service = SupabaseService(client=mock_client, validate_connection=True)
        
        # Assert
        assert service.client is mock_client
        # 驗證有呼叫驗證查詢
        mock_client.table.assert_called_once_with('users')

    def test_validation_timeout_raises_error(self):
        """
        測試連線驗證超時時拋出錯誤
        Requirements: 14.5, 14.7
        """
        # Arrange
        mock_client = MagicMock()
        # 模擬超時
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = TimeoutError("Connection timed out")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "timed out" in str(exc_info.value).lower()
        assert "troubleshooting" in exc_info.value.context
        assert "timeout_seconds" in exc_info.value.context

    def test_validation_authentication_error_provides_hints(self):
        """
        測試認證錯誤時提供特定的故障排除提示
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("401 Unauthorized")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "Failed to validate Supabase connection" in str(exc_info.value)
        assert "troubleshooting" in exc_info.value.context
        # 應該包含認證相關的提示
        hints = exc_info.value.context["troubleshooting"]
        assert any("SUPABASE_KEY" in hint for hint in hints)
        assert any("permissions" in hint.lower() for hint in hints)

    def test_validation_not_found_error_provides_hints(self):
        """
        測試 404 錯誤時提供特定的故障排除提示
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("404 Not Found")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "Failed to validate Supabase connection" in str(exc_info.value)
        hints = exc_info.value.context["troubleshooting"]
        # 應該包含 URL 相關的提示
        assert any("SUPABASE_URL" in hint for hint in hints)
        assert any("project exists" in hint.lower() for hint in hints)

    def test_validation_network_error_provides_hints(self):
        """
        測試網路錯誤時提供特定的故障排除提示
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Network connection failed")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "Failed to validate Supabase connection" in str(exc_info.value)
        hints = exc_info.value.context["troubleshooting"]
        # 應該包含網路相關的提示
        assert any("internet" in hint.lower() or "connectivity" in hint.lower() for hint in hints)
        assert any("dns" in hint.lower() for hint in hints)

    def test_validation_ssl_error_provides_hints(self):
        """
        測試 SSL 錯誤時提供特定的故障排除提示
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("SSL certificate verification failed")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "Failed to validate Supabase connection" in str(exc_info.value)
        hints = exc_info.value.context["troubleshooting"]
        # 應該包含 SSL 相關的提示
        assert any("ssl" in hint.lower() or "certificate" in hint.lower() for hint in hints)
        assert any("system time" in hint.lower() for hint in hints)

    def test_validation_error_includes_error_type(self):
        """
        測試驗證錯誤包含錯誤類型資訊
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = ValueError("Invalid response")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "error_type" in exc_info.value.context
        assert exc_info.value.context["error_type"] == "ValueError"

    def test_validation_error_includes_supabase_url(self):
        """
        測試驗證錯誤包含 Supabase URL（用於除錯）
        Requirements: 14.5
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            SupabaseService(client=mock_client, validate_connection=True)
        
        assert "supabase_url" in exc_info.value.context
        # URL 應該來自 settings
        from app.core.config import settings
        assert exc_info.value.context["supabase_url"] == settings.supabase_url
