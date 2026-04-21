#!/usr/bin/env python3
"""
Verify migration 009: Check if notification day fields exist

This script verifies that the notification_day_of_week and notification_day_of_month
fields have been added to the user_notification_preferences table.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client


def verify_migration():
    """Verify the migration was applied successfully."""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)

    # Create client
    client = create_client(supabase_url, supabase_key)

    print("🔍 Verifying migration 009...")

    try:
        # Try to query with the new fields
        result = client.table("user_notification_preferences").select(
            "id, notification_day_of_week, notification_day_of_month"
        ).limit(1).execute()

        print("✅ Migration verified successfully!")
        print(f"   Found {len(result.data)} record(s)")

        if result.data:
            sample = result.data[0]
            print(f"\n📊 Sample data:")
            print(f"   notification_day_of_week: {sample.get('notification_day_of_week', 'N/A')}")
            print(f"   notification_day_of_month: {sample.get('notification_day_of_month', 'N/A')}")

        return True

    except Exception as e:
        error_msg = str(e).lower()
        if "column" in error_msg and ("notification_day_of_week" in error_msg or "notification_day_of_month" in error_msg):
            print("❌ Migration not applied yet!")
            print(f"   Error: {e}")
            print("\n📝 To apply the migration:")
            print("   1. Go to Supabase Dashboard > SQL Editor")
            print("   2. Copy and paste the contents of:")
            print(f"      scripts/migrations/009_add_notification_day_fields.sql")
            print("   3. Run the SQL")
            return False
        else:
            print(f"❌ Unexpected error: {e}")
            return False


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
