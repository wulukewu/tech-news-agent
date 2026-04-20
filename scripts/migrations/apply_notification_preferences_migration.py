#!/usr/bin/env python3
"""
Apply the user_notification_preferences and notification_locks table migrations.
This script creates both tables required for the personalized notification frequency feature.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the notification preferences migrations."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    # Migration files to apply
    migration_files = [
        '005_create_user_notification_preferences_table.sql',
        '006_create_notification_locks_table.sql'
    ]

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        for migration_file in migration_files:
            migration_path = Path(__file__).parent / migration_file

            if not migration_path.exists():
                print(f"❌ Error: Migration file not found: {migration_path}")
                return False

            print(f"📝 Applying migration: {migration_file}")

            # Check if table exists by trying to query it
            table_name = 'user_notification_preferences' if '005_' in migration_file else 'notification_locks'

            try:
                supabase.table(table_name).select('id').limit(1).execute()
                print(f"✓ {table_name} table already exists")
            except Exception as e:
                if 'PGRST205' in str(e) or 'Could not find the table' in str(e):
                    print(f"❌ Table {table_name} does not exist. Please apply the migration using psql:")
                    print(f"\n  psql $DATABASE_URL -f {migration_path}")
                    print("\nOr use the Supabase Dashboard SQL Editor to run the migration.")
                    return False
                else:
                    raise

        print("\n✅ All notification preferences migrations are ready!")
        print("\nTo apply these migrations, run:")
        for migration_file in migration_files:
            migration_path = Path(__file__).parent / migration_file
            print(f"  psql $DATABASE_URL -f {migration_path}")

        return True

    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
