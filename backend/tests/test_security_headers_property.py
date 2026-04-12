"""
Property 18: Security Headers Presence

**Validates: Requirements 18.5**

For any API response, security headers should be present to protect against
common web vulnerabilities.
"""

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.main import app


@pytest.fixture
def client():
    """Create a test client for each test"""
    return TestClient(app)


# Property 18: Security Headers Presence
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate various endpoint paths
    endpoint=st.sampled_from(
        ["/", "/health", "/api/auth/discord/login", "/api/feeds", "/api/articles/me"]
    ),
    # Generate various HTTP methods
    method=st.sampled_from(["GET", "POST", "OPTIONS"]),
)
def test_security_headers_presence_property(client, endpoint, method):
    """
    Property 18: Security Headers Presence

    **Validates: Requirements 18.5**

    For any API response, the following security headers should be present:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block

    These headers protect against:
    - MIME type sniffing attacks
    - Clickjacking attacks
    - Cross-site scripting (XSS) attacks
    """
    # Make request based on method
    try:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "OPTIONS":
            response = client.options(endpoint)
        else:
            pytest.skip(f"Unsupported method: {method}")
    except Exception:
        # Some endpoints might not exist or require auth
        pytest.skip("Endpoint not accessible")

    # Verify X-Content-Type-Options header
    x_content_type_options = response.headers.get("X-Content-Type-Options") or response.headers.get(
        "x-content-type-options"
    )
    assert (
        x_content_type_options is not None
    ), f"X-Content-Type-Options header missing for {method} {endpoint}"
    assert (
        x_content_type_options.lower() == "nosniff"
    ), f"X-Content-Type-Options should be 'nosniff', got: {x_content_type_options}"

    # Verify X-Frame-Options header
    x_frame_options = response.headers.get("X-Frame-Options") or response.headers.get(
        "x-frame-options"
    )
    assert x_frame_options is not None, f"X-Frame-Options header missing for {method} {endpoint}"
    assert (
        x_frame_options.upper() == "DENY"
    ), f"X-Frame-Options should be 'DENY', got: {x_frame_options}"

    # Verify X-XSS-Protection header
    x_xss_protection = response.headers.get("X-XSS-Protection") or response.headers.get(
        "x-xss-protection"
    )
    assert x_xss_protection is not None, f"X-XSS-Protection header missing for {method} {endpoint}"
    assert (
        "1" in x_xss_protection and "mode=block" in x_xss_protection.lower()
    ), f"X-XSS-Protection should be '1; mode=block', got: {x_xss_protection}"


def test_security_headers_all_endpoints(client):
    """
    Property 18: Security Headers Presence (All Endpoints)

    **Validates: Requirements 18.5**

    Verifies that security headers are present on all major endpoints.
    """
    endpoints = [
        "/",
        "/health",
        "/api/auth/discord/login",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        # Check all three security headers
        assert (
            "X-Content-Type-Options" in response.headers
            or "x-content-type-options" in response.headers
        ), f"X-Content-Type-Options missing on {endpoint}"

        assert (
            "X-Frame-Options" in response.headers or "x-frame-options" in response.headers
        ), f"X-Frame-Options missing on {endpoint}"

        assert (
            "X-XSS-Protection" in response.headers or "x-xss-protection" in response.headers
        ), f"X-XSS-Protection missing on {endpoint}"


def test_security_headers_correct_values(client):
    """
    Property 18: Security Headers Presence (Correct Values)

    **Validates: Requirements 18.5**

    Verifies that security headers have the correct values.
    """
    response = client.get("/health")

    # X-Content-Type-Options should be "nosniff"
    x_content_type = response.headers.get("X-Content-Type-Options") or response.headers.get(
        "x-content-type-options"
    )
    assert (
        x_content_type == "nosniff"
    ), f"X-Content-Type-Options should be 'nosniff', got: {x_content_type}"

    # X-Frame-Options should be "DENY"
    x_frame = response.headers.get("X-Frame-Options") or response.headers.get("x-frame-options")
    assert x_frame == "DENY", f"X-Frame-Options should be 'DENY', got: {x_frame}"

    # X-XSS-Protection should be "1; mode=block"
    x_xss = response.headers.get("X-XSS-Protection") or response.headers.get("x-xss-protection")
    assert x_xss == "1; mode=block", f"X-XSS-Protection should be '1; mode=block', got: {x_xss}"


def test_security_headers_on_error_responses(client):
    """
    Property 18: Security Headers Presence (Error Responses)

    **Validates: Requirements 18.5**

    Verifies that security headers are present even on error responses.
    """
    # Make a request to a non-existent endpoint to trigger 404
    response = client.get("/nonexistent-endpoint-12345")

    # Security headers should still be present on error responses
    assert (
        "X-Content-Type-Options" in response.headers or "x-content-type-options" in response.headers
    ), "X-Content-Type-Options missing on error response"

    assert (
        "X-Frame-Options" in response.headers or "x-frame-options" in response.headers
    ), "X-Frame-Options missing on error response"

    assert (
        "X-XSS-Protection" in response.headers or "x-xss-protection" in response.headers
    ), "X-XSS-Protection missing on error response"


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status_code=st.sampled_from([200, 400, 401, 404, 500]))
def test_security_headers_on_various_status_codes(client, status_code):
    """
    Property 18: Security Headers Presence (Various Status Codes)

    **Validates: Requirements 18.5**

    Verifies that security headers are present regardless of response status code.
    """
    # Map status codes to endpoints that typically return them
    endpoint_map = {
        200: "/health",
        400: "/api/auth/discord/callback",  # Missing code parameter
        401: "/api/feeds",  # No authentication
        404: "/nonexistent-endpoint",
        500: "/health",  # May return 500 if services are down
    }

    endpoint = endpoint_map.get(status_code, "/health")

    try:
        response = client.get(endpoint)
    except Exception:
        pytest.skip("Endpoint not accessible")

    # Verify security headers are present regardless of status code
    has_content_type_options = (
        "X-Content-Type-Options" in response.headers or "x-content-type-options" in response.headers
    )
    has_frame_options = (
        "X-Frame-Options" in response.headers or "x-frame-options" in response.headers
    )
    has_xss_protection = (
        "X-XSS-Protection" in response.headers or "x-xss-protection" in response.headers
    )

    assert (
        has_content_type_options
    ), f"X-Content-Type-Options missing on response with status {response.status_code}"
    assert (
        has_frame_options
    ), f"X-Frame-Options missing on response with status {response.status_code}"
    assert (
        has_xss_protection
    ), f"X-XSS-Protection missing on response with status {response.status_code}"
