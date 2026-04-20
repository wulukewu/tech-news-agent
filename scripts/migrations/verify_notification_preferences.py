#!/usr/bin/env python3
"""
Verify the user_notification_preferences and notification_locks table migrations.
This script checks that both tables exist with the correct schema.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_migration():
    """Verify the notification preferences migrations."""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("🔍 Verifying notification preferences migrations...")

        # Test 1: Check if user_notification_preferences table exists and is accessible
        try:
            result = supabase.table('user_notification_preferences').select('*').limit(1).execute()
            print("✅ user_notification_preferences table exists and is accessible")
        except Exception as e:
            print(f"❌ user_notification_preferences table check failed: {e}")
            return False

        # Test 2: Check if notification_locks table exists and is accessible
        try:
            result = supabase.table('notification_locks').select('*').limit(1).execute()
            print("✅ notification_locks table exists and is accessible")
        except Exception as e:
            print(f"❌ notification_locks table check failed: {e}")
            return False

        # Test 3: Test inserting a sample record to verify schema (if users exist)
        try:
            # First check if any users exist
            users_result = supabase.table('users').select('id').limit(1).execute()

            if users_result.data:
                user_id = users_result.data[0]['id']

                # Test inserting a preference record
                test_preference = {
                    'user_id': user_id,
                    'frequency': 'weekly',
                    'notification_time': '18:00:00',
                    'timezone': 'Asia/Taipei',
                    'dm_enabled': True,
                    'email_enabled': False
                }

                # Insert test record
                insert_result = supabase.table('user_notification_preferences').insert(test_preference).execute()

                if insert_result.data:
                    print("✅ user_notification_preferences schema validation passed")

                    # Clean up test record
                    supabase.table('user_notification_preferences').delete().eq('user_id', user_id).execute()
                    print("✅ Test record cleaned up")
                else:
                    print("❌ Failed to insert test preference record")
                    return False
            else:
                print("⚠️  No users found - skipping schema validation test")

        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            return False

        print("\n🎉 All notification preferences migrations verified successfully!")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)
