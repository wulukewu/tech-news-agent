"""
Centralized Logging System

This module provides structured logging with consistent format, multiple log levels,
request context injection, and log filtering capabilities.

Validates: Requirements 5.1, 5.2, 5.3
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from logging import LogRecord
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variables for request-scoped data
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs with consistent format.

    Format includes:
    - timestamp: ISO 8601 format
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - context: Request context (user_id, request_id) when available
    - extra: Additional fields passed to the logger
    """

    def format(self, record: LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        request_id = request_id_var.get()
        user_id = user_id_var.get()

        if request_id or user_id:
            log_data["context"] = {}
            if request_id:
                log_data["context"]["request_id"] = request_id
            if user_id:
                log_data["context"]["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (custom fields passed to logger)
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_data["extra"] = record.extra_fields

        # Add source location for ERROR and CRITICAL levels
        if record.levelno >= logging.ERROR:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture and inject request context into logs.

    Captures:
    - request_id: Unique identifier for each request (from X-Request-ID header or generated)
    - user_id: User identifier from authentication (if available)

    This context is automatically included in all logs during request processing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and inject context."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            import uuid

            request_id = str(uuid.uuid4())

        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Set context variables
        request_id_token = request_id_var.set(request_id)
        user_id_token = user_id_var.set(user_id)

        try:
            # Add request ID to response headers
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset context variables
            request_id_var.reset(request_id_token)
            user_id_var.reset(user_id_token)


class StructuredLogger:
    """
    Wrapper around Python's logging module with structured logging support.

    Provides:
    - Structured logging with consistent format
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Request context injection
    - Extra fields support
    - Log filtering by level and context
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically module name)
            level: Minimum log level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Add console handler with structured formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _log(self, level: int, message: str, **extra_fields):
        """Internal method to log with extra fields."""
        # Create a log record with extra fields
        if extra_fields:
            extra = {"extra_fields": extra_fields}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def debug(self, message: str, **extra_fields):
        """Log debug message."""
        self._log(logging.DEBUG, message, **extra_fields)

    def info(self, message: str, **extra_fields):
        """Log info message."""
        self._log(logging.INFO, message, **extra_fields)

    def warning(self, message: str, **extra_fields):
        """Log warning message."""
        self._log(logging.WARNING, message, **extra_fields)

    def error(self, message: str, exc_info: bool = False, **extra_fields):
        """
        Log error message.

        Args:
            message: Error message
            exc_info: Include exception traceback (default: False)
            **extra_fields: Additional fields to include in log
        """
        if exc_info:
            extra = {"extra_fields": extra_fields} if extra_fields else {}
            self.logger.error(message, exc_info=True, extra=extra)
        else:
            self._log(logging.ERROR, message, **extra_fields)

    def critical(self, message: str, exc_info: bool = False, **extra_fields):
        """
        Log critical message.

        Args:
            message: Critical message
            exc_info: Include exception traceback (default: False)
            **extra_fields: Additional fields to include in log
        """
        if exc_info:
            extra = {"extra_fields": extra_fields} if extra_fields else {}
            self.logger.critical(message, exc_info=True, extra=extra)
        else:
            self._log(logging.CRITICAL, message, **extra_fields)

    def set_level(self, level: int):
        """
        Set minimum log level.

        Args:
            level: Log level (logging.DEBUG, logging.INFO, etc.)
        """
        self.logger.setLevel(level)


def get_logger(name: str, level: int | None = None) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name (typically __name__)
        level: Minimum log level (default: INFO)

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id="123", action="login")
    """
    if level is None:
        level = logging.INFO

    return StructuredLogger(name, level)


# Convenience function to set global log level
def set_global_log_level(level: int):
    """
    Set log level for all loggers.

    Args:
        level: Log level (logging.DEBUG, logging.INFO, etc.)
    """
    logging.root.setLevel(level)


# Convenience function to get request context
def get_request_context() -> dict[str, str | None]:
    """
    Get current request context.

    Returns:
        Dictionary with request_id and user_id (if available)
    """
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
    }
