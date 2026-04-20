#!/usr/bin/env python3
"""
Database Migration Runner

This script executes the pending database migrations for the notification system.
It reads the SQL migration files and executes them using Supabase's exec_sql RPC function.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

def load_env():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found. Please create it from .env.example")
        sys.exit(1)

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    return create_client(url, key)

def check_table_exists(supabase: Client, table_name: str) -> bool:
    """Check if a table exists in the database"""
    try:
        # Try to query the table with a limit of 0 to check existence
        supabase.table(table_name).select('*').limit(0).execute()
        return True
    except Exception:
        return False

def execute_migration(supabase: Client, migration_file: Path) -> bool:
    """Execute a single migration file"""
    print(f"📄 Executing migration: {migration_file.name}")

    try:
        # Read the SQL content
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Execute the SQL using RPC
        result = supabase.rpc('exec_sql', {'query': sql_content}).execute()

        print(f"✅ Migration {migration_file.name} executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to execute migration {migration_file.name}: {e}")
        return False

def main():
    """Main function to run migrations"""
    print("🚀 Starting database migration process...")

    # Load environment variables
    load_env()

    # Create Supabase client
    supabase = get_supabase_client()

    # Test connection
    try:
        supabase.table('users').select('count').limit(1).execute()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Check which tables need to be created
    migrations_needed = []

    # Check user_notification_preferences table
    if not check_table_exists(supabase, 'user_notification_preferences'):
        migrations_needed.append(Path('scripts/migrations/005_create_user_notification_preferences_table.sql'))
        print("📋 user_notification_preferences table missing - will create")
    else:
        print("✅ user_notification_preferences table already exists")

    # Check notification_locks table
    if not check_table_exists(supabase, 'notification_locks'):
        migrations_needed.append(Path('scripts/migrations/006_create_notification_locks_table.sql'))
        print("📋 notification_locks table missing - will create")
    else:
        print("✅ notification_locks table already exists")

    if not migrations_needed:
        print("🎉 All required tables already exist. No migrations needed!")
        return

    print(f"\n📋 Found {len(migrations_needed)} migration(s) to execute:")
    for migration in migrations_needed:
        print(f"  - {migration.name}")

    # Confirm execution
    response = input("\n❓ Do you want to proceed with these migrations? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled by user")
        return

    # Execute migrations
    print("\n🔄 Executing migrations...")
    success_count = 0

    for migration_file in migrations_needed:
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            continue

        if execute_migration(supabase, migration_file):
            success_count += 1

    # Summary
    print(f"\n📊 Migration Summary:")
    print(f"  - Total migrations: {len(migrations_needed)}")
    print(f"  - Successful: {success_count}")
    print(f"  - Failed: {len(migrations_needed) - success_count}")

    if success_count == len(migrations_needed):
        print("\n🎉 All migrations completed successfully!")
        print("✅ The notification preferences system is now ready to use.")
    else:
        print("\n⚠️  Some migrations failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
