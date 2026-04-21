#!/usr/bin/env python3
"""
Test script for notification day fields update functionality.

This script tests the ability to update notification_day_of_week and
notification_day_of_month fields through the API.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository,
)
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
)
from app.services.preference_service import PreferenceService
from app.services.supabase_service import SupabaseService


async def test_day_fields_update():
    """Test updating notification day fields."""
    print("=" * 80)
    print("Testing Notification Day Fields Update")
    print("=" * 80)

    # Initialize services
    supabase = SupabaseService()
    prefs_repo = UserNotificationPreferencesRepository(supabase.client)
    preference_service = PreferenceService(prefs_repo)

    # Use a test user ID (replace with actual user ID from your database)
    test_user_id = UUID("bc627dfa-7101-4e98-8e92-bbc02f97e7cd")

    print(f"\n1. Getting current preferences for user {test_user_id}")
    current_prefs = await preference_service.get_user_preferences(test_user_id)
    print(f"   Current frequency: {current_prefs.frequency}")
    print(f"   Current notification_time: {current_prefs.notification_time}")
    print(f"   Current notification_day_of_week: {current_prefs.notification_day_of_week}")
    print(f"   Current notification_day_of_month: {current_prefs.notification_day_of_month}")

    print("\n2. Testing weekly notification - updating day_of_week to Monday (1)")
    update_request = UpdateUserNotificationPreferencesRequest(
        frequency="weekly",
        notification_time="10:00",
        notification_day_of_week=1,  # Monday
    )
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Updated frequency: {updated_prefs.frequency}")
    print(f"   ✓ Updated notification_time: {updated_prefs.notification_time}")
    print(f"   ✓ Updated notification_day_of_week: {updated_prefs.notification_day_of_week}")
    assert updated_prefs.notification_day_of_week == 1, "Day of week should be 1 (Monday)"

    print("\n3. Testing monthly notification - updating day_of_month to 15")
    update_request = UpdateUserNotificationPreferencesRequest(
        frequency="monthly",
        notification_time="14:00",
        notification_day_of_month=15,  # 15th of month
    )
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Updated frequency: {updated_prefs.frequency}")
    print(f"   ✓ Updated notification_time: {updated_prefs.notification_time}")
    print(f"   ✓ Updated notification_day_of_month: {updated_prefs.notification_day_of_month}")
    assert updated_prefs.notification_day_of_month == 15, "Day of month should be 15"

    print("\n4. Testing updating only day_of_week without changing frequency")
    update_request = UpdateUserNotificationPreferencesRequest(
        notification_day_of_week=3,  # Wednesday
    )
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Frequency unchanged: {updated_prefs.frequency}")
    print(f"   ✓ Updated notification_day_of_week: {updated_prefs.notification_day_of_week}")
    assert updated_prefs.notification_day_of_week == 3, "Day of week should be 3 (Wednesday)"
    assert updated_prefs.frequency == "monthly", "Frequency should remain monthly"

    print("\n5. Testing edge cases")
    # Test Sunday (0)
    update_request = UpdateUserNotificationPreferencesRequest(
        frequency="weekly", notification_day_of_week=0
    )
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Sunday (0): {updated_prefs.notification_day_of_week}")
    assert updated_prefs.notification_day_of_week == 0, "Day of week should be 0 (Sunday)"

    # Test Saturday (6)
    update_request = UpdateUserNotificationPreferencesRequest(notification_day_of_week=6)
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Saturday (6): {updated_prefs.notification_day_of_week}")
    assert updated_prefs.notification_day_of_week == 6, "Day of week should be 6 (Saturday)"

    # Test first day of month (1)
    update_request = UpdateUserNotificationPreferencesRequest(
        frequency="monthly", notification_day_of_month=1
    )
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ First day of month (1): {updated_prefs.notification_day_of_month}")
    assert updated_prefs.notification_day_of_month == 1, "Day of month should be 1"

    # Test last day of month (31)
    update_request = UpdateUserNotificationPreferencesRequest(notification_day_of_month=31)
    updated_prefs = await preference_service.update_preferences(
        test_user_id, update_request, source="test"
    )
    print(f"   ✓ Last day of month (31): {updated_prefs.notification_day_of_month}")
    assert updated_prefs.notification_day_of_month == 31, "Day of month should be 31"

    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_day_fields_update())
