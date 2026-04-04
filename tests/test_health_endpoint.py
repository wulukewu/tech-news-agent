"""
Integration tests for the /health/scheduler endpoint.

Validates: Requirements 10.1, 10.5, 10.6, 10.7
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.tasks.scheduler import _scheduler_health


class TestHealthEndpoint:
    """Integration tests for the /health/scheduler endpoint."""
    
    @pytest.fixture(autouse=True)
    def reset_health_state(self):
        """Reset health state before each test."""
        _scheduler_health["last_execution_time"] = None
        _scheduler_health["last_articles_processed"] = 0
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 0
        yield
    
    def test_health_endpoint_returns_200_when_healthy(self):
        """
        Test that /health/scheduler returns 200 when scheduler is healthy.
        
        Validates: Requirements 10.1, 10.5
        """
        # Set up healthy state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 15
        _scheduler_health["last_failed_operations"] = 2
        _scheduler_health["last_total_operations"] = 15
        
        # Create test client
        client = TestClient(app)
        
        # Call endpoint
        response = client.get("/health/scheduler")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_healthy"] is True
        assert data["articles_processed"] == 15
        assert data["failed_operations"] == 2
        assert data["total_operations"] == 15
    
    def test_health_endpoint_returns_503_when_stale(self):
        """
        Test that /health/scheduler returns 503 when scheduler is stale.
        
        Validates: Requirements 10.1, 10.6
        """
        # Set up stale state
        stale_time = datetime.now(timezone.utc) - timedelta(hours=15)
        _scheduler_health["last_execution_time"] = stale_time
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10
        
        # Create test client
        client = TestClient(app)
        
        # Call endpoint
        response = client.get("/health/scheduler")
        
        # Verify response
        assert response.status_code == 503
        data = response.json()
        assert data["is_healthy"] is False
        assert len(data["issues"]) > 0
    
    def test_health_endpoint_returns_503_when_high_failure_rate(self):
        """
        Test that /health/scheduler returns 503 when failure rate is high.
        
        Validates: Requirements 10.1, 10.7
        """
        # Set up high failure rate state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 18
        _scheduler_health["last_total_operations"] = 20
        
        # Create test client
        client = TestClient(app)
        
        # Call endpoint
        response = client.get("/health/scheduler")
        
        # Verify response
        assert response.status_code == 503
        data = response.json()
        assert data["is_healthy"] is False
        assert any("failure rate" in issue for issue in data["issues"])
    
    def test_health_endpoint_returns_503_when_never_executed(self):
        """
        Test that /health/scheduler returns 503 when scheduler has never run.
        
        Validates: Requirements 10.1, 10.6
        """
        # Health state is already reset (never executed)
        
        # Create test client
        client = TestClient(app)
        
        # Call endpoint
        response = client.get("/health/scheduler")
        
        # Verify response
        assert response.status_code == 503
        data = response.json()
        assert data["is_healthy"] is False
        assert data["last_execution_time"] is None
        assert any("never executed" in issue for issue in data["issues"])
    
    def test_health_endpoint_returns_json_content_type(self):
        """
        Test that /health/scheduler returns JSON content type.
        
        Validates: Requirement 10.1
        """
        # Set up healthy state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10
        
        # Create test client
        client = TestClient(app)
        
        # Call endpoint
        response = client.get("/health/scheduler")
        
        # Verify content type
        assert "application/json" in response.headers["content-type"]
