"""
Helper script to apply migration 003 for testing.
This script applies the migration directly using Supabase client.
"""

import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def apply_migration_003():
    """Apply migration 003 to add recommendation columns to feeds table."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    client = create_client(url, key)

    # Check if migration is already applied
    try:
        client.table("feeds").select("is_recommended").limit(1).execute()
        print("✅ Migration 003 already applied")
        return True
    except Exception:
        pass

    print("📝 Applying migration 003...")
    print("⚠️  Note: This requires manual application via Supabase SQL Editor")
    print("\nPlease run the following SQL in Supabase SQL Editor:")
    print("=" * 80)

    with open("scripts/migrations/003_extend_feeds_table_for_recommendations.sql") as f:
        sql = f.read()
        print(sql)

    print("=" * 80)
    print("\nAfter applying the SQL, run the tests again.")
    return False


if __name__ == "__main__":
    apply_migration_003()
