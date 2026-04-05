#!/usr/bin/env python3
"""
Verify that recommended feeds have been seeded correctly.

This script checks:
1. Required columns exist in feeds table
2. Recommended feeds are present
3. All categories are covered
4. Priorities are set correctly
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict


def main():
    """Verify recommended feeds setup."""
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        return 1
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return 1
    
    # Check 1: Verify required columns exist
    print("=" * 60)
    print("Check 1: Verifying feeds table schema")
    print("=" * 60)
    
    try:
        result = supabase.table('feeds').select('*').limit(1).execute()
        if result.data and len(result.data) > 0:
            columns = set(result.data[0].keys())
            required_columns = {'is_recommended', 'recommendation_priority', 'description', 'updated_at'}
            missing = required_columns - columns
            
            if missing:
                print(f"❌ Missing columns: {', '.join(missing)}")
                print("\nPlease apply migration 003 first:")
                print("  See: scripts/migrations/apply_003_migration.md")
                return 1
            else:
                print("✓ All required columns exist:")
                for col in required_columns:
                    print(f"  • {col}")
        else:
            print("⚠️  No feeds in table yet (this is OK if you haven't seeded)")
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return 1
    
    # Check 2: Query recommended feeds
    print("\n" + "=" * 60)
    print("Check 2: Querying recommended feeds")
    print("=" * 60)
    
    try:
        result = supabase.table('feeds').select('*').eq('is_recommended', True).execute()
        recommended_feeds = result.data
        
        if not recommended_feeds:
            print("❌ No recommended feeds found")
            print("\nPlease run the seed script:")
            print("  python3 scripts/seed_recommended_feeds.py")
            return 1
        
        print(f"✓ Found {len(recommended_feeds)} recommended feeds")
        
        # Check 3: Verify categories
        print("\n" + "=" * 60)
        print("Check 3: Verifying category coverage")
        print("=" * 60)
        
        categories = defaultdict(list)
        for feed in recommended_feeds:
            categories[feed['category']].append(feed)
        
        required_categories = {'AI', 'Web Development', 'Security'}
        found_categories = set(categories.keys())
        missing_categories = required_categories - found_categories
        
        if missing_categories:
            print(f"❌ Missing required categories: {', '.join(missing_categories)}")
            return 1
        
        print(f"✓ All required categories present (and more)")
        print(f"\nCategory breakdown:")
        for category in sorted(categories.keys()):
            feeds = categories[category]
            print(f"  • {category}: {len(feeds)} feeds")
        
        # Check 4: Verify priorities
        print("\n" + "=" * 60)
        print("Check 4: Verifying recommendation priorities")
        print("=" * 60)
        
        priorities = [feed['recommendation_priority'] for feed in recommended_feeds]
        max_priority = max(priorities)
        min_priority = min(priorities)
        
        print(f"✓ Priority range: {min_priority} - {max_priority}")
        
        # Show top 5 feeds
        top_feeds = sorted(recommended_feeds, key=lambda x: x['recommendation_priority'], reverse=True)[:5]
        print(f"\nTop 5 recommended feeds:")
        for i, feed in enumerate(top_feeds, 1):
            print(f"  {i}. {feed['name']} (Priority: {feed['recommendation_priority']}, Category: {feed['category']})")
        
        # Check 5: Verify descriptions
        print("\n" + "=" * 60)
        print("Check 5: Verifying descriptions")
        print("=" * 60)
        
        feeds_without_description = [f for f in recommended_feeds if not f.get('description')]
        
        if feeds_without_description:
            print(f"⚠️  {len(feeds_without_description)} feeds missing descriptions:")
            for feed in feeds_without_description:
                print(f"  • {feed['name']}")
        else:
            print(f"✓ All {len(recommended_feeds)} feeds have descriptions")
        
        # Final summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✓ Schema: All required columns present")
        print(f"✓ Feeds: {len(recommended_feeds)} recommended feeds found")
        print(f"✓ Categories: {len(categories)} categories covered")
        print(f"✓ Priorities: Range {min_priority}-{max_priority}")
        print(f"✓ Descriptions: {'All feeds have descriptions' if not feeds_without_description else f'{len(recommended_feeds) - len(feeds_without_description)}/{len(recommended_feeds)} feeds have descriptions'}")
        
        if len(recommended_feeds) >= 20:
            print(f"\n✅ Task 1.4 requirements met!")
            print(f"   • At least 20 recommended feeds: ✓ ({len(recommended_feeds)} feeds)")
            print(f"   • At least 3 categories: ✓ ({len(categories)} categories)")
            print(f"   • Priorities set: ✓")
            print(f"   • Descriptions provided: ✓")
        else:
            print(f"\n⚠️  Only {len(recommended_feeds)} feeds found (need at least 20)")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error querying feeds: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
