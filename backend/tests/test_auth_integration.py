"""
Integration tests for authentication flow

Tests the complete OAuth2 login, token refresh, and logout flows.

**Validates: Requirements 1.*, 2.*, 3.*, 12.*, 13.*, 14.***
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.auth import create_access_token, get_token_blacklist
from app.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_discord_api():
    """Mock Discord API responses"""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock token exchange response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "mock_discord_token",
            "token_type": "Bearer",
        }

        # Mock user info response
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "id": "123456789",
            "username": "testuser",
            "discriminator": "0001",
        }

        # Configure mock client
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(return_value=mock_token_response)
        mock_instance.get = AsyncMock(return_value=mock_user_response)

        yield mock_client


@pytest.fixture
def mock_supabase():
    """Mock Supabase service"""
    with patch("app.api.auth.SupabaseService") as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.get_or_create_user = AsyncMock(return_value=uuid4())
        yield mock_service


def test_oauth2_login_redirect(client):
    """
    Test OAuth2 login endpoint redirects to Discord

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    response = client.get("/api/auth/discord/login", follow_redirects=False)

    # Should return 302 redirect
    assert response.status_code == 302

    # Should redirect to Discord
    location = response.headers.get("location")
    assert location is not None
    assert "discord.com/api/oauth2/authorize" in location

    # Should include required parameters
    assert "client_id=" in location
    assert "redirect_uri=" in location
    assert "response_type=code" in location
    assert "scope=identify" in location


def test_oauth2_callback_user_denied(client):
    """
    Test OAuth2 callback when user denies authorization

    **Validates: Requirements 12.1, 12.2**
    """
    response = client.get(
        "/api/auth/discord/callback?error=access_denied&error_description=User%20denied"
    )

    # Should return 400 Bad Request
    assert response.status_code == 400

    # Should include error details
    data = response.json()
    assert "error" in data or "detail" in data


def test_oauth2_callback_missing_code(client):
    """
    Test OAuth2 callback with missing authorization code

    **Validates: Requirements 12.3**
    """
    response = client.get("/api/auth/discord/callback")

    # Should return 400 Bad Request
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_oauth2_callback_success(client, mock_discord_api, mock_supabase):
    """
    Test successful OAuth2 callback flow

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.1, 3.6, 4.7**
    """
    response = client.get("/api/auth/discord/callback?code=test_auth_code")

    # Should return 200 OK
    assert response.status_code == 200

    # Should return JSON with access_token
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"

    # Should set HttpOnly cookie
    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()


@pytest.mark.asyncio
async def test_token_refresh_flow(client):
    """
    Test token refresh flow

    **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7**
    """
    # Create a valid token
    user_id = uuid4()
    discord_id = "test_user_123"

    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        mock_settings.cookie_secure = False

        old_token = create_access_token(user_id=user_id, discord_id=discord_id)

        # Call refresh endpoint
        response = client.post("/api/auth/refresh", cookies={"access_token": old_token})

        # Should return 200 OK
        assert response.status_code == 200

        # Should return new token
        data = response.json()
        assert "access_token" in data
        new_token = data["access_token"]

        # New token should be different from old token
        assert new_token != old_token

        # Old token should be blacklisted
        blacklist = get_token_blacklist()
        is_blacklisted = await blacklist.is_blacklisted(old_token)
        assert is_blacklisted is True


@pytest.mark.asyncio
async def test_logout_flow(client):
    """
    Test logout flow

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6**
    """
    # Create a valid token
    user_id = uuid4()
    discord_id = "test_user_123"

    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        mock_settings.cookie_secure = False

        token = create_access_token(user_id=user_id, discord_id=discord_id)

        # Call logout endpoint
        response = client.post("/api/auth/logout", cookies={"access_token": token})

        # Should return 200 OK
        assert response.status_code == 200

        # Should return success message
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]

        # Token should be blacklisted
        blacklist = get_token_blacklist()
        is_blacklisted = await blacklist.is_blacklisted(token)
        assert is_blacklisted is True

        # Cookie should be cleared
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert "max-age=0" in set_cookie.lower() or "max_age=0" in set_cookie.lower()


def test_complete_auth_flow(client, mock_discord_api, mock_supabase):
    """
    Test complete authentication flow: login → refresh → logout

    **Validates: Complete authentication flow**
    """
    # Step 1: Login redirect
    login_response = client.get("/api/auth/discord/login", follow_redirects=False)
    assert login_response.status_code == 302

    # Step 2: OAuth callback (simulated)
    callback_response = client.get("/api/auth/discord/callback?code=test_code")
    assert callback_response.status_code == 200

    # Extract token from response
    callback_data = callback_response.json()
    token = callback_data["access_token"]

    # Step 3: Use token to access protected endpoint
    feeds_response = client.get("/api/feeds", headers={"Authorization": f"Bearer {token}"})
    # May return 500 if database is not available, but should not return 401
    assert feeds_response.status_code != 401

    # Step 4: Refresh token
    refresh_response = client.post("/api/auth/refresh", cookies={"access_token": token})
    assert refresh_response.status_code == 200

    # Extract new token
    refresh_data = refresh_response.json()
    new_token = refresh_data["access_token"]

    # Step 5: Old token should not work
    old_token_response = client.get("/api/feeds", headers={"Authorization": f"Bearer {token}"})
    assert old_token_response.status_code == 401

    # Step 6: New token should work
    new_token_response = client.get("/api/feeds", headers={"Authorization": f"Bearer {new_token}"})
    assert new_token_response.status_code != 401

    # Step 7: Logout
    logout_response = client.post("/api/auth/logout", cookies={"access_token": new_token})
    assert logout_response.status_code == 200

    # Step 8: Token should not work after logout
    after_logout_response = client.get(
        "/api/feeds", headers={"Authorization": f"Bearer {new_token}"}
    )
    assert after_logout_response.status_code == 401


def test_error_handling_token_exchange_failure(client):
    """
    Test error handling when Discord token exchange fails

    **Validates: Requirements 12.4, 12.5**
    """
    with patch("httpx.AsyncClient") as mock_client:
        # Mock failed token exchange
        mock_token_response = Mock()
        mock_token_response.status_code = 400

        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(return_value=mock_token_response)

        response = client.get("/api/auth/discord/callback?code=invalid_code")

        # Should return 401 Unauthorized
        assert response.status_code == 401


def test_error_handling_discord_api_failure(client):
    """
    Test error handling when Discord API fails

    **Validates: Requirements 12.6**
    """
    with patch("httpx.AsyncClient") as mock_client:
        # Mock successful token exchange but failed user info
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "test_token"}

        mock_user_response = Mock()
        mock_user_response.status_code = 500

        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(return_value=mock_token_response)
        mock_instance.get = AsyncMock(return_value=mock_user_response)

        response = client.get("/api/auth/discord/callback?code=test_code")

        # Should return 500 Internal Server Error
        assert response.status_code == 500
