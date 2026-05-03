#!/usr/bin/env python3
"""
Test reminder settings API
"""
import asyncio
import sys

from app.services.supabase_service import SupabaseService


async def test_reminder_settings():
    """Test reminder settings CRUD operations"""
    print("🧪 Testing reminder settings API...")

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

        # Test 1: Create initial settings
        print("\n📝 Testing create settings...")
        try:
            initial_settings = {
                "user_id": user_id,
                "enabled": True,
                "max_daily_reminders": 5,
                "preferred_channels": ["discord"],
                "timezone": "UTC",
                "reminder_frequency": "smart",
            }

            result = (
                supabase_service.client.table("reminder_settings")
                .upsert(initial_settings)
                .execute()
            )
            print(f"✅ Created initial settings: {result.data[0]['enabled']}")

        except Exception as e:
            print(f"❌ Error creating settings: {e}")

        # Test 2: Update enabled to False
        print("\n🔄 Testing update enabled to False...")
        try:
            # Check if settings exist first
            existing = (
                supabase_service.client.table("reminder_settings")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if existing.data:
                # Update existing
                result = (
                    supabase_service.client.table("reminder_settings")
                    .update({"enabled": False})
                    .eq("user_id", user_id)
                    .execute()
                )
                print(
                    f"✅ Updated enabled to: {result.data[0]['enabled'] if result.data else 'unknown'}"
                )
            else:
                print("❌ No existing settings found")

        except Exception as e:
            print(f"❌ Error updating settings: {e}")

        # Test 3: Read settings back
        print("\n📖 Testing read settings...")
        try:
            result = (
                supabase_service.client.table("reminder_settings")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                settings = result.data[0]
                print(f"✅ Read settings - enabled: {settings['enabled']}, id: {settings['id']}")
            else:
                print("❌ No settings found")

        except Exception as e:
            print(f"❌ Error reading settings: {e}")

        # Test 4: Update enabled to True
        print("\n🔄 Testing update enabled to True...")
        try:
            result = (
                supabase_service.client.table("reminder_settings")
                .update({"enabled": True})
                .eq("user_id", user_id)
                .execute()
            )
            print(
                f"✅ Updated enabled to: {result.data[0]['enabled'] if result.data else 'unknown'}"
            )

        except Exception as e:
            print(f"❌ Error updating settings: {e}")

        print("\n🎉 Reminder settings test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_reminder_settings())
    sys.exit(0 if success else 1)
