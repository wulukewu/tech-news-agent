"""
Integration tests for TimezoneConverter with PreferenceService.

Tests the integration between TimezoneConverter utility and PreferenceService
to ensure timezone validation works correctly in the full system.

Requirements: 5.3
"""

import zoneinfo
from datetime import datetime

import pytest

from app.core.timezone_converter import TimezoneConverter
from app.schemas.user_notification_preferences import UpdateUserNotificationPreferencesRequest
from app.services.preference_service import PreferenceService


class TestTimezoneConverterIntegration:
    """Integration tests for TimezoneConverter with other services."""

    def test_preference_service_uses_timezone_converter_validation(self):
        """Test that PreferenceService uses TimezoneConverter for timezone validation."""
        # Create a mock preference service (we don't need a real repo for validation testing)
        preference_service = PreferenceService(preferences_repo=None)

        # Test valid timezone
        valid_request = UpdateUserNotificationPreferencesRequest(
            timezone="Asia/Tokyo", notification_time="18:00"
        )

        result = preference_service.validate_preferences(valid_request)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_preference_service_rejects_invalid_timezone(self):
        """Test that PreferenceService rejects invalid timezones using TimezoneConverter."""
        # Create a mock preference service
        preference_service = PreferenceService(preferences_repo=None)

        # Create a request object manually to bypass Pydantic validation
        # This tests the service-level validation specifically
        class MockRequest:
            def __init__(self):
                self.timezone = "Invalid/Timezone"
                self.notification_time = "18:00"

        invalid_request = MockRequest()

        result = preference_service.validate_preferences(invalid_request)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid timezone identifier" in result.errors[0]

    def test_timezone_converter_handles_common_timezones(self):
        """Test TimezoneConverter with commonly used timezones."""
        common_timezones = [
            "UTC",
            "Asia/Taipei",
            "Asia/Tokyo",
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Australia/Sydney",
            "Asia/Shanghai",
            "America/Chicago",
        ]

        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        for timezone in common_timezones:
            # Test timezone validation
            assert TimezoneConverter.is_valid_timezone(timezone) is True

            # Test conversion
            local_time = TimezoneConverter.convert_to_user_time(utc_time, timezone)
            assert local_time.tzinfo == zoneinfo.ZoneInfo(timezone)

            # Test round-trip conversion
            back_to_utc = TimezoneConverter.convert_to_utc(local_time, timezone)
            assert back_to_utc == utc_time

    def test_next_notification_time_calculation_realistic_scenarios(self):
        """Test next notification time calculation for realistic user scenarios."""
        # Scenario 1: Daily notifications for a user in Tokyo
        next_time = TimezoneConverter.get_next_notification_time(
            frequency="daily",
            notification_time="09:00",  # 9 AM local time
            timezone="Asia/Tokyo",
            from_date=datetime(
                2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC")
            ),  # 7 PM Tokyo
        )

        # Should be next day at 9 AM Tokyo = 12 AM UTC
        assert next_time.hour == 0  # 9 AM Tokyo = 12 AM UTC
        assert next_time.day == 16  # Next day

        # Scenario 2: Weekly notifications for a user in New York
        next_time = TimezoneConverter.get_next_notification_time(
            frequency="weekly",
            notification_time="17:00",  # 5 PM local time
            timezone="America/New_York",
            from_date=datetime(
                2024, 1, 15, 15, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC")
            ),  # Monday 10 AM EST
        )

        # Should be Friday (Jan 19) at 5 PM EST = 10 PM UTC
        assert next_time.weekday() == 4  # Friday
        assert next_time.day == 19  # Friday Jan 19
        assert next_time.hour == 22  # 5 PM EST = 10 PM UTC (winter time)

        # Scenario 3: Monthly notifications for a user in London
        next_time = TimezoneConverter.get_next_notification_time(
            frequency="monthly",
            notification_time="12:00",  # Noon local time
            timezone="Europe/London",
            from_date=datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC")),
        )

        # Should be February 1st at noon London = noon UTC (winter time)
        assert next_time.month == 2
        assert next_time.day == 1
        assert next_time.hour == 12

    def test_daylight_saving_time_handling(self):
        """Test that TimezoneConverter correctly handles daylight saving time transitions."""
        # Test during standard time (winter)
        winter_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        ny_winter = TimezoneConverter.convert_to_user_time(winter_time, "America/New_York")
        assert ny_winter.hour == 7  # UTC-5 (EST)

        # Test during daylight time (summer)
        summer_time = datetime(2024, 7, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        ny_summer = TimezoneConverter.convert_to_user_time(summer_time, "America/New_York")
        assert ny_summer.hour == 8  # UTC-4 (EDT)

        # Test timezone offset calculation
        winter_offset = TimezoneConverter.get_timezone_offset("America/New_York", winter_time)
        summer_offset = TimezoneConverter.get_timezone_offset("America/New_York", summer_time)

        assert winter_offset == "-05:00"  # EST
        assert summer_offset == "-04:00"  # EDT

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling in TimezoneConverter."""
        # Test with None values
        result = TimezoneConverter.get_next_notification_time(
            frequency="disabled", notification_time="18:00", timezone="UTC"
        )
        assert result is None

        # Test with invalid frequency
        with pytest.raises(ValueError, match="Invalid frequency"):
            TimezoneConverter.get_next_notification_time(
                frequency="invalid", notification_time="18:00", timezone="UTC"
            )

        # Test with invalid time format
        with pytest.raises(ValueError, match="Invalid notification_time format"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily", notification_time="25:00", timezone="UTC"
            )

        # Test with invalid timezone
        with pytest.raises(ValueError, match="Invalid timezone identifier"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily", notification_time="18:00", timezone="Invalid/Timezone"
            )

    def test_timezone_converter_performance(self):
        """Test TimezoneConverter performance with multiple operations."""
        import time

        # Test timezone validation performance
        start_time = time.perf_counter()
        for _ in range(100):
            TimezoneConverter.is_valid_timezone("Asia/Tokyo")
        validation_time = time.perf_counter() - start_time

        # Should complete 100 validations in reasonable time (< 1 second)
        assert validation_time < 1.0

        # Test conversion performance
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        start_time = time.perf_counter()
        for _ in range(100):
            TimezoneConverter.convert_to_user_time(utc_time, "Asia/Tokyo")
        conversion_time = time.perf_counter() - start_time

        # Should complete 100 conversions in reasonable time (< 1 second)
        assert conversion_time < 1.0
