"""
Integration tests for the complete notification system integration.

These tests verify that all components are properly wired together and work
as a cohesive system.

Requirements: All requirements integration testing
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.notification_system_integration import (
    NotificationSystemIntegration,
    initialize_notification_system_integration,
)
from app.services.supabase_service import SupabaseService


class TestNotificationSystemIntegration:
    """Test suite for notification system integration."""

    @pytest.fixture
    def mock_supabase_service(self):
        """Mock Supabase service."""
        mock_service = MagicMock(spec=SupabaseService)
        mock_service.client = MagicMock()
        return mock_service

    @pytest.fixture
    def mock_dynamic_scheduler(self):
        """Mock dynamic scheduler."""
        mock_scheduler = AsyncMock()
        mock_scheduler.schedule_user_notification = AsyncMock()
        mock_scheduler.cancel_user_notification = AsyncMock()
        mock_scheduler.reschedule_user_notification = AsyncMock()
        mock_scheduler.get_user_job_info = AsyncMock()
        mock_scheduler.get_scheduler_stats = AsyncMock(
            return_value={
                "total_jobs": 10,
                "user_notification_jobs": 8,
                "scheduler_running": True,
            }
        )
        mock_scheduler.cleanup_expired_jobs = AsyncMock(return_value=2)
        return mock_scheduler

    @pytest.fixture
    def mock_bot_client(self):
        """Mock Discord bot client."""
        mock_bot = MagicMock()
        mock_bot.is_ready.return_value = True
        return mock_bot

    @pytest.fixture
    def integration_service(self, mock_supabase_service, mock_dynamic_scheduler, mock_bot_client):
        """Create integration service with mocked dependencies."""
        with patch(
            "app.services.notification_system_integration.UserNotificationPreferencesRepository"
        ), patch("app.services.notification_system_integration.PreferenceService"), patch(
            "app.services.notification_system_integration.LockManager"
        ), patch(
            "app.services.notification_system_integration.NotificationService"
        ), patch(
            "app.services.notification_system_integration.get_preference_event_system"
        ):
            service = NotificationSystemIntegration(
                supabase_service=mock_supabase_service,
                dynamic_scheduler=mock_dynamic_scheduler,
                bot_client=mock_bot_client,
            )
            return service

    @pytest.mark.asyncio
    async def test_integration_service_initialization(self, integration_service):
        """Test that the integration service initializes all components properly."""
        # Verify that all required services are initialized
        assert integration_service.supabase_service is not None
        assert integration_service.dynamic_scheduler is not None
        assert integration_service.bot_client is not None
        assert integration_service.preferences_repo is not None
        assert integration_service.preference_service is not None
        assert integration_service.lock_manager is not None
        assert integration_service.notification_service is not None
        assert integration_service.event_system is not None

    @pytest.mark.asyncio
    async def test_send_user_notification_integration(self, integration_service):
        """Test the complete user notification flow."""
        user_id = uuid4()

        # Mock preference service to return enabled preferences
        mock_preferences = MagicMock()
        mock_preferences.frequency = "weekly"
        mock_preferences.dm_enabled = True
        mock_preferences.email_enabled = False

        integration_service.preference_service.get_user_preferences = AsyncMock(
            return_value=mock_preferences
        )

        # Mock notification service to return successful results
        from app.services.notification_service import NotificationResult

        mock_results = [NotificationResult(True, "discord_dm")]

        integration_service.notification_service.send_notification = AsyncMock(
            return_value=mock_results
        )

        # Test sending notification
        results = await integration_service.send_user_notification(
            user_id=user_id, notification_type="test", subject="Test Notification"
        )

        # Verify the flow
        integration_service.preference_service.get_user_preferences.assert_called_once_with(user_id)
        integration_service.notification_service.send_notification.assert_called_once()

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].channel == "discord_dm"

    @pytest.mark.asyncio
    async def test_schedule_user_notifications_integration(self, integration_service):
        """Test the user notification scheduling integration."""
        user_id = uuid4()

        # Mock preference service
        mock_preferences = MagicMock()
        mock_preferences.frequency = "weekly"
        mock_preferences.notification_time = "18:00"
        mock_preferences.timezone = "Asia/Taipei"

        integration_service.preference_service.get_user_preferences = AsyncMock(
            return_value=mock_preferences
        )

        # Test scheduling
        success = await integration_service.schedule_user_notifications(user_id)

        # Verify the flow
        integration_service.preference_service.get_user_preferences.assert_called_once_with(user_id)
        integration_service.dynamic_scheduler.schedule_user_notification.assert_called_once_with(
            user_id, mock_preferences
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_update_user_preferences_integration(self, integration_service):
        """Test the user preference update integration."""
        user_id = uuid4()
        updates = {"frequency": "daily", "notification_time": "09:00"}

        # Mock preference service
        mock_updated_preferences = MagicMock()
        mock_updated_preferences.frequency = "daily"
        mock_updated_preferences.notification_time = "09:00"

        integration_service.preference_service.update_preferences = AsyncMock(
            return_value=mock_updated_preferences
        )

        # Test updating preferences
        result = await integration_service.update_user_preferences(
            user_id=user_id, updates=updates, source="test"
        )

        # Verify the flow
        integration_service.preference_service.update_preferences.assert_called_once()
        assert result == mock_updated_preferences

    @pytest.mark.asyncio
    async def test_initialize_user_notifications_integration(self, integration_service):
        """Test the user notification initialization integration."""
        user_id = uuid4()

        # Mock preference service
        mock_preferences = MagicMock()
        mock_preferences.frequency = "weekly"
        mock_preferences.notification_time = "18:00"
        mock_preferences.timezone = "Asia/Taipei"

        integration_service.preference_service.create_default_preferences = AsyncMock(
            return_value=mock_preferences
        )

        # Test initialization
        success = await integration_service.initialize_user_notifications(user_id)

        # Verify the flow
        integration_service.preference_service.create_default_preferences.assert_called_once_with(
            user_id, source="system"
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_get_user_notification_status_integration(self, integration_service):
        """Test getting comprehensive user notification status."""
        user_id = uuid4()

        # Mock preference service
        mock_preferences = MagicMock()
        mock_preferences.frequency = "weekly"
        mock_preferences.notification_time = "18:00"
        mock_preferences.timezone = "Asia/Taipei"
        mock_preferences.dm_enabled = True
        mock_preferences.email_enabled = False

        integration_service.preference_service.get_user_preferences = AsyncMock(
            return_value=mock_preferences
        )

        # Mock scheduler job info
        mock_job_info = {"job_id": "user_notification_123", "next_run_time": "2024-01-01T18:00:00Z"}
        integration_service.dynamic_scheduler.get_user_job_info = AsyncMock(
            return_value=mock_job_info
        )

        # Mock lock manager stats
        mock_lock_stats = {"total_locks": 5, "active_locks": 3, "expired_locks": 2}
        integration_service.lock_manager.get_lock_statistics = AsyncMock(
            return_value=mock_lock_stats
        )

        # Test getting status
        status = await integration_service.get_user_notification_status(user_id)

        # Verify the comprehensive status
        assert status["user_id"] == str(user_id)
        assert status["preferences"]["frequency"] == "weekly"
        assert status["scheduling"]["is_scheduled"] is True
        assert status["scheduling"]["next_run_time"] == "2024-01-01T18:00:00Z"
        assert status["system"]["dynamic_scheduler_available"] is True
        assert status["system"]["lock_manager_stats"] == mock_lock_stats

    @pytest.mark.asyncio
    async def test_get_system_health_integration(self, integration_service):
        """Test getting comprehensive system health."""
        # Mock all component health checks
        integration_service.preference_service.get_users_with_frequency = AsyncMock(
            return_value=[MagicMock(), MagicMock()]  # 2 users
        )

        # Test getting system health
        health = await integration_service.get_system_health()

        # Verify comprehensive health report
        assert "overall_status" in health
        assert "components" in health
        assert "statistics" in health

        # Check component health
        components = health["components"]
        assert "preference_service" in components
        assert "dynamic_scheduler" in components
        assert "lock_manager" in components
        assert "notification_service" in components

        # Check statistics
        statistics = health["statistics"]
        assert "event_system" in statistics

    @pytest.mark.asyncio
    async def test_cleanup_system_resources_integration(self, integration_service):
        """Test system resource cleanup integration."""
        # Mock cleanup operations
        integration_service.lock_manager.cleanup_expired_locks = AsyncMock(return_value=3)
        integration_service.dynamic_scheduler.cleanup_expired_jobs = AsyncMock(return_value=2)

        # Test cleanup
        results = await integration_service.cleanup_system_resources()

        # Verify cleanup results
        assert results["overall_success"] is True
        assert results["components"]["lock_manager"]["success"] is True
        assert results["components"]["lock_manager"]["expired_locks_cleaned"] == 3
        assert results["components"]["dynamic_scheduler"]["success"] is True
        assert results["components"]["dynamic_scheduler"]["expired_jobs_cleaned"] == 2

    @pytest.mark.asyncio
    async def test_preference_change_event_handling(self, integration_service):
        """Test that preference change events trigger scheduler updates."""
        user_id = uuid4()

        # Create mock preference change event
        from app.services.preference_event_system import PreferenceChangeEvent

        mock_old_preferences = MagicMock()
        mock_old_preferences.frequency = "weekly"

        mock_new_preferences = MagicMock()
        mock_new_preferences.frequency = "daily"
        mock_new_preferences.notification_time = "09:00"
        mock_new_preferences.timezone = "Asia/Taipei"

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=mock_old_preferences,
            new_preferences=mock_new_preferences,
            changed_fields=["frequency"],
            source="test",
        )

        # Test event handling
        await integration_service._handle_preference_change(event)

        # Verify scheduler was updated
        integration_service.dynamic_scheduler.reschedule_user_notification.assert_called_once_with(
            user_id, mock_new_preferences
        )

    @pytest.mark.asyncio
    async def test_disabled_notifications_handling(self, integration_service):
        """Test handling of disabled notifications."""
        user_id = uuid4()

        # Mock preference service to return disabled preferences
        mock_preferences = MagicMock()
        mock_preferences.frequency = "disabled"

        integration_service.preference_service.get_user_preferences = AsyncMock(
            return_value=mock_preferences
        )

        # Test sending notification with disabled preferences
        results = await integration_service.send_user_notification(
            user_id=user_id, notification_type="test"
        )

        # Verify notification was skipped
        assert len(results) == 1
        assert results[0].success is False
        assert "disabled" in results[0].error

        # Verify notification service was not called
        integration_service.notification_service.send_notification.assert_not_called()


class TestGlobalIntegrationService:
    """Test the global integration service initialization."""

    @pytest.mark.asyncio
    async def test_global_service_initialization(self):
        """Test global service initialization and retrieval."""
        with patch("app.services.notification_system_integration.SupabaseService"), patch(
            "app.services.notification_system_integration.UserNotificationPreferencesRepository"
        ), patch("app.services.notification_system_integration.PreferenceService"), patch(
            "app.services.notification_system_integration.LockManager"
        ), patch(
            "app.services.notification_system_integration.NotificationService"
        ), patch(
            "app.services.notification_system_integration.get_preference_event_system"
        ):
            # Test initialization
            mock_supabase = MagicMock()
            mock_scheduler = MagicMock()
            mock_bot = MagicMock()

            service = initialize_notification_system_integration(
                supabase_service=mock_supabase,
                dynamic_scheduler=mock_scheduler,
                bot_client=mock_bot,
            )

            # Verify service was created
            assert service is not None
            assert isinstance(service, NotificationSystemIntegration)

            # Test retrieval
            from app.services.notification_system_integration import (
                get_notification_system_integration,
            )

            retrieved_service = get_notification_system_integration()

            assert retrieved_service is service
