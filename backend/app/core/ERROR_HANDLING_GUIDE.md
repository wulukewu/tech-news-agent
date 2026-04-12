# Unified Error Handling System Guide

## Overview

The unified error handling system provides consistent error responses, standard error codes, and error recovery strategies across the Tech News Agent backend.

**Validates: Requirements 4.1, 4.2, 4.4, 4.5**

## Quick Start

### Basic Usage

```python
from app.core.errors import (
    AppException,
    AuthenticationError,
    DatabaseError,
    NotFoundError,
    ErrorCode
)

# Raise a specific error
raise NotFoundError(
    message="Feed not found",
    details={"feed_id": feed_id}
)

# Raise a custom error
raise AppException(
    message="Custom error occurred",
    error_code=ErrorCode.INTERNAL_ERROR,
    status_code=500,
    details={"context": "additional info"}
)
```

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Feed not found",
    "details": {
      "feed_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }
}
```

## Error Codes

Error codes follow the format: `CATEGORY_SPECIFIC_ERROR`

### Authentication & Authorization (401, 403)

- `AUTH_INVALID_TOKEN` - Invalid or malformed token
- `AUTH_TOKEN_EXPIRED` - Token has expired
- `AUTH_MISSING_TOKEN` - No token provided
- `AUTH_INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `AUTH_OAUTH_FAILED` - OAuth authentication failed

### Database (500)

- `DB_CONNECTION_FAILED` - Cannot connect to database
- `DB_QUERY_FAILED` - Database query failed
- `DB_CONSTRAINT_VIOLATION` - Database constraint violated
- `DB_TRANSACTION_FAILED` - Transaction failed

### Validation (422)

- `VALIDATION_FAILED` - General validation error
- `VALIDATION_MISSING_FIELD` - Required field missing
- `VALIDATION_INVALID_FORMAT` - Invalid field format
- `VALIDATION_BUSINESS_RULE` - Business rule violation

### External Services (502, 503)

- `EXTERNAL_SERVICE_UNAVAILABLE` - External service unavailable
- `EXTERNAL_SERVICE_TIMEOUT` - External service timeout
- `EXTERNAL_API_ERROR` - External API error
- `EXTERNAL_RSS_FETCH_FAILED` - RSS feed fetch failed
- `EXTERNAL_LLM_ERROR` - LLM service error
- `EXTERNAL_DISCORD_ERROR` - Discord API error

### Resources (404)

- `NOT_FOUND` - Generic not found
- `RESOURCE_NOT_FOUND` - Specific resource not found

### Rate Limiting (429)

- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded

### Configuration (500)

- `CONFIG_MISSING` - Required configuration missing
- `CONFIG_INVALID` - Invalid configuration

### Internal (500)

- `INTERNAL_ERROR` - Generic internal error
- `INTERNAL_UNEXPECTED` - Unexpected error

## Exception Classes

### Base Exception

```python
from app.core.errors import AppException, ErrorCode

raise AppException(
    message="User-friendly error message",
    error_code=ErrorCode.INTERNAL_ERROR,
    status_code=500,
    details={"key": "value"},  # Optional
    original_error=original_exception  # Optional
)
```

### Specific Exceptions

#### AuthenticationError (401)

```python
from app.core.errors import AuthenticationError, ErrorCode

raise AuthenticationError(
    message="Invalid token",
    error_code=ErrorCode.AUTH_INVALID_TOKEN
)
```

#### AuthorizationError (403)

```python
from app.core.errors import AuthorizationError

raise AuthorizationError(
    message="Insufficient permissions",
    details={"required_role": "admin"}
)
```

#### NotFoundError (404)

```python
from app.core.errors import NotFoundError

raise NotFoundError(
    message="Feed not found",
    details={"feed_id": feed_id}
)
```

#### ValidationError (422)

```python
from app.core.errors import ValidationError, ErrorCode

raise ValidationError(
    message="Invalid email format",
    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
    details={"field": "email", "value": email}
)
```

#### DatabaseError (500)

```python
from app.core.errors import DatabaseError, ErrorCode

try:
    # Database operation
    result = await db.query(...)
except Exception as e:
    raise DatabaseError(
        message="Failed to fetch user data",
        error_code=ErrorCode.DB_QUERY_FAILED,
        original_error=e
    )
```

#### ExternalServiceError (502, 503)

```python
from app.core.errors import ExternalServiceError, ErrorCode

raise ExternalServiceError(
    message="LLM service unavailable",
    error_code=ErrorCode.EXTERNAL_LLM_ERROR,
    status_code=503
)
```

#### RateLimitError (429)

```python
from app.core.errors import RateLimitError

raise RateLimitError(
    message="Too many requests",
    details={"retry_after": 60}
)
```

## Error Recovery Strategies

### Retry Strategy

Automatically retry operations that fail with transient errors.

```python
from app.core.errors import RetryStrategy, ExternalServiceError

# Create retry strategy
retry = RetryStrategy(
    max_attempts=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=60.0,
    retry_on=(ExternalServiceError, DatabaseError)
)

# Execute with retry
async def fetch_data():
    # ... operation that might fail
    pass

result = await retry.execute(fetch_data)
```

#### Using Decorator

```python
from app.core.errors import with_retry, ExternalServiceError

@with_retry(max_attempts=3, initial_delay=1.0)
async def fetch_rss_feed(url: str):
    # ... fetch RSS feed
    # Will automatically retry on ExternalServiceError or DatabaseError
    pass
```

### Fallback Strategy

Provide fallback value or function when operation fails.

```python
from app.core.errors import FallbackStrategy, ExternalServiceError

# Fallback with value
fallback = FallbackStrategy(
    fallback=[],  # Return empty list on failure
    fallback_on=(ExternalServiceError,)
)

result = await fallback.execute(get_recommendations)
```

#### Using Decorator

```python
from app.core.errors import with_fallback

@with_fallback(fallback=[])
async def get_recommendations(user_id: str):
    # ... fetch recommendations
    # Will return [] if operation fails
    pass
```

#### Fallback with Function

```python
from app.core.errors import with_fallback

async def get_default_recommendations():
    return ["default1", "default2"]

@with_fallback(fallback=get_default_recommendations)
async def get_personalized_recommendations(user_id: str):
    # ... fetch personalized recommendations
    # Will call get_default_recommendations() if operation fails
    pass
```

## FastAPI Integration

The error handlers are automatically registered in `app/main.py`:

```python
from app.core.errors import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

### In API Routes

```python
from fastapi import APIRouter, Depends
from app.core.errors import NotFoundError, DatabaseError, ErrorCode

router = APIRouter()

@router.get("/feeds/{feed_id}")
async def get_feed(feed_id: str):
    try:
        feed = await db.get_feed(feed_id)

        if not feed:
            raise NotFoundError(
                message="Feed not found",
                details={"feed_id": feed_id}
            )

        return {"data": feed}

    except Exception as e:
        raise DatabaseError(
            message="Failed to retrieve feed",
            error_code=ErrorCode.DB_QUERY_FAILED,
            original_error=e
        )
```

## Logging Integration

All errors are automatically logged with appropriate severity:

- **500+ errors**: Logged as ERROR with full traceback
- **400-499 errors**: Logged as WARNING
- **Request context**: Automatically included (request_id, user_id, path, method)

```python
# Errors are automatically logged by exception handlers
raise DatabaseError("Database query failed")

# Log output:
# {
#   "timestamp": "2024-01-15T10:30:00Z",
#   "level": "ERROR",
#   "logger": "app.api.feeds",
#   "message": "Server error: Database query failed",
#   "context": {
#     "request_id": "abc-123",
#     "user_id": "user-456"
#   },
#   "error_code": "DB_QUERY_FAILED",
#   "status_code": 500,
#   "path": "/api/feeds/123",
#   "method": "GET"
# }
```

## Migration from Legacy Exceptions

### Legacy Exception Classes

The following legacy exceptions are still supported but deprecated:

- `TechNewsException` → Use `AppException`
- `RSSScrapingError` → Use `ExternalServiceError` with `ErrorCode.EXTERNAL_RSS_FETCH_FAILED`
- `LLMServiceError` → Use `ExternalServiceError` with `ErrorCode.EXTERNAL_LLM_ERROR`
- `SupabaseServiceError` → Use `DatabaseError`

### Migration Helper

```python
from app.core.exceptions import convert_to_app_exception, RSSScrapingError

try:
    # Legacy code
    raise RSSScrapingError("Failed to fetch RSS")
except RSSScrapingError as e:
    # Convert to new exception
    new_exc = convert_to_app_exception(e)
    raise new_exc
```

### Gradual Migration Strategy

1. **Phase 1**: Keep legacy exceptions, add new error handling
2. **Phase 2**: Update new code to use new exceptions
3. **Phase 3**: Gradually migrate existing code
4. **Phase 4**: Remove legacy exceptions

## Best Practices

### 1. Use Specific Exception Classes

```python
# Good
raise NotFoundError(message="Feed not found")

# Avoid
raise AppException(message="Feed not found", error_code=ErrorCode.NOT_FOUND)
```

### 2. Include Helpful Details

```python
# Good
raise ValidationError(
    message="Invalid email format",
    details={
        "field": "email",
        "value": email,
        "expected_format": "user@example.com"
    }
)

# Avoid
raise ValidationError(message="Invalid email")
```

### 3. Preserve Original Errors

```python
# Good
try:
    result = await external_api.call()
except httpx.HTTPError as e:
    raise ExternalServiceError(
        message="External API failed",
        original_error=e  # Preserve for debugging
    )

# Avoid
try:
    result = await external_api.call()
except httpx.HTTPError:
    raise ExternalServiceError(message="External API failed")
```

### 4. Use Recovery Strategies for Transient Errors

```python
# Good - Retry transient errors
@with_retry(max_attempts=3)
async def fetch_rss_feed(url: str):
    return await httpx.get(url)

# Good - Fallback for non-critical features
@with_fallback(fallback=[])
async def get_recommendations(user_id: str):
    return await recommendation_service.get(user_id)
```

### 5. Don't Catch and Re-raise Without Adding Value

```python
# Avoid
try:
    result = await db.query()
except Exception as e:
    raise e  # No value added

# Good
try:
    result = await db.query()
except Exception as e:
    raise DatabaseError(
        message="Failed to fetch user data",
        details={"user_id": user_id},
        original_error=e
    )
```

## Testing

### Testing Exception Handling

```python
import pytest
from app.core.errors import NotFoundError, ErrorCode

def test_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        raise NotFoundError(
            message="Feed not found",
            details={"feed_id": "123"}
        )

    exc = exc_info.value
    assert exc.status_code == 404
    assert exc.error_code == ErrorCode.RESOURCE_NOT_FOUND
    assert exc.details["feed_id"] == "123"
```

### Testing Retry Strategy

```python
import pytest
from app.core.errors import RetryStrategy, ExternalServiceError

@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    call_count = 0

    async def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ExternalServiceError("Transient error")
        return "success"

    strategy = RetryStrategy(max_attempts=3, initial_delay=0.01)
    result = await strategy.execute(failing_then_success)

    assert result == "success"
    assert call_count == 3
```

## API Documentation

Error responses are automatically documented in OpenAPI/Swagger:

- Visit `/docs` to see interactive API documentation
- All error responses follow the standard format
- Error codes are documented in response examples

## Summary

The unified error handling system provides:

✅ **Consistent error responses** across all endpoints
✅ **Standard error codes** for easy identification
✅ **Automatic logging** with request context
✅ **Error recovery strategies** (retry, fallback)
✅ **Type-safe exception classes**
✅ **FastAPI integration** with automatic handlers
✅ **Backward compatibility** with legacy exceptions

For questions or issues, refer to the test suite in `tests/test_core_errors.py`.
