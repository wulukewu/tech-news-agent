#!/usr/bin/env python3
"""
Apply missing dm_sent_articles migration to Supabase database.

This script checks if the dm_sent_articles table exists and creates it if missing.
Run this after refactoring to ensure all required tables are present.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    parent_env = backend_dir.parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)


def check_table_exists(client, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        client.table(table_name).select("id").limit(1).execute()
        return True
    except Exception:
        return False


def apply_migration():
    """Apply the dm_sent_articles migration."""
    print("🔍 Checking Supabase connection...")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return False

    try:
        client = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # Check if table already exists
    print("\n🔍 Checking if dm_sent_articles table exists...")
    if check_table_exists(client, "dm_sent_articles"):
        print("✅ dm_sent_articles table already exists - no migration needed")
        return True

    print("📝 Table doesn't exist, applying migration...")

    # Read migration SQL
    migration_path = (
        backend_dir / "scripts" / "migrations" / "003_create_dm_sent_articles_table.sql"
    )

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    with open(migration_path) as f:
        sql = f.read()

    print("\n" + "=" * 60)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 60)
    print("\nThe dm_sent_articles table needs to be created manually.")
    print("Please follow these steps:\n")
    print("1. Go to your Supabase Dashboard")
    print("2. Navigate to: SQL Editor")
    print("3. Create a new query")
    print("4. Copy and paste the following SQL:\n")
    print("-" * 60)
    print(sql)
    print("-" * 60)
    print("\n5. Click 'Run' to execute the SQL")
    print("6. Verify the table was created successfully")
    print("\nAlternatively, you can run this SQL file directly if you have psql access:")
    print(f"   psql <connection_string> -f {migration_path}")
    print("\n" + "=" * 60)

    return False


if __name__ == "__main__":
    print("🚀 Starting migration check...\n")
    success = apply_migration()

    if success:
        print("\n✅ Migration check completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Manual migration required - see instructions above")
        sys.exit(1)
