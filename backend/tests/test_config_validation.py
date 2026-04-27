"""
Tests for enhanced configuration validation

Validates: Requirements 6.1, 6.3, 6.4
"""

import pytest

from app.core.config import Settings, get_env_file
from app.core.exceptions import ConfigurationError


class TestConfigurationValidation:
    """Test configuration validation with fail-fast behavior"""

    def setup_valid_env(self, monkeypatch):
        """Helper to set up valid environment variables"""
        monkeypatch.setenv("APP_ENV", "dev")  # Ensure strict validation
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "a" * 30)  # Valid length
        monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)  # Valid length
        monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
        monkeypatch.setenv(
            "DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback"
        )
        monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    def test_valid_configuration_loads_successfully(self, monkeypatch):
        """Test that valid configuration loads without errors"""
        self.setup_valid_env(monkeypatch)

        settings = Settings()

        assert settings.supabase_url == "https://test.supabase.co"
        assert settings.discord_token == "a" * 60
        assert settings.jwt_secret == "a" * 32

    def test_missing_supabase_url_fails_fast(self, monkeypatch):
        """Test that empty SUPABASE_URL fails with clear error message"""
        self.setup_valid_env(monkeypatch)
        # Set empty value instead of deleting
        monkeypatch.setenv("SUPABASE_URL", "")

        with pytest.raises((ConfigurationError, Exception)) as exc_info:
            Settings()

        # Should fail during validation
        error_msg = str(exc_info.value)
        assert "SUPABASE_URL" in error_msg

    def test_invalid_supabase_url_format_fails(self, monkeypatch):
        """Test that invalid SUPABASE_URL format fails with clear error"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("SUPABASE_URL", "http://invalid.com")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        # Should fail on https:// check first
        assert "https://" in str(exc_info.value)

    def test_short_supabase_key_fails(self, monkeypatch):
        """Test that short SUPABASE_KEY fails with clear error"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("SUPABASE_KEY", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "SUPABASE_KEY" in str(exc_info.value)
        assert "service role key" in str(exc_info.value)

    def test_short_discord_token_fails(self, monkeypatch):
        """Test that short DISCORD_TOKEN fails with clear error"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("DISCORD_TOKEN", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "DISCORD_TOKEN" in str(exc_info.value)
        assert "too short" in str(exc_info.value)

    def test_non_numeric_discord_client_id_fails(self, monkeypatch):
        """Test that non-numeric DISCORD_CLIENT_ID fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("DISCORD_CLIENT_ID", "not_a_number")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "DISCORD_CLIENT_ID" in str(exc_info.value)
        assert "numeric" in str(exc_info.value)

    def test_short_discord_client_secret_fails(self, monkeypatch):
        """Test that short DISCORD_CLIENT_SECRET fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "DISCORD_CLIENT_SECRET" in str(exc_info.value)
        assert "too short" in str(exc_info.value)

    def test_invalid_discord_redirect_uri_fails(self, monkeypatch):
        """Test that invalid DISCORD_REDIRECT_URI fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "not_a_url")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "DISCORD_REDIRECT_URI" in str(exc_info.value)
        assert "http://" in str(exc_info.value) or "https://" in str(exc_info.value)

    def test_invalid_groq_api_key_prefix_fails(self, monkeypatch):
        """Test that GROQ_API_KEY without gsk_ prefix fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("GROQ_API_KEY", "invalid_key")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "GROQ_API_KEY" in str(exc_info.value)
        assert "gsk_" in str(exc_info.value)

    def test_short_jwt_secret_fails(self, monkeypatch):
        """Test that JWT_SECRET < 32 characters fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("JWT_SECRET", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "JWT_SECRET" in str(exc_info.value)
        assert "32 characters" in str(exc_info.value)

    def test_insecure_jwt_secret_fails(self, monkeypatch):
        """Test that insecure JWT_SECRET patterns fail"""
        self.setup_valid_env(monkeypatch)
        insecure_values = [
            "please_change_this_secret_key_now",
            "my_test_secret_key_for_development",
            "example_jwt_secret_key_32_chars_long",
        ]

        for insecure_value in insecure_values:
            monkeypatch.setenv("JWT_SECRET", insecure_value)

            with pytest.raises(ConfigurationError) as exc_info:
                Settings()

            assert (
                "placeholder" in str(exc_info.value).lower()
                or "insecure" in str(exc_info.value).lower()
            )

    def test_invalid_cors_origins_format_fails(self, monkeypatch):
        """Test that invalid CORS_ORIGINS format fails"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("CORS_ORIGINS", "not_a_url,also_not_a_url")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "CORS" in str(exc_info.value) or "origin" in str(exc_info.value).lower()

    def test_production_environment_validation(self, monkeypatch):
        """Test production-specific validation rules"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.setenv("COOKIE_SECURE", "false")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "COOKIE_SECURE" in str(exc_info.value)
        assert "production" in str(exc_info.value).lower()

    def test_production_localhost_cors_fails(self, monkeypatch):
        """Test that localhost in CORS_ORIGINS fails in production"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.setenv("COOKIE_SECURE", "true")  # Fix cookie_secure first
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
        monkeypatch.setenv(
            "DISCORD_REDIRECT_URI", "https://example.com/callback"
        )  # Fix redirect URI

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "localhost" in str(exc_info.value).lower()
        assert "production" in str(exc_info.value).lower()

    def test_production_http_redirect_uri_fails(self, monkeypatch):
        """Test that HTTP redirect URI fails in production"""
        self.setup_valid_env(monkeypatch)
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.setenv("COOKIE_SECURE", "true")  # Fix cookie_secure first
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")  # Fix CORS first
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://example.com/callback")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        assert "HTTPS" in str(exc_info.value) or "https" in str(exc_info.value)
        assert "production" in str(exc_info.value).lower()


class TestEnvironmentSpecificConfig:
    """Test environment-specific configuration file loading"""

    def test_get_env_file_defaults_to_dev(self, monkeypatch):
        """Test that get_env_file defaults to dev environment"""
        monkeypatch.delenv("APP_ENV", raising=False)

        env_file = get_env_file()

        # Should try .env.dev first, fall back to .env
        assert env_file in [".env.dev", ".env"]

    def test_get_env_file_respects_app_env(self, monkeypatch):
        """Test that get_env_file respects APP_ENV variable"""
        monkeypatch.setenv("APP_ENV", "prod")

        env_file = get_env_file()

        # Should try .env.prod first, fall back to .env
        assert env_file in [".env.prod", ".env"]

    def test_app_env_field_defaults_to_dev(self, monkeypatch):
        """Test that app_env field defaults to dev"""
        # Set up minimal valid config
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "a" * 30)
        monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)
        monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
        monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
        monkeypatch.setenv("JWT_SECRET", "a" * 32)

        settings = Settings()

        assert settings.app_env == "dev"

    def test_app_env_can_be_set(self, monkeypatch):
        """Test that app_env can be set via environment variable"""
        # Set up minimal valid config
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "a" * 30)
        monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)
        monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
        monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
        monkeypatch.setenv("JWT_SECRET", "a" * 32)

        settings = Settings()

        assert settings.app_env == "test"


class TestConfigurationErrorMessages:
    """Test that error messages are clear and actionable"""

    def test_error_messages_include_how_to_fix(self, monkeypatch):
        """Test that error messages include actionable guidance"""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "a" * 30)
        monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)
        monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
        monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
        monkeypatch.setenv("JWT_SECRET", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        error_message = str(exc_info.value)
        # Should include how to generate a secure key
        assert "openssl rand -hex 32" in error_message or "Generate" in error_message

    def test_error_messages_include_where_to_get_values(self, monkeypatch):
        """Test that error messages include where to get configuration values"""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "short")
        monkeypatch.setenv("DISCORD_TOKEN", "a" * 60)
        monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
        monkeypatch.setenv("DISCORD_CLIENT_SECRET", "a" * 30)
        monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
        monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "a" * 30)
        monkeypatch.setenv("JWT_SECRET", "a" * 32)

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        error_message = str(exc_info.value)
        # Should include where to get the value
        assert "supabase.com" in error_message.lower() or "Get it from" in error_message
