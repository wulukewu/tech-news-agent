#!/usr/bin/env python3
"""
Verify Discord bot health and database connectivity.

This script checks:
1. Supabase connection
2. Required tables exist
3. Bot configuration is valid
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
    parent_env = backend_dir.parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)


def check_env_vars():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "DISCORD_BOT_TOKEN",
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False

    print("✅ All required environment variables are set")
    return True


def check_supabase_connection():
    """Check Supabase connection."""
    print("\n🔍 Checking Supabase connection...")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    try:
        client = create_client(url, key)
        # Try a simple query
        client.table("users").select("id").limit(1).execute()
        print("✅ Supabase connection successful")
        return True, client
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False, None


def check_table_exists(client, table_name: str) -> bool:
    """Check if a table exists."""
    try:
        client.table(table_name).select("id").limit(1).execute()
        return True
    except Exception:
        return False


def check_required_tables(client):
    """Check if all required tables exist."""
    print("\n🔍 Checking required tables...")

    required_tables = [
        "users",
        "feeds",
        "articles",
        "user_subscriptions",
        "reading_list",
    ]

    optional_tables = [
        "dm_sent_articles",  # Optional - enables deduplication
    ]

    all_good = True

    for table in required_tables:
        exists = check_table_exists(client, table)
        if exists:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING (REQUIRED)")
            all_good = False

    print("\n🔍 Checking optional tables...")
    for table in optional_tables:
        exists = check_table_exists(client, table)
        if exists:
            print(f"  ✅ {table}")
        else:
            print(f"  ⚠️  {table} - MISSING (optional, but recommended)")
            print("     Run: python3 scripts/apply_missing_migration.py")

    return all_good


def main():
    """Run all health checks."""
    print("🚀 Discord Bot Health Check\n")
    print("=" * 60)

    # Check environment variables
    if not check_env_vars():
        print("\n❌ Health check failed: Missing environment variables")
        return False

    # Check Supabase connection
    success, client = check_supabase_connection()
    if not success:
        print("\n❌ Health check failed: Cannot connect to Supabase")
        return False

    # Check required tables
    if not check_required_tables(client):
        print("\n❌ Health check failed: Missing required tables")
        return False

    print("\n" + "=" * 60)
    print("✅ Health check passed!")
    print("\nThe Discord bot should be able to run successfully.")
    print("\nNote: If dm_sent_articles table is missing, article deduplication")
    print("      won't work, but the bot will still function.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
