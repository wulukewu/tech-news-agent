"""
Integration tests for Centralized Logging System with FastAPI

Validates: Requirements 5.1, 5.2, 5.3
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import (
    RequestContextMiddleware,
    get_logger,
    get_request_context,
)


class TestLoggingIntegration:
    """Test logging system integration with FastAPI application."""

    @pytest.fixture
    def app_with_logging(self):
        """Create FastAPI app with logging middleware and test endpoints."""
        app = FastAPI()

        # Simulate auth middleware
        class MockAuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                if "Authorization" in request.headers:
                    # Extract user_id from auth header (simplified)
                    request.state.user_id = "user-123"
                return await call_next(request)

        # Add middlewares in correct order
        app.add_middleware(RequestContextMiddleware)
        app.add_middleware(MockAuthMiddleware)

        @app.get("/api/test")
        async def test_endpoint(request: Request):
            context = get_request_context()
            return {"message": "success", "context": context}

        @app.get("/api/articles/{article_id}")
        async def get_article(article_id: str, request: Request):
            context = get_request_context()
            return {"article_id": article_id, "context": context}

        return app

    def test_request_context_middleware_integration(self, app_with_logging):
        """Test that request context middleware works in FastAPI app."""
        client = TestClient(app_with_logging)

        # Make request with custom request ID
        response = client.get("/api/test", headers={"X-Request-ID": "test-req-123"})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == "test-req-123"

        # Verify context was captured
        data = response.json()
        assert data["context"]["request_id"] == "test-req-123"
        assert data["context"]["user_id"] is None

    def test_request_context_with_auth(self, app_with_logging):
        """Test that request context includes user_id for authenticated requests."""
        client = TestClient(app_with_logging)

        # Make authenticated request
        response = client.get("/api/test", headers={"Authorization": "Bearer token123"})

        assert response.status_code == 200

        # Verify user_id is captured
        data = response.json()
        assert data["context"]["user_id"] == "user-123"
        assert data["context"]["request_id"] is not None

    def test_request_context_auto_generated_id(self, app_with_logging):
        """Test that request ID is auto-generated if not provided."""
        client = TestClient(app_with_logging)

        response = client.get("/api/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        # Verify auto-generated request_id
        data = response.json()
        assert data["context"]["request_id"] is not None
        assert len(data["context"]["request_id"]) > 0

    def test_request_context_isolated_between_requests(self, app_with_logging):
        """Test that request contexts are isolated between requests."""
        client = TestClient(app_with_logging)

        # Make two requests with different request IDs
        response1 = client.get("/api/test", headers={"X-Request-ID": "req-001"})
        response2 = client.get("/api/test", headers={"X-Request-ID": "req-002"})

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify each request has correct context
        data1 = response1.json()
        data2 = response2.json()

        assert data1["context"]["request_id"] == "req-001"
        assert data2["context"]["request_id"] == "req-002"

    def test_logger_can_be_used_in_endpoints(self, app_with_logging):
        """Test that logger can be used within endpoint handlers."""
        # This test verifies the logger doesn't cause errors when used
        # The actual log output is tested in test_logger.py

        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)

        logger = get_logger("test_endpoint")

        @app.get("/test")
        async def test_with_logging(request: Request):
            # These should not raise errors
            logger.info("Endpoint called")
            logger.debug("Debug info", extra_field="value")
            logger.warning("Warning message")

            context = get_request_context()
            return {"context": context}

        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "test-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["context"]["request_id"] == "test-123"


class TestLoggingPerformance:
    """Test logging system performance characteristics."""

    def test_logging_overhead_minimal(self):
        """Test that structured logging has minimal overhead."""
        import time

        logger = get_logger("performance_test")

        # Measure time for 1000 log calls
        start = time.time()
        for i in range(1000):
            logger.info("Test message", iteration=i, data="test")
        end = time.time()

        elapsed = end - start

        # Should complete in reasonable time (< 1 second for 1000 logs)
        assert elapsed < 1.0, f"Logging took {elapsed}s for 1000 calls"

    def test_disabled_logs_near_zero_cost(self):
        """Test that disabled log levels have near-zero cost."""
        import logging
        import time

        logger = get_logger("performance_test", level=logging.WARNING)

        # Measure time for 10000 disabled DEBUG calls
        start = time.time()
        for i in range(10000):
            logger.debug("Debug message", iteration=i)
        end = time.time()

        elapsed = end - start

        # Should be very fast (< 0.1 second for 10000 disabled calls)
        assert elapsed < 0.1, f"Disabled logging took {elapsed}s for 10000 calls"
