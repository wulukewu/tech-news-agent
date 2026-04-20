#!/usr/bin/env python3
"""
Test Phase 1 Advanced Notification APIs

This script tests the quiet hours and technical depth APIs to ensure
they are working correctly and returning proper responses.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv()

from app.services.supabase_service import SupabaseService
from app.services.quiet_hours_service import QuietHoursService
from app.services.technical_depth_service import TechnicalDepthService
from uuid import UUID


async def test_quiet_hours_api():
    """Test Quiet Hours API endpoints"""
    print("\n" + "="*60)
    print("Testing Quiet Hours API")
    print("="*60)

    supabase = SupabaseService()
    quiet_hours_service = QuietHoursService(supabase)

    # Get a test user
    result = supabase.client.table('users').select('id').limit(1).execute()
    if not result.data:
        print("❌ No users found in database")
        return False

    user_uuid = UUID(result.data[0]['id'])
    print(f"Testing with user: {user_uuid}")

    try:
        # Test GET quiet hours
        print("\n1. GET /api/notifications/quiet-hours")
        quiet_hours = await quiet_hours_service.get_quiet_hours(user_uuid)

        if quiet_hours:
            print(f"   ✅ Retrieved quiet hours:")
            print(f"      - Start: {quiet_hours.start_time}")
            print(f"      - End: {quiet_hours.end_time}")
            print(f"      - Timezone: {quiet_hours.timezone}")
            print(f"      - Enabled: {quiet_hours.enabled}")
        else:
            print("   ℹ️  No quiet hours set, creating default...")
            quiet_hours = await quiet_hours_service.create_default_quiet_hours(
                user_uuid, 'Asia/Taipei'
            )
            print(f"   ✅ Created default quiet hours")

        # Test quiet hours status check
        print("\n2. GET /api/notifications/quiet-hours/status")
        is_quiet, settings = await quiet_hours_service.is_in_quiet_hours(user_uuid)
        print(f"   ✅ Current status: {'In quiet hours' if is_quiet else 'Not in quiet hours'}")

        # Test update quiet hours
        print("\n3. PUT /api/notifications/quiet-hours")
        from datetime import time
        updated = await quiet_hours_service.update_quiet_hours(
            user_uuid,
            start_time=time(22, 0),
            end_time=time(8, 0),
            enabled=True
        )
        print(f"   ✅ Updated quiet hours: {updated.start_time} - {updated.end_time}")

        print("\n✅ All Quiet Hours API tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Quiet Hours API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_technical_depth_api():
    """Test Technical Depth API endpoints"""
    print("\n" + "="*60)
    print("Testing Technical Depth API")
    print("="*60)

    supabase = SupabaseService()
    tech_service = TechnicalDepthService(supabase)

    # Get a test user
    result = supabase.client.table('users').select('id').limit(1).execute()
    if not result.data:
        print("❌ No users found in database")
        return False

    user_uuid = UUID(result.data[0]['id'])
    print(f"Testing with user: {user_uuid}")

    try:
        # Test GET technical depth settings
        print("\n1. GET /api/notifications/tech-depth")
        settings = await tech_service.get_tech_depth_settings(user_uuid)
        settings_dict = settings.to_dict()
        print(f"   ✅ Retrieved settings:")
        print(f"      - Threshold: {settings_dict['threshold']}")
        print(f"      - Enabled: {settings_dict['enabled']}")
        print(f"      - Description: {settings_dict['threshold_description']}")

        # Test GET available levels
        print("\n2. GET /api/notifications/tech-depth/levels")
        levels = tech_service.get_available_levels()
        print(f"   ✅ Available levels: {len(levels)}")
        for level in levels:
            print(f"      - {level['value']}: {level['description']}")

        # Test UPDATE settings
        print("\n3. PUT /api/notifications/tech-depth")
        updated = await tech_service.update_tech_depth_settings(
            user_uuid,
            threshold='advanced',
            enabled=True
        )
        print(f"   ✅ Updated settings: {updated.threshold} (enabled: {updated.enabled})")

        # Test filtering check
        print("\n4. POST /api/notifications/tech-depth/check-filter")
        should_send, reason = await tech_service.should_send_notification(
            user_uuid, 'expert'
        )
        print(f"   ✅ Filter check: {should_send}")
        print(f"      Reason: {reason}")

        # Test article depth estimation
        print("\n5. POST /api/notifications/tech-depth/estimate")
        estimated = tech_service.estimate_article_depth(
            "This article covers advanced algorithms, performance optimization, "
            "and distributed systems architecture",
            "Advanced System Design"
        )
        print(f"   ✅ Estimated depth: {estimated}")

        # Test statistics
        print("\n6. GET /api/notifications/tech-depth/stats")
        stats = await tech_service.get_filtering_stats(user_uuid)
        print(f"   ✅ Statistics:")
        print(f"      - Enabled: {stats['enabled']}")
        print(f"      - Message: {stats['message']}")

        print("\n✅ All Technical Depth API tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Technical Depth API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("Phase 1 Advanced Notification APIs Test Suite")
    print("="*60)

    results = []

    # Test Quiet Hours API
    results.append(await test_quiet_hours_api())

    # Test Technical Depth API
    results.append(await test_technical_depth_api())

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All API tests passed! The backend is ready for frontend integration.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
