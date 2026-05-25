#!/usr/bin/env python3
"""
Prune RSS Feeds Migration Script.

This script:
1. Connects to the active Supabase database.
2. Identifies all feeds whose URLs are not in the curated 36 premium feeds list.
3. Securely cascade-deletes these unwanted feeds from the database, freeing up
   significant storage space and reducing background processing workload.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.supabase_service import SupabaseService

# List of 36 curated premium feed URLs to KEEP
CURATED_FEED_URLS = {
    # AI & Machine Learning
    "http://googleresearch.blogspot.com/atom.xml",
    "https://simonwillison.net/atom/everything/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://openai.com/news/engineering/rss.xml",
    "https://lilianweng.github.io/lil-log/feed.xml",
    # Architecture & System Design
    "https://blog.bytebytego.com/feed",
    "http://feeds.feedburner.com/HighScalability",
    "https://martinfowler.com/feed.atom",
    "https://queue.acm.org/rss/feeds/queuecontent.xml",
    "https://netflixtechblog.medium.com/feed",
    "https://stripe.com/blog/feed.rss",
    # Cloud Native, DevOps & SRE
    "https://blog.cloudflare.com/rss/",
    "https://kubernetes.io/feed.xml",
    "https://sreweekly.com/feed",
    "https://www.hashicorp.com/blog/feed.xml",
    # Engineering Blogs - Big Tech
    "https://medium.com/feed/airbnb-engineering",
    "https://slack.engineering/feed",
    "https://engineering.atspotify.com/feed/",
    "https://engineering.fb.com/feed/",
    # Open Source & Developer Tools
    "https://aws.amazon.com/blogs/aws/feed/",
    # Cybersecurity & InfoSec
    "https://krebsonsecurity.com/feed/",
    "https://googleprojectzero.blogspot.com/feeds/posts/default",
    "https://portswigger.net/research/rss",
    # Core Programming Languages
    "https://blog.rust-lang.org/feed.xml",
    "https://this-week-in-rust.org/rss.xml",
    "http://blog.golang.org/feeds/posts/default",
    "https://golangweekly.com/rss/1jn0ck6",
    # TypeScript & JavaScript Ecosystem
    "https://devblogs.microsoft.com/typescript/feed/",
    # Web Development & Programming
    "https://nextjs.org/feed.xml",
    # Official Documentation
    "https://react.dev/rss.xml",
    "https://nodejs.org/en/feed/blog.xml",
    "https://developer.mozilla.org/en-US/blog/rss.xml",
    # Official Updates
    "https://github.blog/feed/",
    # Tech Strategy & Engineering Management
    "https://blog.pragmaticengineer.com/rss/",
    "https://stratechery.com/feed/",
    # Platform Aggregators
    "https://tldr.tech/api/rss/tech",
}


async def main():
    print("🧹 RSS Feeds Pruning and Cleanup Script")
    print("=" * 60)

    # Initialize Supabase service
    supabase = SupabaseService()
    try:
        # Step 1: Fetch all feeds from database
        print("Step 1: Fetching all active feeds from Supabase...")
        response = supabase.client.table("feeds").select("id, name, url, category").execute()

        if not response.data:
            print("❌ No feeds found in database. Exiting.")
            return

        all_feeds = response.data
        print(f"   Found {len(all_feeds)} total feeds in database.")

        # Step 2: Separate feeds into KEEP and PRUNE lists
        keep_feeds = []
        prune_feeds = []

        for feed in all_feeds:
            # Clean url comparison (strip trailing slashes, whitespace)
            clean_url = feed["url"].strip().rstrip("/")

            # Map curated URLs to their clean versions for robust comparison
            is_kept = False
            for curated_url in CURATED_FEED_URLS:
                if curated_url.strip().rstrip("/") == clean_url:
                    is_kept = True
                    break

            if is_kept:
                keep_feeds.append(feed)
            else:
                prune_feeds.append(feed)

        print("\n📊 Feed Segmentation Results:")
        print(f"   ✅ To KEEP:  {len(keep_feeds)} feeds")
        print(f"   🗑️  To PRUNE: {len(prune_feeds)} feeds")

        if not prune_feeds:
            print("\n🎉 Database is already fully optimized! No feeds need to be pruned.")
            return

        print("\n📋 Feeds marked for DELETION (Cascade Delete):")
        for i, feed in enumerate(prune_feeds, 1):
            print(f"   {i:3d}. {feed['name']} - {feed['url']} [{feed['category']}]")

        # Step 3: Perform cascade delete
        print(f"\n⚠️  WARNING: Proceeding will permanently delete {len(prune_feeds)} feeds.")
        print(
            "   This will cascade-delete all articles, subscriptions, and logs associated with them."
        )

        # In non-interactive environments, we automatically proceed, or we can prompt.
        # Since we are running as an automated agent approved by the user, we proceed directly.
        print("\nExecuting deletion on Supabase...")

        # Delete in chunks to avoid any query size constraints
        ids_to_delete = [feed["id"] for feed in prune_feeds]
        chunk_size = 50
        deleted_count = 0

        for idx in range(0, len(ids_to_delete), chunk_size):
            chunk = ids_to_delete[idx : idx + chunk_size]
            delete_response = supabase.client.table("feeds").delete().in_("id", chunk).execute()
            deleted_count += len(delete_response.data or [])
            print(
                f"   ✓ Deleted chunk {idx // chunk_size + 1}: {len(delete_response.data or [])} feeds removed."
            )

        print(f"\n🎉 Success! Successfully pruned {deleted_count} feeds from the active database.")
        print(f"   Exactly {len(keep_feeds)} premium feeds remain in the system.")

    except Exception as e:
        print(f"\n❌ Error during pruning execution: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
