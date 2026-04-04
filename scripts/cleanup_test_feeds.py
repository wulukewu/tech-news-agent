#!/usr/bin/env python3
"""
Cleanup script to remove test feeds from the database.

This script removes all feeds with URLs matching test patterns:
- https://test-feed-*.com/rss.xml
- https://feed-*.com/rss
- Any feed with 'Test Feed' as the name

Run this script to clean up test data that may have been left in the database.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def cleanup_test_feeds():
    """Remove all test feeds from the database."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    # Patterns to match test feeds
    test_patterns = [
        'test-feed-%',
        'feed-%',
    ]
    
    total_deleted = 0
    
    for pattern in test_patterns:
        try:
            # Find feeds matching the pattern
            result = client.table('feeds').select('id, name, url').like('url', f'%{pattern}%').execute()
            feeds = result.data
            
            if feeds:
                print(f"\nFound {len(feeds)} feeds matching pattern '{pattern}':")
                for feed in feeds:
                    print(f"  - {feed['name']}: {feed['url']}")
                
                # Delete the feeds
                for feed in feeds:
                    client.table('feeds').delete().eq('id', feed['id']).execute()
                    total_deleted += 1
                    print(f"  ✓ Deleted feed: {feed['url']}")
        except Exception as e:
            print(f"Error processing pattern '{pattern}': {e}")
    
    # Also delete feeds with 'Test Feed' name
    try:
        result = client.table('feeds').select('id, name, url').eq('name', 'Test Feed').execute()
        feeds = result.data
        
        if feeds:
            print(f"\nFound {len(feeds)} feeds named 'Test Feed':")
            for feed in feeds:
                print(f"  - {feed['url']}")
                client.table('feeds').delete().eq('id', feed['id']).execute()
                total_deleted += 1
                print(f"  ✓ Deleted feed: {feed['url']}")
    except Exception as e:
        print(f"Error deleting 'Test Feed' entries: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {total_deleted} test feeds.")

if __name__ == "__main__":
    print("🧹 Cleaning up test feeds from database...")
    cleanup_test_feeds()
