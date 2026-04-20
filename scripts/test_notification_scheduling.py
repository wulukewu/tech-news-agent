#!/usr/bin/env python3
"""
Test notification scheduling functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from uuid import UUID
from datetime import datetime, timedelta
from app.services.dynamic_scheduler import DynamicScheduler
from app.services.preference_service import PreferenceService
from app.services.supabase_service import SupabaseService


async def test_scheduling():
    """Test notification scheduling"""

    print("🧪 Testing Notification Scheduling")
    print("=" * 50)

    # Initialize services
    supabase = SupabaseService()
    scheduler = DynamicScheduler()
    preference_service = PreferenceService()

    # Get all active users
    print("\n1. Getting all active users...")
    try:
        from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        all_prefs = await prefs_repo.get_all_active_preferences()

        print(f"   ✅ Found {len(all_prefs)} active users")

        for pref in all_prefs:
            print(f"\n   User: {pref.user_id}")
            print(f"   - Frequency: {pref.frequency}")
            print(f"   - Time: {pref.notification_time}")
            print(f"   - Timezone: {pref.timezone}")
            print(f"   - DM Enabled: {pref.dm_enabled}")
            print(f"   - Email Enabled: {pref.email_enabled}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Check scheduler status
    print("\n2. Checking scheduler status...")
    try:
        jobs = scheduler.scheduler.get_jobs()
        print(f"   ✅ Total jobs in scheduler: {len(jobs)}")

        user_notification_jobs = [j for j in jobs if j.id.startswith("user_notification_")]
        print(f"   ✅ User notification jobs: {len(user_notification_jobs)}")

        for job in user_notification_jobs:
            print(f"\n   Job ID: {job.id}")
            print(f"   - Name: {job.name}")
            print(f"   - Next run: {job.next_run_time}")
            print(f"   - Trigger: {job.trigger}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Test manual notification trigger
    print("\n3. Testing manual notification trigger...")
    if all_prefs:
        test_user = all_prefs[0]
        print(f"   Testing with user: {test_user.user_id}")

        try:
            # Try to manually trigger the notification function
            from app.services.notification_system_integration import get_notification_system_integration

            integration = get_notification_system_integration()
            if integration:
                print("   ✅ Notification system integration available")

                # Check if we can send a test notification
                print("   ℹ️  To send a test notification, use the frontend 'Send Test Notification' button")
            else:
                print("   ❌ Notification system integration not available")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Check if scheduler is running
    print("\n4. Checking if scheduler is running...")
    try:
        is_running = scheduler.scheduler.running
        print(f"   Scheduler running: {is_running}")

        if is_running:
            print("   ✅ Scheduler is active and will execute jobs at scheduled times")
        else:
            print("   ❌ Scheduler is not running!")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 50)
    print("✅ Test completed")
    print("\n📝 Notes:")
    print("   - Notifications will be sent at the scheduled times")
    print("   - Check backend logs for notification execution")
    print("   - Use 'Send Test Notification' button in frontend to test immediately")


if __name__ == "__main__":
    asyncio.run(test_scheduling())
