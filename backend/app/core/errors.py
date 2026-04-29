"""
Unified Error Handling System

This module provides standard error types, error codes, base exception classes,
FastAPI exception handlers, and error recovery strategies.

Validates: Requirements 4.1, 4.2, 4.4, 4.5
"""

from enum import Enum
from typing import Any, TypeVar

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import get_logger
from app.schemas.responses import ErrorDetail, error_response

logger = get_logger(__name__)

T = TypeVar("T")


# ============================================================================
# Error Codes
# ============================================================================


class ErrorCode(str, Enum):
    """
    Standard error codes for consistent error identification.

    Format: CATEGORY_SPECIFIC_ERROR
    Categories: AUTH, DB, VALIDATION, EXTERNAL, INTERNAL, RATE_LIMIT, NOT_FOUND
    """

    # Authentication & Authorization Errors (401, 403)
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_MISSING_TOKEN = "AUTH_MISSING_TOKEN"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_OAUTH_FAILED = "AUTH_OAUTH_FAILED"

    # Database Errors (500)
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    DB_QUERY_FAILED = "DB_QUERY_FAILED"
    DB_CONSTRAINT_VIOLATION = "DB_CONSTRAINT_VIOLATION"
    DB_TRANSACTION_FAILED = "DB_TRANSACTION_FAILED"

    # Validation Errors (422)
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_BUSINESS_RULE = "VALIDATION_BUSINESS_RULE"

    # External Service Errors (502, 503)
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    EXTERNAL_RSS_FETCH_FAILED = "EXTERNAL_RSS_FETCH_FAILED"
    EXTERNAL_LLM_ERROR = "EXTERNAL_LLM_ERROR"
    EXTERNAL_DISCORD_ERROR = "EXTERNAL_DISCORD_ERROR"

    # Resource Errors (404)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Configuration Errors (500)
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"

    # Internal Errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INTERNAL_UNEXPECTED = "INTERNAL_UNEXPECTED"


# ============================================================================
# Base Exception Classes
# ============================================================================


class AppException(Exception):
    """
    Base exception class for all application exceptions.

    Provides:
    - Error code for consistent identification
    - User-friendly message
    - HTTP status code
    - Additional context/details
    - Original exception tracking
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """
        Initialize application exception.

        Args:
            message: User-friendly error message
            error_code: Standard error code for identification
            status_code: HTTP status code (default: 500)
            details: Additional context/details
            original_error: Original exception if wrapping another error
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        error_dict = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
            }
        }

        if self.details:
            error_dict["error"]["details"] = self.details

        return error_dict

    def __str__(self) -> str:
        """String representation for logging."""
        parts = [f"{self.error_code.value}: {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.original_error:
            parts.append(f"Original: {type(self.original_error).__name__}: {self.original_error}")
        return " | ".join(parts)


# ============================================================================
# Specific Exception Classes
# ============================================================================


class AuthenticationError(AppException):
    """Authentication-related errors (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: ErrorCode = ErrorCode.AUTH_INVALID_TOKEN,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            original_error=original_error,
        )


class AuthorizationError(AppException):
    """Authorization-related errors (403)."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: ErrorCode = ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            original_error=original_error,
        )


class NotFoundError(AppException):
    """Resource not found errors (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            original_error=original_error,
        )


class ValidationError(AppException):
    """Validation errors (422)."""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: ErrorCode = ErrorCode.VALIDATION_FAILED,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            original_error=original_error,
        )


class DatabaseError(AppException):
    """Database-related errors (500)."""

    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: ErrorCode = ErrorCode.DB_QUERY_FAILED,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            original_error=original_error,
        )


class ExternalServiceError(AppException):
    """External service errors (502, 503)."""

    def __init__(
        self,
        message: str = "External service unavailable",
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
            original_error=original_error,
        )


class RateLimitError(AppException):
    """Rate limiting errors (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            original_error=original_error,
        )


class ConfigurationError(AppException):
    """Configuration errors (500)."""

    def __init__(
        self,
        message: str = "Configuration error",
        error_code: ErrorCode = ErrorCode.CONFIG_INVALID,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            original_error=original_error,
        )


class ServiceError(AppException):
    """Service layer errors (500)."""

    def __init__(
        self,
        message: str = "Service operation failed",
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            original_error=original_error,
        )


# ============================================================================
# FastAPI Exception Handlers
# ============================================================================


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for AppException and its subclasses.

    Returns standardized error response with error code, message, and details.
    Logs error with appropriate severity level.

    Validates: Requirements 4.2, 4.4
    """
    # Log error with context
    log_data = {
        "error_code": exc.error_code.value,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    }

    if exc.details:
        log_data["details"] = exc.details

    # Log with appropriate level based on status code
    if exc.status_code >= 500:
        logger.error(
            f"Server error: {exc.message}", exc_info=exc.original_error is not None, **log_data
        )
    elif exc.status_code >= 400:
        logger.warning(f"Client error: {exc.message}", **log_data)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            error=exc.message,
            error_code=exc.error_code.value,
            details=(
                [ErrorDetail(message=str(v), field=k) for k, v in exc.details.items()]
                if exc.details
                else None
            ),
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for Starlette HTTPException.

    Converts to standardized error response format.

    Validates: Requirements 4.2
    """
    # Map HTTP status code to error code
    error_code_map = {
        401: ErrorCode.AUTH_INVALID_TOKEN,
        403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.NOT_FOUND,
        422: ErrorCode.VALIDATION_FAILED,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.EXTERNAL_API_ERROR,
        503: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Log error
    logger.warning(
        f"HTTP exception: {exc.detail}",
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            error=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            error_code=error_code.value,
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.

    Returns standardized error response with validation details.

    Validates: Requirements 4.2
    """
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append(
            ErrorDetail(
                field=".".join(str(loc) for loc in error["loc"]),
                message=error["msg"],
                code=error["type"],
            )
        )

    # Log validation error
    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=[e.dict() for e in validation_errors],
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            error="Validation failed",
            error_code=ErrorCode.VALIDATION_FAILED.value,
            details=validation_errors,
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions.

    Returns generic error response and logs full exception details.

    Validates: Requirements 4.2, 4.4
    """
    # Log unexpected error with full traceback
    logger.critical(
        f"Unexpected error: {exc!s}",
        exc_info=True,
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            error="An unexpected error occurred. Please try again later.",
            error_code=ErrorCode.INTERNAL_UNEXPECTED.value,
        ).model_dump(),
    )


# ============================================================================
# Error Recovery Strategies
# ============================================================================
