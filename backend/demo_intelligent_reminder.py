#!/usr/bin/env python3
"""
Intelligent Reminder Agent Demo
Creates a working demonstration without requiring new database tables
"""

import asyncio
import sys

sys.path.append("/app")

from app.qa_agent.intelligent_reminder.intelligent_reminder_agent import IntelligentReminderAgent
from app.qa_agent.intelligent_reminder.models import ReminderContext
from app.services.supabase_service import SupabaseService


async def demo_intelligent_reminders():
    """Demonstrate intelligent reminder functionality"""
    print("🎯 Intelligent Reminder Agent Demo")
    print("=" * 50)

    try:
        # Initialize services
        supabase = SupabaseService()
        agent = IntelligentReminderAgent()

        # Get real user and articles from database
        users_result = supabase.client.table("users").select("id, discord_id").limit(1).execute()
        if not users_result.data:
            print("❌ No users found. Please create a user first.")
            return

        user = users_result.data[0]
        user_id = user["id"]
        discord_id = user.get("discord_id")

        articles_result = (
            supabase.client.table("articles")
            .select("id, title, url, ai_summary")
            .limit(5)
            .execute()
        )
        if len(articles_result.data) < 2:
            print("❌ Need at least 2 articles for demo.")
            return

        articles = articles_result.data

        print(f"👤 Demo User: {discord_id or user_id}")
        print(f"📚 Available Articles: {len(articles)}")
        print()

        # Demo 1: Article Relationship Reminder
        print("🔗 Demo 1: Article Relationship Reminder")
        print("-" * 40)

        article1 = articles[0]
        article2 = articles[1]

        relationship_context = ReminderContext(
            title="Follow-up Reading Suggestion",
            description=f"Based on your interest in '{article1['title']}', you might find this related article valuable.",
            related_articles=[
                {
                    "title": article2["title"],
                    "url": article2.get("url", "#"),
                    "summary": article2.get("ai_summary", "No summary available")[:100] + "...",
                    "relationship": "This article builds upon concepts from your previous reading",
                    "confidence": 0.85,
                }
            ],
            reading_time_estimate=7,
            priority_score=0.8,
            action_url=article2.get("url", "#"),
        )

        # Format the reminder
        from app.qa_agent.intelligent_reminder.context_generator import ContentFormatter

        text_reminder = ContentFormatter.format_to_text(relationship_context)
        html_reminder = ContentFormatter.format_to_html(relationship_context)

        print("📱 Discord Message Preview:")
        print("```")
        print(text_reminder)
        print("```")
        print()

        # Demo 2: Version Update Reminder
        print("🔄 Demo 2: Technology Version Update Reminder")
        print("-" * 40)

        version_context = ReminderContext(
            title="React 19 Released - Action Required",
            description="A new major version of React has been released with breaking changes that affect your recent reading.",
            related_articles=[
                {
                    "title": "React 19 Migration Guide",
                    "url": "https://react.dev/blog/2024/04/25/react-19",
                    "summary": "Learn about the new features and breaking changes in React 19",
                    "relationship": "Updates concepts from articles you've read about React 18",
                    "confidence": 0.95,
                }
            ],
            version_info={
                "technology": "React",
                "old_version": "18.x",
                "new_version": "19.0",
                "version_type": "major",
                "breaking_changes": True,
                "impact_level": "high",
            },
            reading_time_estimate=12,
            priority_score=0.9,
            action_url="https://react.dev/blog/2024/04/25/react-19",
        )

        version_reminder = ContentFormatter.format_to_text(version_context)

        print("📱 Discord Message Preview:")
        print("```")
        print(version_reminder)
        print("```")
        print()

        # Demo 3: Learning Path Reminder
        print("🎓 Demo 3: Learning Path Progress Reminder")
        print("-" * 40)

        learning_context = ReminderContext(
            title="Continue Your AI/ML Learning Journey",
            description="You've completed the fundamentals. Ready for the next step?",
            related_articles=[
                {
                    "title": "Advanced Neural Networks",
                    "url": "#",
                    "summary": "Deep dive into advanced neural network architectures",
                    "relationship": "Next logical step after your recent ML readings",
                    "confidence": 0.88,
                },
                {
                    "title": "Production ML Systems",
                    "url": "#",
                    "summary": "Learn how to deploy ML models in production",
                    "relationship": "Practical application of your theoretical knowledge",
                    "confidence": 0.82,
                },
            ],
            reading_time_estimate=15,
            priority_score=0.75,
            action_url="/app/learning",
        )

        learning_reminder = ContentFormatter.format_to_text(learning_context)

        print("📱 Discord Message Preview:")
        print("```")
        print(learning_reminder)
        print("```")
        print()

        # Demo 4: Multi-channel sync demonstration
        print("🔄 Demo 4: Multi-Channel Sync Logic")
        print("-" * 40)

        print("Scenario: User reads article on web, Discord reminder gets auto-dismissed")
        print()

        # Simulate the sync logic
        content_id = article1["id"]

        print(f"1. User reads article '{article1['title']}' on web interface")
        print("2. System checks: any pending Discord reminders for this article?")
        print("3. Found pending reminder → Auto-mark as 'read' (cross-channel sync)")
        print("4. User won't get duplicate notification on Discord ✅")
        print()

        # Demo 5: Channel fallback logic
        print("📡 Demo 5: Channel Fallback Logic")
        print("-" * 40)

        print("Scenario: Discord DM fails 3 times → Switch to web notifications")
        print()
        print("1. Attempt 1: Discord DM failed (user blocked bot)")
        print("2. Attempt 2: Discord DM failed (user offline)")
        print("3. Attempt 3: Discord DM failed (rate limited)")
        print("4. System switches to web push notifications ✅")
        print("5. Future reminders will use web channel until Discord recovers")
        print()

        print("🎉 Demo Complete!")
        print()
        print("💡 Key Benefits You'll Experience:")
        print("   🎯 Smart timing - reminders when you're most likely to read")
        print("   🔗 Relationship awareness - suggests related content intelligently")
        print("   🔄 No duplicates - cross-platform sync prevents spam")
        print("   📡 Reliable delivery - automatic fallback if one channel fails")
        print("   📊 Learning optimization - tracks what works and adapts")
        print()
        print("🚀 To activate full system:")
        print("   1. Execute the SQL script in Supabase Dashboard")
        print("   2. Add some articles to your reading list")
        print("   3. Rate a few articles (helps the AI learn your preferences)")
        print("   4. The system will start sending intelligent reminders!")

        return True

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(demo_intelligent_reminders())
    sys.exit(0 if success else 1)
