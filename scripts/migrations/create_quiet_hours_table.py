#!/usr/bin/env python3
"""
Create user_quiet_hours table using Supabase client.
This script manually creates the table structure since we can't execute raw SQL.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_quiet_hours_table():
    """Create the user_quiet_hours table structure."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("📝 Checking if user_quiet_hours table exists...")

        # Check if table exists
        try:
            result = supabase.table('user_quiet_hours').select('id').limit(1).execute()
            print("✓ user_quiet_hours table already exists")

            # Check record count
            count_result = supabase.table('user_quiet_hours').select('id', count='exact').execute()
            record_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"✓ Found {record_count} quiet hours records")

            return True

        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e) or 'relation "user_quiet_hours" does not exist' in str(e):
                print("❌ Table does not exist. Please create it manually using one of these methods:")
                print("\n1. Using Supabase Dashboard SQL Editor:")
                print("   - Go to your Supabase project dashboard")
                print("   - Navigate to SQL Editor")
                print("   - Copy and paste the following SQL:")
                print("\n" + "="*60)

                # Read and display the simplified SQL
                sql_file = Path(__file__).parent / "007_create_user_quiet_hours_table_simple.sql"
                if sql_file.exists():
                    with open(sql_file, 'r') as f:
                        print(f.read())
                else:
                    print("-- SQL file not found, showing basic structure:")
                    print("""
CREATE TABLE user_quiet_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    weekdays INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7],
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_quiet_hours_user_id ON user_quiet_hours(user_id);
CREATE INDEX idx_user_quiet_hours_enabled ON user_quiet_hours(user_id, enabled);
CREATE UNIQUE INDEX idx_user_quiet_hours_unique_user ON user_quiet_hours(user_id);
                    """)

                print("="*60)
                print("\n2. After creating the table, run this script again to verify.")
                print("\n3. Then run the following to create default records:")
                print("   python3 create_default_quiet_hours.py")

                return False
            else:
                raise

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_default_quiet_hours():
    """Create default quiet hours for existing users."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("📝 Creating default quiet hours for existing users...")

        # Get all users
        users_result = supabase.table('users').select('id').execute()
        users = users_result.data

        if not users:
            print("✓ No users found, no default records needed")
            return True

        print(f"📝 Found {len(users)} users")

        # Check existing quiet hours
        existing_result = supabase.table('user_quiet_hours').select('user_id').execute()
        existing_user_ids = {record['user_id'] for record in existing_result.data}

        # Create default quiet hours for users who don't have them
        new_records = []
        for user in users:
            user_id = user['id']
            if user_id not in existing_user_ids:
                # Get user's timezone from notification preferences if available
                try:
                    pref_result = supabase.table('user_notification_preferences').select('timezone').eq('user_id', user_id).execute()
                    timezone = pref_result.data[0]['timezone'] if pref_result.data else 'UTC'
                except:
                    timezone = 'UTC'

                new_records.append({
                    'user_id': user_id,
                    'start_time': '22:00:00',
                    'end_time': '08:00:00',
                    'timezone': timezone,
                    'weekdays': [1, 2, 3, 4, 5, 6, 7],  # All days
                    'enabled': False  # Disabled by default for backward compatibility
                })

        if new_records:
            print(f"📝 Creating {len(new_records)} default quiet hours records...")
            result = supabase.table('user_quiet_hours').insert(new_records).execute()

            if hasattr(result, 'error') and result.error:
                print(f"❌ Error creating default records: {result.error}")
                return False

            print(f"✅ Created {len(new_records)} default quiet hours records")
        else:
            print("✓ All users already have quiet hours records")

        return True

    except Exception as e:
        print(f"❌ Error creating default records: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create user_quiet_hours table and default records")
    parser.add_argument(
        "--create-defaults",
        action="store_true",
        help="Create default quiet hours for existing users"
    )

    args = parser.parse_args()

    if args.create_defaults:
        success = create_default_quiet_hours()
    else:
        success = create_quiet_hours_table()

    sys.exit(0 if success else 1)
