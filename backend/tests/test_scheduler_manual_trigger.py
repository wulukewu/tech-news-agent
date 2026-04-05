"""
Tests for manual scheduler trigger API endpoint.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass login requirement."""
    with patch('app.api.scheduler.get_current_user') as mock:
        mock.return_value = MagicMock(
            discord_id="123456789",
            username="test_user"
        )
        yield mock


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestSchedulerManualTrigger:
    """Test manual scheduler trigger endpoint."""
    
    def test_trigger_scheduler_requires_authentication(self, client):
        """Test that trigger endpoint requires authentication."""
        response = client.post("/api/scheduler/trigger")
        assert response.status_code == 401
    
    @patch('app.api.scheduler.background_fetch_job')
    def test_trigger_scheduler_success(self, mock_job, client, mock_auth):
        """Test successful manual trigger."""
        mock_job.return_value = AsyncMock()
        
        response = client.post("/api/scheduler/trigger")
        
        assert response.status_code == 202
        assert response.json()["status"] == "triggered"
        assert "background" in response.json()["message"].lower()
    
    def test_get_scheduler_status_requires_authentication(self, client):
        """Test that status endpoint requires authentication."""
        response = client.get("/api/scheduler/status")
        assert response.status_code == 401
    
    @patch('app.api.scheduler.get_scheduler_health')
    async def test_get_scheduler_status_success(self, mock_health, client, mock_auth):
        """Test successful status retrieval."""
        mock_health.return_value = {
            "last_execution_time": "2024-01-01T00:00:00Z",
            "articles_processed": 10,
            "failed_operations": 0,
            "total_operations": 10,
            "is_healthy": True,
            "issues": []
        }
        
        response = client.get("/api/scheduler/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_healthy"] is True
        assert data["articles_processed"] == 10
