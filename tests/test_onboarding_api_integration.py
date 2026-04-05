"""
Integration tests for Onboarding API endpoints

Tests the complete onboarding flow including status queries, progress updates,
completion, skip, and reset functionality.

**Validates: Requirements 1.4, 1.5, 1.6, 10.3, 10.6**
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4

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
    discord_id = "test_user_onboarding_123"
    
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
def mock_onboarding_service():
    """Mock OnboardingService"""
    with patch("app.api.onboarding.OnboardingService") as mock_service:
        yield mock_service


def test_get_onboarding_status_unauthorized(client):
    """
    Test getting onboarding status without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.get("/api/onboarding/status")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_get_onboarding_status_success(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test successfully getting onboarding status
    
    **Validates: Requirements 1.4, 10.3, 10.4**
    """
    # Mock onboarding status
    from app.schemas.onboarding import OnboardingStatus
    mock_status = OnboardingStatus(
        onboarding_completed=False,
        onboarding_step="welcome",
        onboarding_skipped=False,
        tooltip_tour_completed=False,
        should_show_onboarding=True
    )
    
    mock_instance = mock_onboarding_service.return_value
    mock_instance.get_onboarding_status = AsyncMock(return_value=mock_status)
    
    response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return onboarding status
    data = response.json()
    assert data["onboarding_completed"] is False
    assert data["onboarding_step"] == "welcome"
    assert data["onboarding_skipped"] is False
    assert data["tooltip_tour_completed"] is False
    assert data["should_show_onboarding"] is True


def test_update_onboarding_progress_unauthorized(client):
    """
    Test updating onboarding progress without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.post(
        "/api/onboarding/progress",
        json={"step": "welcome", "completed": True}
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_update_onboarding_progress_success(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test successfully updating onboarding progress
    
    **Validates: Requirements 1.4, 10.3**
    """
    mock_instance = mock_onboarding_service.return_value
    mock_instance.update_onboarding_progress = AsyncMock()
    
    response = client.post(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"step": "recommendations", "completed": True}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return success message
    data = response.json()
    assert "message" in data
    assert "引導進度已更新" in data["message"]


def test_update_onboarding_progress_invalid_request(client, auth_token):
    """
    Test updating onboarding progress with invalid request body
    
    **Validates: Request validation**
    """
    response = client.post(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"invalid_field": "value"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_mark_onboarding_completed_unauthorized(client):
    """
    Test marking onboarding completed without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.post("/api/onboarding/complete")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_mark_onboarding_completed_success(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test successfully marking onboarding as completed
    
    **Validates: Requirements 1.5, 10.3**
    """
    mock_instance = mock_onboarding_service.return_value
    mock_instance.mark_onboarding_completed = AsyncMock()
    
    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return success message
    data = response.json()
    assert "message" in data
    assert "引導已完成" in data["message"]


def test_mark_onboarding_skipped_unauthorized(client):
    """
    Test marking onboarding skipped without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.post("/api/onboarding/skip")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_mark_onboarding_skipped_success(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test successfully marking onboarding as skipped
    
    **Validates: Requirements 1.6, 1.7, 10.3**
    """
    mock_instance = mock_onboarding_service.return_value
    mock_instance.mark_onboarding_skipped = AsyncMock()
    
    response = client.post(
        "/api/onboarding/skip",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return success message
    data = response.json()
    assert "message" in data
    assert "已跳過引導" in data["message"]


def test_reset_onboarding_unauthorized(client):
    """
    Test resetting onboarding without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.post("/api/onboarding/reset")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_reset_onboarding_success(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test successfully resetting onboarding
    
    **Validates: Requirements 10.6, 10.7**
    """
    mock_instance = mock_onboarding_service.return_value
    mock_instance.reset_onboarding = AsyncMock()
    
    response = client.post(
        "/api/onboarding/reset",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return success message
    data = response.json()
    assert "message" in data
    assert "引導已重置" in data["message"]


def test_complete_onboarding_flow(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test complete onboarding flow: status → progress → complete
    
    **Validates: Complete onboarding flow**
    """
    from app.schemas.onboarding import OnboardingStatus
    
    mock_instance = mock_onboarding_service.return_value
    
    # Step 1: Get initial status (not started)
    mock_instance.get_onboarding_status = AsyncMock(return_value=OnboardingStatus(
        onboarding_completed=False,
        onboarding_step=None,
        onboarding_skipped=False,
        tooltip_tour_completed=False,
        should_show_onboarding=True
    ))
    
    status_response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert status_response.status_code == 200
    assert status_response.json()["should_show_onboarding"] is True
    
    # Step 2: Update progress to welcome step
    mock_instance.update_onboarding_progress = AsyncMock()
    
    progress_response_1 = client.post(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"step": "welcome", "completed": True}
    )
    assert progress_response_1.status_code == 200
    
    # Step 3: Update progress to recommendations step
    progress_response_2 = client.post(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"step": "recommendations", "completed": True}
    )
    assert progress_response_2.status_code == 200
    
    # Step 4: Mark as completed
    mock_instance.mark_onboarding_completed = AsyncMock()
    
    complete_response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert complete_response.status_code == 200
    
    # Step 5: Get final status (completed)
    mock_instance.get_onboarding_status = AsyncMock(return_value=OnboardingStatus(
        onboarding_completed=True,
        onboarding_step="complete",
        onboarding_skipped=False,
        tooltip_tour_completed=False,
        should_show_onboarding=False
    ))
    
    final_status_response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert final_status_response.status_code == 200
    assert final_status_response.json()["onboarding_completed"] is True
    assert final_status_response.json()["should_show_onboarding"] is False


def test_skip_onboarding_flow(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test skip onboarding flow: status → skip → status
    
    **Validates: Skip functionality**
    """
    from app.schemas.onboarding import OnboardingStatus
    
    mock_instance = mock_onboarding_service.return_value
    
    # Step 1: Get initial status
    mock_instance.get_onboarding_status = AsyncMock(return_value=OnboardingStatus(
        onboarding_completed=False,
        onboarding_step=None,
        onboarding_skipped=False,
        tooltip_tour_completed=False,
        should_show_onboarding=True
    ))
    
    status_response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert status_response.status_code == 200
    assert status_response.json()["should_show_onboarding"] is True
    
    # Step 2: Skip onboarding
    mock_instance.mark_onboarding_skipped = AsyncMock()
    
    skip_response = client.post(
        "/api/onboarding/skip",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert skip_response.status_code == 200
    
    # Step 3: Get status after skip
    mock_instance.get_onboarding_status = AsyncMock(return_value=OnboardingStatus(
        onboarding_completed=False,
        onboarding_step=None,
        onboarding_skipped=True,
        tooltip_tour_completed=False,
        should_show_onboarding=False
    ))
    
    final_status_response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert final_status_response.status_code == 200
    assert final_status_response.json()["onboarding_skipped"] is True
    assert final_status_response.json()["should_show_onboarding"] is False


def test_error_handling_service_failure(client, auth_token, mock_supabase, mock_onboarding_service):
    """
    Test error handling when OnboardingService fails
    
    **Validates: Error handling**
    """
    from app.services.onboarding_service import OnboardingServiceError
    
    mock_instance = mock_onboarding_service.return_value
    mock_instance.get_onboarding_status = AsyncMock(
        side_effect=OnboardingServiceError("Database error")
    )
    
    response = client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    
    # Should return user-friendly error message
    data = response.json()
    assert "detail" in data
    assert "無法取得引導進度" in data["detail"]
