"""
Integration tests for notifications API endpoints

Tests the complete flow from API endpoints to services.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user_123", "discord_id": "discord_123", "username": "testuser"}


class TestNotificationsAPI:
    """Integration tests for notifications API"""

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.NotificationSettingsService")
    def test_get_notification_settings_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful retrieval of notification settings"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.enabled = True
        mock_settings.dm_enabled = True
        mock_settings.email_enabled = False
        mock_settings.frequency = "immediate"

        mock_service.get_notification_settings.return_value = mock_settings
        mock_service_class.return_value = mock_service

        # Make request
        response = client.get("/api/notifications/settings")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.NotificationSettingsService")
    def test_update_notification_settings_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful update of notification settings"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.enabled = True
        mock_settings.dm_enabled = False

        mock_service.update_notification_settings.return_value = mock_settings
        mock_service_class.return_value = mock_service

        # Make request
        response = client.patch("/api/notifications/settings", json={"dmEnabled": False})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.NotificationSettingsService")
    def test_send_test_notification_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful sending of test notification"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_service.send_test_notification.return_value = None
        mock_service_class.return_value = mock_service

        # Make request
        response = client.post("/api/notifications/test")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data["data"]

    @patch("app.api.notifications.get_current_user")
    def test_get_notification_history_success(self, mock_get_user, client, mock_user):
        """Test successful retrieval of notification history"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        # Make request
        response = client.get("/api/notifications/history")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totalSent" in data["data"]
        assert "totalFailed" in data["data"]

    def test_get_notification_settings_unauthorized(self, client):
        """Test notifications endpoint without authentication"""
        response = client.get("/api/notifications/settings")

        # Should return 401 or 403 (depending on auth implementation)
        assert response.status_code in [401, 403]

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.NotificationSettingsService")
    def test_get_notification_settings_service_error(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test handling of service errors"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_service.get_notification_settings.side_effect = Exception("Service error")
        mock_service_class.return_value = mock_service

        # Make request
        response = client.get("/api/notifications/settings")

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "系統錯誤" in data["detail"]
