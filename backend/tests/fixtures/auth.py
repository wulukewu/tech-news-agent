"""
Authentication-related test fixtures.

Provides fixtures for JWT tokens, OAuth mocks, and authenticated requests.
"""

from datetime import datetime, timedelta
from typing import Any

import pytest


@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZXhwIjoxNzM1Njg5NjAwfQ.test"


@pytest.fixture
def mock_jwt_payload() -> dict[str, Any]:
    """Mock JWT payload for testing."""
    return {
        "sub": "test-user-123",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }


@pytest.fixture
def mock_discord_oauth_response() -> dict[str, Any]:
    """Mock Discord OAuth response for testing."""
    return {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "expires_in": 604800,
        "refresh_token": "mock_refresh_token",
        "scope": "identify email",
    }


@pytest.fixture
def mock_discord_user_info() -> dict[str, Any]:
    """Mock Discord user info for testing."""
    return {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "0001",
        "email": "test@example.com",
        "verified": True,
    }


@pytest.fixture
def authenticated_headers(mock_jwt_token: str) -> dict[str, str]:
    """Headers with authentication token for testing."""
    return {"Authorization": f"Bearer {mock_jwt_token}", "Content-Type": "application/json"}
