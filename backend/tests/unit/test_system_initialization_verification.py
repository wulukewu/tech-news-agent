"""
System Initialization Verification Tests

Quick verification that system initialization components are properly implemented.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.supabase_service import SupabaseService
from app.services.system_initialization import (
    SystemInitializationService,
    initialize_personalized_notification_system,
)


class TestSystemInitializationVerification:
    """Test system initialization service verification."""

    @pytest.fixture
    def mock_supabase_service(self):
        """Create a mock Supabase service."""
        service = MagicMock(spec=SupabaseService)
        service.client = MagicMock()
        return service

    @pytest.fixture
    def system_init_service(self, mock_supabase_service):
        """Create a SystemInitializationService instance."""
        return SystemInitializationService(mock_supabase_service)

    def test_system_initialization_service_creation(self, system_init_service):
        """Test that SystemInitializationService can be created."""
        assert system_init_service is not None
        assert hasattr(system_init_service, "initialize_system")
        assert hasattr(system_init_service, "_migrate_existing_users")
        assert hasattr(system_init_service, "_initialize_user_scheduling")
        assert hasattr(system_init_service, "_start_background_cleanup")
        assert hasattr(system_init_service, "_validate_system_health")

    @pytest.mark.asyncio
    async def test_initialize_personalized_notification_system_function(
        self, mock_supabase_service
    ):
        """Test that the main initialization function exists and can be called."""
        with patch(
            "app.services.system_initialization.SystemInitializationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.initialize_system.return_value = {
                "success": True,
                "migration": {"migrated_count": 5},
                "scheduling": {"scheduled_count": 3},
                "cleanup": {"success": True},
                "validation": {"success": True},
            }
            mock_service_class.return_value = mock_service

            result = await initialize_personalized_notification_system(mock_supabase_service)

            assert result["success"] is True
            assert "migration" in result
            assert "scheduling" in result
            mock_service_class.assert_called_once_with(mock_supabase_service)
            mock_service.initialize_system.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_initialization_methods_exist(self, system_init_service):
        """Test that all required initialization methods exist."""
        # Test that all required methods are callable
        assert callable(getattr(system_init_service, "initialize_system"))
        assert callable(getattr(system_init_service, "_migrate_existing_users"))
        assert callable(getattr(system_init_service, "_initialize_user_scheduling"))
        assert callable(getattr(system_init_service, "_start_background_cleanup"))
        assert callable(getattr(system_init_service, "_validate_system_health"))

    @pytest.mark.asyncio
    async def test_migrate_existing_users_method_structure(self, system_init_service):
        """Test that migrate_existing_users method has proper structure."""
        # Mock the database response
        system_init_service.supabase_service.client.table.return_value.select.return_value.execute.return_value.data = (
            []
        )

        with patch(
            "app.services.system_initialization.get_notification_system_integration"
        ) as mock_get_integration:
            mock_integration = AsyncMock()
            mock_get_integration.return_value = mock_integration

            result = await system_init_service._migrate_existing_users()

            assert isinstance(result, dict)
            assert "success" in result
            assert "total_users" in result
            assert "migrated_count" in result

    @pytest.mark.asyncio
    async def test_initialize_user_scheduling_method_structure(self, system_init_service):
        """Test that initialize_user_scheduling method has proper structure."""
        # Mock the preferences repository
        system_init_service.preferences_repo.list_all = AsyncMock(return_value=[])

        with patch(
            "app.services.system_initialization.get_notification_system_integration"
        ) as mock_get_integration:
            mock_integration = AsyncMock()
            mock_get_integration.return_value = mock_integration

            result = await system_init_service._initialize_user_scheduling()

            assert isinstance(result, dict)
            assert "success" in result
            assert "total_users" in result
            assert "scheduled_count" in result

    @pytest.mark.asyncio
    async def test_start_background_cleanup_method_structure(self, system_init_service):
        """Test that start_background_cleanup method has proper structure."""
        with patch(
            "app.services.system_initialization.get_notification_system_integration"
        ) as mock_get_integration:
            mock_integration = AsyncMock()
            mock_integration.cleanup_system_resources.return_value = {"overall_success": True}
            mock_get_integration.return_value = mock_integration

            result = await system_init_service._start_background_cleanup()

            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_validate_system_health_method_structure(self, system_init_service):
        """Test that validate_system_health method has proper structure."""
        with patch(
            "app.services.system_initialization.get_notification_system_integration"
        ) as mock_get_integration:
            mock_integration = AsyncMock()
            mock_integration.get_system_health.return_value = {"overall_status": "healthy"}
            mock_get_integration.return_value = mock_integration

            result = await system_init_service._validate_system_health()

            assert isinstance(result, dict)
            assert "success" in result
            assert "health" in result
