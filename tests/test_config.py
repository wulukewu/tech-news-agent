"""Tests for configuration module"""
import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_settings_with_valid_jwt_secret(monkeypatch):
    """Test that Settings accepts JWT secret with >= 32 characters"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("DISCORD_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
    monkeypatch.setenv("JWT_SECRET", "a" * 32)  # Exactly 32 characters
    
    settings = Settings()
    settings.validate_jwt_secret()  # Should not raise
    
    assert settings.jwt_secret == "a" * 32
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_days == 7


def test_settings_with_short_jwt_secret_raises_error(monkeypatch):
    """Test that Settings raises ValueError for JWT secret < 32 characters"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("JWT_SECRET", "short")  # Less than 32 characters
    
    settings = Settings()
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters"):
        settings.validate_jwt_secret()


def test_settings_without_jwt_secret_raises_error(monkeypatch):
    """Test that validate_jwt_secret raises ValueError when JWT_SECRET is not set"""
    # Set all required environment variables except JWT_SECRET
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    settings = Settings()
    with pytest.raises(ValueError, match="JWT_SECRET is required"):
        settings.validate_jwt_secret()


def test_discord_oauth_config_fields(monkeypatch):
    """Test that Discord OAuth2 configuration fields are present"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("DISCORD_CLIENT_ID", "my_client_id")
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", "my_client_secret")
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback")
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    
    settings = Settings()
    
    assert settings.discord_client_id == "my_client_id"
    assert settings.discord_client_secret == "my_client_secret"
    assert settings.discord_redirect_uri == "http://localhost:8000/api/auth/discord/callback"


def test_jwt_config_fields(monkeypatch):
    """Test that JWT configuration fields are present with correct defaults"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("JWT_SECRET", "my_super_secret_jwt_key_32chars")
    
    settings = Settings()
    
    assert settings.jwt_secret == "my_super_secret_jwt_key_32chars"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_days == 7


def test_cors_config_fields(monkeypatch):
    """Test that CORS configuration fields are present with correct defaults"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    settings = Settings()
    
    assert settings.cors_origins == "http://localhost:3000"


def test_rate_limit_config_fields(monkeypatch):
    """Test that rate limiting configuration fields are present with correct defaults"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    settings = Settings()
    
    assert settings.rate_limit_per_minute_unauth == 100
    assert settings.rate_limit_per_minute_auth == 300


def test_security_config_fields(monkeypatch):
    """Test that security configuration fields are present with correct defaults"""
    # Set all required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    settings = Settings()
    
    assert settings.cookie_secure is True


def test_custom_config_values(monkeypatch):
    """Test that custom configuration values override defaults"""
    # Set all required environment variables with custom values
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
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


def test_oauth_fields_optional_for_backward_compatibility(monkeypatch):
    """Test that OAuth fields are optional for backward compatibility"""
    # Set only the original required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    # Should not raise ValidationError
    settings = Settings()
    
    # OAuth fields should be None
    assert settings.discord_client_id is None
    assert settings.discord_client_secret is None
    assert settings.discord_redirect_uri is None
    assert settings.jwt_secret is None
