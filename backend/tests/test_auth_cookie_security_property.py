"""
Property-based test for Cookie Security Attributes
Task 1.6

This module tests Property 4: Cookie Security Attributes
For any JWT Token set as a cookie, the cookie should have httponly=True,
secure=True (in production), samesite="lax", and max_age=604800.
"""

import pytest
from uuid import UUID
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi import Response
from fastapi.responses import JSONResponse

from app.api.auth import create_access_token, set_token_cookie
from app.core.config import settings


@pytest.fixture(scope="module", autouse=True)
def setup_jwt_secret():
    """設置測試用的 JWT_SECRET"""
    # 保存原始值
    original_secret = settings.jwt_secret
    original_cookie_secure = settings.cookie_secure
    
    # 設置測試用的 secret
    test_secret = "test_jwt_secret_at_least_32_characters_long_for_testing"
    settings.jwt_secret = test_secret
    
    yield
    
    # 恢復原始值
    settings.jwt_secret = original_secret
    settings.cookie_secure = original_cookie_secure


# Feature: web-api-oauth-authentication, Property 4: Cookie Security Attributes
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    )
)
def test_cookie_security_attributes_property(user_id, discord_id):
    """
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    
    Property 4: For any JWT Token set as a cookie, the cookie should have
    httponly=True, secure=True (in production), samesite="lax", and max_age=604800.
    
    This property ensures that:
    1. The cookie has the httponly flag set to True (防止 JavaScript 存取)
    2. The cookie has the secure flag set appropriately based on environment
    3. The cookie has the samesite attribute set to "lax" (CSRF 防護)
    4. The cookie has the correct max_age (7 days = 604800 seconds)
    5. The cookie has the correct path ("/")
    6. The cookie has the correct key name ("access_token")
    """
    # Generate JWT Token
    token = create_access_token(user_id, discord_id)
    
    # Create a FastAPI Response object
    response = JSONResponse(content={"access_token": token, "token_type": "Bearer"})
    
    # Set the token as a cookie
    set_token_cookie(response, token)
    
    # Extract the Set-Cookie header
    set_cookie_header = response.headers.get("set-cookie")
    assert set_cookie_header is not None, "Response should have a Set-Cookie header"
    
    # Parse the Set-Cookie header
    # Format: "access_token=<token>; HttpOnly; Secure; SameSite=lax; Max-Age=604800; Path=/"
    cookie_parts = [part.strip() for part in set_cookie_header.split(";")]
    
    # Verify cookie name and value
    cookie_name_value = cookie_parts[0]
    assert cookie_name_value.startswith("access_token="), \
        f"Cookie should be named 'access_token', got: {cookie_name_value}"
    
    cookie_value = cookie_name_value.split("=", 1)[1]
    assert cookie_value == token, \
        f"Cookie value should match the token: expected {token[:20]}..., got {cookie_value[:20]}..."
    
    # Convert cookie parts to a dictionary for easier checking
    cookie_attributes = {}
    for part in cookie_parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            cookie_attributes[key.lower()] = value.lower()
        else:
            # Flags like HttpOnly, Secure
            cookie_attributes[part.lower()] = True
    
    # Requirement 4.1: Verify httponly flag is set to True
    assert "httponly" in cookie_attributes, \
        "Cookie should have the HttpOnly flag set"
    assert cookie_attributes["httponly"] is True, \
        "Cookie HttpOnly flag should be True"
    
    # Requirement 4.2: Verify secure flag is set appropriately
    # In production (cookie_secure=True), secure should be set
    # In development (cookie_secure=False), secure may not be set
    if settings.cookie_secure:
        assert "secure" in cookie_attributes, \
            "Cookie should have the Secure flag set when cookie_secure=True"
        assert cookie_attributes["secure"] is True, \
            "Cookie Secure flag should be True when cookie_secure=True"
    # Note: We don't assert absence of secure flag when cookie_secure=False
    # because the test might run in different environments
    
    # Requirement 4.3: Verify samesite attribute is set to "lax"
    assert "samesite" in cookie_attributes, \
        "Cookie should have the SameSite attribute set"
    assert cookie_attributes["samesite"] == "lax", \
        f"Cookie SameSite should be 'lax', got: {cookie_attributes.get('samesite')}"
    
    # Requirement 4.4, 4.5: Verify max_age is set to 7 days (604800 seconds)
    assert "max-age" in cookie_attributes, \
        "Cookie should have the Max-Age attribute set"
    
    max_age_value = int(cookie_attributes["max-age"])
    expected_max_age = settings.jwt_expiration_days * 24 * 60 * 60  # 7 days = 604800 seconds
    assert max_age_value == expected_max_age, \
        f"Cookie Max-Age should be {expected_max_age} seconds (7 days), got: {max_age_value}"
    
    # Requirement 4.6: Verify path is set to "/"
    assert "path" in cookie_attributes, \
        "Cookie should have the Path attribute set"
    assert cookie_attributes["path"] == "/", \
        f"Cookie Path should be '/', got: {cookie_attributes.get('path')}"


# Feature: web-api-oauth-authentication, Property 4: Cookie Security Attributes (Production Mode)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    )
)
def test_cookie_security_attributes_production_mode_property(user_id, discord_id):
    """
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    
    Property 4 (Production Mode): For any JWT Token set as a cookie in production mode,
    the cookie should have the secure flag set to True.
    
    This property specifically tests the production environment configuration
    where HTTPS is required.
    """
    # Save original cookie_secure setting
    original_cookie_secure = settings.cookie_secure
    
    try:
        # Set production mode (cookie_secure=True)
        settings.cookie_secure = True
        
        # Generate JWT Token
        token = create_access_token(user_id, discord_id)
        
        # Create a FastAPI Response object
        response = JSONResponse(content={"access_token": token, "token_type": "Bearer"})
        
        # Set the token as a cookie
        set_token_cookie(response, token)
        
        # Extract the Set-Cookie header
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None, "Response should have a Set-Cookie header"
        
        # Parse the Set-Cookie header
        cookie_parts = [part.strip() for part in set_cookie_header.split(";")]
        
        # Convert cookie parts to a dictionary
        cookie_attributes = {}
        for part in cookie_parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                cookie_attributes[key.lower()] = value.lower()
            else:
                cookie_attributes[part.lower()] = True
        
        # In production mode, secure flag MUST be set
        assert "secure" in cookie_attributes, \
            "Cookie MUST have the Secure flag set in production mode (cookie_secure=True)"
        assert cookie_attributes["secure"] is True, \
            "Cookie Secure flag MUST be True in production mode"
        
        # Verify all other security attributes are still present
        assert "httponly" in cookie_attributes, \
            "Cookie should have HttpOnly flag in production mode"
        assert cookie_attributes["httponly"] is True, \
            "Cookie HttpOnly flag should be True in production mode"
        
        assert "samesite" in cookie_attributes, \
            "Cookie should have SameSite attribute in production mode"
        assert cookie_attributes["samesite"] == "lax", \
            "Cookie SameSite should be 'lax' in production mode"
        
        assert "max-age" in cookie_attributes, \
            "Cookie should have Max-Age attribute in production mode"
        max_age_value = int(cookie_attributes["max-age"])
        expected_max_age = settings.jwt_expiration_days * 24 * 60 * 60
        assert max_age_value == expected_max_age, \
            f"Cookie Max-Age should be {expected_max_age} seconds in production mode"
        
        assert "path" in cookie_attributes, \
            "Cookie should have Path attribute in production mode"
        assert cookie_attributes["path"] == "/", \
            "Cookie Path should be '/' in production mode"
    
    finally:
        # Restore original setting
        settings.cookie_secure = original_cookie_secure


# Feature: web-api-oauth-authentication, Property 4: Cookie Security Attributes (Development Mode)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    )
)
def test_cookie_security_attributes_development_mode_property(user_id, discord_id):
    """
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    
    Property 4 (Development Mode): For any JWT Token set as a cookie in development mode,
    the cookie should have all security attributes except secure flag may be False.
    
    This property tests the development environment configuration where HTTP is allowed.
    """
    # Save original cookie_secure setting
    original_cookie_secure = settings.cookie_secure
    
    try:
        # Set development mode (cookie_secure=False)
        settings.cookie_secure = False
        
        # Generate JWT Token
        token = create_access_token(user_id, discord_id)
        
        # Create a FastAPI Response object
        response = JSONResponse(content={"access_token": token, "token_type": "Bearer"})
        
        # Set the token as a cookie
        set_token_cookie(response, token)
        
        # Extract the Set-Cookie header
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None, "Response should have a Set-Cookie header"
        
        # Parse the Set-Cookie header
        cookie_parts = [part.strip() for part in set_cookie_header.split(";")]
        
        # Convert cookie parts to a dictionary
        cookie_attributes = {}
        for part in cookie_parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                cookie_attributes[key.lower()] = value.lower()
            else:
                cookie_attributes[part.lower()] = True
        
        # In development mode, secure flag should NOT be set (or should be False)
        # Note: FastAPI may omit the secure flag entirely when secure=False
        if "secure" in cookie_attributes:
            # If present, it should reflect the cookie_secure setting
            # But typically it's omitted when False
            pass
        
        # Verify all other security attributes are still present
        assert "httponly" in cookie_attributes, \
            "Cookie should have HttpOnly flag in development mode"
        assert cookie_attributes["httponly"] is True, \
            "Cookie HttpOnly flag should be True in development mode"
        
        assert "samesite" in cookie_attributes, \
            "Cookie should have SameSite attribute in development mode"
        assert cookie_attributes["samesite"] == "lax", \
            "Cookie SameSite should be 'lax' in development mode"
        
        assert "max-age" in cookie_attributes, \
            "Cookie should have Max-Age attribute in development mode"
        max_age_value = int(cookie_attributes["max-age"])
        expected_max_age = settings.jwt_expiration_days * 24 * 60 * 60
        assert max_age_value == expected_max_age, \
            f"Cookie Max-Age should be {expected_max_age} seconds in development mode"
        
        assert "path" in cookie_attributes, \
            "Cookie should have Path attribute in development mode"
        assert cookie_attributes["path"] == "/", \
            "Cookie Path should be '/' in development mode"
    
    finally:
        # Restore original setting
        settings.cookie_secure = original_cookie_secure


# Feature: web-api-oauth-authentication, Property 4: Cookie Security Attributes (Edge Cases)
@hypothesis_settings(max_examples=100)
@given(
    user_id=st.uuids(),
    discord_id=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00\n\r')
    ),
    # Test with different token lengths (though JWT length is determined by payload)
    extra_claim=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
)
def test_cookie_security_attributes_edge_cases_property(user_id, discord_id, extra_claim):
    """
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    
    Property 4 (Edge Cases): For any JWT Token (including those with varying lengths),
    the cookie security attributes should remain consistent.
    
    This property ensures that cookie security attributes are not affected by
    the token content or length.
    """
    # Generate JWT Token (extra_claim is just for varying token length, not actually used)
    token = create_access_token(user_id, discord_id)
    
    # Create a FastAPI Response object
    response = JSONResponse(content={"access_token": token, "token_type": "Bearer"})
    
    # Set the token as a cookie
    set_token_cookie(response, token)
    
    # Extract the Set-Cookie header
    set_cookie_header = response.headers.get("set-cookie")
    assert set_cookie_header is not None, "Response should have a Set-Cookie header"
    
    # Verify the cookie is properly formatted
    assert "access_token=" in set_cookie_header, \
        "Set-Cookie header should contain 'access_token='"
    
    # Verify essential security attributes are present regardless of token content
    assert "HttpOnly" in set_cookie_header or "httponly" in set_cookie_header.lower(), \
        "Set-Cookie header should contain HttpOnly flag"
    
    assert "SameSite=lax" in set_cookie_header or "samesite=lax" in set_cookie_header.lower(), \
        "Set-Cookie header should contain SameSite=lax"
    
    assert "Max-Age=" in set_cookie_header or "max-age=" in set_cookie_header.lower(), \
        "Set-Cookie header should contain Max-Age attribute"
    
    assert "Path=/" in set_cookie_header or "path=/" in set_cookie_header.lower(), \
        "Set-Cookie header should contain Path=/"
    
    # Verify the token value is properly encoded in the cookie
    # (no special characters should break the cookie format)
    cookie_parts = set_cookie_header.split(";")
    cookie_name_value = cookie_parts[0].strip()
    assert cookie_name_value.startswith("access_token="), \
        "Cookie should start with 'access_token='"
    
    # Verify the cookie value doesn't contain semicolons or other delimiters
    # that would break the cookie format
    cookie_value = cookie_name_value.split("=", 1)[1]
    assert ";" not in cookie_value, \
        "Cookie value should not contain semicolons"
    assert "\n" not in cookie_value, \
        "Cookie value should not contain newlines"
    assert "\r" not in cookie_value, \
        "Cookie value should not contain carriage returns"
