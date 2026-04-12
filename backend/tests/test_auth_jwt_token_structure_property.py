"""
Property-based test for JWT Token Structure
Task 1.4

This module tests Property 2: JWT Token Structure
For any user data (user_id, discord_id), the generated JWT Token should decode
to a payload containing the correct sub, discord_id, exp, and iat claims,
and the signature should be valid when verified with the same secret.
"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st
from jose import JWTError

from app.api.auth import create_access_token, decode_token
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


# Feature: web-api-oauth-authentication, Property 2: JWT Token Structure
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_characters="\x00\n\r"
        ),
    ),
)
def test_jwt_token_structure_property(user_id, discord_id):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property 2: For any user data (user_id, discord_id), the generated JWT Token
    should decode to a payload containing the correct sub, discord_id, exp, and iat claims,
    and the signature should be valid when verified with the same secret.

    This property ensures that:
    1. Token generation always produces a valid JWT
    2. The payload contains all required claims (sub, discord_id, exp, iat)
    3. The sub claim matches the input user_id
    4. The discord_id claim matches the input discord_id
    5. The exp claim is set to a future time
    6. The iat claim is set to the current time
    7. The token signature is valid and can be verified
    """
    # Generate JWT Token
    token = create_access_token(user_id, discord_id)

    # Verify token is a non-empty string
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 0, "Token should not be empty"

    # Decode the token (this also verifies the signature)
    try:
        payload = decode_token(token)
    except JWTError as e:
        pytest.fail(f"Token decoding failed with JWTError: {e}")

    # Verify all required claims are present
    assert "sub" in payload, "Payload should contain 'sub' claim"
    assert "discord_id" in payload, "Payload should contain 'discord_id' claim"
    assert "exp" in payload, "Payload should contain 'exp' claim"
    assert "iat" in payload, "Payload should contain 'iat' claim"

    # Verify sub claim matches user_id
    assert payload["sub"] == str(
        user_id
    ), f"Payload 'sub' should match user_id: expected {user_id!s}, got {payload['sub']}"

    # Verify sub can be converted back to UUID
    try:
        decoded_user_id = UUID(payload["sub"])
        assert (
            decoded_user_id == user_id
        ), f"Decoded user_id should match original: expected {user_id}, got {decoded_user_id}"
    except ValueError as e:
        pytest.fail(f"Payload 'sub' is not a valid UUID: {e}")

    # Verify discord_id claim matches input
    assert (
        payload["discord_id"] == discord_id
    ), f"Payload 'discord_id' should match input: expected {discord_id}, got {payload['discord_id']}"

    # Verify exp claim is a future timestamp
    assert isinstance(payload["exp"], (int, float)), "Payload 'exp' should be a numeric timestamp"
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    current_time = datetime.utcnow()
    assert (
        exp_time > current_time
    ), f"Expiration time should be in the future: exp={exp_time}, now={current_time}"

    # Verify iat claim is approximately the current time (within 5 seconds)
    assert isinstance(payload["iat"], (int, float)), "Payload 'iat' should be a numeric timestamp"
    iat_time = datetime.utcfromtimestamp(payload["iat"])
    time_diff = abs((current_time - iat_time).total_seconds())
    assert (
        time_diff < 5
    ), f"Issued-at time should be approximately now: iat={iat_time}, now={current_time}, diff={time_diff}s"

    # Verify exp is after iat
    assert payload["exp"] > payload["iat"], "Expiration time should be after issued-at time"

    # Verify the expiration delta is approximately the configured value
    exp_delta_seconds = payload["exp"] - payload["iat"]
    expected_delta_seconds = settings.jwt_expiration_days * 24 * 60 * 60
    # Allow 5 seconds tolerance for execution time
    assert (
        abs(exp_delta_seconds - expected_delta_seconds) < 5
    ), f"Expiration delta should match configured value: expected {expected_delta_seconds}s, got {exp_delta_seconds}s"


# Feature: web-api-oauth-authentication, Property 2: JWT Token Structure (Edge Cases)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_characters="\x00\n\r"
        ),
    ),
    expires_delta=st.one_of(
        st.none(),
        st.builds(timedelta, seconds=st.integers(min_value=1, max_value=365 * 24 * 60 * 60)),
    ),
)
def test_jwt_token_structure_with_custom_expiration_property(user_id, discord_id, expires_delta):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property 2 (Extended): For any user data and custom expiration delta,
    the generated JWT Token should decode to a payload with the correct
    expiration time based on the provided delta.

    This property ensures that custom expiration times are correctly applied.
    """
    # Generate JWT Token with custom expiration
    token = create_access_token(user_id, discord_id, expires_delta)

    # Decode the token
    payload = decode_token(token)

    # Verify all required claims are present
    assert "sub" in payload
    assert "discord_id" in payload
    assert "exp" in payload
    assert "iat" in payload

    # Verify claims match input
    assert payload["sub"] == str(user_id)
    assert payload["discord_id"] == discord_id

    # Verify expiration delta
    exp_delta_seconds = payload["exp"] - payload["iat"]

    if expires_delta is None:
        # Should use default expiration
        expected_delta_seconds = settings.jwt_expiration_days * 24 * 60 * 60
    else:
        # Should use provided expiration
        expected_delta_seconds = expires_delta.total_seconds()

    # Allow 5 seconds tolerance
    assert (
        abs(exp_delta_seconds - expected_delta_seconds) < 5
    ), f"Expiration delta should match: expected {expected_delta_seconds}s, got {exp_delta_seconds}s"
