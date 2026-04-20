"""
Unit tests for TimezoneConverter utility class.

Tests timezone conversion functionality, next notification time calculation,
and edge cases like daylight saving time transitions.

Requirements: 5.3
"""

import zoneinfo
from datetime import datetime, timedelta

import pytest

from app.core.timezone_converter import TimezoneConverter


class TestTimezoneConverter:
    """Test cases for TimezoneConverter utility class."""

    def test_convert_to_user_time_basic(self):
        """Test basic UTC to user timezone conversion."""
        # Test conversion to Asia/Taipei (+8)
        utc_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        user_time = TimezoneConverter.convert_to_user_time(utc_time, "Asia/Taipei")

        assert user_time.hour == 18  # 10 + 8 = 18
        assert user_time.minute == 0
        assert user_time.tzinfo == zoneinfo.ZoneInfo("Asia/Taipei")

    def test_convert_to_user_time_naive_datetime(self):
        """Test conversion with naive UTC datetime."""
        # Test with naive datetime (assumes UTC)
        utc_time = datetime(2024, 1, 15, 10, 0, 0)  # No timezone info
        user_time = TimezoneConverter.convert_to_user_time(utc_time, "America/New_York")

        # New York is UTC-5 in winter
        assert user_time.hour == 5  # 10 - 5 = 5
        assert user_time.tzinfo == zoneinfo.ZoneInfo("America/New_York")

    def test_convert_to_user_time_invalid_timezone(self):
        """Test conversion with invalid timezone."""
        utc_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        with pytest.raises(ValueError, match="Invalid timezone identifier"):
            TimezoneConverter.convert_to_user_time(utc_time, "Invalid/Timezone")

    def test_convert_to_utc_basic(self):
        """Test basic user timezone to UTC conversion."""
        # Test conversion from Asia/Taipei (+8)
        local_time = datetime(2024, 1, 15, 18, 0, 0)  # 6 PM local
        utc_time = TimezoneConverter.convert_to_utc(local_time, "Asia/Taipei")

        assert utc_time.hour == 10  # 18 - 8 = 10
        assert utc_time.minute == 0
        assert utc_time.tzinfo == zoneinfo.ZoneInfo("UTC")

    def test_convert_to_utc_with_timezone_aware(self):
        """Test conversion with timezone-aware datetime."""
        # Create timezone-aware datetime
        taipei_tz = zoneinfo.ZoneInfo("Asia/Taipei")
        local_time = datetime(2024, 1, 15, 18, 0, 0, tzinfo=taipei_tz)
        utc_time = TimezoneConverter.convert_to_utc(local_time, "Asia/Taipei")

        assert utc_time.hour == 10
        assert utc_time.tzinfo == zoneinfo.ZoneInfo("UTC")

    def test_convert_to_utc_invalid_timezone(self):
        """Test conversion with invalid timezone."""
        local_time = datetime(2024, 1, 15, 18, 0, 0)

        with pytest.raises(ValueError, match="Invalid timezone identifier"):
            TimezoneConverter.convert_to_utc(local_time, "Invalid/Timezone")

    def test_get_next_notification_time_disabled(self):
        """Test next notification time for disabled frequency."""
        result = TimezoneConverter.get_next_notification_time(
            frequency="disabled", notification_time="18:00", timezone="Asia/Taipei"
        )

        assert result is None

    def test_get_next_notification_time_daily_future(self):
        """Test daily notification when time hasn't passed today."""
        # Set reference time to 10 AM UTC (6 PM Taipei)
        from_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Notification at 8 PM Taipei (should be today)
        result = TimezoneConverter.get_next_notification_time(
            frequency="daily",
            notification_time="20:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be today at 8 PM Taipei = 12 PM UTC
        assert result.hour == 12
        assert result.day == 15

    def test_get_next_notification_time_daily_past(self):
        """Test daily notification when time has passed today."""
        # Set reference time to 2 PM UTC (10 PM Taipei)
        from_date = datetime(2024, 1, 15, 14, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Notification at 6 PM Taipei (should be tomorrow)
        result = TimezoneConverter.get_next_notification_time(
            frequency="daily",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be tomorrow at 6 PM Taipei = 10 AM UTC next day
        assert result.hour == 10
        assert result.day == 16

    def test_get_next_notification_time_weekly_friday(self):
        """Test weekly notification (defaults to Friday)."""
        # Set reference time to Monday
        from_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))  # Monday

        result = TimezoneConverter.get_next_notification_time(
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be Friday (4 days later)
        expected_friday = from_date + timedelta(days=4)
        assert result.weekday() == 4  # Friday
        assert result.hour == 10  # 6 PM Taipei = 10 AM UTC

    def test_get_next_notification_time_weekly_friday_past(self):
        """Test weekly notification when it's Friday but time has passed."""
        # Set reference time to Friday 2 PM UTC (10 PM Taipei)
        from_date = datetime(2024, 1, 19, 14, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))  # Friday

        result = TimezoneConverter.get_next_notification_time(
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be next Friday
        assert result.weekday() == 4  # Friday
        assert result.day == 26  # Next Friday
        assert result.hour == 10  # 6 PM Taipei = 10 AM UTC

    def test_get_next_notification_time_monthly(self):
        """Test monthly notification."""
        # Set reference time to January 15
        from_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        result = TimezoneConverter.get_next_notification_time(
            frequency="monthly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be February 1st
        assert result.month == 2
        assert result.day == 1
        assert result.hour == 10  # 6 PM Taipei = 10 AM UTC

    def test_get_next_notification_time_monthly_december(self):
        """Test monthly notification in December (year rollover)."""
        # Set reference time to December 15
        from_date = datetime(2024, 12, 15, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        result = TimezoneConverter.get_next_notification_time(
            frequency="monthly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be January 1st next year
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1

    def test_get_next_notification_time_invalid_frequency(self):
        """Test with invalid frequency."""
        with pytest.raises(ValueError, match="Invalid frequency"):
            TimezoneConverter.get_next_notification_time(
                frequency="invalid", notification_time="18:00", timezone="Asia/Taipei"
            )

    def test_get_next_notification_time_invalid_time_format(self):
        """Test with invalid time format."""
        with pytest.raises(ValueError, match="Invalid notification_time format"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily", notification_time="25:00", timezone="Asia/Taipei"  # Invalid hour
            )

        with pytest.raises(ValueError, match="Invalid notification_time format"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily",
                notification_time="18:70",  # Invalid minute
                timezone="Asia/Taipei",
            )

        with pytest.raises(ValueError, match="Invalid notification_time format"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily",
                notification_time="invalid",  # Invalid format
                timezone="Asia/Taipei",
            )

    def test_get_next_notification_time_invalid_timezone(self):
        """Test with invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone identifier"):
            TimezoneConverter.get_next_notification_time(
                frequency="daily", notification_time="18:00", timezone="Invalid/Timezone"
            )

    def test_is_valid_timezone(self):
        """Test timezone validation."""
        # Valid timezones
        assert TimezoneConverter.is_valid_timezone("Asia/Taipei") is True
        assert TimezoneConverter.is_valid_timezone("America/New_York") is True
        assert TimezoneConverter.is_valid_timezone("UTC") is True
        assert TimezoneConverter.is_valid_timezone("Europe/London") is True

        # Invalid timezones
        assert TimezoneConverter.is_valid_timezone("Invalid/Timezone") is False
        assert TimezoneConverter.is_valid_timezone("") is False
        assert TimezoneConverter.is_valid_timezone("GMT+8") is False  # Not IANA format

    def test_get_timezone_offset_basic(self):
        """Test getting timezone offset."""
        # Test Asia/Taipei (+8)
        offset = TimezoneConverter.get_timezone_offset("Asia/Taipei")
        assert offset == "+08:00"

        # Test America/New_York (varies by season)
        at_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))  # Winter
        offset = TimezoneConverter.get_timezone_offset("America/New_York", at_time)
        assert offset == "-05:00"  # EST

    def test_get_timezone_offset_dst(self):
        """Test timezone offset during daylight saving time."""
        # Test America/New_York during summer (DST)
        summer_time = datetime(2024, 7, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        offset = TimezoneConverter.get_timezone_offset("America/New_York", summer_time)
        assert offset == "-04:00"  # EDT

    def test_get_timezone_offset_invalid_timezone(self):
        """Test timezone offset with invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone identifier"):
            TimezoneConverter.get_timezone_offset("Invalid/Timezone")

    def test_daylight_saving_transition(self):
        """Test timezone conversion during daylight saving time transition."""
        # Test spring forward transition in America/New_York
        # March 10, 2024 at 2 AM EST becomes 3 AM EDT
        before_dst = datetime(2024, 3, 10, 6, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))  # 1 AM EST
        after_dst = datetime(2024, 3, 10, 8, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))  # 4 AM EDT

        local_before = TimezoneConverter.convert_to_user_time(before_dst, "America/New_York")
        local_after = TimezoneConverter.convert_to_user_time(after_dst, "America/New_York")

        # Verify the conversion handles DST correctly
        assert local_before.hour == 1  # 1 AM EST
        assert local_after.hour == 4  # 4 AM EDT

    def test_round_trip_conversion(self):
        """Test that UTC -> Local -> UTC conversion is consistent."""
        original_utc = datetime(2024, 1, 15, 12, 30, 45, tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Convert to local time and back
        local_time = TimezoneConverter.convert_to_user_time(original_utc, "Asia/Tokyo")
        back_to_utc = TimezoneConverter.convert_to_utc(local_time, "Asia/Tokyo")

        # Should be identical
        assert back_to_utc == original_utc

    def test_edge_case_midnight_notification(self):
        """Test notification at midnight."""
        from_date = datetime(
            2024, 1, 15, 16, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC")
        )  # 12 AM Taipei next day

        result = TimezoneConverter.get_next_notification_time(
            frequency="daily",
            notification_time="00:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be next day at midnight Taipei = 4 PM UTC
        assert result.hour == 16
        assert result.day == 16

    def test_edge_case_leap_year_february(self):
        """Test monthly notification in leap year February."""
        # February 29, 2024 (leap year)
        from_date = datetime(2024, 2, 29, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        result = TimezoneConverter.get_next_notification_time(
            frequency="monthly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            from_date=from_date,
        )

        # Should be March 1st
        assert result.month == 3
        assert result.day == 1
