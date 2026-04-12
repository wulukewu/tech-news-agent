"""
Unit tests for TokenBlacklist class

Tests the token blacklist management functionality including:
- Adding tokens to blacklist
- Checking if tokens are blacklisted
- Cleaning up expired tokens
"""

import asyncio
from datetime import timedelta
from uuid import uuid4

import pytest

from app.api.auth import TokenBlacklist, create_access_token
from app.core.config import settings


@pytest.fixture(scope="module", autouse=True)
def setup_jwt_secret():
    """設置測試用的 JWT_SECRET"""
    # 保存原始值
    original_secret = settings.jwt_secret

    # 設置測試用的 secret
    test_secret = "test_jwt_secret_at_least_32_characters_long_for_testing"
    settings.jwt_secret = test_secret

    yield

    # 恢復原始值
    settings.jwt_secret = original_secret


@pytest.mark.asyncio
async def test_add_token_to_blacklist():
    """Test adding a token to the blacklist"""
    blacklist = TokenBlacklist()
    token = "test_token_123"

    await blacklist.add(token)

    assert await blacklist.is_blacklisted(token) is True


@pytest.mark.asyncio
async def test_token_not_in_blacklist():
    """Test checking a token that is not in the blacklist"""
    blacklist = TokenBlacklist()
    token = "test_token_123"

    assert await blacklist.is_blacklisted(token) is False


@pytest.mark.asyncio
async def test_multiple_tokens_in_blacklist():
    """Test adding multiple tokens to the blacklist"""
    blacklist = TokenBlacklist()
    tokens = ["token1", "token2", "token3"]

    for token in tokens:
        await blacklist.add(token)

    for token in tokens:
        assert await blacklist.is_blacklisted(token) is True


@pytest.mark.asyncio
async def test_cleanup_expired_tokens():
    """Test cleaning up expired tokens from the blacklist"""
    blacklist = TokenBlacklist()

    # Create an expired token (expires in -1 day, i.e., already expired)
    user_id = uuid4()
    discord_id = "123456789"
    expired_token = create_access_token(
        user_id=user_id, discord_id=discord_id, expires_delta=timedelta(days=-1)
    )

    # Create a valid token
    valid_token = create_access_token(
        user_id=user_id, discord_id=discord_id, expires_delta=timedelta(days=7)
    )

    # Add both tokens to blacklist
    await blacklist.add(expired_token)
    await blacklist.add(valid_token)

    # Verify both are in blacklist
    assert await blacklist.is_blacklisted(expired_token) is True
    assert await blacklist.is_blacklisted(valid_token) is True

    # Run cleanup
    await blacklist.cleanup_expired()

    # Expired token should be removed, valid token should remain
    assert await blacklist.is_blacklisted(expired_token) is False
    assert await blacklist.is_blacklisted(valid_token) is True


@pytest.mark.asyncio
async def test_concurrent_access():
    """Test concurrent access to the blacklist (thread safety)"""
    blacklist = TokenBlacklist()

    async def add_tokens(start: int, count: int):
        for i in range(start, start + count):
            await blacklist.add(f"token_{i}")

    # Add tokens concurrently
    await asyncio.gather(add_tokens(0, 100), add_tokens(100, 100), add_tokens(200, 100))

    # Verify all tokens were added
    for i in range(300):
        assert await blacklist.is_blacklisted(f"token_{i}") is True


@pytest.mark.asyncio
async def test_cleanup_with_invalid_tokens():
    """Test cleanup removes invalid tokens"""
    blacklist = TokenBlacklist()

    # Add some invalid tokens (not proper JWT format)
    invalid_tokens = ["invalid1", "invalid2", "not_a_jwt"]
    for token in invalid_tokens:
        await blacklist.add(token)

    # Add a valid token
    user_id = uuid4()
    discord_id = "123456789"
    valid_token = create_access_token(
        user_id=user_id, discord_id=discord_id, expires_delta=timedelta(days=7)
    )
    await blacklist.add(valid_token)

    # Run cleanup
    await blacklist.cleanup_expired()

    # Invalid tokens should be removed
    for token in invalid_tokens:
        assert await blacklist.is_blacklisted(token) is False

    # Valid token should remain
    assert await blacklist.is_blacklisted(valid_token) is True


@pytest.mark.asyncio
async def test_empty_blacklist_cleanup():
    """Test cleanup on an empty blacklist doesn't cause errors"""
    blacklist = TokenBlacklist()

    # Should not raise any errors
    await blacklist.cleanup_expired()

    # Blacklist should still be empty
    assert await blacklist.is_blacklisted("any_token") is False
