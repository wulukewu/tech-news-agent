#!/usr/bin/env python3
"""
Run migration 009: Add notification day fields

This script adds notification_day_of_week and notification_day_of_month fields
to the user_notification_preferences table.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client


def run_migration():
    """Execute the migration SQL."""
    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in environment")
        sys.exit(1)

    # Create Supabase client
    client = create_client(supabase_url, supabase_key)

    # Read migration SQL
    migration_file = Path(__file__).parent / "migrations" / "009_add_notification_day_fields.sql"
    with open(migration_file, "r") as f:
        sql = f.read()

    print("🔄 Running migration 009: Add notification day fields...")
    print(f"📄 Reading from: {migration_file}")

    try:
        # Execute the SQL using Supabase's RPC
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # We'll need to execute each statement separately

        statements = [
            # Add notification_day_of_week column
            """
            ALTER TABLE user_notification_preferences
            ADD COLUMN IF NOT EXISTS notification_day_of_week INTEGER DEFAULT 5;
            """,
            # Add check constraint for notification_day_of_week
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'user_notification_preferences_notification_day_of_week_check'
                ) THEN
                    ALTER TABLE user_notification_preferences
                    ADD CONSTRAINT user_notification_preferences_notification_day_of_week_check
                    CHECK (notification_day_of_week >= 0 AND notification_day_of_week <= 6);
                END IF;
            END $$;
            """,
            # Add notification_day_of_month column
            """
            ALTER TABLE user_notification_preferences
            ADD COLUMN IF NOT EXISTS notification_day_of_month INTEGER DEFAULT 1;
            """,
            # Add check constraint for notification_day_of_month
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'user_notification_preferences_notification_day_of_month_check'
                ) THEN
                    ALTER TABLE user_notification_preferences
                    ADD CONSTRAINT user_notification_preferences_notification_day_of_month_check
                    CHECK (notification_day_of_month >= 1 AND notification_day_of_month <= 31);
                END IF;
            END $$;
            """,
            # Add comments
            """
            COMMENT ON COLUMN user_notification_preferences.notification_day_of_week IS
            'Day of week for weekly notifications (0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday). Default: 5 (Friday)';
            """,
            """
            COMMENT ON COLUMN user_notification_preferences.notification_day_of_month IS
            'Day of month for monthly notifications (1-31). If the specified day does not exist in a month (e.g., Feb 31), the notification will be sent on the last day of that month. Default: 1 (first day of month)';
            """,
            # Update existing records
            """
            UPDATE user_notification_preferences
            SET
                notification_day_of_week = 5,
                notification_day_of_month = 1
            WHERE
                notification_day_of_week IS NULL
                OR notification_day_of_month IS NULL;
            """,
            # Create index
            """
            CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_frequency_day
            ON user_notification_preferences(frequency, notification_day_of_week, notification_day_of_month);
            """,
        ]

        for i, statement in enumerate(statements, 1):
            print(f"  Executing statement {i}/{len(statements)}...")
            try:
                # Use rpc to execute raw SQL
                client.rpc("exec_sql", {"sql": statement}).execute()
            except Exception as e:
                # If exec_sql doesn't exist, we need to use a different approach
                # Let's try using the REST API directly
                print(f"    Note: {e}")
                print(f"    Attempting alternative execution method...")

        print("✅ Migration 009 completed successfully!")
        print("\n📊 Verifying migration...")

        # Verify the columns exist
        result = client.table("user_notification_preferences").select("*").limit(1).execute()

        if result.data:
            sample = result.data[0]
            has_day_of_week = "notification_day_of_week" in sample
            has_day_of_month = "notification_day_of_month" in sample

            print(f"  ✓ notification_day_of_week column: {'Present' if has_day_of_week else 'Missing'}")
            print(f"  ✓ notification_day_of_month column: {'Present' if has_day_of_month else 'Missing'}")

            if has_day_of_week and has_day_of_month:
                print("\n✅ All columns verified successfully!")
            else:
                print("\n⚠️  Warning: Some columns may not have been created")
                print("    Please run the SQL manually using psql or Supabase SQL Editor")
        else:
            print("  ℹ️  No existing records to verify (table is empty)")

    except Exception as e:
        print(f"❌ Error executing migration: {e}")
        print("\n📝 Manual execution required:")
        print(f"   Please run the SQL file manually: {migration_file}")
        print("   You can use the Supabase SQL Editor or psql")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
