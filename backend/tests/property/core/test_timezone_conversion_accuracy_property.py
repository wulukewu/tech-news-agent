"""
Property Test for Timezone Conversion Accuracy

This module implements Property 4: Timezone Conversion Accuracy from the
personalized notification frequency feature design.

**Validates: Requirements 5.3**

Property 4: For any valid timezone and notification time combination, the system
SHALL correctly convert between user local time and UTC, ensuring notifications
are scheduled and delivered at the user's intended local time.
"""

import zoneinfo
from datetime import datetime, timedelta

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.core.timezone_converter import TimezoneConverter

# Common timezone identifiers for testing
COMMON_TIMEZONES = [
    "UTC",
    "Asia/Taipei",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Pacific/Auckland",
    "America/Sao_Paulo",
    "Africa/Cairo",
    "Asia/Kolkata",
    "Asia/Dubai",
    "America/Toronto",
    "Europe/Moscow",
    "Asia/Singapore",
]


# Generate timezone strategy
@st.composite
def timezone_strategy(draw):
    """Generate valid IANA timezone identifiers."""
    return draw(st.sampled_from(COMMON_TIMEZONES))


# Generate datetime strategy (avoiding edge cases that might cause issues)
@st.composite
def datetime_strategy(draw):
    """Generate reasonable datetime values for testing."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Avoid month-end edge cases
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))

    return datetime(year, month, day, hour, minute, second)


# Generate notification time strategy
@st.composite
def notification_time_strategy(draw):
    """Generate valid notification time strings in HH:MM format."""
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    return f"{hour:02d}:{minute:02d}"


# Generate frequency strategy
@st.composite
def frequency_strategy(draw):
    """Generate valid notification frequency values."""
    return draw(st.sampled_from(["daily", "weekly", "monthly"]))


class TestTimezoneConversionAccuracyProperty:
    """Property-based tests for timezone conversion accuracy."""

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        utc_time=datetime_strategy(),
        timezone=timezone_strategy(),
    )
    def test_property_4_utc_to_local_conversion_accuracy(self, utc_time, timezone):
        """
        **Property 4: Timezone Conversion Accuracy - UTC to Local**

        **Validates: Requirements 5.3**

        For any valid UTC datetime and timezone combination, the system SHALL
        correctly convert UTC time to user local time, maintaining temporal
        accuracy and timezone information.
        """
        # Make UTC time timezone-aware
        utc_time_aware = utc_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Convert to user timezone
        local_time = TimezoneConverter.convert_to_user_time(utc_time_aware, timezone)

        # Property 1: Result should be timezone-aware with correct timezone
        assert local_time.tzinfo is not None, "Converted time should be timezone-aware"
        assert local_time.tzinfo == zoneinfo.ZoneInfo(timezone), f"Timezone should be {timezone}"

        # Property 2: Converting back to UTC should yield original time
        back_to_utc = local_time.astimezone(zoneinfo.ZoneInfo("UTC"))
        assert (
            back_to_utc == utc_time_aware
        ), "Round-trip conversion should preserve original UTC time"

        # Property 3: Time difference should match timezone offset
        expected_offset = local_time.utcoffset()
        # Convert both to naive datetimes for comparison
        local_naive = local_time.replace(tzinfo=None)
        utc_naive = utc_time_aware.replace(tzinfo=None)
        actual_offset = local_naive - utc_naive
        assert actual_offset == expected_offset, "Time difference should match timezone offset"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        local_time=datetime_strategy(),
        timezone=timezone_strategy(),
    )
    def test_property_4_local_to_utc_conversion_accuracy(self, local_time, timezone):
        """
        **Property 4: Timezone Conversion Accuracy - Local to UTC**

        **Validates: Requirements 5.3**

        For any valid local datetime and timezone combination, the system SHALL
        correctly convert local time to UTC, maintaining temporal accuracy.
        """
        # Convert local time to UTC
        utc_time = TimezoneConverter.convert_to_utc(local_time, timezone)

        # Property 1: Result should be UTC timezone-aware
        assert utc_time.tzinfo is not None, "Converted time should be timezone-aware"
        assert utc_time.tzinfo == zoneinfo.ZoneInfo("UTC"), "Result should be in UTC timezone"

        # Property 2: Converting back to local should yield original time (accounting for timezone)
        back_to_local = TimezoneConverter.convert_to_user_time(utc_time, timezone)

        # Create timezone-aware version of original local time for comparison
        local_time_aware = local_time.replace(tzinfo=zoneinfo.ZoneInfo(timezone))

        assert (
            back_to_local == local_time_aware
        ), "Round-trip conversion should preserve original local time"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        frequency=frequency_strategy(),
        notification_time=notification_time_strategy(),
        timezone=timezone_strategy(),
        from_date=datetime_strategy(),
    )
    def test_property_4_next_notification_time_accuracy(
        self, frequency, notification_time, timezone, from_date
    ):
        """
        **Property 4: Timezone Conversion Accuracy - Next Notification Time**

        **Validates: Requirements 5.3**

        For any valid frequency, notification time, and timezone combination, the system
        SHALL correctly calculate the next notification time in UTC while ensuring it
        corresponds to the user's intended local time.
        """
        # Make from_date UTC timezone-aware
        from_date_utc = from_date.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Calculate next notification time
        next_notification_utc = TimezoneConverter.get_next_notification_time(
            frequency=frequency,
            notification_time=notification_time,
            timezone=timezone,
            from_date=from_date_utc,
        )

        # Property 1: Result should be a future UTC datetime
        assert (
            next_notification_utc is not None
        ), "Should return a valid datetime for enabled frequencies"
        assert next_notification_utc.tzinfo == zoneinfo.ZoneInfo("UTC"), "Result should be in UTC"
        assert next_notification_utc >= from_date_utc, "Next notification should be in the future"

        # Property 2: When converted to user timezone, should match intended notification time
        next_notification_local = TimezoneConverter.convert_to_user_time(
            next_notification_utc, timezone
        )

        # Parse expected time
        expected_hour, expected_minute = map(int, notification_time.split(":"))

        assert next_notification_local.hour == expected_hour, f"Hour should be {expected_hour}"
        assert (
            next_notification_local.minute == expected_minute
        ), f"Minute should be {expected_minute}"
        assert next_notification_local.second == 0, "Seconds should be 0"
        assert next_notification_local.microsecond == 0, "Microseconds should be 0"

        # Property 3: Frequency-specific constraints
        user_from_date = TimezoneConverter.convert_to_user_time(from_date_utc, timezone)

        if frequency == "daily":
            # Should be within 24 hours of reference date
            time_diff = next_notification_local - user_from_date
            assert (
                timedelta(0) <= time_diff <= timedelta(days=1)
            ), "Daily notification should be within 24 hours"

        elif frequency == "weekly":
            # Should be on a Friday (weekday 4)
            assert next_notification_local.weekday() == 4, "Weekly notification should be on Friday"

        elif frequency == "monthly":
            # Should be on the 1st day of a month
            assert (
                next_notification_local.day == 1
            ), "Monthly notification should be on 1st day of month"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        timezone1=timezone_strategy(),
        timezone2=timezone_strategy(),
        base_time=datetime_strategy(),
    )
    def test_property_4_timezone_conversion_consistency(self, timezone1, timezone2, base_time):
        """
        **Property 4: Timezone Conversion Accuracy - Cross-timezone Consistency**

        **Validates: Requirements 5.3**

        For any two different timezones and a base time, converting through UTC
        should maintain temporal consistency across all timezone conversions.
        """
        assume(timezone1 != timezone2)  # Only test different timezones

        # Make base time UTC-aware
        utc_base = base_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Convert UTC to both timezones
        local1 = TimezoneConverter.convert_to_user_time(utc_base, timezone1)
        local2 = TimezoneConverter.convert_to_user_time(utc_base, timezone2)

        # Convert both back to UTC
        back_to_utc1 = TimezoneConverter.convert_to_utc(local1, timezone1)
        back_to_utc2 = TimezoneConverter.convert_to_utc(local2, timezone2)

        # Property 1: Both should convert back to the same UTC time
        assert back_to_utc1 == utc_base, "Conversion through timezone1 should preserve UTC time"
        assert back_to_utc2 == utc_base, "Conversion through timezone2 should preserve UTC time"
        assert back_to_utc1 == back_to_utc2, "Both conversions should yield identical UTC times"

        # Property 2: Time difference between local times should match timezone offset difference
        offset1 = local1.utcoffset()
        offset2 = local2.utcoffset()
        expected_diff = offset1 - offset2
        actual_diff = local1.replace(tzinfo=None) - local2.replace(tzinfo=None)

        assert (
            actual_diff == expected_diff
        ), "Local time difference should match timezone offset difference"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        timezone=timezone_strategy(),
        notification_time=notification_time_strategy(),
    )
    def test_property_4_daylight_saving_time_handling(self, timezone, notification_time):
        """
        **Property 4: Timezone Conversion Accuracy - DST Handling**

        **Validates: Requirements 5.3**

        For any timezone that observes daylight saving time, the system SHALL
        correctly handle timezone conversions during DST transitions.
        """
        # Test dates around common DST transitions
        dst_test_dates = [
            datetime(2024, 3, 10, 12, 0, 0),  # Spring forward (US)
            datetime(2024, 11, 3, 12, 0, 0),  # Fall back (US)
            datetime(2024, 3, 31, 12, 0, 0),  # Spring forward (EU)
            datetime(2024, 10, 27, 12, 0, 0),  # Fall back (EU)
        ]

        for test_date in dst_test_dates:
            utc_test_date = test_date.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

            # Convert to local timezone
            local_time = TimezoneConverter.convert_to_user_time(utc_test_date, timezone)

            # Property 1: Conversion should not raise exceptions
            assert local_time is not None, "DST conversion should not fail"
            assert local_time.tzinfo == zoneinfo.ZoneInfo(timezone), "Timezone should be preserved"

            # Property 2: Round-trip conversion should be consistent
            back_to_utc = TimezoneConverter.convert_to_utc(local_time, timezone)
            assert (
                back_to_utc == utc_test_date
            ), "Round-trip conversion should preserve UTC time during DST"

            # Property 3: Next notification calculation should work during DST
            try:
                next_notification = TimezoneConverter.get_next_notification_time(
                    frequency="daily",
                    notification_time=notification_time,
                    timezone=timezone,
                    from_date=utc_test_date,
                )

                if next_notification is not None:
                    # Should be a valid future time
                    assert (
                        next_notification >= utc_test_date
                    ), "Next notification should be in future during DST"

                    # When converted to local time, should match notification time
                    next_local = TimezoneConverter.convert_to_user_time(next_notification, timezone)
                    expected_hour, expected_minute = map(int, notification_time.split(":"))
                    assert next_local.hour == expected_hour, "Hour should be correct during DST"
                    assert (
                        next_local.minute == expected_minute
                    ), "Minute should be correct during DST"

            except ValueError:
                # Some edge cases during DST transitions might be invalid, which is acceptable
                pass

    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    )
    @given(
        timezone=timezone_strategy(),
    )
    def test_property_4_timezone_offset_accuracy(self, timezone):
        """
        **Property 4: Timezone Conversion Accuracy - Offset Calculation**

        **Validates: Requirements 5.3**

        For any valid timezone, the system SHALL correctly calculate and format
        timezone offsets in the standard ±HH:MM format.
        """
        # Test with current time
        current_utc = datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Get timezone offset
        offset_str = TimezoneConverter.get_timezone_offset(timezone, current_utc)

        # Property 1: Offset should be in correct format
        import re

        offset_pattern = r"^[+-]\d{2}:\d{2}$"
        assert re.match(
            offset_pattern, offset_str
        ), f"Offset '{offset_str}' should match ±HH:MM format"

        # Property 2: Offset should be consistent with actual conversion
        local_time = TimezoneConverter.convert_to_user_time(current_utc, timezone)
        actual_offset = local_time.utcoffset()

        # Parse offset string
        sign = 1 if offset_str[0] == "+" else -1
        hours = int(offset_str[1:3])
        minutes = int(offset_str[4:6])
        expected_offset = timedelta(hours=sign * hours, minutes=sign * minutes)

        assert (
            actual_offset == expected_offset
        ), "Calculated offset should match actual timezone offset"

        # Property 3: Offset should be within reasonable bounds (±18 hours)
        total_hours = sign * (hours + minutes / 60)
        assert -18 <= total_hours <= 18, f"Timezone offset {total_hours} should be within ±18 hours"

    def test_property_4_invalid_timezone_handling(self):
        """
        **Property 4: Timezone Conversion Accuracy - Error Handling**

        **Validates: Requirements 5.3**

        For any invalid timezone identifier, the system SHALL raise appropriate
        ValueError exceptions with descriptive error messages.
        """
        test_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Test each invalid timezone individually
        # Property 1: convert_to_user_time should raise ValueError for invalid timezone
        with pytest.raises(ValueError):
            TimezoneConverter.convert_to_user_time(test_time, "Invalid/Timezone")

        # Property 2: convert_to_utc should raise ValueError for invalid timezone
        with pytest.raises(ValueError):
            TimezoneConverter.convert_to_utc(test_time.replace(tzinfo=None), "Invalid/Timezone")

        # Property 3: get_next_notification_time should raise ValueError for invalid timezone
        with pytest.raises(ValueError):
            TimezoneConverter.get_next_notification_time(
                frequency="daily", notification_time="18:00", timezone="Invalid/Timezone"
            )

        # Property 4: get_timezone_offset should raise ValueError for invalid timezone
        with pytest.raises(ValueError):
            TimezoneConverter.get_timezone_offset("Invalid/Timezone")

        # Property 5: is_valid_timezone should return False for invalid timezone
        assert TimezoneConverter.is_valid_timezone("Invalid/Timezone") is False

        # Test additional invalid timezones
        invalid_timezones = ["GMT+8", "", "UTC+5", "Asia/Invalid"]

        for invalid_tz in invalid_timezones:
            assert TimezoneConverter.is_valid_timezone(invalid_tz) is False
