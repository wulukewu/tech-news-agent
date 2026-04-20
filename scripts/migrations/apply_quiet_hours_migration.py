#!/usr/bin/env python3
"""
Apply user_quiet_hours table migration.

This script creates the user_quiet_hours table and sets up default quiet hours
for existing users (disabled by default for backward compatibility).
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the user_quiet_hours table migration."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    migration_file = '007_create_user_quiet_hours_table.sql'
    migration_path = Path(__file__).parent / migration_file

    if not migration_path.exists():
        print(f"❌ Error: Migration file not found: {migration_path}")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print(f"📝 Checking migration: {migration_file}")

        # Check if table exists by trying to query it
        try:
            result = supabase.table('user_quiet_hours').select('id').limit(1).execute()
            print("✓ user_quiet_hours table already exists")

            # Check if we have any records
            count_result = supabase.table('user_quiet_hours').select('id', count='exact').execute()
            record_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"✓ Found {record_count} quiet hours records")

            return True

        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e) or 'relation "user_quiet_hours" does not exist' in str(e):
                print(f"❌ Table user_quiet_hours does not exist. Attempting to create it...")

                # Read and execute the migration SQL
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()

                # Split the SQL into individual statements
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

                print(f"📝 Executing {len(statements)} SQL statements...")

                # Execute each statement using RPC
                for i, statement in enumerate(statements, 1):
                    if statement.strip():
                        try:
                            # Skip comments and empty statements
                            if statement.strip().startswith('--') or not statement.strip():
                                continue

                            print(f"  {i}/{len(statements)}: Executing statement...")

                            # Use RPC to execute raw SQL
                            result = supabase.rpc('exec_sql', {'sql': statement}).execute()

                            if hasattr(result, 'error') and result.error:
                                print(f"❌ Error in statement {i}: {result.error}")
                                return False

                        except Exception as stmt_error:
                            print(f"❌ Error executing statement {i}: {stmt_error}")
                            # Continue with next statement for some errors
                            if 'already exists' not in str(stmt_error):
                                return False

                print("✅ Migration executed successfully!")

                # Verify the table was created
                try:
                    result = supabase.table('user_quiet_hours').select('id').limit(1).execute()
                    print("✓ user_quiet_hours table created and accessible")
                    return True
                except Exception as verify_error:
                    print(f"❌ Table creation verification failed: {verify_error}")
                    return False

            else:
                raise

    except Exception as e:
        print(f"❌ Migration failed: {e}")
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

        print("🔄 Checking if user_quiet_hours table exists for rollback...")

        try:
            supabase.table('user_quiet_hours').select('id').limit(1).execute()
            print("❌ Table exists. Please run the following SQL to rollback:")
            print("\n  psql $DATABASE_URL -c \"DROP TABLE IF EXISTS user_quiet_hours CASCADE;\"")
            print("  psql $DATABASE_URL -c \"DROP FUNCTION IF EXISTS update_user_quiet_hours_updated_at();\"")
            return True

        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e):
                print("✓ Table user_quiet_hours does not exist (already rolled back)")
                return True
            else:
                raise

    except Exception as e:
        print(f"❌ Rollback check failed: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply user_quiet_hours table migration")
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
