"""
Integration tests for Discord bot decorators.
Tests the ensure_user_registered function with actual SupabaseService.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""

import os
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.bot.utils.decorators import ensure_user_registered


@pytest.mark.asyncio
async def test_ensure_user_registered_integration_new_user(test_supabase_client, cleanup_test_data):
    """
    Integration test: ensure_user_registered creates a new user in the database.

    Validates: Requirement 1.1, 1.2
    """
    # Arrange
    test_discord_id = f"integration_test_{os.urandom(8).hex()}"
    mock_interaction = Mock()
    mock_interaction.user.id = int(test_discord_id.replace("integration_test_", "")[:10], 16)

    # Act
    result = await ensure_user_registered(mock_interaction)

    # Assert
    assert isinstance(result, UUID)

    # Verify user was created in database
    user_response = test_supabase_client.table("users").select("*").eq("id", str(result)).execute()
    assert len(user_response.data) == 1
    assert user_response.data[0]["id"] == str(result)

    # Track for cleanup
    cleanup_test_data["users"].append(str(result))


@pytest.mark.asyncio
async def test_ensure_user_registered_integration_existing_user(test_supabase_client, test_user):
    """
    Integration test: ensure_user_registered returns existing user UUID.

    Validates: Requirement 1.2, 1.5
    """
    # Arrange
    mock_interaction = Mock()
    # Use the actual discord_id from test_user, not a conversion
    mock_interaction.user.id = test_user["discord_id"]

    # Act
    result = await ensure_user_registered(mock_interaction)

    # Assert
    assert isinstance(result, UUID)
    assert str(result) == test_user["id"]


@pytest.mark.asyncio
async def test_ensure_user_registered_integration_idempotent(
    test_supabase_client, cleanup_test_data
):
    """
    Integration test: calling ensure_user_registered multiple times returns same UUID.

    Validates: Requirement 1.5
    """
    # Arrange
    test_discord_id = f"idempotent_test_{os.urandom(8).hex()}"
    mock_interaction = Mock()
    mock_interaction.user.id = int(test_discord_id.replace("idempotent_test_", "")[:10], 16)

    # Act
    result1 = await ensure_user_registered(mock_interaction)
    result2 = await ensure_user_registered(mock_interaction)
    result3 = await ensure_user_registered(mock_interaction)

    # Assert
    assert result1 == result2 == result3
    assert isinstance(result1, UUID)

    # Verify only one user was created
    user_response = test_supabase_client.table("users").select("*").eq("id", str(result1)).execute()
    assert len(user_response.data) == 1

    # Track for cleanup
    cleanup_test_data["users"].append(str(result1))
