"""
Property-Based Tests for Error Handling System

Tests error response consistency, error recovery execution, and error message clarity
using Hypothesis for property-based testing.

**Validates: Requirements 4.2, 4.5, 13.1, 15.3**
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
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
    http_exception_handler,
)

# ============================================================================
# Helper Functions
# ============================================================================


def create_mock_request():
    """Create a mock FastAPI request."""

    class MockURL:
        path = "/api/test"

    class MockRequest:
        url = MockURL()
        method = "GET"

    return MockRequest()


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating error messages
error_messages = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())

# Strategy for generating error details
error_details = st.dictionaries(
    keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    values=st.one_of(st.text(max_size=100), st.integers(), st.booleans(), st.none()),
    max_size=10,
)


# Strategy for generating all AppException subclasses
@st.composite
def app_exception_instances(draw):
    """Generate instances of AppException subclasses."""
    exception_class = draw(
        st.sampled_from(
            [
                AuthenticationError,
                AuthorizationError,
                NotFoundError,
                ValidationError,
                DatabaseError,
                ExternalServiceError,
                RateLimitError,
                ConfigurationError,
            ]
        )
    )

    message = draw(error_messages)
    details = draw(st.one_of(st.none(), error_details))

    return exception_class(message=message, details=details)


# Strategy for HTTP status codes
http_status_codes = st.sampled_from([400, 401, 403, 404, 422, 429, 500, 502, 503])


# ============================================================================
# Property 2: Error Response Consistency
# **Validates: Requirements 4.2, 15.3**
# ============================================================================


@given(exception=app_exception_instances())
@settings(max_examples=50)
def test_property_2_error_response_structure_consistency(exception):
    """
    Property 2: Error Response Consistency

    For any AppException subclass instance, the error response SHALL contain
    the same standardized structure with error code, message, and optional details.

    **Validates: Requirements 4.2, 15.3**
    """
    # Convert exception to dictionary
    error_dict = exception.to_dict()

    # Assert standardized structure exists
    assert "error" in error_dict, "Response must have 'error' field"
    assert isinstance(error_dict["error"], dict), "'error' must be a dictionary"

    # Assert required fields in error object
    assert "code" in error_dict["error"], "Error must have 'code' field"
    assert "message" in error_dict["error"], "Error must have 'message' field"

    # Assert field types
    assert isinstance(error_dict["error"]["code"], str), "Error code must be string"
    assert isinstance(error_dict["error"]["message"], str), "Error message must be string"

    # Assert code is a valid ErrorCode
    assert error_dict["error"]["code"] in [
        e.value for e in ErrorCode
    ], "Error code must be valid ErrorCode enum value"

    # If details exist, they should be a dictionary
    if "details" in error_dict["error"]:
        assert isinstance(
            error_dict["error"]["details"], dict
        ), "Error details must be a dictionary"


@pytest.mark.asyncio
@given(exception=app_exception_instances())
@settings(max_examples=30)
async def test_property_2_handler_response_consistency(exception):
    """
    Property 2: Error Response Consistency (Handler Level)

    For any AppException handled by app_exception_handler, the JSON response
    SHALL maintain the same standardized structure.

    **Validates: Requirements 4.2, 15.3**
    """
    # Create mock request
    mock_request = create_mock_request()

    # Handle exception
    response = await app_exception_handler(mock_request, exception)

    # Parse response body
    import json

    body = json.loads(response.body)

    # Assert standardized structure
    assert "error" in body
    assert "error_code" in body
    assert "success" in body

    # Assert types
    assert isinstance(body["error_code"], str)
    assert isinstance(body["error"], str)
    assert isinstance(body["success"], bool)
    assert body["success"] is False

    # Assert status code matches exception
    assert response.status_code == exception.status_code


@pytest.mark.asyncio
@given(status_code=http_status_codes, detail=error_messages)
@settings(max_examples=30)
async def test_property_2_http_exception_standardization(status_code, detail):
    """
    Property 2: Error Response Consistency (HTTP Exception)

    For any HTTPException, the handler SHALL convert it to the standardized
    error response structure.

    **Validates: Requirements 4.2, 15.3**
    """
    # Create mock request
    mock_request = create_mock_request()

    # Create HTTP exception
    exc = StarletteHTTPException(status_code=status_code, detail=detail)

    # Handle exception
    response = await http_exception_handler(mock_request, exc)

    # Parse response body
    import json

    body = json.loads(response.body)

    # Assert standardized structure
    assert "error" in body
    assert "error_code" in body
    assert "success" in body

    # Assert types
    assert isinstance(body["error_code"], str)
    assert isinstance(body["error"], str)
    assert isinstance(body["success"], bool)
    assert body["success"] is False

    # Assert status code preserved
    assert response.status_code == status_code


# ============================================================================
# Property 13: Error Recovery Execution
# **Validates: Requirements 4.5**
# ============================================================================


@given(
    max_attempts=st.integers(min_value=1, max_value=5),
    success_on_attempt=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=30, deadline=5000)
@pytest.mark.asyncio
async def test_property_13_retry_strategy_executes_recovery(max_attempts, success_on_attempt):
    """
    Property 13: Error Recovery Execution (Retry Strategy)

    For any error that supports retry recovery, the RetryStrategy SHALL execute
    retry attempts and return the recovery result when successful.

    **Validates: Requirements 4.5**
    """
    assume(success_on_attempt <= max_attempts)

    call_count = 0

    async def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < success_on_attempt:
            raise ExternalServiceError("Transient error")
        return "success"

    # Create retry strategy
    strategy = RetryStrategy(max_attempts=max_attempts, initial_delay=0.01, backoff_factor=1.5)

    # Execute with retry
    result = await strategy.execute(failing_then_success)

    # Assert recovery succeeded
    assert result == "success"
    assert call_count == success_on_attempt


@given(max_attempts=st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=5000)
@pytest.mark.asyncio
async def test_property_13_retry_strategy_exhausts_attempts(max_attempts):
    """
    Property 13: Error Recovery Execution (Retry Exhaustion)

    For any error that persists beyond max attempts, the RetryStrategy SHALL
    raise the final error after exhausting all recovery attempts.

    **Validates: Requirements 4.5**
    """
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise DatabaseError("Persistent error")

    # Create retry strategy
    strategy = RetryStrategy(max_attempts=max_attempts, initial_delay=0.01)

    # Execute with retry - should raise after max attempts
    with pytest.raises(DatabaseError):
        await strategy.execute(always_fails)

    # Assert all attempts were made
    assert call_count == max_attempts


@given(
    fallback_value=st.one_of(
        st.text(), st.integers(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers())
    )
)
@settings(max_examples=30)
@pytest.mark.asyncio
async def test_property_13_fallback_strategy_executes_recovery(fallback_value):
    """
    Property 13: Error Recovery Execution (Fallback Strategy)

    For any error that supports fallback recovery, the FallbackStrategy SHALL
    execute the fallback and return the fallback result.

    **Validates: Requirements 4.5**
    """

    async def failing_func():
        raise ExternalServiceError("Service unavailable")

    # Create fallback strategy
    strategy = FallbackStrategy(fallback=fallback_value)

    # Execute with fallback
    result = await strategy.execute(failing_func)

    # Assert fallback was returned
    assert result == fallback_value


@given(success_value=st.text(min_size=1))
@settings(max_examples=20)
@pytest.mark.asyncio
async def test_property_13_fallback_returns_success_when_no_error(success_value):
    """
    Property 13: Error Recovery Execution (No Fallback on Success)

    For any successful operation, the FallbackStrategy SHALL return the
    success result without executing fallback.

    **Validates: Requirements 4.5**
    """

    async def successful_func():
        return success_value

    # Create fallback strategy
    strategy = FallbackStrategy(fallback="fallback_value")

    # Execute - should return success value
    result = await strategy.execute(successful_func)

    # Assert success value returned, not fallback
    assert result == success_value


# ============================================================================
# Property 16: Error Message Clarity
# **Validates: Requirements 13.1**
# ============================================================================


@given(exception=app_exception_instances())
@settings(max_examples=50)
def test_property_16_error_message_is_non_empty(exception):
    """
    Property 16: Error Message Clarity (Non-Empty)

    For any error that occurs, the error message SHALL be non-empty and
    contain meaningful text.

    **Validates: Requirements 13.1**
    """
    # Get error message
    message = exception.message

    # Assert message is non-empty
    assert message, "Error message must not be empty"
    assert len(message.strip()) > 0, "Error message must contain non-whitespace characters"


@given(exception=app_exception_instances())
@settings(max_examples=50)
def test_property_16_error_code_provides_context(exception):
    """
    Property 16: Error Message Clarity (Error Code Context)

    For any error that occurs, the error code SHALL provide categorical
    context about the error type.

    **Validates: Requirements 13.1**
    """
    # Get error code
    error_code = exception.error_code.value

    # Assert error code follows naming convention (CATEGORY_SPECIFIC)
    assert "_" in error_code, "Error code must follow CATEGORY_SPECIFIC format"

    # Extract category
    category = error_code.split("_")[0]

    # Assert category is meaningful
    valid_categories = [
        "AUTH",
        "DB",
        "VALIDATION",
        "EXTERNAL",
        "INTERNAL",
        "RATE",
        "NOT",
        "RESOURCE",
        "CONFIG",
    ]
    assert category in valid_categories, f"Error code category must be one of {valid_categories}"


@given(exception=app_exception_instances())
@settings(max_examples=30)
def test_property_16_error_details_enhance_clarity(exception):
    """
    Property 16: Error Message Clarity (Details Enhancement)

    For any error with details, the details SHALL provide additional
    actionable context beyond the base message.

    **Validates: Requirements 13.1**
    """
    # If details exist, they should be structured
    if exception.details:
        assert isinstance(exception.details, dict), "Error details must be a dictionary"
        assert len(exception.details) > 0, "Error details must not be empty if provided"

        # Details should have meaningful keys
        for key in exception.details.keys():
            assert len(key.strip()) > 0, "Detail keys must be non-empty"


@given(message=error_messages, error_code=st.sampled_from(list(ErrorCode)))
@settings(max_examples=30)
def test_property_16_string_representation_includes_context(message, error_code):
    """
    Property 16: Error Message Clarity (String Representation)

    For any error, the string representation SHALL include both the error
    code and message for complete context.

    **Validates: Requirements 13.1**
    """
    # Create exception
    exc = AppException(message=message, error_code=error_code)

    # Get string representation
    str_repr = str(exc)

    # Assert both code and message are present
    assert error_code.value in str_repr, "String representation must include error code"
    assert message in str_repr, "String representation must include error message"


@pytest.mark.asyncio
@given(exception=app_exception_instances())
@settings(max_examples=30)
async def test_property_16_api_response_provides_actionable_info(exception):
    """
    Property 16: Error Message Clarity (API Response)

    For any error returned via API, the response SHALL include error code
    and message that together provide actionable information.

    **Validates: Requirements 13.1**
    """
    # Create mock request
    mock_request = create_mock_request()

    # Handle exception
    response = await app_exception_handler(mock_request, exception)

    # Parse response
    import json

    body = json.loads(response.body)

    # Assert actionable information is present
    assert "error" in body
    assert "error_code" in body

    # Both code and message should be meaningful
    assert len(body["error_code"]) > 0
    assert len(body["error"]) > 0

    # Code should categorize the error
    assert "_" in body["error_code"], "Error code should provide categorical context"
