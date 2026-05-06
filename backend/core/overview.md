# Core Module

This module contains core functionality used throughout the backend application.

## Configuration Manager

The configuration manager (`config.py`) provides type-safe, validated configuration management with environment-specific support.

### Features

- **Type Safety**: Uses Pydantic Settings for automatic type validation
- **Environment-Specific Config**: Supports `.env.dev`, `.env.test`, `.env.prod`
- **Comprehensive Validation**: Validates all required fields with clear error messages
- **Fail-Fast Behavior**: Application fails immediately on startup if configuration is invalid
- **Clear Error Messages**: Provides actionable guidance for fixing configuration issues

### Usage

#### Basic Usage

```python
from app.core.config import settings

# Access configuration values
database_url = settings.supabase_url
api_key = settings.groq_api_key
```

#### Environment-Specific Configuration

Set the `APP_ENV` environment variable to load environment-specific configuration:

```bash
# Development (default)
APP_ENV=dev python -m uvicorn app.main:app

# Testing
APP_ENV=test python -m pytest

# Production
APP_ENV=prod python -m uvicorn app.main:app
```

The configuration manager will load files in this priority:

1. `.env.{APP_ENV}` (e.g., `.env.prod`)
2. `.env` (fallback)

### Configuration Files

Example configuration files are provided for each environment:

- `.env.dev.example` - Development environment
- `.env.test.example` - Testing environment
- `.env.prod.example` - Production environment

Copy the appropriate example file and fill in your values:

```bash
cp .env.dev.example .env.dev
# Edit .env.dev with your values
```

### Required Configuration

The following configuration values are **required** and will cause the application to fail if missing or invalid:

#### Supabase

- `SUPABASE_URL` - Must be a valid Supabase URL (https://\*.supabase.co)
- `SUPABASE_KEY` - Service role key (minimum 20 characters)

#### Discord

- `DISCORD_TOKEN` - Bot token (minimum 50 characters)
- `DISCORD_CLIENT_ID` - OAuth2 client ID (numeric)
- `DISCORD_CLIENT_SECRET` - OAuth2 client secret (minimum 20 characters)
- `DISCORD_REDIRECT_URI` - OAuth2 callback URL (must include /callback)

#### LLM

- `GROQ_API_KEY` - Groq API key (must start with 'gsk\_')

#### Security

- `JWT_SECRET` - JWT signing secret (minimum 32 characters, no common patterns)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated URLs)

### Validation Rules

#### Development Environment (`APP_ENV=dev`)

- `COOKIE_SECURE` can be `false`
- `CORS_ORIGINS` can include `localhost`
- `DISCORD_REDIRECT_URI` can use `http://`

#### Production Environment (`APP_ENV=prod`)

- `COOKIE_SECURE` **must** be `true`
- `CORS_ORIGINS` **must not** include `localhost`
- `DISCORD_REDIRECT_URI` **must** use `https://`
- `JWT_SECRET` **must not** contain common insecure patterns

### Error Messages

The configuration manager provides clear, actionable error messages:

```
ConfigurationError: JWT_SECRET must be at least 32 characters for security.
Current length: 16. Generate a secure one with: openssl rand -hex 32
```

```
ConfigurationError: SUPABASE_URL must be a valid Supabase URL. Got: http://invalid.com
Get it from: https://supabase.com/dashboard > Settings > API > Project URL
```

### Testing

Comprehensive tests are provided in:

- `tests/test_config.py` - Basic configuration tests
- `tests/test_config_validation.py` - Validation and error handling tests

Run tests:

```bash
python -m pytest backend/tests/test_config*.py -v
```

### Architecture

The configuration manager follows these design principles:

1. **Fail-Fast**: Invalid configuration causes immediate failure on import
2. **Type Safety**: Pydantic ensures type correctness at runtime
3. **Clear Errors**: Every validation error includes how to fix it
4. **Environment Awareness**: Different rules for dev/test/prod
5. **Single Source of Truth**: All configuration accessed through `settings` instance

### Related Requirements

This module validates:

- Requirement 6.1: Configuration loading from environment variables
- Requirement 6.3: Validation of required configuration values
- Requirement 6.4: Fail-fast behavior with clear error messages

## Exceptions

The `exceptions.py` module defines custom exception types used throughout the application:

- `TechNewsException` - Base exception for all application errors
- `ConfigurationError` - Configuration validation errors
- `RSSScrapingError` - RSS feed scraping errors
- `LLMServiceError` - LLM processing errors
- `SupabaseServiceError` - Database operation errors

### Usage

```python
from app.core.exceptions import ConfigurationError

if not valid_config:
    raise ConfigurationError(
        "Invalid configuration: missing required field. "
        "Check your .env file."
    )
```
