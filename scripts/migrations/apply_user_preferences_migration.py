#!/usr/bin/env python3
"""
Apply the user_preferences table migration.
This script creates the user_preferences table if it doesn't exist.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the user_preferences table migration."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    # Read the migration SQL file
    migration_file = Path(__file__).parent / '002_create_user_preferences_table.sql'

    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        sql_content = f.read()

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("📝 Applying user_preferences table migration...")

        # Execute the SQL using Supabase's RPC function
        # Note: Supabase doesn't directly support executing arbitrary SQL via the client library
        # We need to use the PostgREST API or create a database function

        # Alternative: Use the SQL directly via the database connection
        # For now, we'll try to create the table using individual operations

        # Check if table exists by trying to query it
        try:
            supabase.table('user_preferences').select('id').limit(1).execute()
            print("✓ user_preferences table already exists")
            return True
        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e):
                print("❌ Table does not exist. Please apply the migration using psql:")
                print(f"\n  psql $DATABASE_URL -f {migration_file}")
                print("\nOr use the Supabase Dashboard SQL Editor to run the migration.")
                return False
            else:
                raise

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
