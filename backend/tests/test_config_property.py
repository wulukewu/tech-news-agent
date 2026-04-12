"""
Property-Based Tests for Configuration Manager

This module contains property-based tests using Hypothesis to validate
the configuration manager's behavior across a wide range of inputs.

**Validates: Requirements 6.1, 6.3, 6.4**
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# Import Settings class directly, not the global settings instance
# This avoids triggering config loading at import time
from app.core.exceptions import ConfigurationError

# ============================================================================
# Test Strategies
# ============================================================================


@st.composite
def valid_url_strategy(draw):
    """Generate valid HTTPS URLs for Supabase."""
    subdomain = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=5,
            max_size=20,
        )
    )
    return f"https://{subdomain}.supabase.co"


@st.composite
def valid_key_strategy(draw, min_length=20):
    """Generate valid API keys with sufficient length."""
    length = draw(st.integers(min_value=min_length, max_value=100))
    return draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=length,
            max_size=length,
        )
    )


@st.composite
def valid_discord_token_strategy(draw):
    """Generate valid Discord bot tokens."""
    length = draw(st.integers(min_value=50, max_value=100))
    return draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65),
            min_size=length,
            max_size=length,
        )
    )


@st.composite
def valid_discord_client_id_strategy(draw):
    """Generate valid Discord client IDs (numeric strings)."""
    return str(draw(st.integers(min_value=100000000000000000, max_value=999999999999999999)))


@st.composite
def valid_jwt_secret_strategy(draw):
    """Generate valid JWT secrets (32+ chars, not insecure patterns)."""
    # Generate random alphanumeric string that doesn't contain insecure patterns
    length = draw(st.integers(min_value=32, max_value=64))
    secret = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=length,
            max_size=length,
        )
    )
    # Ensure it doesn't contain insecure patterns
    insecure_patterns = ["change", "secret", "password", "example", "test", "demo"]
    assume(not any(pattern in secret.lower() for pattern in insecure_patterns))
    return secret


@st.composite
def valid_cors_origin_strategy(draw):
    """Generate valid CORS origins."""
    protocol = draw(st.sampled_from(["http", "https"]))
    domain = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=3,
            max_size=15,
        )
    )
    tld = draw(st.sampled_from(["com", "org", "net", "io"]))
    port = draw(st.one_of(st.none(), st.integers(min_value=3000, max_value=9999)))

    if port:
        return f"{protocol}://{domain}.{tld}:{port}"
    return f"{protocol}://{domain}.{tld}"


@st.composite
def valid_groq_api_key_strategy(draw):
    """Generate valid Groq API keys (starts with gsk_)."""
    suffix_length = draw(st.integers(min_value=30, max_value=50))
    suffix = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=suffix_length,
            max_size=suffix_length,
        )
    )
    return f"gsk_{suffix}"


@st.composite
def valid_redirect_uri_strategy(draw):
    """Generate valid Discord redirect URIs."""
    protocol = draw(st.sampled_from(["http", "https"]))
    host = draw(st.sampled_from(["localhost", "example.com", "myapp.com"]))
    port = draw(st.one_of(st.none(), st.integers(min_value=3000, max_value=9999)))

    if port and host == "localhost":
        base = f"{protocol}://{host}:{port}"
    else:
        base = f"{protocol}://{host}"

    return f"{base}/api/auth/discord/callback"


@st.composite
def valid_config_env_strategy(draw):
    """Generate a complete set of valid environment variables."""
    return {
        "SUPABASE_URL": draw(valid_url_strategy()),
        "SUPABASE_KEY": draw(valid_key_strategy(min_length=30)),
        "DISCORD_TOKEN": draw(valid_discord_token_strategy()),
        "DISCORD_CLIENT_ID": draw(valid_discord_client_id_strategy()),
        "DISCORD_CLIENT_SECRET": draw(valid_key_strategy(min_length=30)),
        "DISCORD_REDIRECT_URI": draw(valid_redirect_uri_strategy()),
        "GROQ_API_KEY": draw(valid_groq_api_key_strategy()),
        "JWT_SECRET": draw(valid_jwt_secret_strategy()),
        "CORS_ORIGINS": draw(valid_cors_origin_strategy()),
    }


# ============================================================================
# Property 6: Configuration Loading
# ============================================================================


@given(config_env=valid_config_env_strategy())
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_6_valid_config_loads_successfully(config_env, monkeypatch):
    """
    **Property 6: Configuration Loading**

    For any environment variable set in the system, the Config Manager SHALL
    correctly load and provide type-safe access to that configuration value.

    **Validates: Requirements 6.1**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)

    # Load settings
    settings = Settings()

    # Verify all values are loaded correctly
    assert settings.supabase_url == config_env["SUPABASE_URL"]
    assert settings.supabase_key == config_env["SUPABASE_KEY"]
    assert settings.discord_token == config_env["DISCORD_TOKEN"]
    assert settings.discord_client_id == config_env["DISCORD_CLIENT_ID"]
    assert settings.discord_client_secret == config_env["DISCORD_CLIENT_SECRET"]
    assert settings.discord_redirect_uri == config_env["DISCORD_REDIRECT_URI"]
    assert settings.groq_api_key == config_env["GROQ_API_KEY"]
    assert settings.jwt_secret == config_env["JWT_SECRET"]
    assert settings.cors_origins == config_env["CORS_ORIGINS"]


# ============================================================================
# Property 5: Configuration Validation - Missing Values
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    missing_key=st.sampled_from(
        [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "DISCORD_TOKEN",
            "DISCORD_CLIENT_ID",
            "DISCORD_CLIENT_SECRET",
            "DISCORD_REDIRECT_URI",
            "GROQ_API_KEY",
            "JWT_SECRET",
            "CORS_ORIGINS",
        ]
    ),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_missing_required_config_fails_fast(config_env, missing_key, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any required configuration value that is missing or invalid at startup,
    the Config Manager SHALL fail immediately with a clear error message
    identifying the missing/invalid configuration.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from pydantic_core import ValidationError

    from app.core.config import Settings

    # Disable .env file loading to ensure we only use monkeypatched values
    monkeypatch.setenv("SKIP_CONFIG_LOAD", "1")

    # Set all environment variables except the missing one
    for key, value in config_env.items():
        if key != missing_key:
            monkeypatch.setenv(key, value)
        else:
            # Explicitly set to empty string to override .env file
            monkeypatch.setenv(key, "")

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, ValidationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions the missing key or indicates a required field
    error_msg = str(exc_info.value).upper()
    assert (
        missing_key.upper() in error_msg
        or "REQUIRED" in error_msg
        or "MISSING" in error_msg
        or "FIELD REQUIRED" in error_msg
    )


# ============================================================================
# Property 5: Configuration Validation - Invalid URL Format
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    invalid_url=st.one_of(
        st.just(""),
        st.just("http://invalid.com"),  # Not HTTPS
        st.just("https://notsupabase.com"),  # Not supabase.co
        st.text(
            alphabet=st.characters(blacklist_characters=":/"), min_size=1, max_size=20
        ),  # No protocol
    ),
)
@settings(
    max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_invalid_supabase_url_fails_fast(config_env, invalid_url, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any required configuration value that is invalid at startup,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Set all environment variables with invalid SUPABASE_URL
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SUPABASE_URL", invalid_url)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message is clear and actionable
    error_msg = str(exc_info.value)
    assert "SUPABASE_URL" in error_msg or "supabase" in error_msg.lower()


# ============================================================================
# Property 5: Configuration Validation - Short Keys
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    key_field=st.sampled_from(
        [
            ("SUPABASE_KEY", 20),
            ("DISCORD_TOKEN", 50),
            ("DISCORD_CLIENT_SECRET", 20),
            ("JWT_SECRET", 32),
        ]
    ),
)
@settings(
    max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_short_keys_fail_fast(config_env, key_field, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any required configuration value that is too short (invalid),
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    field_name, min_length = key_field

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)

    # Set the field to a short value (below minimum)
    short_value = "a" * (min_length - 1)
    monkeypatch.setenv(field_name, short_value)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions the field
    error_msg = str(exc_info.value)
    assert field_name in error_msg or field_name.lower() in error_msg.lower()


# ============================================================================
# Property 5: Configuration Validation - Invalid Discord Client ID
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    invalid_client_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),  # Letters only, no digits
        min_size=5,
        max_size=20,
    ),
)
@settings(
    max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_non_numeric_discord_client_id_fails(config_env, invalid_client_id, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any DISCORD_CLIENT_ID that is not numeric,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Ensure the client ID is not numeric
    assume(not invalid_client_id.isdigit())

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DISCORD_CLIENT_ID", invalid_client_id)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions Discord client ID or numeric requirement
    error_msg = str(exc_info.value)
    assert "DISCORD_CLIENT_ID" in error_msg or "numeric" in error_msg.lower()


# ============================================================================
# Property 5: Configuration Validation - Invalid Groq API Key
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    invalid_groq_key=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=20, max_size=50
    ),
)
@settings(
    max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_invalid_groq_api_key_prefix_fails(config_env, invalid_groq_key, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any GROQ_API_KEY that doesn't start with 'gsk_',
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Ensure the key doesn't start with gsk_
    assume(not invalid_groq_key.startswith("gsk_"))

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GROQ_API_KEY", invalid_groq_key)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions Groq API key or gsk_ prefix
    error_msg = str(exc_info.value)
    assert "GROQ_API_KEY" in error_msg or "gsk_" in error_msg


# ============================================================================
# Property 5: Configuration Validation - Insecure JWT Secret
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    insecure_pattern=st.sampled_from(["change", "secret", "password", "example", "test", "demo"]),
)
@settings(
    max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_insecure_jwt_secret_fails(config_env, insecure_pattern, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any JWT_SECRET that contains insecure patterns,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)

    # Create an insecure JWT secret with the pattern
    insecure_secret = f"my_{insecure_pattern}_key_for_jwt_authentication_system"
    monkeypatch.setenv("JWT_SECRET", insecure_secret)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions JWT secret or security concern
    error_msg = str(exc_info.value).lower()
    assert "jwt_secret" in error_msg or "placeholder" in error_msg or "insecure" in error_msg


# ============================================================================
# Property 5: Configuration Validation - Invalid CORS Origins
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    invalid_cors=st.text(
        alphabet=st.characters(blacklist_characters=":/" + "\x00"), min_size=5, max_size=20
    ),
)
@settings(
    max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_invalid_cors_origins_fails(config_env, invalid_cors, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any CORS_ORIGINS that doesn't start with http:// or https://,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Ensure the CORS origin is invalid (no protocol)
    assume(not invalid_cors.startswith("http://") and not invalid_cors.startswith("https://"))

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("CORS_ORIGINS", invalid_cors)

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions CORS or origin
    error_msg = str(exc_info.value).lower()
    assert "cors" in error_msg or "origin" in error_msg


# ============================================================================
# Property 5: Configuration Validation - Production Environment
# ============================================================================


@given(
    config_env=valid_config_env_strategy(),
    prod_violation=st.sampled_from(
        [
            ("COOKIE_SECURE", "false"),
            ("CORS_ORIGINS", "http://localhost:3000"),
            ("DISCORD_REDIRECT_URI", "http://example.com/callback"),
        ]
    ),
)
@settings(
    max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_5_production_validation_fails(config_env, prod_violation, monkeypatch):
    """
    **Property 5: Configuration Validation**

    For any production environment with insecure configuration,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    field_name, invalid_value = prod_violation

    # Set all environment variables for production
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("APP_ENV", "prod")

    # Set the violating field
    monkeypatch.setenv(field_name, invalid_value)

    # Fix other production requirements to isolate the violation
    if field_name != "COOKIE_SECURE":
        monkeypatch.setenv("COOKIE_SECURE", "true")
    if field_name != "CORS_ORIGINS":
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
    if field_name != "DISCORD_REDIRECT_URI":
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "https://example.com/callback")

    # Attempt to load settings - should fail
    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Verify error message mentions production or the specific field
    error_msg = str(exc_info.value).lower()
    assert "production" in error_msg or field_name.lower() in error_msg
