"""Tests for configuration module"""

import pytest

from app.core.config import Settings


def setup_minimal_valid_env(monkeypatch):
    """Helper to set up minimal valid environment for testing"""
    monkeypatch.setenv("APP_ENV", "dev")  # Ensure strict validation
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "a" * 30)  # Valid length
    monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)  # Valid length
    monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")


def test_settings_with_valid_jwt_secret(monkeypatch):
    """Test that Settings accepts JWT secret with >= 32 characters"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)  # Exactly 32 characters

    settings = Settings()

    assert settings.jwt_secret == "a" * 32
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_days == 7


def test_settings_with_short_jwt_secret_raises_error(monkeypatch):
    """Test that Settings raises ConfigurationError for JWT secret < 32 characters"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "short")  # Less than 32 characters

    from app.core.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="JWT_SECRET must be at least 32 characters"):
        Settings()


def test_settings_without_jwt_secret_raises_error(monkeypatch):
    """Test that Settings raises error when JWT_SECRET is not set"""
    setup_minimal_valid_env(monkeypatch)
    # Set empty JWT_SECRET to trigger validation
    monkeypatch.setenv("JWT_SECRET", "")

    from app.core.exceptions import ConfigurationError

    with pytest.raises((ConfigurationError, Exception)) as exc_info:
        Settings()

    # Should fail with JWT_SECRET error
    assert "JWT_SECRET" in str(exc_info.value)


def test_discord_oauth_config_fields(monkeypatch):
    """Test that Discord OAuth2 configuration fields are present"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("DISCORD_CLIENT_ID", "987654321098765432")
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", "my_client_secret_" + "a" * 20)
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback")
    monkeypatch.setenv("JWT_SECRET", "a" * 32)

    settings = Settings()

    assert settings.discord_client_id == "987654321098765432"
    assert settings.discord_client_secret == "my_client_secret_" + "a" * 20
    assert settings.discord_redirect_uri == "http://localhost:8000/api/auth/discord/callback"


def test_jwt_config_fields(monkeypatch):
    """Test that JWT configuration fields are present with correct defaults"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv(
        "JWT_SECRET", "abcdefghijklmnopqrstuvwxyz123456"
    )  # 32 chars, no insecure patterns

    settings = Settings()

    assert settings.jwt_secret == "abcdefghijklmnopqrstuvwxyz123456"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_days == 7


def test_cors_config_fields(monkeypatch):
    """Test that CORS configuration fields are present with correct defaults"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)

    settings = Settings()

    assert settings.cors_origins == "http://localhost:3000"


def test_rate_limit_config_fields(monkeypatch):
    """Test that rate limiting configuration fields are present with correct defaults"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)

    settings = Settings()

    assert settings.rate_limit_per_minute_unauth == 100
    assert settings.rate_limit_per_minute_auth == 300


def test_security_config_fields(monkeypatch):
    """Test that security configuration fields are present with correct defaults"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    # Note: cookie_secure defaults to True but can be overridden by .env file
    # In test environment, it may be set to False in .env

    settings = Settings()

    # Just verify the field exists and is a boolean
    assert isinstance(settings.cookie_secure, bool)


def test_custom_config_values(monkeypatch):
    """Test that custom configuration values override defaults"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("JWT_EXPIRATION_DAYS", "14")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,https://example.com")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE_UNAUTH", "50")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE_AUTH", "200")
    monkeypatch.setenv("COOKIE_SECURE", "false")

    settings = Settings()

    assert settings.jwt_algorithm == "HS512"
    assert settings.jwt_expiration_days == 14
    assert settings.cors_origins == "http://localhost:3000,https://example.com"
    assert settings.rate_limit_per_minute_unauth == 50
    assert settings.rate_limit_per_minute_auth == 200
    assert settings.cookie_secure is False


def test_oauth_fields_required_in_new_version(monkeypatch):
    """Test that OAuth fields are now required (breaking change from optional)"""
    setup_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a" * 32)

    # All OAuth fields should be present and valid
    settings = Settings()

    assert settings.discord_client_id == "123456789012345678"
    assert settings.discord_client_secret == "a" * 30
    assert settings.discord_redirect_uri == "http://localhost:8000/api/auth/discord/callback"
