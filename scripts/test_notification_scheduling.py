#!/usr/bin/env python3
"""
Test notification scheduling with new day fields

This script tests the updated scheduling logic with notification_day_of_week
and notification_day_of_month fields.
"""

import sys
from datetime import datetime, time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.timezone_converter import TimezoneConverter


def test_daily_notifications():
    """Test daily notification scheduling."""
    print("\n📅 Testing Daily Notifications")
    print("=" * 50)

    next_time = TimezoneConverter.get_next_notification_time(
        frequency="daily",
        notification_time="09:00",
        timezone="Asia/Taipei",
    )

    if next_time:
        local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
        print(f"✅ Next daily notification:")
        print(f"   UTC: {next_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Day: {local_time.strftime('%A')}")
    else:
        print("❌ Failed to calculate next time")


def test_weekly_notifications():
    """Test weekly notification scheduling with different days."""
    print("\n📅 Testing Weekly Notifications")
    print("=" * 50)

    days = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
    }

    for day_num, day_name in days.items():
        next_time = TimezoneConverter.get_next_notification_time(
            frequency="weekly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            notification_day_of_week=day_num,
        )

        if next_time:
            local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
            print(f"\n✅ Next {day_name} notification:")
            print(f"   UTC: {next_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Day: {local_time.strftime('%A')}")

            # Verify it's the correct day
            expected_weekday = (day_num - 1) % 7  # Convert to Python weekday
            actual_weekday = local_time.weekday()
            if actual_weekday == expected_weekday:
                print(f"   ✓ Correct day verified")
            else:
                print(f"   ✗ Wrong day! Expected {expected_weekday}, got {actual_weekday}")
        else:
            print(f"❌ Failed to calculate next time for {day_name}")


def test_monthly_notifications():
    """Test monthly notification scheduling with different days."""
    print("\n📅 Testing Monthly Notifications")
    print("=" * 50)

    test_days = [1, 5, 10, 15, 20, 25, 28, 31]

    for day in test_days:
        next_time = TimezoneConverter.get_next_notification_time(
            frequency="monthly",
            notification_time="18:00",
            timezone="Asia/Taipei",
            notification_day_of_month=day,
        )

        if next_time:
            local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
            print(f"\n✅ Next notification on day {day}:")
            print(f"   UTC: {next_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Day of month: {local_time.day}")

            # Note: Day might be adjusted for months with fewer days
            if local_time.day == day:
                print(f"   ✓ Exact day {day}")
            else:
                print(f"   ℹ️  Adjusted to day {local_time.day} (month has fewer days)")
        else:
            print(f"❌ Failed to calculate next time for day {day}")


def test_default_values():
    """Test scheduling with default values (backward compatibility)."""
    print("\n📅 Testing Default Values (Backward Compatibility)")
    print("=" * 50)

    # Weekly without day_of_week (should default to Friday)
    next_time = TimezoneConverter.get_next_notification_time(
        frequency="weekly",
        notification_time="18:00",
        timezone="Asia/Taipei",
    )

    if next_time:
        local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
        print(f"\n✅ Weekly (default):")
        print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S %A')}")
        if local_time.weekday() == 4:  # Friday
            print(f"   ✓ Correctly defaults to Friday")
        else:
            print(f"   ✗ Wrong day! Expected Friday, got {local_time.strftime('%A')}")

    # Monthly without day_of_month (should default to 1st)
    next_time = TimezoneConverter.get_next_notification_time(
        frequency="monthly",
        notification_time="18:00",
        timezone="Asia/Taipei",
    )

    if next_time:
        local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
        print(f"\n✅ Monthly (default):")
        print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if local_time.day == 1:
            print(f"   ✓ Correctly defaults to 1st of month")
        else:
            print(f"   ✗ Wrong day! Expected 1st, got {local_time.day}")


def test_edge_cases():
    """Test edge cases like February 31st."""
    print("\n📅 Testing Edge Cases")
    print("=" * 50)

    # Test February 31st (should adjust to Feb 28/29)
    print("\n🔍 Testing February 31st:")

    # Force a date in January to test February
    from datetime import datetime
    import zoneinfo

    jan_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

    next_time = TimezoneConverter.get_next_notification_time(
        frequency="monthly",
        notification_time="18:00",
        timezone="Asia/Taipei",
        notification_day_of_month=31,
        from_date=jan_date,
    )

    if next_time:
        local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
        print(f"   Local: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if local_time.month == 2:
            print(f"   ✓ Correctly scheduled for February")
            if local_time.day in [28, 29]:
                print(f"   ✓ Correctly adjusted to last day of February ({local_time.day})")
            else:
                print(f"   ✗ Wrong day! Expected 28 or 29, got {local_time.day}")
        else:
            print(f"   ℹ️  Scheduled for {local_time.strftime('%B')} instead")


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("🧪 Notification Scheduling Tests")
    print("=" * 50)

    try:
        test_daily_notifications()
        test_weekly_notifications()
        test_monthly_notifications()
        test_default_values()
        test_edge_cases()

        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
