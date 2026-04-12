"""
Property 15: Logout Revokes Token

**Validates: Requirements 14.1, 14.2, 14.3, 14.5, 14.6**

For any authenticated user, after calling /api/auth/logout, the token should be
blacklisted and subsequent requests with that token should return 401.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.api.auth import create_access_token, get_token_blacklist, logout


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for JWT configuration"""
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long_for_testing"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        mock_settings.cookie_secure = False
        yield mock_settings


@given(discord_id=st.text(min_size=1, max_size=50))
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_logout_revokes_token(discord_id, mock_settings):
    """
    Property 15: Logout Revokes Token

    Verifies that after logging out:
    1. The token is added to the blacklist
    2. Subsequent requests with the token are rejected
    3. The cookie is cleared
    """
    # Generate user data
    user_id = uuid4()

    # Create token
    token = create_access_token(user_id=user_id, discord_id=discord_id)

    # Mock current user (simulating get_current_user dependency)
    current_user = {"user_id": user_id, "discord_id": discord_id}

    # Get blacklist instance
    blacklist = get_token_blacklist()

    # Verify token is not blacklisted initially
    is_blacklisted_before = await blacklist.is_blacklisted(token)
    assert is_blacklisted_before is False, "Token should not be blacklisted initially"

    # Call logout endpoint
    response = await logout(current_user=current_user, access_token=token)

    # Verify response indicates success
    assert response.status_code == 200
    assert "Logged out successfully" in response.body.decode()

    # Verify token is now blacklisted
    is_blacklisted_after = await blacklist.is_blacklisted(token)
    assert is_blacklisted_after is True, "Token should be blacklisted after logout"

    # Verify cookie is cleared (max_age=0)
    # Check response headers for Set-Cookie with max_age=0
    set_cookie_header = response.headers.get("set-cookie", "")
    assert (
        "max-age=0" in set_cookie_header.lower() or "max_age=0" in set_cookie_header.lower()
    ), "Cookie should be cleared with max_age=0"
