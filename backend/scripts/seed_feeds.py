#!/usr/bin/env python3
"""
Seed script for initializing default RSS feeds in Supabase database.

This script:
1. Loads environment variables from .env file
2. Validates required Supabase credentials
3. Establishes connection to Supabase
4. Inserts predefined RSS feeds into the feeds table

Usage:
    python scripts/seed_feeds.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client


def main():
    """Main function to seed feeds into Supabase database."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Validate required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_URL\n"
            "Please copy .env.example to .env and fill in the values"
        )
    
    if not supabase_key:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_KEY\n"
            "Please copy .env.example to .env and fill in the values"
        )
    
    # Create Supabase client connection
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Successfully connected to Supabase")
    except Exception as e:
        raise ConnectionError(
            f"Error: Failed to connect to Supabase\n"
            f"Please check:\n"
            f"1. SUPABASE_URL is correct (format: https://xxx.supabase.co)\n"
            f"2. SUPABASE_KEY is valid (check Supabase Dashboard > Settings > API)\n"
            f"3. Network connection is available\n"
            f"Details: {str(e)}"
        )
    
    # Define default RSS feeds data structure
    default_feeds = [
        # 前端開發類別
        {
            "name": "Vue.js News",
            "url": "https://news.vuejs.org/rss.xml",
            "category": "前端開發",
            "is_active": True
        },
        {
            "name": "Nuxt",
            "url": "https://nuxt.com/blog/rss.xml",
            "category": "前端開發",
            "is_active": True
        },
        {
            "name": "VitePress",
            "url": "https://vitepress.dev/blog/rss.xml",
            "category": "前端開發",
            "is_active": True
        },
        {
            "name": "Express",
            "url": "https://expressjs.com/feed.xml",
            "category": "前端開發",
            "is_active": True
        },
        {
            "name": "Vue.js Developers",
            "url": "https://vuejsdevelopers.com/atom.xml",
            "category": "前端開發",
            "is_active": True
        },
        # 自架服務類別
        {
            "name": "Reddit r/selfhosted",
            "url": "https://www.reddit.com/r/selfhosted/.rss",
            "category": "自架服務",
            "is_active": True
        },
        {
            "name": "Reddit r/docker",
            "url": "https://www.reddit.com/r/docker/.rss",
            "category": "自架服務",
            "is_active": True
        },
        {
            "name": "Home Assistant",
            "url": "https://www.home-assistant.io/atom.xml",
            "category": "自架服務",
            "is_active": True
        },
        {
            "name": "Awesome-Selfhosted",
            "url": "https://github.com/awesome-selfhosted/awesome-selfhosted/commits/master.atom",
            "category": "自架服務",
            "is_active": True
        },
        # AI 應用類別
        {
            "name": "Simon Willison's Weblog",
            "url": "https://simonwillison.net/atom/everything/",
            "category": "AI 應用",
            "is_active": True
        },
        {
            "name": "Reddit r/LocalLLaMA",
            "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
            "category": "AI 應用",
            "is_active": True
        },
        {
            "name": "Vue.js Community Newsletters",
            "url": "https://news.vuejs.org/issues.rss",
            "category": "AI 應用",
            "is_active": True
        }
    ]
    
    print("Supabase client initialized successfully")
    print(f"Ready to seed {len(default_feeds)} feeds...")
    
    # Insert feeds with error handling
    inserted_count = 0
    skipped_count = 0
    
    for feed in default_feeds:
        try:
            # Attempt to insert the feed
            supabase.table('feeds').insert(feed).execute()
            inserted_count += 1
            print(f"✓ Inserted: {feed['name']}")
        except Exception as e:
            error_message = str(e).lower()
            
            # Handle duplicate URL error
            if 'duplicate' in error_message or 'unique' in error_message:
                skipped_count += 1
                print(f"⊘ Skipped (duplicate URL): {feed['name']} - {feed['url']}")
                continue
            
            # Handle connection errors
            elif 'connection' in error_message or 'network' in error_message or 'timeout' in error_message:
                raise ConnectionError(
                    f"Error: Network error while inserting feed '{feed['name']}'\n"
                    f"Please check your internet connection and try again\n"
                    f"If the problem persists, check Supabase status at status.supabase.com\n"
                    f"Details: {str(e)}"
                )
            
            # Re-raise other unexpected errors
            else:
                raise Exception(
                    f"Error: Unexpected error while inserting feed '{feed['name']}'\n"
                    f"Details: {str(e)}"
                )
    
    # Print summary
    print("\n" + "="*50)
    print(f"Seeding completed!")
    print(f"Successfully inserted: {inserted_count} feeds")
    if skipped_count > 0:
        print(f"Skipped (duplicates): {skipped_count} feeds")
    print("="*50)


if __name__ == "__main__":
    main()
