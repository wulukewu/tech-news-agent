"""
Unit Tests for Unified Error Handling System

Tests error codes, exception classes, FastAPI handlers, and recovery strategies.

Validates: Requirements 4.1, 4.2, 4.4, 4.5
"""

import asyncio

import pytest
from fastapi import status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    ErrorCode,
    ExternalServiceError,
    FallbackStrategy,
    NotFoundError,
    RateLimitError,
    RetryStrategy,
    ValidationError,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    with_fallback,
    with_retry,
)

# ============================================================================
# Test Error Codes
# ============================================================================


def test_error_codes_are_strings():
    """Error codes should be string enums."""
    assert isinstance(ErrorCode.AUTH_INVALID_TOKEN.value, str)
    assert isinstance(ErrorCode.DB_QUERY_FAILED.value, str)
    assert isinstance(ErrorCode.VALIDATION_FAILED.value, str)


def test_error_codes_follow_naming_convention():
    """Error codes should follow CATEGORY_SPECIFIC_ERROR format."""
    # Auth codes
    assert ErrorCode.AUTH_INVALID_TOKEN.value.startswith("AUTH_")
    assert ErrorCode.AUTH_TOKEN_EXPIRED.value.startswith("AUTH_")

    # Database codes
    assert ErrorCode.DB_CONNECTION_FAILED.value.startswith("DB_")
    assert ErrorCode.DB_QUERY_FAILED.value.startswith("DB_")

    # Validation codes
    assert ErrorCode.VALIDATION_FAILED.value.startswith("VALIDATION_")

    # External service codes
    assert ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE.value.startswith("EXTERNAL_")


# ============================================================================
# Test Base Exception Class
# ============================================================================


def test_app_exception_initialization():
    """AppException should initialize with all required fields."""
    exc = AppException(
        message="Test error",
        error_code=ErrorCode.INTERNAL_ERROR,
        status_code=500,
        details={"key": "value"},
    )

    assert exc.message == "Test error"
    assert exc.error_code == ErrorCode.INTERNAL_ERROR
    assert exc.status_code == 500
    assert exc.details == {"key": "value"}
    assert exc.original_error is None


def test_app_exception_to_dict():
    """AppException.to_dict() should return standardized error structure."""
    exc = AppException(
        message="Test error", error_code=ErrorCode.INTERNAL_ERROR, details={"field": "value"}
    )

    result = exc.to_dict()

    assert "error" in result
    assert result["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
    assert result["error"]["message"] == "Test error"
    assert result["error"]["details"] == {"field": "value"}


def test_app_exception_to_dict_without_details():
    """AppException.to_dict() should work without details."""
    exc = AppException(message="Test error", error_code=ErrorCode.INTERNAL_ERROR)

    result = exc.to_dict()

    assert "error" in result
    assert result["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
    assert result["error"]["message"] == "Test error"
    assert "details" not in result["error"]


def test_app_exception_str_representation():
    """AppException.__str__() should include all relevant information."""
    original = ValueError("Original error")
    exc = AppException(
        message="Test error",
        error_code=ErrorCode.INTERNAL_ERROR,
        details={"key": "value"},
        original_error=original,
    )

    str_repr = str(exc)

    assert "INTERNAL_ERROR" in str_repr
    assert "Test error" in str_repr
    assert "key" in str_repr
    assert "ValueError" in str_repr


# ============================================================================
# Test Specific Exception Classes
# ============================================================================


def test_authentication_error_defaults():
    """AuthenticationError should have correct defaults."""
    exc = AuthenticationError()

    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.error_code == ErrorCode.AUTH_INVALID_TOKEN
    assert "Authentication failed" in exc.message


def test_authorization_error_defaults():
    """AuthorizationError should have correct defaults."""
    exc = AuthorizationError()

    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.error_code == ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS


def test_not_found_error_defaults():
    """NotFoundError should have correct defaults."""
    exc = NotFoundError()

    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.error_code == ErrorCode.RESOURCE_NOT_FOUND


def test_validation_error_defaults():
    """ValidationError should have correct defaults."""
    exc = ValidationError()

    assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc.error_code == ErrorCode.VALIDATION_FAILED


def test_database_error_defaults():
    """DatabaseError should have correct defaults."""
    exc = DatabaseError()

    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.error_code == ErrorCode.DB_QUERY_FAILED


def test_external_service_error_defaults():
    """ExternalServiceError should have correct defaults."""
    exc = ExternalServiceError()

    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.error_code == ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE


def test_rate_limit_error_defaults():
    """RateLimitError should have correct defaults."""
    exc = RateLimitError()

    assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED


def test_configuration_error_defaults():
    """ConfigurationError should have correct defaults."""
    exc = ConfigurationError()

    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.error_code == ErrorCode.CONFIG_INVALID


# ============================================================================
# Test FastAPI Exception Handlers
# ============================================================================


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""

    class MockURL:
        path = "/api/test"

    class MockRequest:
        url = MockURL()
        method = "GET"

    return MockRequest()


@pytest.mark.asyncio
async def test_app_exception_handler_returns_json_response(mock_request):
    """app_exception_handler should return JSONResponse with error structure."""
    exc = AppException(message="Test error", error_code=ErrorCode.INTERNAL_ERROR, status_code=500)

    response = await app_exception_handler(mock_request, exc)

    assert response.status_code == 500
    # Response body is in response.body as bytes
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
    assert body["error"]["message"] == "Test error"


@pytest.mark.asyncio
async def test_http_exception_handler_converts_to_standard_format(mock_request):
    """http_exception_handler should convert HTTPException to standard format."""
    exc = StarletteHTTPException(status_code=404, detail="Not found")

    response = await http_exception_handler(mock_request, exc)

    assert response.status_code == 404
    import json

    body = json.loads(response.body)
    assert "error" in body
    assert body["error"]["code"] == ErrorCode.NOT_FOUND.value
    assert body["error"]["message"] == "Not found"


@pytest.mark.asyncio
async def test_validation_exception_handler_includes_field_errors(mock_request):
    """validation_exception_handler should include validation error details."""

    # Create a Pydantic model to generate validation errors
    class TestModel(BaseModel):
        name: str
        age: int

    try:
        TestModel(name=123, age="invalid")  # type: ignore
    except PydanticValidationError as pydantic_error:
        # Convert to RequestValidationError
        exc = RequestValidationError(errors=pydantic_error.errors())

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 422
        import json

        body = json.loads(response.body)
        assert body["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
        assert "validation_errors" in body["error"]["details"]
        assert len(body["error"]["details"]["validation_errors"]) > 0


@pytest.mark.asyncio
async def test_generic_exception_handler_catches_unexpected_errors(mock_request):
    """generic_exception_handler should handle unexpected exceptions."""
    exc = RuntimeError("Unexpected error")

    response = await generic_exception_handler(mock_request, exc)

    assert response.status_code == 500
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.INTERNAL_UNEXPECTED.value
    assert "unexpected error occurred" in body["error"]["message"].lower()


# ============================================================================
# Test Retry Strategy
# ============================================================================


@pytest.mark.asyncio
async def test_retry_strategy_succeeds_on_first_attempt():
    """RetryStrategy should return result on first successful attempt."""
    call_count = 0

    async def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"

    strategy = RetryStrategy(max_attempts=3)
    result = await strategy.execute(successful_func)

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_strategy_retries_on_failure():
    """RetryStrategy should retry on transient failures."""
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


@pytest.mark.asyncio
async def test_retry_strategy_raises_after_max_attempts():
    """RetryStrategy should raise exception after max attempts."""
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ExternalServiceError("Persistent error")

    strategy = RetryStrategy(max_attempts=3, initial_delay=0.01)

    with pytest.raises(ExternalServiceError):
        await strategy.execute(always_fails)

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_strategy_exponential_backoff():
    """RetryStrategy should use exponential backoff."""
    call_times = []

    async def failing_func():
        call_times.append(asyncio.get_event_loop().time())
        raise DatabaseError("Error")

    strategy = RetryStrategy(max_attempts=3, initial_delay=0.1, backoff_factor=2.0)

    with pytest.raises(DatabaseError):
        await strategy.execute(failing_func)

    # Check that delays increase (approximately)
    assert len(call_times) == 3
    delay1 = call_times[1] - call_times[0]
    delay2 = call_times[2] - call_times[1]
    assert delay2 > delay1  # Second delay should be longer


@pytest.mark.asyncio
async def test_retry_strategy_only_retries_specified_exceptions():
    """RetryStrategy should only retry specified exception types."""
    call_count = 0

    async def fails_with_validation_error():
        nonlocal call_count
        call_count += 1
        raise ValidationError("Validation failed")

    # RetryStrategy defaults to retrying ExternalServiceError and DatabaseError
    strategy = RetryStrategy(max_attempts=3, initial_delay=0.01)

    with pytest.raises(ValidationError):
        await strategy.execute(fails_with_validation_error)

    # Should not retry ValidationError
    assert call_count == 1


# ============================================================================
# Test Fallback Strategy
# ============================================================================


@pytest.mark.asyncio
async def test_fallback_strategy_returns_result_on_success():
    """FallbackStrategy should return result when function succeeds."""

    async def successful_func():
        return "success"

    strategy = FallbackStrategy(fallback="fallback_value")
    result = await strategy.execute(successful_func)

    assert result == "success"


@pytest.mark.asyncio
async def test_fallback_strategy_returns_fallback_on_failure():
    """FallbackStrategy should return fallback value on failure."""

    async def failing_func():
        raise ExternalServiceError("Service unavailable")

    strategy = FallbackStrategy(fallback="fallback_value")
    result = await strategy.execute(failing_func)

    assert result == "fallback_value"


@pytest.mark.asyncio
async def test_fallback_strategy_calls_fallback_function():
    """FallbackStrategy should call fallback function if provided."""

    async def failing_func():
        raise DatabaseError("Database error")

    async def fallback_func():
        return "fallback_result"

    strategy = FallbackStrategy(fallback=fallback_func)
    result = await strategy.execute(failing_func)

    assert result == "fallback_result"


@pytest.mark.asyncio
async def test_fallback_strategy_only_catches_specified_exceptions():
    """FallbackStrategy should only fallback on specified exceptions."""

    async def fails_with_validation_error():
        raise ValidationError("Validation failed")

    # FallbackStrategy defaults to catching AppException
    strategy = FallbackStrategy(fallback="fallback_value")

    # ValidationError is a subclass of AppException, so it should be caught
    result = await strategy.execute(fails_with_validation_error)
    assert result == "fallback_value"


# ============================================================================
# Test Decorators
# ============================================================================


@pytest.mark.asyncio
async def test_with_retry_decorator():
    """@with_retry decorator should add retry logic."""
    call_count = 0

    @with_retry(max_attempts=3, initial_delay=0.01)
    async def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ExternalServiceError("Transient error")
        return "success"

    result = await failing_then_success()

    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_with_fallback_decorator():
    """@with_fallback decorator should add fallback logic."""

    @with_fallback(fallback="fallback_value")
    async def failing_func():
        raise DatabaseError("Database error")

    result = await failing_func()

    assert result == "fallback_value"


# ============================================================================
# Test Error Response Consistency (Property 2)
# ============================================================================


def test_all_app_exceptions_have_consistent_structure():
    """All AppException subclasses should produce consistent error structure."""
    exceptions = [
        AuthenticationError("Auth failed"),
        AuthorizationError("Not authorized"),
        NotFoundError("Not found"),
        ValidationError("Invalid data"),
        DatabaseError("DB error"),
        ExternalServiceError("Service down"),
        RateLimitError("Too many requests"),
        ConfigurationError("Config error"),
    ]

    for exc in exceptions:
        error_dict = exc.to_dict()

        # All should have same structure
        assert "error" in error_dict
        assert "code" in error_dict["error"]
        assert "message" in error_dict["error"]

        # Code should be a string
        assert isinstance(error_dict["error"]["code"], str)

        # Message should be a string
        assert isinstance(error_dict["error"]["message"], str)
