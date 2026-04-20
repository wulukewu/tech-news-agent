#!/usr/bin/env python3
"""
Run a single SQL migration file
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_single_migration.py <migration_file.sql>")
        sys.exit(1)

    migration_file = sys.argv[1]

    # Load environment variables
    load_dotenv()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Connected to Supabase")

    # Read the migration SQL
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"📄 Executing migration: {migration_path.name}")

    try:
        # Execute the SQL using RPC
        result = supabase.rpc('exec_sql', {'query': sql_content}).execute()
        print(f"✅ Migration {migration_path.name} executed successfully")

    except Exception as e:
        print(f"❌ Failed to execute migration {migration_path.name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
