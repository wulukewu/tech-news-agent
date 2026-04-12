"""
API-related test fixtures.

Provides fixtures for FastAPI test client and common API testing utilities.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI test client for API endpoint testing."""
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_request_context():
    """Mock request context for testing middleware and logging."""
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state.request_id = "test-request-123"
    request.state.user_id = "test-user-123"
    request.client.host = "127.0.0.1"
    request.method = "GET"
    request.url.path = "/api/test"

    return request
