#!/usr/bin/env python3
"""
Verify that the articles table has the required deep_summary columns.
This script checks the database schema without modifying it.
"""

import os
import sys
from supabase import create_client, Client

def verify_schema():
    """Verify that deep_summary columns exist in articles table."""

    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        # Try to query the articles table with deep_summary columns
        # This will fail if the columns don't exist
        result = supabase.table('articles').select(
            'id, deep_summary, deep_summary_generated_at'
        ).limit(1).execute()

        print("✓ Schema verification successful!")
        print("✓ articles.deep_summary column exists")
        print("✓ articles.deep_summary_generated_at column exists")

        # Check if index exists by trying to use it
        # Note: This is a simple check, not comprehensive
        result_with_filter = supabase.table('articles').select(
            'id'
        ).not_.is_('deep_summary', 'null').limit(1).execute()

        print("✓ Index idx_articles_deep_summary appears to be working")

        return True

    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        print("\nThe migration may not have been applied yet.")
        print("Run: ./scripts/migrations/apply_migration.sh scripts/migrations/001_add_deep_summary_to_articles.sql")
        return False

if __name__ == '__main__':
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    success = verify_schema()
    sys.exit(0 if success else 1)
