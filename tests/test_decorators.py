"""
Unit tests for Discord bot decorators.
Tests the ensure_user_registered function for Task 1.1.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4

from app.bot.utils.decorators import ensure_user_registered
from app.core.exceptions import SupabaseServiceError


@pytest.mark.asyncio
async def test_ensure_user_registered_new_user():
    """
    Test ensure_user_registered with a new user.
    
    Validates: Requirement 1.1, 1.2
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 123456789
    
    expected_uuid = uuid4()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Act
        result = await ensure_user_registered(mock_interaction)
        
        # Assert
        assert result == expected_uuid
        mock_service.get_or_create_user.assert_called_once_with("123456789")


@pytest.mark.asyncio
async def test_ensure_user_registered_existing_user():
    """
    Test ensure_user_registered with an existing user.
    
    Validates: Requirement 1.1, 1.2, 1.5
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 987654321
    
    expected_uuid = uuid4()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Act
        result = await ensure_user_registered(mock_interaction)
        
        # Assert
        assert result == expected_uuid
        assert isinstance(result, UUID)
        mock_service.get_or_create_user.assert_called_once_with("987654321")


@pytest.mark.asyncio
async def test_ensure_user_registered_supabase_error():
    """
    Test ensure_user_registered when SupabaseService raises an error.
    
    Validates: Requirement 1.3
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 111222333
    mock_interaction.user.__str__ = Mock(return_value="TestUser#1234")
    
    error_message = "Database connection failed"
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(
            side_effect=SupabaseServiceError(error_message)
        )
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            await ensure_user_registered(mock_interaction)
        
        assert error_message in str(exc_info.value)
        mock_service.get_or_create_user.assert_called_once_with("111222333")


@pytest.mark.asyncio
async def test_ensure_user_registered_unexpected_error():
    """
    Test ensure_user_registered when an unexpected error occurs.
    
    Validates: Requirement 1.3
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 444555666
    mock_interaction.user.__str__ = Mock(return_value="TestUser#5678")
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )
        
        # Act & Assert
        with pytest.raises(SupabaseServiceError) as exc_info:
            await ensure_user_registered(mock_interaction)
        
        assert "無法註冊使用者" in str(exc_info.value)
        mock_service.get_or_create_user.assert_called_once_with("444555666")


@pytest.mark.asyncio
async def test_ensure_user_registered_converts_discord_id_to_string():
    """
    Test that ensure_user_registered correctly converts discord_id to string.
    
    Validates: Requirement 1.1, 1.2
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 999888777  # Integer
    
    expected_uuid = uuid4()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Act
        result = await ensure_user_registered(mock_interaction)
        
        # Assert
        assert result == expected_uuid
        # Verify that the discord_id was converted to string
        mock_service.get_or_create_user.assert_called_once_with("999888777")


@pytest.mark.asyncio
async def test_ensure_user_registered_returns_uuid_type():
    """
    Test that ensure_user_registered returns a UUID object.
    
    Validates: Requirement 1.2
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 123123123
    
    expected_uuid = uuid4()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Act
        result = await ensure_user_registered(mock_interaction)
        
        # Assert
        assert isinstance(result, UUID)
        assert result == expected_uuid



# Tests for require_user_registration decorator (Task 1.2)

@pytest.mark.asyncio
async def test_require_user_registration_success():
    """
    Test require_user_registration decorator with successful registration.
    
    Validates: Requirement 1.1, 1.2
    """
    from app.bot.utils.decorators import require_user_registration
    
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 123456789
    expected_uuid = uuid4()
    
    # Create a mock command handler
    mock_handler = AsyncMock()
    
    # Create a mock cog instance
    mock_cog = Mock()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Decorate the mock handler
        decorated_handler = require_user_registration(mock_handler)
        
        # Act
        await decorated_handler(mock_cog, mock_interaction)
        
        # Assert
        mock_service.get_or_create_user.assert_called_once_with("123456789")
        mock_handler.assert_called_once_with(mock_cog, mock_interaction, expected_uuid)


@pytest.mark.asyncio
async def test_require_user_registration_with_args():
    """
    Test require_user_registration decorator passes additional arguments correctly.
    
    Validates: Requirement 1.2
    """
    from app.bot.utils.decorators import require_user_registration
    
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 987654321
    expected_uuid = uuid4()
    
    mock_handler = AsyncMock()
    mock_cog = Mock()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        decorated_handler = require_user_registration(mock_handler)
        
        # Act - pass additional arguments
        await decorated_handler(mock_cog, mock_interaction, "arg1", "arg2", kwarg1="value1")
        
        # Assert
        mock_handler.assert_called_once_with(
            mock_cog, mock_interaction, expected_uuid, "arg1", "arg2", kwarg1="value1"
        )


@pytest.mark.asyncio
async def test_require_user_registration_handles_error():
    """
    Test require_user_registration decorator handles registration errors gracefully.
    
    Validates: Requirement 1.3
    """
    from app.bot.utils.decorators import require_user_registration
    
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 111222333
    mock_interaction.response.send_message = AsyncMock()
    
    mock_handler = AsyncMock()
    mock_cog = Mock()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(
            side_effect=SupabaseServiceError("Database error")
        )
        
        decorated_handler = require_user_registration(mock_handler)
        
        # Act
        await decorated_handler(mock_cog, mock_interaction)
        
        # Assert
        # Handler should not be called
        mock_handler.assert_not_called()
        
        # Error message should be sent to user
        mock_interaction.response.send_message.assert_called_once_with(
            "❌ 無法註冊使用者，請稍後再試。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_require_user_registration_preserves_function_metadata():
    """
    Test require_user_registration decorator preserves function metadata.
    
    Validates: Requirement 1.2
    """
    from app.bot.utils.decorators import require_user_registration
    
    # Arrange
    async def sample_command(self, interaction, user_uuid):
        """Sample command docstring."""
        pass
    
    sample_command.__name__ = "sample_command"
    
    # Act
    decorated_handler = require_user_registration(sample_command)
    
    # Assert
    assert decorated_handler.__name__ == "sample_command"
    assert decorated_handler.__doc__ == "Sample command docstring."


@pytest.mark.asyncio
async def test_require_user_registration_returns_handler_result():
    """
    Test require_user_registration decorator returns the handler's result.
    
    Validates: Requirement 1.2
    """
    from app.bot.utils.decorators import require_user_registration
    
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 555666777
    expected_uuid = uuid4()
    expected_result = "command_result"
    
    mock_handler = AsyncMock(return_value=expected_result)
    mock_cog = Mock()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        decorated_handler = require_user_registration(mock_handler)
        
        # Act
        result = await decorated_handler(mock_cog, mock_interaction)
        
        # Assert
        assert result == expected_result


@pytest.mark.asyncio
async def test_ensure_user_registered_concurrent_requests():
    """
    Test ensure_user_registered handles concurrent registration requests gracefully.
    
    This test verifies that when multiple concurrent requests attempt to register
    the same user, the function handles the race condition correctly and returns
    the same UUID for all requests (idempotent operation).
    
    Validates: Requirement 1.5
    """
    # Arrange
    mock_interaction = Mock()
    mock_interaction.user.id = 777888999
    
    expected_uuid = uuid4()
    
    with patch('app.bot.utils.decorators.SupabaseService') as MockSupabaseService:
        mock_service = MockSupabaseService.return_value
        
        # Simulate concurrent registration: first call succeeds, returns UUID
        mock_service.get_or_create_user = AsyncMock(return_value=expected_uuid)
        
        # Act - simulate concurrent calls
        import asyncio
        results = await asyncio.gather(
            ensure_user_registered(mock_interaction),
            ensure_user_registered(mock_interaction),
            ensure_user_registered(mock_interaction)
        )
        
        # Assert - all calls should return the same UUID
        assert len(results) == 3
        assert all(result == expected_uuid for result in results)
        assert results[0] == results[1] == results[2]
        
        # Verify get_or_create_user was called 3 times (once per concurrent request)
        assert mock_service.get_or_create_user.call_count == 3
