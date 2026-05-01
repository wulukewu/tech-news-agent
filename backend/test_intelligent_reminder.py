#!/usr/bin/env python3
"""
Test script for Intelligent Reminder Agent
Run this after creating the database tables to verify functionality.
"""

import asyncio
import sys

# Add the backend directory to Python path
sys.path.append("/app")

from app.qa_agent.intelligent_reminder.intelligent_reminder_agent import IntelligentReminderAgent
from app.services.supabase_service import SupabaseService


async def test_intelligent_reminder_agent():
    """Test the intelligent reminder agent end-to-end"""
    print("🧪 Testing Intelligent Reminder Agent...")

    try:
        # Initialize services
        supabase = SupabaseService()
        agent = IntelligentReminderAgent()

        # Check if tables exist
        print("\n📋 Checking database tables...")
        tables = ["reminder_log", "reminder_settings", "article_graph", "technology_registry"]
        for table in tables:
            try:
                result = supabase.client.table(table).select("*").limit(1).execute()
                print(f"✅ {table}: exists")
            except Exception as e:
                print(f"❌ {table}: {str(e)[:100]}")
                return False

        # Get a test user (first user from users table)
        users_result = supabase.client.table("users").select("id, discord_id").limit(1).execute()
        if not users_result.data:
            print("❌ No users found in database. Please create a user first.")
            return False

        test_user = users_result.data[0]
        user_id = test_user["id"]
        print(f"👤 Using test user: {user_id}")

        # Get some test articles
        articles_result = supabase.client.table("articles").select("id, title").limit(3).execute()
        if len(articles_result.data) < 2:
            print("❌ Need at least 2 articles in database for testing.")
            return False

        articles = articles_result.data
        print(f"📄 Found {len(articles)} articles for testing")

        # Test 1: Create reminder settings for user
        print("\n🔧 Test 1: Creating reminder settings...")
        reminder_settings = {
            "user_id": user_id,
            "enabled": True,
            "max_daily_reminders": 3,
            "preferred_channels": ["discord"],
            "reminder_frequency": "smart",
        }

        # Insert or update reminder settings
        try:
            supabase.client.table("reminder_settings").upsert(reminder_settings).execute()
            print("✅ Reminder settings created")
        except Exception as e:
            print(f"❌ Failed to create reminder settings: {e}")
            return False

        # Test 2: Create article relationships
        print("\n🔗 Test 2: Creating article relationships...")
        if len(articles) >= 2:
            article_relation = {
                "source_article_id": articles[0]["id"],
                "target_article_id": articles[1]["id"],
                "relationship_type": "follow_up",
                "confidence_score": 0.8,
                "analysis_metadata": {"reason": "Test relationship"},
            }

            try:
                supabase.client.table("article_graph").upsert(article_relation).execute()
                print("✅ Article relationship created")
            except Exception as e:
                print(f"❌ Failed to create article relationship: {e}")

        # Test 3: Create a test reminder
        print("\n📬 Test 3: Creating test reminder...")
        test_reminder = {
            "user_id": user_id,
            "reminder_type": "article_relation",
            "content_id": articles[0]["id"],
            "reminder_context": {
                "title": "Test Reminder",
                "message": f'You might be interested in reading: {articles[0]["title"]}',
                "article_title": articles[0]["title"],
                "reason": "Based on your reading history",
            },
            "channel": "discord",
            "status": "pending",
        }

        try:
            reminder_result = supabase.client.table("reminder_log").insert(test_reminder).execute()
            reminder_id = reminder_result.data[0]["id"]
            print(f"✅ Test reminder created: {reminder_id}")
        except Exception as e:
            print(f"❌ Failed to create test reminder: {e}")
            return False

        # Test 4: Get pending reminders
        print("\n📋 Test 4: Getting pending reminders...")
        try:
            pending_reminders = await agent.get_pending_reminders(user_id)
            print(f"✅ Found {len(pending_reminders)} pending reminders")

            if pending_reminders:
                print("📝 Sample reminder:")
                sample = pending_reminders[0]
                print(f"   Type: {sample.get('reminder_type')}")
                print(f"   Channel: {sample.get('channel')}")
                print(f"   Status: {sample.get('status')}")
        except Exception as e:
            print(f"❌ Failed to get pending reminders: {e}")
            return False

        # Test 5: Test multi-channel sync logic
        print("\n🔄 Test 5: Testing multi-channel sync...")
        try:
            # Create a reminder that's already read on another channel
            read_reminder = {
                "user_id": user_id,
                "reminder_type": "article_relation",
                "content_id": articles[0]["id"],  # Same content as before
                "reminder_context": {"title": "Already Read Test"},
                "channel": "web",
                "status": "read",  # Mark as already read
            }

            supabase.client.table("reminder_log").insert(read_reminder).execute()

            # Now try to send the original reminder - it should be skipped
            test_reminder_dict = {
                "id": reminder_id,
                "user_id": user_id,
                "content_id": articles[0]["id"],
                "reminder_context": test_reminder["reminder_context"],
                "channel": "discord",
            }

            await agent._send_reminder(test_reminder_dict)
            print("✅ Multi-channel sync test completed")

        except Exception as e:
            print(f"❌ Multi-channel sync test failed: {e}")

        # Test 6: Generate effectiveness report
        print("\n📊 Test 6: Generating effectiveness report...")
        try:
            report = await agent.generate_effectiveness_report(user_id)
            print("✅ Effectiveness report generated")
            print(f"   Total reminders: {report.total_reminders}")
            print(f"   Click rate: {report.click_rate:.2%}")
            print(f"   Avg response time: {report.avg_response_time}")
        except Exception as e:
            print(f"❌ Failed to generate effectiveness report: {e}")

        print("\n🎉 Intelligent Reminder Agent test completed!")
        print("\n💡 To see reminders in action:")
        print("   1. Make sure the database tables are created in Supabase")
        print("   2. Add some articles to your reading list")
        print("   3. The agent will analyze relationships and send smart reminders")
        print("   4. Check the /app/reminders page in the web interface")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_intelligent_reminder_agent())
    sys.exit(0 if success else 1)
