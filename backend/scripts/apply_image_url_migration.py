#!/usr/bin/env python3
"""
Apply migration 004: Add image_url column to articles table

This script applies the migration to add image_url support for article thumbnails.
"""

import os
import sys
from pathlib import Path

from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )

    return create_client(url, key)


def check_column_exists(client: Client, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    try:
        # Try to query the column
        result = client.table(table).select(column).limit(1).execute()
        return True
    except Exception:
        return False


def apply_migration(client: Client, migration_file: Path) -> bool:
    """Apply a SQL migration file."""
    try:
        with open(migration_file) as f:
            sql = f.read()

        # Execute the SQL
        # Note: Supabase Python client doesn't support raw SQL execution directly
        # You'll need to use the Supabase SQL Editor or psycopg2 for this
        print("⚠️  Please apply the following SQL manually in Supabase SQL Editor:")
        print("\n" + "=" * 80)
        print(sql)
        print("=" * 80 + "\n")

        return True
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False


def main():
    """Main function."""
    print("🚀 Applying migration 004: Add image_url to articles table\n")

    # Get Supabase client
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # Check if column already exists
    print("\n🔍 Checking if image_url column exists...")
    if check_column_exists(client, "articles", "image_url"):
        print("✅ image_url column already exists - no migration needed")
        return True

    # Apply migration
    migration_file = Path(__file__).parent / "migrations" / "004_add_image_url_to_articles.sql"
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print(f"\n📄 Reading migration file: {migration_file.name}")
    return apply_migration(client, migration_file)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
