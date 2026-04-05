"""
Property-based test for JWT Token Round Trip
Task 1.5

This module tests Property 3: JWT Token Round Trip
For any valid JWT Token, decoding and then encoding with the same secret
should produce an equivalent token that validates successfully.
"""

import pytest
from datetime import datetime
from uuid import UUID
from hypothesis import given, strategies as st, settings as hypothesis_settings
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


# Feature: web-api-oauth-authentication, Property 3: JWT Token Round Trip
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    )
)
def test_jwt_round_trip_property(user_id, discord_id):
    """
    **Validates: Requirements 3.1, 3.2, 3.5**
    
    Property 3: For any valid JWT Token, decoding and then encoding with the same secret
    should produce an equivalent token that validates successfully.
    
    This property ensures that:
    1. A token can be decoded to extract user information
    2. The extracted information can be used to create a new token
    3. The new token contains the same user_id and discord_id
    4. Both tokens are valid and can be decoded successfully
    5. The round-trip process preserves user identity information
    """
    # Step 1: Generate original JWT Token
    original_token = create_access_token(user_id, discord_id)
    
    # Verify original token is valid
    assert isinstance(original_token, str), "Original token should be a string"
    assert len(original_token) > 0, "Original token should not be empty"
    
    # Step 2: Decode the original token
    try:
        original_payload = decode_token(original_token)
    except JWTError as e:
        pytest.fail(f"Original token decoding failed with JWTError: {e}")
    
    # Verify original payload has required claims
    assert "sub" in original_payload, "Original payload should contain 'sub' claim"
    assert "discord_id" in original_payload, "Original payload should contain 'discord_id' claim"
    
    # Step 3: Extract user information from payload
    extracted_user_id = UUID(original_payload["sub"])
    extracted_discord_id = original_payload["discord_id"]
    
    # Verify extracted information matches original input
    assert extracted_user_id == user_id, \
        f"Extracted user_id should match original: expected {user_id}, got {extracted_user_id}"
    assert extracted_discord_id == discord_id, \
        f"Extracted discord_id should match original: expected {discord_id}, got {extracted_discord_id}"
    
    # Step 4: Create a new token using the extracted information
    new_token = create_access_token(extracted_user_id, extracted_discord_id)
    
    # Verify new token is valid
    assert isinstance(new_token, str), "New token should be a string"
    assert len(new_token) > 0, "New token should not be empty"
    
    # Step 5: Decode the new token
    try:
        new_payload = decode_token(new_token)
    except JWTError as e:
        pytest.fail(f"New token decoding failed with JWTError: {e}")
    
    # Step 6: Verify the new payload contains the same user information
    assert "sub" in new_payload, "New payload should contain 'sub' claim"
    assert "discord_id" in new_payload, "New payload should contain 'discord_id' claim"
    
    # Verify user_id is preserved through round trip
    new_user_id = UUID(new_payload["sub"])
    assert new_user_id == user_id, \
        f"Round-trip user_id should match original: expected {user_id}, got {new_user_id}"
    
    # Verify discord_id is preserved through round trip
    assert new_payload["discord_id"] == discord_id, \
        f"Round-trip discord_id should match original: expected {discord_id}, got {new_payload['discord_id']}"
    
    # Step 7: Verify both payloads have the same user identity
    assert original_payload["sub"] == new_payload["sub"], \
        "Both tokens should have the same 'sub' claim"
    assert original_payload["discord_id"] == new_payload["discord_id"], \
        "Both tokens should have the same 'discord_id' claim"
    
    # Step 8: Verify both tokens are independently valid
    # (Already verified by successful decode_token calls above)
    
    # Step 9: Verify the round-trip preserves token structure
    assert "exp" in new_payload, "New payload should contain 'exp' claim"
    assert "iat" in new_payload, "New payload should contain 'iat' claim"
    
    # Verify exp is in the future for new token
    exp_time = datetime.utcfromtimestamp(new_payload["exp"])
    current_time = datetime.utcnow()
    assert exp_time > current_time, \
        f"New token expiration should be in the future: exp={exp_time}, now={current_time}"


# Feature: web-api-oauth-authentication, Property 3: JWT Token Round Trip (Multiple Iterations)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    ),
    iterations=st.integers(min_value=2, max_value=5)
)
def test_jwt_multiple_round_trips_property(user_id, discord_id, iterations):
    """
    **Validates: Requirements 3.1, 3.2, 3.5**
    
    Property 3 (Extended): For any valid JWT Token, multiple rounds of
    decoding and encoding should preserve user identity information.
    
    This property ensures that the round-trip process is stable and
    can be repeated multiple times without data loss or corruption.
    """
    current_token = create_access_token(user_id, discord_id)
    
    for i in range(iterations):
        # Decode current token
        try:
            payload = decode_token(current_token)
        except JWTError as e:
            pytest.fail(f"Token decoding failed at iteration {i} with JWTError: {e}")
        
        # Verify user information is preserved
        assert payload["sub"] == str(user_id), \
            f"At iteration {i}, user_id should be preserved: expected {str(user_id)}, got {payload['sub']}"
        assert payload["discord_id"] == discord_id, \
            f"At iteration {i}, discord_id should be preserved: expected {discord_id}, got {payload['discord_id']}"
        
        # Create new token from decoded information
        extracted_user_id = UUID(payload["sub"])
        extracted_discord_id = payload["discord_id"]
        current_token = create_access_token(extracted_user_id, extracted_discord_id)
    
    # Final verification: decode the last token and verify user information
    final_payload = decode_token(current_token)
    final_user_id = UUID(final_payload["sub"])
    final_discord_id = final_payload["discord_id"]
    
    assert final_user_id == user_id, \
        f"After {iterations} iterations, user_id should be preserved: expected {user_id}, got {final_user_id}"
    assert final_discord_id == discord_id, \
        f"After {iterations} iterations, discord_id should be preserved: expected {discord_id}, got {final_discord_id}"


# Feature: web-api-oauth-authentication, Property 3: JWT Token Round Trip (Edge Cases)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.one_of(
        # Normal ASCII strings
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
        ),
        # Strings with special characters
        st.text(min_size=1, max_size=50, alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?'),
        # Numeric strings
        st.text(min_size=1, max_size=50, alphabet='0123456789'),
        # Mixed case strings
        st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    )
)
def test_jwt_round_trip_edge_cases_property(user_id, discord_id):
    """
    **Validates: Requirements 3.1, 3.2, 3.5**
    
    Property 3 (Edge Cases): For any valid JWT Token with various discord_id formats,
    the round-trip process should preserve the exact discord_id value.
    
    This property ensures that special characters, numeric strings, and other
    edge cases in discord_id are handled correctly during encoding/decoding.
    """
    # Generate original token
    original_token = create_access_token(user_id, discord_id)
    
    # Decode original token
    original_payload = decode_token(original_token)
    
    # Verify discord_id is preserved exactly
    assert original_payload["discord_id"] == discord_id, \
        f"Discord ID should be preserved exactly: expected '{discord_id}', got '{original_payload['discord_id']}'"
    
    # Create new token from decoded information
    extracted_user_id = UUID(original_payload["sub"])
    extracted_discord_id = original_payload["discord_id"]
    new_token = create_access_token(extracted_user_id, extracted_discord_id)
    
    # Decode new token
    new_payload = decode_token(new_token)
    
    # Verify discord_id is still preserved exactly after round trip
    assert new_payload["discord_id"] == discord_id, \
        f"Discord ID should be preserved after round trip: expected '{discord_id}', got '{new_payload['discord_id']}'"
    
    # Verify no character encoding issues
    assert len(new_payload["discord_id"]) == len(discord_id), \
        f"Discord ID length should be preserved: expected {len(discord_id)}, got {len(new_payload['discord_id'])}"
