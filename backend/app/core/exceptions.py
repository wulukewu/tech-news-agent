"""
Legacy Exception Classes

This module maintains backward compatibility with existing exception classes.
New code should use the unified error handling system in app.core.errors.

For new error handling, import from app.core.errors:
    from app.core.errors import (
        AppException, AuthenticationError, DatabaseError, ExternalServiceError,
        ErrorCode, with_retry, with_fallback
    )
"""

from app.core.errors import (
    AppException,
    DatabaseError,
    ErrorCode,
    ExternalServiceError,
)
from app.core.errors import (
    ConfigurationError as NewConfigurationError,
)

# ============================================================================
# Legacy Exception Classes (Backward Compatibility)
# ============================================================================


class TechNewsException(Exception):
    """
    Base exception for Tech News Agent (Legacy).

    DEPRECATED: Use AppException from app.core.errors instead.
    """

    pass


class ConfigurationError(ValueError, TechNewsException):
    """
    Exception raised for configuration errors (Legacy).

    Inherits from ValueError to work with Pydantic v2 validators.

    DEPRECATED: Use ConfigurationError from app.core.errors instead.
    This class is maintained for Pydantic validator compatibility.
    """

    pass


class RSSScrapingError(TechNewsException):
    """
    Exception raised for errors during RSS/Atom feed scraping (Legacy).

    DEPRECATED: Use ExternalServiceError with ErrorCode.EXTERNAL_RSS_FETCH_FAILED instead.
    """

    pass


class LLMServiceError(TechNewsException):
    """
    Exception raised for errors in LLM processing (Legacy).

    DEPRECATED: Use ExternalServiceError with ErrorCode.EXTERNAL_LLM_ERROR instead.
    """

    pass


class NotionServiceError(TechNewsException):
    """
    Exception raised for errors in Notion service operations (Legacy).

    DEPRECATED: Legacy compatibility only. Notion integration is no longer used.
    """

    pass


class SupabaseServiceError(Exception):
    """
    Supabase 服務層例外 (Legacy).

    DEPRECATED: Use DatabaseError from app.core.errors instead.
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        context: dict | None = None,
    ):
        """初始化例外

        Args:
            message: 使用者友善的錯誤訊息
            original_error: 原始例外（如果有）
            context: 額外的上下文資訊
        """
        self.message = message
        self.original_error = original_error
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """格式化錯誤訊息"""
        parts = [self.message]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.original_error:
            parts.append(f"Original error: {self.original_error}")
        return " | ".join(parts)


# ============================================================================
# Migration Helpers
# ============================================================================


def convert_to_app_exception(legacy_exception: Exception) -> AppException:
    """
    Convert legacy exception to new AppException.

    Args:
        legacy_exception: Legacy exception instance

    Returns:
        Equivalent AppException instance
    """
    if isinstance(legacy_exception, RSSScrapingError):
        return ExternalServiceError(
            message=str(legacy_exception),
            error_code=ErrorCode.EXTERNAL_RSS_FETCH_FAILED,
            original_error=legacy_exception,
        )
    elif isinstance(legacy_exception, LLMServiceError):
        return ExternalServiceError(
            message=str(legacy_exception),
            error_code=ErrorCode.EXTERNAL_LLM_ERROR,
            original_error=legacy_exception,
        )
    elif isinstance(legacy_exception, SupabaseServiceError):
        return DatabaseError(
            message=legacy_exception.message,
            error_code=ErrorCode.DB_QUERY_FAILED,
            details=legacy_exception.context,
            original_error=legacy_exception.original_error,
        )
    elif isinstance(legacy_exception, ConfigurationError):
        return NewConfigurationError(
            message=str(legacy_exception),
            error_code=ErrorCode.CONFIG_INVALID,
            original_error=legacy_exception,
        )
    else:
        # Generic conversion
        return AppException(
            message=str(legacy_exception),
            error_code=ErrorCode.INTERNAL_ERROR,
            original_error=legacy_exception,
        )
