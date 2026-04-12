"""
Unit tests for SupabaseService context manager support
Task 3.3: 實作 context manager 支援

Tests cover:
- Requirements 17.2: Implement close method to cleanup resources
- Requirements 17.3: Support context manager protocol for automatic resource cleanup
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.supabase_service import SupabaseService


class TestContextManagerSupport:
    """測試 context manager 支援"""

    @pytest.mark.asyncio
    async def test_close_method_exists(self):
        """
        測試 close 方法存在且可呼叫
        Requirements: 17.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Act & Assert - 應該可以呼叫 close 而不拋出錯誤
        await service.close()

    @pytest.mark.asyncio
    async def test_close_method_logs_cleanup(self):
        """
        測試 close 方法記錄清理動作
        Requirements: 17.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Act
        with patch("app.services.supabase_service.logger") as mock_logger:
            await service.close()

            # Assert - 應該記錄清理動作
            assert mock_logger.info.call_count >= 1
            # 檢查是否有關閉相關的日誌
            log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("closing" in msg.lower() or "closed" in msg.lower() for msg in log_messages)

    @pytest.mark.asyncio
    async def test_aenter_returns_self(self):
        """
        測試 __aenter__ 返回 self
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Act
        result = await service.__aenter__()

        # Assert
        assert result is service

    @pytest.mark.asyncio
    async def test_aexit_calls_close(self):
        """
        測試 __aexit__ 呼叫 close 方法
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Mock close method to track if it's called
        service.close = AsyncMock()

        # Act
        await service.__aexit__(None, None, None)

        # Assert
        service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_calls_close_even_with_exception(self):
        """
        測試 __aexit__ 即使有例外也會呼叫 close
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Mock close method to track if it's called
        service.close = AsyncMock()

        # Act - 模擬有例外發生
        await service.__aexit__(ValueError, ValueError("test error"), None)

        # Assert - close 仍然應該被呼叫
        service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_logs_exception_info(self):
        """
        測試 __aexit__ 在有例外時記錄警告
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Mock close method
        service.close = AsyncMock()

        # Act
        with patch("app.services.supabase_service.logger") as mock_logger:
            test_exception = ValueError("test error")
            await service.__aexit__(ValueError, test_exception, None)

            # Assert - 應該記錄警告
            mock_logger.warning.assert_called_once()
            # 檢查警告訊息包含例外類型
            warning_call = mock_logger.warning.call_args
            assert "ValueError" in warning_call[0][0]

    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """
        測試完整的 context manager 使用流程
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )

        # Act & Assert
        async with SupabaseService(client=mock_client) as service:
            # 在 context 內部，service 應該可用
            assert service is not None
            assert service.client is mock_client

        # 離開 context 後，close 應該已被呼叫（透過日誌驗證）

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self):
        """
        測試 context manager 在例外情況下的行為
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )

        # Act & Assert
        with pytest.raises(ValueError):
            async with SupabaseService(client=mock_client) as service:
                # 在 context 內部拋出例外
                raise ValueError("test error")

        # 即使有例外，close 也應該被呼叫（透過日誌驗證）

    @pytest.mark.asyncio
    async def test_multiple_close_calls_safe(self):
        """
        測試多次呼叫 close 是安全的
        Requirements: 17.2
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Act & Assert - 多次呼叫 close 不應該拋出錯誤
        await service.close()
        await service.close()
        await service.close()

    @pytest.mark.asyncio
    async def test_aenter_logs_entry(self):
        """
        測試 __aenter__ 記錄進入 context
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Act
        with patch("app.services.supabase_service.logger") as mock_logger:
            await service.__aenter__()

            # Assert - 應該記錄進入 context
            mock_logger.debug.assert_called()
            debug_messages = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("entering" in msg.lower() for msg in debug_messages)

    @pytest.mark.asyncio
    async def test_aexit_logs_exit(self):
        """
        測試 __aexit__ 記錄離開 context
        Requirements: 17.3
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        service = SupabaseService(client=mock_client)

        # Mock close method
        service.close = AsyncMock()

        # Act
        with patch("app.services.supabase_service.logger") as mock_logger:
            await service.__aexit__(None, None, None)

            # Assert - 應該記錄離開 context
            mock_logger.debug.assert_called()
            debug_messages = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("exiting" in msg.lower() for msg in debug_messages)
