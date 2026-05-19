#!/usr/bin/env python3
"""
Test script for Intelligent Reminder API endpoints
"""

import asyncio
import sys
from uuid import uuid4

from app.qa_agent.intelligent_reminder import IntelligentReminderAgent
from app.services.supabase_service import SupabaseService


async def test_intelligent_reminder_api():
    """Test the intelligent reminder system"""
    print("🧪 Testing Intelligent Reminder API...")

    try:
        # Initialize services
        supabase_service = SupabaseService()
        reminder_agent = IntelligentReminderAgent(supabase_service=supabase_service)

        print("✅ Services initialized successfully")

        # Test 1: Check database tables exist
        print("\n📋 Testing database tables...")

        tables_to_check = [
            "reminder_settings",
            "reminder_log",
            "article_graph",
            "technology_registry",
            "user_behavior_patterns",
        ]

        for table in tables_to_check:
            try:
                result = supabase_service.client.table(table).select("*").limit(1).execute()
                print(f"✅ Table '{table}' exists and accessible")
            except Exception as e:
                print(f"❌ Table '{table}' error: {e}")

        # Test 2: Test reminder agent methods
        print("\n🤖 Testing reminder agent...")

        # Create a test user ID
        test_user_id = uuid4()

        # Test getting user settings (should return defaults)
        try:
            settings = await reminder_agent.timing_engine._get_user_settings(test_user_id)
            print(f"✅ User settings retrieved: {settings is not None}")
        except Exception as e:
            print(f"❌ User settings error: {e}")

        # Test 3: Test API endpoints structure
        print("\n🔌 Testing API endpoint structure...")

        try:
            from app.api.intelligent_reminder import router

            # Check if router has expected endpoints
            routes = [route.path for route in router.routes]
            print(f"Available routes: {routes}")

            expected_routes = [
                "/pending",
                "/{reminder_id}/dismiss",
                "/{reminder_id}/read",
                "/settings",
                "/stats",
            ]

            for expected_route in expected_routes:
                if expected_route in routes:
                    print(f"✅ Route '{expected_route}' exists")
                else:
                    print(f"❌ Route '{expected_route}' missing")
        except Exception as e:
            print(f"❌ Router import error: {e}")

        print("\n🎉 Intelligent Reminder API test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_intelligent_reminder_api())
    sys.exit(0 if success else 1)
