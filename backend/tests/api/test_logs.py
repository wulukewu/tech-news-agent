"""
Tests for Frontend Logs API Endpoint
Task 9.3: Create backend endpoint for frontend logs

Requirements: 5.4
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_receive_frontend_logs_success():
    """Test successful reception of frontend logs"""
    # Prepare test data
    logs_data = {
        "logs": [
            {
                "timestamp": "2026-04-11T10:00:00.000Z",
                "level": "INFO",
                "message": "User logged in",
                "context": {"userId": "123"},
                "userAgent": "Mozilla/5.0",
                "url": "https://example.com/login",
                "userId": "123",
            },
            {
                "timestamp": "2026-04-11T10:01:00.000Z",
                "level": "ERROR",
                "message": "API request failed",
                "context": {"error": "Network timeout"},
                "userAgent": "Mozilla/5.0",
                "url": "https://example.com/api",
                "userId": "123",
            },
        ]
    }

    # Send request
    response = client.post("/api/logs", json=logs_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["received_count"] == 2
    assert "Successfully received" in data["message"]


def test_receive_frontend_logs_empty_batch():
    """Test handling of empty log batch"""
    logs_data = {"logs": []}

    response = client.post("/api/logs", json=logs_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["received_count"] == 0


def test_receive_frontend_logs_different_levels():
    """Test logs with different severity levels"""
    logs_data = {
        "logs": [
            {
                "timestamp": "2026-04-11T10:00:00.000Z",
                "level": "DEBUG",
                "message": "Debug message",
            },
            {
                "timestamp": "2026-04-11T10:00:01.000Z",
                "level": "INFO",
                "message": "Info message",
            },
            {
                "timestamp": "2026-04-11T10:00:02.000Z",
                "level": "WARN",
                "message": "Warning message",
            },
            {
                "timestamp": "2026-04-11T10:00:03.000Z",
                "level": "ERROR",
                "message": "Error message",
            },
        ]
    }

    response = client.post("/api/logs", json=logs_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["received_count"] == 4


def test_receive_frontend_logs_with_context():
    """Test logs with additional context"""
    logs_data = {
        "logs": [
            {
                "timestamp": "2026-04-11T10:00:00.000Z",
                "level": "ERROR",
                "message": "API error",
                "context": {
                    "endpoint": "/api/users",
                    "method": "POST",
                    "statusCode": 500,
                    "error": "Internal server error",
                },
                "userAgent": "Mozilla/5.0",
                "url": "https://example.com/users",
                "userId": "user-123",
            }
        ]
    }

    response = client.post("/api/logs", json=logs_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["received_count"] == 1


def test_receive_frontend_logs_invalid_payload():
    """Test handling of invalid payload"""
    # Missing required 'logs' field
    invalid_data = {"invalid": "data"}

    response = client.post("/api/logs", json=invalid_data)

    assert response.status_code == 422  # Validation error


def test_receive_frontend_logs_invalid_log_entry():
    """Test handling of invalid log entry"""
    # Missing required fields in log entry
    logs_data = {
        "logs": [
            {
                "level": "INFO",
                # Missing 'timestamp' and 'message'
            }
        ]
    }

    response = client.post("/api/logs", json=logs_data)

    assert response.status_code == 422  # Validation error


def test_logs_health_check():
    """Test logs health check endpoint"""
    response = client.get("/api/logs/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "frontend-logs"
    assert "timestamp" in data


def test_receive_frontend_logs_large_batch():
    """Test handling of large log batch"""
    # Create a batch of 100 logs
    logs_data = {
        "logs": [
            {
                "timestamp": f"2026-04-11T10:00:{i:02d}.000Z",
                "level": "INFO",
                "message": f"Log message {i}",
            }
            for i in range(100)
        ]
    }

    response = client.post("/api/logs", json=logs_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["received_count"] == 100
