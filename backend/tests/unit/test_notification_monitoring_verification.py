"""
Notification Monitoring Verification Tests

Quick verification that notification monitoring components are properly implemented.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification_monitoring import (
    NotificationMetrics,
    NotificationMonitoringService,
    get_notification_monitoring_service,
    initialize_notification_monitoring_service,
)
from app.services.supabase_service import SupabaseService


class TestNotificationMonitoringVerification:
    """Test notification monitoring service verification."""

    @pytest.fixture
    def mock_supabase_service(self):
        """Create a mock Supabase service."""
        service = MagicMock(spec=SupabaseService)
        service.client = MagicMock()
        return service

    @pytest.fixture
    def monitoring_service(self, mock_supabase_service):
        """Create a NotificationMonitoringService instance."""
        return NotificationMonitoringService(mock_supabase_service)

    def test_notification_metrics_creation(self):
        """Test that NotificationMetrics can be created and converted to dict."""
        metrics = NotificationMetrics()
        assert metrics is not None

        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert "total_notifications_sent" in metrics_dict
        assert "successful_notifications" in metrics_dict
        assert "failed_notifications" in metrics_dict
        assert "discord_dm_success_rate" in metrics_dict
        assert "email_success_rate" in metrics_dict

    def test_monitoring_service_creation(self, monitoring_service):
        """Test that NotificationMonitoringService can be created."""
        assert monitoring_service is not None
        assert hasattr(monitoring_service, "start_monitoring")
        assert hasattr(monitoring_service, "stop_monitoring")
        assert hasattr(monitoring_service, "get_current_metrics")
        assert hasattr(monitoring_service, "get_metrics_history")
        assert hasattr(monitoring_service, "get_system_report")

    def test_monitoring_service_configuration(self, monitoring_service):
        """Test that monitoring service has proper configuration."""
        assert monitoring_service.health_check_interval > 0
        assert monitoring_service.metrics_collection_interval > 0
        assert isinstance(monitoring_service.alert_thresholds, dict)
        assert "notification_failure_rate" in monitoring_service.alert_thresholds
        assert "lock_contention_rate" in monitoring_service.alert_thresholds

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitoring_service):
        """Test that monitoring can be started and stopped."""
        # Initially not active
        assert not monitoring_service._monitoring_active

        # Mock the monitoring loop to prevent actual background task
        with patch.object(monitoring_service, "_monitoring_loop", new_callable=AsyncMock):
            await monitoring_service.start_monitoring()
            assert monitoring_service._monitoring_active

            await monitoring_service.stop_monitoring()
            assert not monitoring_service._monitoring_active

    @pytest.mark.asyncio
    async def test_get_current_metrics(self, monitoring_service):
        """Test that current metrics can be retrieved."""
        metrics = await monitoring_service.get_current_metrics()

        assert isinstance(metrics, dict)
        assert "metrics" in metrics
        assert "timestamp" in metrics
        assert "monitoring_active" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics_history(self, monitoring_service):
        """Test that metrics history can be retrieved."""
        # Add some test data to history
        test_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_notifications_sent": 10,
            "successful_notifications": 9,
        }
        monitoring_service.metrics_history.append(test_metrics)

        history = await monitoring_service.get_metrics_history(hours=1)
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_system_report(self, monitoring_service):
        """Test that system report can be generated."""
        with patch(
            "app.services.notification_monitoring.get_notification_system_integration"
        ) as mock_get_integration:
            mock_integration = AsyncMock()
            mock_integration.get_system_health.return_value = {"overall_status": "healthy"}
            mock_get_integration.return_value = mock_integration

            report = await monitoring_service.get_system_report()

            assert isinstance(report, dict)
            assert "timestamp" in report
            assert "monitoring_active" in report
            assert "current_metrics" in report

    @pytest.mark.asyncio
    async def test_collect_metrics_method_exists(self, monitoring_service):
        """Test that metrics collection method exists and is callable."""
        assert hasattr(monitoring_service, "_collect_metrics")
        assert callable(getattr(monitoring_service, "_collect_metrics"))

    @pytest.mark.asyncio
    async def test_health_check_method_exists(self, monitoring_service):
        """Test that health check method exists and is callable."""
        assert hasattr(monitoring_service, "_perform_health_check")
        assert callable(getattr(monitoring_service, "_perform_health_check"))

    @pytest.mark.asyncio
    async def test_alert_triggering_method_exists(self, monitoring_service):
        """Test that alert triggering method exists and is callable."""
        assert hasattr(monitoring_service, "_trigger_alert")
        assert callable(getattr(monitoring_service, "_trigger_alert"))

    def test_initialize_monitoring_service_function(self, mock_supabase_service):
        """Test that the initialization function works."""
        service = initialize_notification_monitoring_service(mock_supabase_service)
        assert service is not None
        assert isinstance(service, NotificationMonitoringService)

    def test_get_monitoring_service_function(self, mock_supabase_service):
        """Test that the get service function works."""
        # Initialize first
        initialize_notification_monitoring_service(mock_supabase_service)

        # Then get
        service = get_notification_monitoring_service()
        assert service is not None
        assert isinstance(service, NotificationMonitoringService)

    @pytest.mark.asyncio
    async def test_structured_logging_capabilities(self, monitoring_service):
        """Test that structured logging is properly implemented."""
        # Test alert triggering with structured data
        with patch.object(monitoring_service.logger, "warning") as mock_log:
            await monitoring_service._trigger_alert(
                "warning", "Test alert", {"test_context": "test_value"}
            )

            # Verify structured logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert "ALERT: Test alert" in call_args[0]

    def test_metrics_collection_configuration(self, monitoring_service):
        """Test that metrics collection is properly configured."""
        # Verify alert thresholds are reasonable
        thresholds = monitoring_service.alert_thresholds
        assert 0 < thresholds["notification_failure_rate"] < 1
        assert 0 < thresholds["lock_contention_rate"] < 1
        assert 0 < thresholds["scheduler_job_failure_rate"] < 1
        assert 0 < thresholds["validation_error_rate"] < 1

    def test_metrics_history_management(self, monitoring_service):
        """Test that metrics history is properly managed."""
        assert monitoring_service.max_history_size > 0
        assert isinstance(monitoring_service.metrics_history, list)

        # Test that history has size limit
        assert monitoring_service.max_history_size == 1440  # 24 hours of minute data
