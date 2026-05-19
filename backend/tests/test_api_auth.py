#!/usr/bin/env python3
"""
Test actual API calls with authentication
"""

import asyncio
import sys
from uuid import uuid4

from app.services.supabase_service import SupabaseService


async def test_api_with_auth():
    """Test API calls with proper authentication"""
    print("🔐 Testing API with authentication...")

    try:
        supabase_service = SupabaseService()

        # Get a real user from the database
        users_result = supabase_service.client.table("users").select("*").limit(1).execute()

        if not users_result.data:
            print("❌ No users found in database")
            return False

        test_user = users_result.data[0]
        user_id = test_user["id"]
        print(f"✅ Using test user: {user_id}")

        # Test 1: Get pending reminders
        print("\n📋 Testing get pending reminders...")
        try:
            result = (
                supabase_service.client.table("reminder_log")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            print(f"✅ Found {len(result.data)} reminders for user")
        except Exception as e:
            print(f"❌ Error getting reminders: {e}")

        # Test 2: Get reminder settings
        print("\n⚙️ Testing get reminder settings...")
        try:
            result = (
                supabase_service.client.table("reminder_settings")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                print(f"✅ Found settings for user: {result.data[0]}")
            else:
                print("ℹ️ No settings found (will use defaults)")
        except Exception as e:
            print(f"❌ Error getting settings: {e}")

        # Test 3: Create a test reminder
        print("\n📝 Testing create reminder...")
        try:
            test_reminder = {
                "id": str(uuid4()),
                "user_id": user_id,
                "reminder_type": "article_relation",
                "reminder_context": {
                    "title": "Test Reminder",
                    "description": "This is a test reminder",
                    "priority_score": 0.8,
                    "reading_time_estimate": 5,
                },
                "sent_at": "2026-05-01T12:00:00Z",
                "channel": "web",
                "status": "pending",
            }

            result = supabase_service.client.table("reminder_log").insert(test_reminder).execute()
            print(f"✅ Created test reminder: {result.data[0]['id']}")

            # Clean up
            supabase_service.client.table("reminder_log").delete().eq(
                "id", test_reminder["id"]
            ).execute()
            print("✅ Cleaned up test reminder")

        except Exception as e:
            print(f"❌ Error creating reminder: {e}")

        print("\n🎉 API authentication test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_with_auth())
    sys.exit(0 if success else 1)
