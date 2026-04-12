"""
Tests for Centralized Logging System

Validates: Requirements 5.1, 5.2, 5.3
"""

import json
import logging

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.logger import (
    RequestContextMiddleware,
    StructuredFormatter,
    StructuredLogger,
    get_logger,
    get_request_context,
    request_id_var,
    user_id_var,
)


class TestStructuredFormatter:
    """Test structured log formatting."""

    def test_basic_log_format(self):
        """Test basic log entry contains required fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"

    def test_log_with_request_context(self):
        """Test log includes request context when available."""
        formatter = StructuredFormatter()

        # Set request context
        request_id_var.set("req-123")
        user_id_var.set("user-456")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "context" in log_data
        assert log_data["context"]["request_id"] == "req-123"
        assert log_data["context"]["user_id"] == "user-456"

        # Clean up
        request_id_var.set(None)
        user_id_var.set(None)

    def test_log_with_exception(self):
        """Test log includes exception info when present."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "exception" in log_data
        assert "ValueError: Test error" in log_data["exception"]

    def test_error_log_includes_source(self):
        """Test ERROR and CRITICAL logs include source location."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/app/test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "source" in log_data
        assert log_data["source"]["file"] == "/app/test.py"
        assert log_data["source"]["line"] == 42
        assert log_data["source"]["function"] == "test_function"

    def test_info_log_no_source(self):
        """Test INFO logs do not include source location."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=42,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "source" not in log_data


class TestStructuredLogger:
    """Test StructuredLogger wrapper."""

    def test_logger_creation(self):
        """Test logger can be created with name and level."""
        logger = StructuredLogger("test_logger", level=logging.DEBUG)
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.DEBUG

    def test_log_levels(self, capsys):
        """Test all log levels work correctly."""
        logger = StructuredLogger("test_logger", level=logging.DEBUG)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split("\n")

        assert len(output_lines) == 5

        # Verify each log level
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for i, level in enumerate(levels):
            log_data = json.loads(output_lines[i])
            assert log_data["level"] == level

    def test_log_with_extra_fields(self, capsys):
        """Test logging with extra fields."""
        logger = StructuredLogger("test_logger")

        logger.info("User action", user_id="123", action="login", ip="192.168.1.1")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert "extra" in log_data
        assert log_data["extra"]["user_id"] == "123"
        assert log_data["extra"]["action"] == "login"
        assert log_data["extra"]["ip"] == "192.168.1.1"

    def test_error_with_exception(self, capsys):
        """Test error logging with exception traceback."""
        logger = StructuredLogger("test_logger")

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error("An error occurred", exc_info=True)

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "ERROR"
        assert "exception" in log_data
        assert "ValueError: Test error" in log_data["exception"]

    def test_set_level(self, capsys):
        """Test changing log level filters messages."""
        logger = StructuredLogger("test_logger", level=logging.DEBUG)

        logger.debug("Debug message 1")
        logger.info("Info message 1")

        # Change level to WARNING
        logger.set_level(logging.WARNING)

        logger.debug("Debug message 2")
        logger.info("Info message 2")
        logger.warning("Warning message")

        captured = capsys.readouterr()
        output_lines = [line for line in captured.out.strip().split("\n") if line]

        # Should only have 3 logs (debug1, info1, warning)
        assert len(output_lines) == 3


class TestRequestContextMiddleware:
    """Test request context middleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        app = FastAPI()

        # Simulate auth middleware that runs BEFORE logging middleware
        class MockAuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Simulate auth middleware setting user_id for specific endpoint
                if request.url.path == "/test-with-user":
                    request.state.user_id = "user-789"
                return await call_next(request)

        # Add auth middleware first, then logging middleware
        app.add_middleware(RequestContextMiddleware)
        app.add_middleware(MockAuthMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            context = get_request_context()
            return {"context": context}

        @app.get("/test-with-user")
        async def test_with_user(request: Request):
            context = get_request_context()
            return {"context": context}

        return app

    def test_middleware_generates_request_id(self, app):
        """Test middleware generates request ID if not provided."""
        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        context = response.json()["context"]
        assert context["request_id"] is not None
        assert context["user_id"] is None

    def test_middleware_uses_provided_request_id(self, app):
        """Test middleware uses X-Request-ID header if provided."""
        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "custom-req-id"})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == "custom-req-id"

        context = response.json()["context"]
        assert context["request_id"] == "custom-req-id"

    def test_middleware_captures_user_id(self, app):
        """Test middleware captures user_id from request state."""
        client = TestClient(app)
        response = client.get("/test-with-user")

        assert response.status_code == 200

        context = response.json()["context"]
        assert context["user_id"] == "user-789"


class TestGetLogger:
    """Test get_logger convenience function."""

    def test_get_logger_returns_structured_logger(self):
        """Test get_logger returns StructuredLogger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_module"

    def test_get_logger_with_custom_level(self):
        """Test get_logger with custom log level."""
        logger = get_logger("test_module", level=logging.DEBUG)
        assert logger.logger.level == logging.DEBUG

    def test_get_logger_default_level(self):
        """Test get_logger uses INFO as default level."""
        logger = get_logger("test_module")
        assert logger.logger.level == logging.INFO


class TestGetRequestContext:
    """Test get_request_context function."""

    def test_get_context_with_values(self):
        """Test getting context when values are set."""
        request_id_var.set("req-123")
        user_id_var.set("user-456")

        context = get_request_context()

        assert context["request_id"] == "req-123"
        assert context["user_id"] == "user-456"

        # Clean up
        request_id_var.set(None)
        user_id_var.set(None)

    def test_get_context_without_values(self):
        """Test getting context when no values are set."""
        context = get_request_context()

        assert context["request_id"] is None
        assert context["user_id"] is None
