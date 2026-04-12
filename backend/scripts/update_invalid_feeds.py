#!/usr/bin/env python3
"""
Update script to deactivate invalid RSS feeds and add new ones.

This script:
1. Deactivates feeds with 404 URLs
2. Adds new valid feeds to replace them
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client


def main():
    """Main function to update feeds in Supabase database."""

    # Load environment variables
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Successfully connected to Supabase")

    # Deactivate invalid feeds
    invalid_urls = [
        "https://news.vuejs.org/rss.xml",
        "https://news.vuejs.org/issues.rss",
        "https://vitepress.dev/blog/rss.xml",
        "https://expressjs.com/feed.xml",
    ]

    print("\nDeactivating invalid feeds...")
    for url in invalid_urls:
        try:
            result = supabase.table("feeds").update({"is_active": False}).eq("url", url).execute()
            if result.data:
                print(f"✓ Deactivated: {url}")
            else:
                print(f"⊘ Not found: {url}")
        except Exception as e:
            print(f"✗ Error deactivating {url}: {e!s}")

    # Add new valid feeds
    new_feeds = [
        {
            "name": "Vue.js Blog",
            "url": "https://blog.vuejs.org/feed.rss",
            "category": "前端開發",
            "is_active": True,
        },
        {
            "name": "Vite",
            "url": "https://vitejs.dev/blog.rss",
            "category": "前端開發",
            "is_active": True,
        },
        {
            "name": "React Blog",
            "url": "https://react.dev/rss.xml",
            "category": "前端開發",
            "is_active": True,
        },
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/blog/rss.xml",
            "category": "AI 應用",
            "is_active": True,
        },
    ]

    print("\nAdding new feeds...")
    for feed in new_feeds:
        try:
            supabase.table("feeds").insert(feed).execute()
            print(f"✓ Added: {feed['name']}")
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                print(f"⊘ Already exists: {feed['name']}")
            else:
                print(f"✗ Error adding {feed['name']}: {e!s}")

    print("\n" + "=" * 50)
    print("Feed update completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
