#!/usr/bin/env python3
"""
Educational RSS Feed Seeder
Seeds the database with curated educational RSS feeds for learning content enhancement.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logger import get_logger
from app.services.educational_rss_manager import EDUCATIONAL_FEEDS, EducationalRSSManager
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


async def seed_educational_feeds():
    """Seed the database with educational RSS feeds."""
    try:
        logger.info("Starting educational RSS feed seeding...")

        # Initialize services
        supabase_service = SupabaseService()
        rss_manager = EducationalRSSManager(supabase_service)

        # Check if feeds already exist
        existing_feeds = await rss_manager.get_educational_feeds()
        existing_urls = {
            feed.get("feeds", {}).get("url") for feed in existing_feeds if feed.get("feeds")
        }

        added_count = 0
        skipped_count = 0

        # Add each educational feed
        for feed_config in EDUCATIONAL_FEEDS:
            try:
                if feed_config["url"] in existing_urls:
                    logger.info(f"Skipping existing feed: {feed_config['name']}")
                    skipped_count += 1
                    continue

                feed_id = await rss_manager.add_educational_feed(
                    url=feed_config["url"],
                    name=feed_config["name"],
                    feed_type=feed_config["feed_type"],
                    content_focus=feed_config["content_focus"],
                    target_audience=feed_config["target_audience"],
                    primary_topics=feed_config["primary_topics"],
                )

                logger.info(f"Added educational feed: {feed_config['name']} (ID: {feed_id})")
                added_count += 1

            except Exception as e:
                logger.error(f"Failed to add feed {feed_config['name']}: {e}")
                continue

        logger.info(
            f"Educational feed seeding completed: {added_count} added, {skipped_count} skipped"
        )

        # Display summary
        all_feeds = await rss_manager.get_educational_feeds()
        logger.info(f"Total educational feeds in database: {len(all_feeds)}")

        # Group by type
        type_counts = {}
        for feed in all_feeds:
            feed_type = feed.get("feed_type", "unknown")
            type_counts[feed_type] = type_counts.get(feed_type, 0) + 1

        logger.info("Feed distribution by type:")
        for feed_type, count in type_counts.items():
            logger.info(f"  {feed_type}: {count}")

        return {
            "success": True,
            "added": added_count,
            "skipped": skipped_count,
            "total": len(all_feeds),
            "distribution": type_counts,
        }

    except Exception as e:
        logger.error(f"Educational feed seeding failed: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Main function."""
    print("🌱 Educational RSS Feed Seeder")
    print("=" * 50)

    result = await seed_educational_feeds()

    if result["success"]:
        print(f"✅ Success! Added {result['added']} new feeds")
        print(f"📊 Total educational feeds: {result['total']}")
        print("\n📈 Distribution by type:")
        for feed_type, count in result["distribution"].items():
            print(f"   {feed_type}: {count}")
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
