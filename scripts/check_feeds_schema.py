#!/usr/bin/env python3
"""
Check the current schema of the feeds table.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client


def main():
    """Check feeds table schema."""

    load_dotenv()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

    supabase: Client = create_client(supabase_url, supabase_key)
    print("Connected to Supabase")

    # Try to query a feed to see what columns exist
    try:
        result = supabase.table('feeds').select('*').limit(1).execute()
        if result.data and len(result.data) > 0:
            print("\nCurrent feeds table columns:")
            for key in result.data[0].keys():
                print(f"  - {key}")
        else:
            print("\nNo feeds found in table, checking by inserting a test record...")
            # Try to insert a minimal record to see what's required
            test_feed = {
                "name": "Test Feed",
                "url": "https://test.example.com/feed.xml",
                "category": "Test",
                "is_active": True
            }
            try:
                supabase.table('feeds').insert(test_feed).execute()
                print("✓ Basic columns exist: name, url, category, is_active")
                # Clean up
                supabase.table('feeds').delete().eq('url', test_feed['url']).execute()
            except Exception as e:
                print(f"Error inserting test feed: {e}")

    except Exception as e:
        print(f"Error querying feeds: {e}")


if __name__ == "__main__":
    main()
