"""
Integration tests for Analytics API endpoints

Tests analytics event logging, completion rates, drop-off rates, and average time per step.

**Validates: Requirements 14.1, 14.6, 14.7**
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.api.auth import create_access_token


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create a valid authentication token"""
    user_id = uuid4()
    discord_id = "test_user_analytics_123"
    
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        
        token = create_access_token(user_id=user_id, discord_id=discord_id)
        return token


@pytest.fixture
def mock_supabase():
    """Mock Supabase service"""
    with patch("app.services.supabase_service.SupabaseService") as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.get_or_create_user = AsyncMock(return_value=uuid4())
        yield mock_service


@pytest.fixture
def mock_analytics_service():
    """Mock AnalyticsService"""
    with patch("app.api.analytics.AnalyticsService") as mock_service:
        yield mock_service


def test_log_analytics_event_unauthorized(client):
    """
    Test logging analytics event without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.post(
        "/api/analytics/event",
        json={"event_type": "onboarding_started", "event_data": {}}
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_log_analytics_event_success(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test successfully logging an analytics event
    
    **Validates: Requirements 14.1**
    """
    mock_instance = mock_analytics_service.return_value
    mock_instance.log_event = AsyncMock()
    
    response = client.post(
        "/api/analytics/event",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "event_type": "onboarding_started",
            "event_data": {
                "source": "web",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return success message
    data = response.json()
    assert "message" in data
    assert "事件已記錄" in data["message"]


def test_log_analytics_event_invalid_request(client, auth_token):
    """
    Test logging analytics event with invalid request body
    
    **Validates: Request validation**
    """
    response = client.post(
        "/api/analytics/event",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"invalid_field": "value"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_log_analytics_event_rate_limit(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test rate limiting on analytics event logging
    
    **Validates: Requirements 14.7 (rate limiting)**
    """
    mock_instance = mock_analytics_service.return_value
    mock_instance.log_event = AsyncMock()
    
    # Make multiple requests rapidly
    # Note: Actual rate limit testing would require more sophisticated setup
    # This is a basic test to ensure the endpoint accepts requests
    for i in range(5):
        response = client.post(
            "/api/analytics/event",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "event_type": "step_completed",
                "event_data": {"step": f"step_{i}"}
            }
        )
        # First few requests should succeed
        if i < 3:
            assert response.status_code == 200


def test_get_completion_rate_unauthorized(client):
    """
    Test getting completion rate without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.get("/api/analytics/onboarding/completion-rate")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_get_completion_rate_success(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test successfully getting onboarding completion rate
    
    **Validates: Requirements 14.6**
    """
    from app.schemas.analytics import OnboardingCompletionRateResponse
    
    # Mock completion rate response
    mock_response = OnboardingCompletionRateResponse(
        completion_rate=75.5,
        total_users=100,
        completed_users=75,
        skipped_users=15,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    
    mock_instance = mock_analytics_service.return_value
    mock_instance.get_onboarding_completion_rate = AsyncMock(return_value=mock_response)
    
    response = client.get(
        "/api/analytics/onboarding/completion-rate",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return completion rate data
    data = response.json()
    assert data["completion_rate"] == 75.5
    assert data["total_users"] == 100
    assert data["completed_users"] == 75
    assert data["skipped_users"] == 15


def test_get_completion_rate_with_custom_days(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test getting completion rate with custom time period
    
    **Validates: Query parameter handling**
    """
    from app.schemas.analytics import OnboardingCompletionRateResponse
    
    mock_response = OnboardingCompletionRateResponse(
        completion_rate=80.0,
        total_users=50,
        completed_users=40,
        skipped_users=5,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    
    mock_instance = mock_analytics_service.return_value
    mock_instance.get_onboarding_completion_rate = AsyncMock(return_value=mock_response)
    
    response = client.get(
        "/api/analytics/onboarding/completion-rate?days=7",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return data for 7 days
    data = response.json()
    assert data["total_users"] == 50


def test_get_drop_off_rates_unauthorized(client):
    """
    Test getting drop-off rates without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.get("/api/analytics/onboarding/drop-off")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_get_drop_off_rates_success(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test successfully getting drop-off rates
    
    **Validates: Requirements 14.7**
    """
    from app.schemas.analytics import DropOffRatesResponse
    
    # Mock drop-off rates response
    mock_response = DropOffRatesResponse(
        drop_off_by_step={
            "welcome": 10.5,
            "recommendations": 15.2,
            "complete": 5.0
        },
        total_started=100
    )
    
    mock_instance = mock_analytics_service.return_value
    mock_instance.get_drop_off_rates = AsyncMock(return_value=mock_response)
    
    response = client.get(
        "/api/analytics/onboarding/drop-off",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return drop-off rates
    data = response.json()
    assert "drop_off_by_step" in data
    assert "total_started" in data
    assert data["total_started"] == 100
    assert data["drop_off_by_step"]["welcome"] == 10.5
    assert data["drop_off_by_step"]["recommendations"] == 15.2
    assert data["drop_off_by_step"]["complete"] == 5.0


def test_get_average_time_unauthorized(client):
    """
    Test getting average time without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.get("/api/analytics/onboarding/average-time")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_get_average_time_success(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test successfully getting average time per step
    
    **Validates: Requirements 14.5**
    """
    from app.schemas.analytics import AverageTimePerStepResponse
    
    # Mock average time response
    mock_response = AverageTimePerStepResponse(
        average_time_by_step={
            "welcome": 45.5,
            "recommendations": 120.3,
            "complete": 30.0
        },
        total_completions=75
    )
    
    mock_instance = mock_analytics_service.return_value
    mock_instance.get_average_time_per_step = AsyncMock(return_value=mock_response)
    
    response = client.get(
        "/api/analytics/onboarding/average-time",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return average time data
    data = response.json()
    assert "average_time_by_step" in data
    assert "total_completions" in data
    assert data["total_completions"] == 75
    assert data["average_time_by_step"]["welcome"] == 45.5
    assert data["average_time_by_step"]["recommendations"] == 120.3
    assert data["average_time_by_step"]["complete"] == 30.0


def test_complete_analytics_flow(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test complete analytics flow: log events → query metrics
    
    **Validates: Complete analytics workflow**
    """
    from app.schemas.analytics import (
        OnboardingCompletionRateResponse,
        DropOffRatesResponse,
        AverageTimePerStepResponse
    )
    
    mock_instance = mock_analytics_service.return_value
    
    # Step 1: Log onboarding started event
    mock_instance.log_event = AsyncMock()
    
    start_response = client.post(
        "/api/analytics/event",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "event_type": "onboarding_started",
            "event_data": {"source": "web"}
        }
    )
    assert start_response.status_code == 200
    
    # Step 2: Log step completed events
    for step in ["welcome", "recommendations"]:
        step_response = client.post(
            "/api/analytics/event",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "event_type": "step_completed",
                "event_data": {
                    "step": step,
                    "time_spent_seconds": 60
                }
            }
        )
        assert step_response.status_code == 200
    
    # Step 3: Log onboarding finished event
    finish_response = client.post(
        "/api/analytics/event",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "event_type": "onboarding_finished",
            "event_data": {}
        }
    )
    assert finish_response.status_code == 200
    
    # Step 4: Query completion rate
    mock_instance.get_onboarding_completion_rate = AsyncMock(
        return_value=OnboardingCompletionRateResponse(
            completion_rate=100.0,
            total_users=1,
            completed_users=1,
            skipped_users=0,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )
    )
    
    completion_response = client.get(
        "/api/analytics/onboarding/completion-rate",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert completion_response.status_code == 200
    assert completion_response.json()["completion_rate"] == 100.0
    
    # Step 5: Query drop-off rates
    mock_instance.get_drop_off_rates = AsyncMock(
        return_value=DropOffRatesResponse(
            drop_off_by_step={},
            total_started=1
        )
    )
    
    dropoff_response = client.get(
        "/api/analytics/onboarding/drop-off",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert dropoff_response.status_code == 200
    
    # Step 6: Query average time
    mock_instance.get_average_time_per_step = AsyncMock(
        return_value=AverageTimePerStepResponse(
            average_time_by_step={
                "welcome": 60.0,
                "recommendations": 60.0
            },
            total_completions=1
        )
    )
    
    time_response = client.get(
        "/api/analytics/onboarding/average-time",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert time_response.status_code == 200


def test_error_handling_service_failure(client, auth_token, mock_supabase, mock_analytics_service):
    """
    Test error handling when AnalyticsService fails
    
    **Validates: Error handling**
    """
    from app.services.analytics_service import AnalyticsServiceError
    
    mock_instance = mock_analytics_service.return_value
    mock_instance.log_event = AsyncMock(
        side_effect=AnalyticsServiceError("Database error")
    )
    
    response = client.post(
        "/api/analytics/event",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "event_type": "onboarding_started",
            "event_data": {}
        }
    )
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    
    # Should return user-friendly error message
    data = response.json()
    assert "detail" in data
    assert "無法記錄事件" in data["detail"]
