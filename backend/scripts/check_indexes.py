#!/usr/bin/env python3
"""
Script to check existing indexes on the reading_list table.
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.supabase_service import SupabaseService


def check_indexes():
    """Check existing indexes on reading_list table."""
    service = SupabaseService()

    # Query to get indexes
    # Note: Supabase doesn't expose pg_indexes directly via REST API
    # We'll need to check if the indexes exist by their effects

    print("Checking reading_list table structure...")

    try:
        # Get table structure
        result = service.client.table("reading_list").select("*").limit(0).execute()
        print("✓ reading_list table exists")

        # Check if we can query with different filters (this indirectly tests indexes)
        print("\nTesting query patterns (indexes improve these queries):")

        # Test user_id query
        test1 = (
            service.client.table("reading_list")
            .select("*")
            .eq("user_id", "00000000-0000-0000-0000-000000000000")
            .limit(1)
            .execute()
        )
        print("✓ user_id query works")

        # Test user_id + status query
        test2 = (
            service.client.table("reading_list")
            .select("*")
            .eq("user_id", "00000000-0000-0000-0000-000000000000")
            .eq("status", "Unread")
            .limit(1)
            .execute()
        )
        print("✓ user_id + status query works")

        # Test user_id + rating query
        test3 = (
            service.client.table("reading_list")
            .select("*")
            .eq("user_id", "00000000-0000-0000-0000-000000000000")
            .not_.is_("rating", "null")
            .limit(1)
            .execute()
        )
        print("✓ user_id + rating query works")

        # Test user_id + order by added_at
        test4 = (
            service.client.table("reading_list")
            .select("*")
            .eq("user_id", "00000000-0000-0000-0000-000000000000")
            .order("added_at", desc=True)
            .limit(1)
            .execute()
        )
        print("✓ user_id + order by added_at query works")

        print("\n✓ All query patterns work correctly")
        print("\nNote: To verify indexes exist in the database, you need to:")
        print("1. Connect to Supabase SQL Editor")
        print(
            "2. Run: SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'reading_list';"
        )

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = check_indexes()
    sys.exit(0 if success else 1)
