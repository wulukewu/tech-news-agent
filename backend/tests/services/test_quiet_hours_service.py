"""
Unit tests for QuietHoursService

Tests the quiet hours service functionality including time range checking,
timezone conversion, and database operations.
"""

from datetime import datetime, time
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.exceptions import SupabaseServiceError
from app.services.quiet_hours_service import QuietHoursService, QuietHoursSettings


class TestQuietHoursSettings:
    """Test QuietHoursSettings data class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        user_id = uuid4()
        settings = QuietHoursSettings(
            id=uuid4(),
            user_id=user_id,
            start_time=time(22, 0),
            end_time=time(8, 0),
            timezone="Asia/Taipei",
            weekdays=[1, 2, 3, 4, 5],
            enabled=True,
            created_at=datetime(2026, 4, 20, 10, 0, 0),
            updated_at=datetime(2026, 4, 20, 11, 0, 0),
        )

        result = settings.to_dict()

        assert result["user_id"] == str(user_id)
        assert result["start_time"] == "22:00:00"
        assert result["end_time"] == "08:00:00"
        assert result["timezone"] == "Asia/Taipei"
        assert result["weekdays"] == [1, 2, 3, 4, 5]
        assert result["enabled"] is True

    def test_from_dict(self):
        """Test creation from dictionary."""
        user_id = uuid4()
        data = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "start_time": "22:00:00",
            "end_time": "08:00:00",
            "timezone": "Asia/Taipei",
            "weekdays": [1, 2, 3, 4, 5],
            "enabled": True,
            "created_at": "2026-04-20T10:00:00",
            "updated_at": "2026-04-20T11:00:00",
        }

        settings = QuietHoursSettings.from_dict(data)

        assert settings.user_id == user_id
        assert settings.start_time == time(22, 0)
        assert settings.end_time == time(8, 0)
        assert settings.timezone == "Asia/Taipei"
        assert settings.weekdays == [1, 2, 3, 4, 5]
        assert settings.enabled is True


class TestQuietHoursService:
    """Test QuietHoursService functionality."""

    @pytest.fixture
    def mock_supabase_service(self):
        """Create mock SupabaseService."""
        mock_service = Mock()
        mock_service.client = Mock()
        mock_service.client.table = Mock()
        return mock_service

    @pytest.fixture
    def service(self, mock_supabase_service):
        """Create QuietHoursService with mocked dependencies."""
        return QuietHoursService(mock_supabase_service)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()

    @pytest.fixture
    def sample_quiet_hours_data(self, sample_user_id):
        """Sample quiet hours data."""
        return {
            "id": str(uuid4()),
            "user_id": str(sample_user_id),
            "start_time": "22:00:00",
            "end_time": "08:00:00",
            "timezone": "Asia/Taipei",
            "weekdays": [1, 2, 3, 4, 5, 6, 7],
            "enabled": True,
            "created_at": "2026-04-20T10:00:00",
            "updated_at": "2026-04-20T11:00:00",
        }

    @pytest.mark.asyncio
    async def test_get_quiet_hours_success(self, service, sample_user_id, sample_quiet_hours_data):
        """Test successful retrieval of quiet hours."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = await service.get_quiet_hours(sample_user_id)

        # Verify
        assert result is not None
        assert result.user_id == sample_user_id
        assert result.start_time == time(22, 0)
        assert result.end_time == time(8, 0)
        assert result.timezone == "Asia/Taipei"
        assert result.enabled is True

    @pytest.mark.asyncio
    async def test_get_quiet_hours_not_found(self, service, sample_user_id):
        """Test retrieval when no quiet hours exist."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = []
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = await service.get_quiet_hours(sample_user_id)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_update_quiet_hours_create_new(self, service, sample_user_id):
        """Test creating new quiet hours settings."""
        # Setup mocks
        # First call (check existing) returns empty
        mock_empty_result = Mock()
        mock_empty_result.data = []

        # Second call (insert) returns new data
        new_data = {
            "id": str(uuid4()),
            "user_id": str(sample_user_id),
            "start_time": "22:00:00",
            "end_time": "08:00:00",
            "timezone": "UTC",
            "weekdays": [1, 2, 3, 4, 5, 6, 7],
            "enabled": True,
            "created_at": "2026-04-20T10:00:00",
            "updated_at": "2026-04-20T10:00:00",
        }
        mock_insert_result = Mock()
        mock_insert_result.data = [new_data]

        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_empty_result
        )
        service.supabase_service.client.table.return_value.insert.return_value.execute.return_value = (
            mock_insert_result
        )

        # Execute
        result = await service.update_quiet_hours(
            user_id=sample_user_id, start_time=time(22, 0), end_time=time(8, 0), enabled=True
        )

        # Verify
        assert result is not None
        assert result.user_id == sample_user_id
        assert result.start_time == time(22, 0)
        assert result.end_time == time(8, 0)
        assert result.enabled is True

    @pytest.mark.asyncio
    async def test_update_quiet_hours_update_existing(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test updating existing quiet hours settings."""
        # Setup mocks
        # First call (check existing) returns data
        mock_existing_result = Mock()
        mock_existing_result.data = [sample_quiet_hours_data]

        # Second call (update) returns updated data
        updated_data = sample_quiet_hours_data.copy()
        updated_data["enabled"] = False
        mock_update_result = Mock()
        mock_update_result.data = [updated_data]

        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_result
        )
        service.supabase_service.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_update_result
        )

        # Execute
        result = await service.update_quiet_hours(user_id=sample_user_id, enabled=False)

        # Verify
        assert result is not None
        assert result.enabled is False

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_disabled(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test quiet hours check when disabled."""
        # Setup mock with disabled quiet hours
        disabled_data = sample_quiet_hours_data.copy()
        disabled_data["enabled"] = False
        mock_result = Mock()
        mock_result.data = [disabled_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id)

        # Verify
        assert is_quiet is False
        assert settings is not None
        assert settings.enabled is False

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_wrong_weekday(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test quiet hours check on wrong weekday."""
        # Setup mock with weekdays 1-5 (Monday-Friday)
        weekday_data = sample_quiet_hours_data.copy()
        weekday_data["weekdays"] = [1, 2, 3, 4, 5]  # Monday-Friday only
        mock_result = Mock()
        mock_result.data = [weekday_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test on Saturday (weekday 6)
        saturday = datetime(2026, 4, 26, 23, 0, 0)  # Saturday 11 PM

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id, saturday)

        # Verify
        assert is_quiet is False
        assert settings is not None

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_same_day_range(self, service, sample_user_id):
        """Test quiet hours check with same-day range (9 AM to 5 PM)."""
        # Setup mock with same-day range
        same_day_data = {
            "id": str(uuid4()),
            "user_id": str(sample_user_id),
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "timezone": "UTC",
            "weekdays": [1, 2, 3, 4, 5, 6, 7],
            "enabled": True,
            "created_at": "2026-04-20T10:00:00",
            "updated_at": "2026-04-20T10:00:00",
        }
        mock_result = Mock()
        mock_result.data = [same_day_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test during quiet hours (12 PM)
        test_time = datetime(2026, 4, 21, 12, 0, 0)  # Monday 12 PM UTC

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id, test_time)

        # Verify
        assert is_quiet is True
        assert settings is not None

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_overnight_range(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test quiet hours check with overnight range (10 PM to 8 AM)."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test during quiet hours (11 PM)
        test_time = datetime(2026, 4, 21, 23, 0, 0)  # Monday 11 PM UTC

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id, test_time)

        # Verify
        assert is_quiet is True
        assert settings is not None

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_overnight_range_early_morning(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test quiet hours check with overnight range in early morning."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test during quiet hours (6 AM)
        test_time = datetime(2026, 4, 22, 6, 0, 0)  # Tuesday 6 AM UTC

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id, test_time)

        # Verify
        assert is_quiet is True
        assert settings is not None

    @pytest.mark.asyncio
    async def test_is_in_quiet_hours_outside_range(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test quiet hours check outside the range."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test outside quiet hours (2 PM)
        test_time = datetime(2026, 4, 21, 14, 0, 0)  # Monday 2 PM UTC

        # Execute
        is_quiet, settings = await service.is_in_quiet_hours(sample_user_id, test_time)

        # Verify
        assert is_quiet is False
        assert settings is not None

    @pytest.mark.asyncio
    async def test_get_next_notification_time_not_in_quiet_hours(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test getting next notification time when not in quiet hours."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test outside quiet hours
        base_time = datetime(2026, 4, 21, 14, 0, 0)  # Monday 2 PM UTC

        # Execute
        result = await service.get_next_notification_time(sample_user_id, base_time)

        # Verify - should return the base time since not in quiet hours
        assert result == base_time

    @pytest.mark.asyncio
    async def test_get_next_notification_time_in_quiet_hours(
        self, service, sample_user_id, sample_quiet_hours_data
    ):
        """Test getting next notification time when in quiet hours."""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [sample_quiet_hours_data]
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Test during quiet hours (11 PM in Taipei = 3 PM UTC)
        base_time = datetime(2026, 4, 21, 15, 0, 0)  # Monday 3 PM UTC (11 PM Taipei)

        # Execute
        result = await service.get_next_notification_time(sample_user_id, base_time)

        # Verify - should return time after quiet hours end
        assert result is not None
        assert result > base_time

    def test_validate_weekdays_valid(self, service):
        """Test weekdays validation with valid input."""
        # Should not raise exception
        service._validate_weekdays([1, 2, 3, 4, 5])
        service._validate_weekdays([7])  # Sunday only
        service._validate_weekdays([1, 2, 3, 4, 5, 6, 7])  # All days

    def test_validate_weekdays_invalid(self, service):
        """Test weekdays validation with invalid input."""
        with pytest.raises(ValueError):
            service._validate_weekdays([])  # Empty list

        with pytest.raises(ValueError):
            service._validate_weekdays([0])  # Invalid day

        with pytest.raises(ValueError):
            service._validate_weekdays([8])  # Invalid day

        with pytest.raises(ValueError):
            service._validate_weekdays(None)  # None

    def test_validate_timezone_valid(self, service):
        """Test timezone validation with valid input."""
        # Should not raise exception
        service._validate_timezone("UTC")
        service._validate_timezone("Asia/Taipei")
        service._validate_timezone("America/New_York")

    def test_validate_timezone_invalid(self, service):
        """Test timezone validation with invalid input."""
        with pytest.raises(ValueError):
            service._validate_timezone("Invalid/Timezone")

        with pytest.raises(ValueError):
            service._validate_timezone("Not_A_Timezone")

    def test_is_time_in_range_same_day(self, service):
        """Test time range checking for same-day ranges."""
        start_time = time(9, 0)  # 9 AM
        end_time = time(17, 0)  # 5 PM

        # Inside range
        assert service._is_time_in_range(time(12, 0), start_time, end_time) is True
        assert service._is_time_in_range(time(9, 0), start_time, end_time) is True
        assert service._is_time_in_range(time(17, 0), start_time, end_time) is True

        # Outside range
        assert service._is_time_in_range(time(8, 0), start_time, end_time) is False
        assert service._is_time_in_range(time(18, 0), start_time, end_time) is False

    def test_is_time_in_range_overnight(self, service):
        """Test time range checking for overnight ranges."""
        start_time = time(22, 0)  # 10 PM
        end_time = time(8, 0)  # 8 AM

        # Inside range (late night)
        assert service._is_time_in_range(time(23, 0), start_time, end_time) is True
        assert service._is_time_in_range(time(22, 0), start_time, end_time) is True

        # Inside range (early morning)
        assert service._is_time_in_range(time(7, 0), start_time, end_time) is True
        assert service._is_time_in_range(time(8, 0), start_time, end_time) is True

        # Outside range
        assert service._is_time_in_range(time(12, 0), start_time, end_time) is False
        assert service._is_time_in_range(time(18, 0), start_time, end_time) is False

    @pytest.mark.asyncio
    async def test_create_default_quiet_hours(self, service, sample_user_id):
        """Test creating default quiet hours."""
        # Setup mock
        new_data = {
            "id": str(uuid4()),
            "user_id": str(sample_user_id),
            "start_time": "22:00:00",
            "end_time": "08:00:00",
            "timezone": "Asia/Taipei",
            "weekdays": [1, 2, 3, 4, 5, 6, 7],
            "enabled": False,  # Default is disabled
            "created_at": "2026-04-20T10:00:00",
            "updated_at": "2026-04-20T10:00:00",
        }

        # Mock the update_quiet_hours method
        service.update_quiet_hours = AsyncMock(return_value=QuietHoursSettings.from_dict(new_data))

        # Execute
        result = await service.create_default_quiet_hours(sample_user_id, "Asia/Taipei")

        # Verify
        assert result is not None
        assert result.user_id == sample_user_id
        assert result.start_time == time(22, 0)
        assert result.end_time == time(8, 0)
        assert result.timezone == "Asia/Taipei"
        assert result.enabled is False  # Default is disabled

    @pytest.mark.asyncio
    async def test_delete_quiet_hours(self, service, sample_user_id):
        """Test deleting quiet hours."""
        # Setup mock
        mock_result = Mock()
        service.supabase_service.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = await service.delete_quiet_hours(sample_user_id)

        # Verify
        assert result is True
        service.supabase_service.client.table.assert_called_with("user_quiet_hours")

    @pytest.mark.asyncio
    async def test_error_handling(self, service, sample_user_id):
        """Test error handling in service methods."""
        # Setup mock to raise exception
        service.supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception(
            "Database error"
        )

        # Execute and verify exception is raised
        with pytest.raises(SupabaseServiceError):
            await service.get_quiet_hours(sample_user_id)
