"""
Tests for Notification Preferences API Endpoints

Tests the new personalized notification frequency API endpoints including
preference management, preview functionality, and status checking.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.user_notification_preferences import UserNotificationPreferences


class TestNotificationPreferencesAPI:
    """Test cases for notification preferences API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {"user_id": "test_user_123", "discord_id": "123456789012345678"}

    @pytest.fixture
    def sample_preferences(self):
        """Sample user notification preferences."""
        return UserNotificationPreferences(
            id=uuid4(),
            user_id=uuid4(),
            frequency="weekly",
            notification_time=time(18, 0),
            timezone="Asia/Taipei",
            dm_enabled=True,
            email_enabled=False,
        )

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.UserNotificationPreferencesRepository")
    @patch("app.api.notifications.PreferenceService")
    def test_get_notification_preferences_success(
        self,
        mock_preference_service_class,
        mock_repo_class,
        mock_supabase_class,
        mock_get_current_user,
        client,
        mock_user,
        sample_preferences,
    ):
        """Test successful retrieval of notification preferences."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user.return_value = str(sample_preferences.user_id)
        mock_supabase_class.return_value = mock_supabase

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_preference_service = AsyncMock()
        mock_preference_service.get_user_preferences.return_value = sample_preferences
        mock_preference_service_class.return_value = mock_preference_service

        # Make request
        response = client.get("/api/notifications/preferences")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["frequency"] == "weekly"
        assert data["data"]["timezone"] == "Asia/Taipei"
        assert data["data"]["dmEnabled"] is True

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.UserNotificationPreferencesRepository")
    @patch("app.api.notifications.PreferenceService")
    @patch("app.api.notifications.get_dynamic_scheduler")
    def test_update_notification_preferences_success(
        self,
        mock_get_dynamic_scheduler,
        mock_preference_service_class,
        mock_repo_class,
        mock_supabase_class,
        mock_get_current_user,
        client,
        mock_user,
        sample_preferences,
    ):
        """Test successful update of notification preferences."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user.return_value = str(sample_preferences.user_id)
        mock_supabase_class.return_value = mock_supabase

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Updated preferences
        updated_preferences = UserNotificationPreferences(
            id=sample_preferences.id,
            user_id=sample_preferences.user_id,
            frequency="daily",
            notification_time=time(9, 0),
            timezone="America/New_York",
            dm_enabled=True,
            email_enabled=True,
        )

        mock_preference_service = AsyncMock()
        mock_preference_service.update_preferences.return_value = updated_preferences
        mock_preference_service_class.return_value = mock_preference_service

        mock_scheduler = AsyncMock()
        mock_scheduler.reschedule_user_notification.return_value = None
        mock_get_dynamic_scheduler.return_value = mock_scheduler

        # Make request
        update_data = {
            "frequency": "daily",
            "notificationTime": "09:00",
            "timezone": "America/New_York",
            "emailEnabled": True,
        }
        response = client.put("/api/notifications/preferences", json=update_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["frequency"] == "daily"
        assert data["data"]["timezone"] == "America/New_York"
        assert data["data"]["emailEnabled"] is True

        # Verify scheduler was called
        mock_scheduler.reschedule_user_notification.assert_called_once()

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.TimezoneConverter")
    def test_preview_notification_time_success(
        self, mock_timezone_converter, mock_get_current_user, client, mock_user
    ):
        """Test successful notification time preview."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        from datetime import datetime

        next_time = datetime(2024, 1, 5, 10, 0, 0)  # UTC time
        local_time = datetime(2024, 1, 5, 18, 0, 0)  # Local time

        mock_timezone_converter.get_next_notification_time.return_value = next_time
        mock_timezone_converter.convert_to_user_time.return_value = local_time

        # Make request
        params = {"frequency": "weekly", "notification_time": "18:00", "timezone": "Asia/Taipei"}
        response = client.get("/api/notifications/preferences/preview", params=params)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["next_notification_time"] is not None
        assert data["data"]["local_time"] is not None
        assert "下次通知時間" in data["data"]["message"]

    @patch("app.api.notifications.get_current_user")
    def test_preview_notification_time_disabled(self, mock_get_current_user, client, mock_user):
        """Test notification time preview for disabled notifications."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        # Make request with disabled frequency
        params = {"frequency": "disabled", "notification_time": "18:00", "timezone": "Asia/Taipei"}

        with patch(
            "app.api.notifications.TimezoneConverter.get_next_notification_time", return_value=None
        ):
            response = client.get("/api/notifications/preferences/preview", params=params)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["next_notification_time"] is None
        assert data["data"]["message"] == "通知已停用"

    def test_preview_notification_time_invalid_frequency(self, client):
        """Test notification time preview with invalid frequency."""
        # Make request with invalid frequency
        params = {"frequency": "invalid", "notification_time": "18:00", "timezone": "Asia/Taipei"}

        with patch("app.api.notifications.get_current_user", return_value={"user_id": "test"}):
            response = client.get("/api/notifications/preferences/preview", params=params)

        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid frequency" in data["detail"]

    def test_get_supported_timezones_success(self, client):
        """Test successful retrieval of supported timezones."""
        # Make request
        response = client.get("/api/notifications/preferences/timezones")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "timezones" in data["data"]
        assert data["data"]["total"] > 0

        # Check timezone format
        timezones = data["data"]["timezones"]
        assert len(timezones) > 0

        first_timezone = timezones[0]
        assert "value" in first_timezone
        assert "label" in first_timezone
        assert "offset" in first_timezone

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.get_dynamic_scheduler")
    def test_get_notification_status_scheduled(
        self,
        mock_get_dynamic_scheduler,
        mock_supabase_class,
        mock_get_current_user,
        client,
        mock_user,
    ):
        """Test getting notification status when notification is scheduled."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user.return_value = str(uuid4())
        mock_supabase_class.return_value = mock_supabase

        mock_scheduler = AsyncMock()
        job_info = {
            "job_id": "user_notification_123",
            "next_run_time": "2024-01-05T18:00:00",
            "name": "User Notification",
        }
        mock_scheduler.get_user_job_info.return_value = job_info
        mock_get_dynamic_scheduler.return_value = mock_scheduler

        # Make request
        response = client.get("/api/notifications/preferences/status")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduled"] is True
        assert data["data"]["job_id"] == "user_notification_123"
        assert data["data"]["next_run_time"] == "2024-01-05T18:00:00"

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.get_dynamic_scheduler")
    def test_get_notification_status_not_scheduled(
        self,
        mock_get_dynamic_scheduler,
        mock_supabase_class,
        mock_get_current_user,
        client,
        mock_user,
    ):
        """Test getting notification status when no notification is scheduled."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user.return_value = str(uuid4())
        mock_supabase_class.return_value = mock_supabase

        mock_scheduler = AsyncMock()
        mock_scheduler.get_user_job_info.return_value = None
        mock_get_dynamic_scheduler.return_value = mock_scheduler

        # Make request
        response = client.get("/api/notifications/preferences/status")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduled"] is False
        assert "無排程通知" in data["data"]["message"]

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.get_dynamic_scheduler")
    def test_get_notification_status_scheduler_disabled(
        self, mock_get_dynamic_scheduler, mock_get_current_user, client, mock_user
    ):
        """Test getting notification status when dynamic scheduler is disabled."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_dynamic_scheduler.return_value = None

        # Make request
        response = client.get("/api/notifications/preferences/status")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduled"] is False
        assert "動態排程器未啟用" in data["data"]["message"]

    @patch("app.api.notifications.get_current_user")
    @patch("app.api.notifications.SupabaseService")
    @patch("app.api.notifications.PreferenceService")
    def test_update_preferences_validation_error(
        self,
        mock_preference_service_class,
        mock_supabase_class,
        mock_get_current_user,
        client,
        mock_user,
    ):
        """Test update preferences with validation error."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user

        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user.return_value = str(uuid4())
        mock_supabase_class.return_value = mock_supabase

        from app.core.errors import ValidationError

        mock_preference_service = AsyncMock()
        mock_preference_service.update_preferences.side_effect = ValidationError(
            "Invalid time format"
        )
        mock_preference_service_class.return_value = mock_preference_service

        # Make request with invalid data
        update_data = {"notificationTime": "25:00"}  # Invalid time
        response = client.put("/api/notifications/preferences", json=update_data)

        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid time format" in data["detail"]
