#!/usr/bin/env python3
"""
Execute migration 009 using Supabase REST API

This script directly executes the SQL statements via HTTP requests.
"""

import os
import sys
import requests
from pathlib import Path


def execute_sql(supabase_url: str, supabase_key: str, sql: str) -> bool:
    """Execute SQL using Supabase REST API."""
    # Supabase uses PostgREST, which doesn't support arbitrary SQL
    # We need to use the Management API or execute via a stored procedure

    # For now, let's just print the SQL and instructions
    print("⚠️  Direct SQL execution via Python is not supported by Supabase client")
    print("    Please use one of the following methods:\n")
    return False


def main():
    """Main execution function."""
    # Load environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        print("   Run: source .env (or set them manually)")
        sys.exit(1)

    # Read migration file
    migration_file = Path(__file__).parent / "migrations" / "009_add_notification_day_fields.sql"

    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, "r") as f:
        sql = f.read()

    print("📋 Migration 009: Add notification day fields")
    print("=" * 50)
    print(f"\n📄 SQL file: {migration_file}")
    print(f"📏 SQL length: {len(sql)} characters\n")

    # Try to execute
    success = execute_sql(supabase_url, supabase_key, sql)

    if not success:
        print("📝 Manual execution required:")
        print("\n" + "=" * 50)
        print("Method 1: Supabase Dashboard (Easiest)")
        print("=" * 50)
        print("1. Go to: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Navigate to: SQL Editor")
        print("4. Create a new query")
        print("5. Copy and paste the SQL below:")
        print("\n" + "-" * 50)
        print(sql)
        print("-" * 50)
        print("\n6. Click 'Run' or press Cmd/Ctrl + Enter")
        print("\n" + "=" * 50)
        print("Method 2: Command Line (if psql is installed)")
        print("=" * 50)
        print(f'psql "postgresql://postgres.ieqskggdhlvepuslouxy:YOUR_PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres" -f {migration_file}')
        print("\n" + "=" * 50)
        print("\n✅ After running the SQL, verify with:")
        print("   python3 scripts/verify_migration_009.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
