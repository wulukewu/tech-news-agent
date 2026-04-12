#!/usr/bin/env python3
"""
Apply the feeds table extension migration.
This script applies migration 003 to add recommendation columns to the feeds table.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client


def main():
    """Apply the feeds table extension migration."""

    # Load environment variables
    load_dotenv()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Connected to Supabase")

    # Read the migration SQL
    with open('scripts/migrations/003_extend_feeds_table_for_recommendations.sql', 'r') as f:
        migration_sql = f.read()

    print("Applying migration 003: Extend feeds table for recommendations...")

    try:
        # Execute the migration
        # Note: Supabase Python client doesn't support raw SQL execution directly
        # We need to use the SQL editor in Supabase dashboard or use psycopg2
        print("\n⚠️  This script cannot apply SQL migrations directly.")
        print("Please apply the migration using one of these methods:")
        print("\n1. Supabase Dashboard:")
        print("   - Go to SQL Editor in your Supabase dashboard")
        print("   - Copy and paste the contents of:")
        print("     scripts/migrations/003_extend_feeds_table_for_recommendations.sql")
        print("   - Click 'Run'")
        print("\n2. Using psql command line:")
        print("   psql <your-connection-string> -f scripts/migrations/003_extend_feeds_table_for_recommendations.sql")
        print("\n3. Using the apply_migration.sh script:")
        print("   cd scripts/migrations && ./apply_migration.sh 003_extend_feeds_table_for_recommendations.sql")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
