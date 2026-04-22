"""
Centralized Configuration Manager

This module provides type-safe configuration management with environment-specific
support and comprehensive validation.

Validates: Requirements 6.1, 6.3, 6.4
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """
    Type-safe configuration settings using Pydantic.

    Supports environment-specific configuration files:
    - .env (default)
    - .env.dev (development)
    - .env.test (testing)
    - .env.prod (production)

    Environment is determined by APP_ENV variable (defaults to 'dev').
    """

    # Environment Configuration
    app_env: Literal["dev", "test", "prod"] = "dev"

    # Supabase Configuration (Required)
    supabase_url: str
    supabase_key: str

    # Discord Configuration (Required)
    discord_token: str
    discord_channel_id: int | None = None  # Optional: DM notifications used instead

    # Discord OAuth2 Configuration (Required for authentication)
    discord_client_id: str
    discord_client_secret: str
    discord_redirect_uri: str

    # LLM (Groq) Configuration (Required)
    groq_api_key: str

    # Timezone Configuration
    timezone: str = "Asia/Taipei"

    # RSS Configuration
    rss_fetch_days: int = 7

    # Scheduler Configuration
    scheduler_cron: str = "0 * * * *"  # Every hour by default (有去重機制，不會增加 LLM 用量)
    scheduler_timezone: str | None = None  # Defaults to timezone if not set

    # Batch Processing Configuration
    batch_size: int = 50  # Maximum articles per batch
    batch_split_threshold: int = 100  # Split into multiple batches above this

    # JWT Configuration (Required)
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # CORS Configuration
    cors_origins: str = "http://localhost:3000"  # Comma-separated list

    # Rate Limiting Configuration
    rate_limit_per_minute_unauth: int = 100
    rate_limit_per_minute_auth: int = 300

    # Security Configuration
    cookie_secure: bool = True  # Use HTTPS in production

    # Frontend Configuration (Required for OAuth redirects)
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Validate Supabase URL format."""
        if not v:
            raise ConfigurationError(
                "SUPABASE_URL is required. "
                "Get it from: https://supabase.com/dashboard > Settings > API > Project URL"
            )
        if not v.startswith("https://"):
            raise ConfigurationError(f"SUPABASE_URL must start with 'https://'. Got: {v}")
        # Check for valid Supabase domain (must end with .supabase.co)
        if not (".supabase.co" in v and v.split("//")[1].endswith(".supabase.co")):
            raise ConfigurationError(
                f"SUPABASE_URL must be a valid Supabase URL (*.supabase.co). Got: {v}"
            )
        return v

    @field_validator("supabase_key")
    @classmethod
    def validate_supabase_key(cls, v: str) -> str:
        """Validate Supabase key is not empty."""
        if not v or len(v) < 20:
            raise ConfigurationError(
                "SUPABASE_KEY is required and must be a valid service role key. "
                "Get it from: https://supabase.com/dashboard > Settings > API > service_role key"
            )
        return v

    @field_validator("discord_token")
    @classmethod
    def validate_discord_token(cls, v: str) -> str:
        """Validate Discord bot token format."""
        if not v:
            raise ConfigurationError(
                "DISCORD_TOKEN is required. "
                "Get it from: https://discord.com/developers/applications > Bot > Token"
            )
        if len(v) < 50:
            raise ConfigurationError(
                f"DISCORD_TOKEN appears invalid (too short). Expected length > 50, got: {len(v)}"
            )
        return v

    @field_validator("discord_client_id")
    @classmethod
    def validate_discord_client_id(cls, v: str) -> str:
        """Validate Discord OAuth2 client ID."""
        if not v:
            raise ConfigurationError(
                "DISCORD_CLIENT_ID is required for OAuth2 authentication. "
                "Get it from: https://discord.com/developers/applications > OAuth2 > Client ID"
            )
        if not v.isdigit():
            raise ConfigurationError(f"DISCORD_CLIENT_ID must be numeric. Got: {v}")
        return v

    @field_validator("discord_client_secret")
    @classmethod
    def validate_discord_client_secret(cls, v: str) -> str:
        """Validate Discord OAuth2 client secret."""
        if not v:
            raise ConfigurationError(
                "DISCORD_CLIENT_SECRET is required for OAuth2 authentication. "
                "Get it from: https://discord.com/developers/applications > OAuth2 > Client Secret"
            )
        if len(v) < 20:
            raise ConfigurationError(
                f"DISCORD_CLIENT_SECRET appears invalid (too short). Expected length > 20, got: {len(v)}"
            )
        return v

    @field_validator("discord_redirect_uri")
    @classmethod
    def validate_discord_redirect_uri(cls, v: str) -> str:
        """Validate Discord OAuth2 redirect URI."""
        if not v:
            raise ConfigurationError(
                "DISCORD_REDIRECT_URI is required for OAuth2 authentication. "
                "Example: http://localhost:8000/api/auth/discord/callback"
            )
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ConfigurationError(
                f"DISCORD_REDIRECT_URI must start with http:// or https://. Got: {v}"
            )
        if "/callback" not in v:
            raise ConfigurationError(f"DISCORD_REDIRECT_URI should contain '/callback'. Got: {v}")
        return v

    @field_validator("groq_api_key")
    @classmethod
    def validate_groq_api_key(cls, v: str) -> str:
        """Validate Groq API key."""
        if not v:
            raise ConfigurationError(
                "GROQ_API_KEY is required for LLM processing. "
                "Get it from: https://console.groq.com/keys"
            )
        if not v.startswith("gsk_"):
            raise ConfigurationError(f"GROQ_API_KEY should start with 'gsk_'. Got: {v[:10]}...")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret strength."""
        if not v:
            raise ConfigurationError(
                "JWT_SECRET is required for authentication. "
                "Generate one with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ConfigurationError(
                f"JWT_SECRET must be at least 32 characters for security. "
                f"Current length: {len(v)}. Generate a secure one with: openssl rand -hex 32"
            )
        # Warn about common insecure values
        insecure_patterns = ["change", "secret", "password", "example", "test", "demo"]
        if any(pattern in v.lower() for pattern in insecure_patterns):
            raise ConfigurationError(
                "JWT_SECRET appears to be a placeholder or insecure value. "
                "Generate a secure one with: openssl rand -hex 32"
            )
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v:
            raise ConfigurationError("CORS_ORIGINS is required. Example: http://localhost:3000")
        # Validate each origin
        origins = [origin.strip() for origin in v.split(",")]
        for origin in origins:
            if not (origin.startswith("http://") or origin.startswith("https://")):
                raise ConfigurationError(
                    f"CORS origin must start with http:// or https://. Got: {origin}"
                )
        return v

    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, v: str) -> str:
        """Validate frontend URL format."""
        if not v:
            raise ConfigurationError(
                "FRONTEND_URL is required for OAuth redirects. Example: http://localhost:3000"
            )
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ConfigurationError(f"FRONTEND_URL must start with http:// or https://. Got: {v}")
        # Remove trailing slash for consistency
        return v.rstrip("/")

    @model_validator(mode="after")
    def validate_environment_specific_settings(self) -> "Settings":
        """Validate environment-specific configuration requirements."""
        # Production-specific validations
        if self.app_env == "prod":
            if not self.cookie_secure:
                raise ConfigurationError(
                    "COOKIE_SECURE must be true in production environment for security"
                )
            if "localhost" in self.cors_origins:
                raise ConfigurationError(
                    "CORS_ORIGINS should not include localhost in production environment"
                )
            if "http://" in self.discord_redirect_uri:
                raise ConfigurationError(
                    "DISCORD_REDIRECT_URI must use HTTPS in production environment"
                )
            if "localhost" in self.frontend_url:
                raise ConfigurationError(
                    "FRONTEND_URL should not include localhost in production environment"
                )
            if "http://" in self.frontend_url:
                raise ConfigurationError("FRONTEND_URL must use HTTPS in production environment")

        # Test-specific validations
        if self.app_env == "test":
            # Test environment can be more lenient
            pass

        return self


def get_env_file() -> str:
    """
    Determine which .env file to load based on APP_ENV.

    Priority:
    1. ../.env.{APP_ENV} (e.g., ../.env.prod)
    2. ../.env (default, in project root)

    Returns:
        Path to the environment file to load
    """
    app_env = os.getenv("APP_ENV", "dev")
    env_file = f"../.env.{app_env}"

    # Check if environment-specific file exists
    if Path(env_file).exists():
        return env_file

    # Fall back to default .env in project root
    return "../.env"


def load_settings() -> Settings:
    """
    Load and validate settings with fail-fast behavior.

    This function provides clear error messages for configuration issues
    and fails immediately if required values are missing or invalid.

    Returns:
        Validated Settings instance

    Raises:
        ConfigurationError: If configuration is invalid or incomplete
    """
    try:
        # Determine which env file to use
        env_file = get_env_file()

        # Update model_config to use the correct env file
        Settings.model_config["env_file"] = env_file

        # Load and validate settings
        settings_instance = Settings()

        return settings_instance

    except ConfigurationError:
        # Re-raise our custom configuration errors
        raise
    except Exception as e:
        # Wrap other errors in ConfigurationError with helpful message
        raise ConfigurationError(
            f"Failed to load configuration: {e!s}. "
            f"Check your .env file and ensure all required variables are set."
        ) from e


# Global settings instance
# This will fail fast on import if configuration is invalid
settings: Settings | None = None

try:
    if os.getenv("SKIP_CONFIG_LOAD") != "1":
        settings = load_settings()
        if settings is None:
            raise ConfigurationError("Settings loaded but returned None")
except ConfigurationError as e:
    # Log the specific configuration error
    import sys

    print(f"Configuration Error: {e}", file=sys.stderr)
    # In production, we want to fail fast
    if os.getenv("APP_ENV") == "prod":
        raise
    # In development/test, allow the module to load
    settings = None
except Exception as e:
    # Log unexpected errors
    import sys

    print(f"Unexpected error loading configuration: {e}", file=sys.stderr)
    # In production, we want to fail fast
    if os.getenv("APP_ENV") == "prod":
        raise ConfigurationError(
            f"Failed to load configuration: {e}. "
            "Ensure all required environment variables are set in your deployment platform."
        ) from e
    # In development/test, allow the module to load
    settings = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings instance

    Raises:
        ConfigurationError: If settings are not loaded or invalid
    """
    global settings
    if settings is None:
        settings = load_settings()
    return settings
