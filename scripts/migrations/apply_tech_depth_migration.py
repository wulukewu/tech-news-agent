#!/usr/bin/env python3
"""
Apply technical depth threshold migration.

This script adds technical depth filtering columns to the user_notification_preferences table.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the technical depth threshold migration."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    migration_file = '008_add_technical_depth_settings.sql'
    migration_path = Path(__file__).parent / migration_file

    if not migration_path.exists():
        print(f"❌ Error: Migration file not found: {migration_path}")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print(f"📝 Checking migration: {migration_file}")

        # Check if columns exist by querying the table structure
        try:
            # Try to select the new columns
            result = supabase.table('user_notification_preferences').select('tech_depth_threshold, tech_depth_enabled').limit(1).execute()
            print("✓ Technical depth columns already exist")

            # Check record count
            count_result = supabase.table('user_notification_preferences').select('id', count='exact').execute()
            record_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"✓ Found {record_count} user notification preference records")

            return True

        except Exception as e:
            if 'column "tech_depth_threshold" does not exist' in str(e) or 'column "tech_depth_enabled" does not exist' in str(e):
                print("❌ Technical depth columns do not exist. Please apply the migration using one of these methods:")
                print("\n1. Using Supabase Dashboard SQL Editor:")
                print("   - Go to your Supabase project dashboard")
                print("   - Navigate to SQL Editor")
                print("   - Copy and paste the following SQL:")
                print("\n" + "="*60)

                # Read and display the SQL
                with open(migration_path, 'r') as f:
                    print(f.read())

                print("="*60)
                print("\n2. After applying the migration, run this script again to verify.")

                return False
            else:
                raise

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def rollback_migration():
    """Rollback the migration (for testing purposes)."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("🔄 Checking if technical depth columns exist for rollback...")

        try:
            supabase.table('user_notification_preferences').select('tech_depth_threshold, tech_depth_enabled').limit(1).execute()
            print("❌ Columns exist. Please run the following SQL to rollback:")
            print("\n  -- Remove technical depth columns")
            print("  ALTER TABLE user_notification_preferences DROP COLUMN IF EXISTS tech_depth_threshold;")
            print("  ALTER TABLE user_notification_preferences DROP COLUMN IF EXISTS tech_depth_enabled;")
            print("  DROP INDEX IF EXISTS idx_user_notification_preferences_tech_depth;")
            return True

        except Exception as e:
            if 'column "tech_depth_threshold" does not exist' in str(e):
                print("✓ Technical depth columns do not exist (already rolled back)")
                return True
            else:
                raise

    except Exception as e:
        print(f"❌ Rollback check failed: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply technical depth threshold migration")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Check rollback status instead of applying migration"
    )

    args = parser.parse_args()

    if args.rollback:
        success = rollback_migration()
    else:
        success = apply_migration()

    sys.exit(0 if success else 1)
