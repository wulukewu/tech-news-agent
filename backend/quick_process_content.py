#!/usr/bin/env python3
"""
Quick data processing to ensure we have content for the learning content page.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.rss_service import RSSService
from app.services.supabase_service import SupabaseService


async def process_educational_feeds():
    """Process educational feeds to get fresh content."""
    try:
        print("🔄 Processing educational RSS feeds...")

        supabase = SupabaseService()
        rss_service = RSSService(supabase)

        # Get educational feeds
        feeds_result = (
            supabase.client.table("feed_categories")
            .select("feed_id, feeds(id, name, url)")
            .in_("feed_type", ["educational", "official"])
            .execute()
        )

        if not feeds_result.data:
            print("❌ No educational feeds found")
            return

        processed_count = 0
        total_articles = 0

        for feed_data in feeds_result.data[:5]:  # Process first 5 feeds
            try:
                feed = feed_data["feeds"]
                print(f"📡 Processing: {feed['name']}")

                # Fetch articles
                articles = await rss_service.fetch_feed_articles(feed["url"])

                if articles:
                    print(f"   ✅ Found {len(articles)} articles")
                    total_articles += len(articles)
                else:
                    print("   ⚠️  No new articles")

                processed_count += 1

            except Exception as e:
                print(
                    f"   ❌ Error processing {feed_data.get('feeds', {}).get('name', 'unknown')}: {e}"
                )
                continue

        print("\n📊 Summary:")
        print(f"   📡 Processed feeds: {processed_count}")
        print(f"   📰 Total articles: {total_articles}")

        # Check final article count
        final_count = supabase.client.table("articles").select("*", count="exact").execute()
        print(f"   🗄️  Articles in database: {final_count.count}")

        return True

    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False


async def main():
    """Main function."""
    print("🚀 Quick Educational Content Processing")
    print("=" * 50)

    success = await process_educational_feeds()

    if success:
        print("\n✅ Processing completed!")
        print("\n📋 Next steps:")
        print("1. Visit http://localhost:3000/learning-content")
        print("2. Login with Discord")
        print("3. Browse educational content")
    else:
        print("\n❌ Processing failed")


if __name__ == "__main__":
    asyncio.run(main())
