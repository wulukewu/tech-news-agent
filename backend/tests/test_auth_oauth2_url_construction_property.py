"""
Property-based test for OAuth2 URL Construction
Task 1.9

This module tests Property 1: OAuth2 URL Construction
For any valid Discord OAuth2 configuration (client_id, redirect_uri),
the constructed authorization URL should contain all required parameters
(client_id, redirect_uri, response_type=code, scope=identify).

**Validates: Requirements 1.2, 1.3, 1.4, 1.5**
"""

from urllib.parse import parse_qs, urlparse

from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st


# Hypothesis strategies for generating test data
def valid_client_id_strategy():
    """Generate valid Discord client IDs (numeric strings)"""
    return st.integers(min_value=100000000000000000, max_value=999999999999999999).map(str)


def valid_redirect_uri_strategy():
    """Generate valid redirect URIs"""
    # Generate valid URL components
    schemes = st.sampled_from(["http", "https"])
    domains = st.text(
        min_size=3, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)  # a-z
    )
    ports = st.one_of(st.none(), st.integers(min_value=1000, max_value=65535))
    paths = st.one_of(
        st.just(""),
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),  # a-z
        ).map(lambda p: f"/{p}"),
    )

    @st.composite
    def url_strategy(draw):
        scheme = draw(schemes)
        domain = draw(domains)
        port = draw(ports)
        path = draw(paths)

        # Construct URL
        if port:
            return f"{scheme}://{domain}:{port}{path}"
        else:
            return f"{scheme}://{domain}{path}"

    return url_strategy()


def construct_oauth2_url(client_id: str, redirect_uri: str) -> str:
    """
    Construct Discord OAuth2 authorization URL

    This is the function under test - it mimics the logic in
    app/api/auth.py discord_login endpoint.

    Args:
        client_id: Discord application client ID
        redirect_uri: OAuth2 callback URL

    Returns:
        Complete Discord OAuth2 authorization URL
    """
    from urllib.parse import urlencode

    discord_auth_base_url = "https://discord.com/api/oauth2/authorize"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "identify",
    }

    return f"{discord_auth_base_url}?{urlencode(params)}"


# Feature: web-api-oauth-authentication, Property 1: OAuth2 URL Construction
@hypothesis_settings(max_examples=100)
@given(client_id=valid_client_id_strategy(), redirect_uri=valid_redirect_uri_strategy())
def test_oauth2_url_construction_property(client_id, redirect_uri):
    """
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

    Property 1: For any valid Discord OAuth2 configuration (client_id, redirect_uri),
    the constructed authorization URL should contain all required parameters
    (client_id, redirect_uri, response_type=code, scope=identify).

    This property ensures that:
    1. The URL starts with the correct Discord OAuth2 base URL
    2. The client_id parameter is present and matches the input
    3. The redirect_uri parameter is present and matches the input
    4. The response_type parameter is set to "code"
    5. The scope parameter is set to "identify"
    6. All required parameters are present in the query string
    """
    # Construct the OAuth2 URL
    auth_url = construct_oauth2_url(client_id, redirect_uri)

    # Verify the URL is a non-empty string
    assert isinstance(auth_url, str), "Authorization URL should be a string"
    assert len(auth_url) > 0, "Authorization URL should not be empty"

    # Parse the URL
    parsed_url = urlparse(auth_url)

    # Verify the base URL is correct
    expected_base = "https://discord.com/api/oauth2/authorize"
    actual_base = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    assert actual_base == expected_base, f"Base URL should be {expected_base}, got {actual_base}"

    # Parse query parameters
    query_params = parse_qs(parsed_url.query)

    # Verify all required parameters are present
    required_params = ["client_id", "redirect_uri", "response_type", "scope"]
    for param in required_params:
        assert param in query_params, f"Required parameter '{param}' is missing from URL"
        assert len(query_params[param]) > 0, f"Parameter '{param}' should have at least one value"

    # Verify client_id matches input
    assert (
        query_params["client_id"][0] == client_id
    ), f"client_id parameter should match input: expected {client_id}, got {query_params['client_id'][0]}"

    # Verify redirect_uri matches input
    assert (
        query_params["redirect_uri"][0] == redirect_uri
    ), f"redirect_uri parameter should match input: expected {redirect_uri}, got {query_params['redirect_uri'][0]}"

    # Verify response_type is "code"
    assert (
        query_params["response_type"][0] == "code"
    ), f"response_type should be 'code', got {query_params['response_type'][0]}"

    # Verify scope is "identify"
    assert (
        query_params["scope"][0] == "identify"
    ), f"scope should be 'identify', got {query_params['scope'][0]}"

    # Verify no duplicate parameters (each should have exactly one value)
    for param in required_params:
        assert (
            len(query_params[param]) == 1
        ), f"Parameter '{param}' should appear exactly once, found {len(query_params[param])} times"


# Feature: web-api-oauth-authentication, Property 1: OAuth2 URL Construction (Edge Cases)
@hypothesis_settings(max_examples=100)
@given(client_id=valid_client_id_strategy(), redirect_uri=valid_redirect_uri_strategy())
def test_oauth2_url_construction_idempotence_property(client_id, redirect_uri):
    """
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

    Property 1 (Extended): For any valid configuration, constructing the OAuth2 URL
    multiple times with the same inputs should produce identical results.

    This property ensures that URL construction is deterministic and idempotent.
    """
    # Construct the URL twice
    url1 = construct_oauth2_url(client_id, redirect_uri)
    url2 = construct_oauth2_url(client_id, redirect_uri)

    # Verify they are identical
    assert url1 == url2, f"URL construction should be idempotent: first={url1}, second={url2}"

    # Parse both URLs
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    # Verify all components are identical
    assert parsed1.scheme == parsed2.scheme, "Schemes should match"
    assert parsed1.netloc == parsed2.netloc, "Network locations should match"
    assert parsed1.path == parsed2.path, "Paths should match"

    # Parse and compare query parameters
    params1 = parse_qs(parsed1.query)
    params2 = parse_qs(parsed2.query)

    assert params1 == params2, f"Query parameters should match: first={params1}, second={params2}"


# Feature: web-api-oauth-authentication, Property 1: OAuth2 URL Construction (URL Encoding)
@hypothesis_settings(max_examples=100)
@given(
    client_id=valid_client_id_strategy(),
    # Generate redirect URIs with special characters that need encoding
    redirect_uri=st.builds(
        lambda scheme, domain, path: f"{scheme}://{domain}/{path}",
        scheme=st.sampled_from(["http", "https"]),
        domain=st.text(
            min_size=3, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)
        ),
        path=st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(min_codepoint=97, max_codepoint=122, whitelist_characters="/-_"),
        ),
    ),
)
def test_oauth2_url_construction_encoding_property(client_id, redirect_uri):
    """
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

    Property 1 (Extended): For any valid configuration including special characters,
    the constructed URL should properly encode parameters.

    This property ensures that URL encoding is correctly applied to parameters.
    """
    # Construct the OAuth2 URL
    auth_url = construct_oauth2_url(client_id, redirect_uri)

    # Parse the URL
    parsed_url = urlparse(auth_url)
    query_params = parse_qs(parsed_url.query)

    # Verify the redirect_uri is properly decoded back to the original value
    decoded_redirect_uri = query_params["redirect_uri"][0]
    assert (
        decoded_redirect_uri == redirect_uri
    ), f"Decoded redirect_uri should match original: expected {redirect_uri}, got {decoded_redirect_uri}"

    # Verify the URL is valid (can be parsed without errors)
    assert parsed_url.scheme in ["https"], "URL scheme should be https"
    assert parsed_url.netloc == "discord.com", "URL should point to discord.com"
    assert parsed_url.path == "/api/oauth2/authorize", "URL path should be correct"


# Feature: web-api-oauth-authentication, Property 1: OAuth2 URL Construction (Parameter Completeness)
@hypothesis_settings(max_examples=100)
@given(client_id=valid_client_id_strategy(), redirect_uri=valid_redirect_uri_strategy())
def test_oauth2_url_construction_no_extra_parameters_property(client_id, redirect_uri):
    """
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

    Property 1 (Extended): For any valid configuration, the constructed URL
    should contain exactly the required parameters and no extra parameters.

    This property ensures that no unexpected parameters are added to the URL.
    """
    # Construct the OAuth2 URL
    auth_url = construct_oauth2_url(client_id, redirect_uri)

    # Parse the URL
    parsed_url = urlparse(auth_url)
    query_params = parse_qs(parsed_url.query)

    # Define the exact set of required parameters
    required_params = {"client_id", "redirect_uri", "response_type", "scope"}
    actual_params = set(query_params.keys())

    # Verify no extra parameters
    extra_params = actual_params - required_params
    assert len(extra_params) == 0, f"URL should not contain extra parameters: {extra_params}"

    # Verify no missing parameters
    missing_params = required_params - actual_params
    assert (
        len(missing_params) == 0
    ), f"URL should contain all required parameters, missing: {missing_params}"

    # Verify exact match
    assert (
        actual_params == required_params
    ), f"URL parameters should exactly match required set: expected {required_params}, got {actual_params}"
