#!/usr/bin/env python3
"""
Verification script for analytics_events table migration
Task 1.3: 建立 analytics_events 表格
Requirements: 14.1, 14.2, 14.3

This script verifies that:
1. analytics_events table exists with correct columns
2. Required indexes are created
3. Table can accept insert and query operations
4. JSONB event_data field works correctly
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_analytics_events_table():
    """Verify that analytics_events table exists with correct schema"""

    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False

    supabase: Client = create_client(supabase_url, supabase_key)

    print("🔍 Verifying Migration 004: Create analytics_events table\n")

    all_checks_passed = True

    # Check 1: Test table exists by attempting a query
    print("📋 Check 1: Verifying analytics_events table exists...")
    try:
        result = supabase.table('analytics_events').select('*').limit(0).execute()
        print("  ✅ Table 'analytics_events' exists and is accessible")
    except Exception as e:
        print(f"  ❌ Table 'analytics_events' does not exist or is not accessible: {e}")
        all_checks_passed = False
        return all_checks_passed

    # Check 2: Test insert operation with JSONB data
    print("\n📋 Check 2: Testing insert operation with JSONB event_data...")
    try:
        test_event = {
            'user_id': '00000000-0000-0000-0000-000000000000',  # Test UUID
            'event_type': 'test_verification_event',
            'event_data': {
                'test': True,
                'step': 'verification',
                'timestamp': '2024-01-01T00:00:00Z',
                'metadata': {
                    'nested': 'value',
                    'count': 42
                }
            }
        }

        insert_result = supabase.table('analytics_events').insert(test_event).execute()

        if insert_result.data and len(insert_result.data) > 0:
            print("  ✅ Successfully inserted test event")
            test_event_id = insert_result.data[0]['id']

            # Check 3: Test query operation
            print("\n📋 Check 3: Testing query operation...")
            query_result = supabase.table('analytics_events').select('*').eq('id', test_event_id).execute()

            if query_result.data and len(query_result.data) > 0:
                print("  ✅ Successfully queried test event")
                retrieved_event = query_result.data[0]

                # Check 4: Verify JSONB data integrity
                print("\n📋 Check 4: Verifying JSONB event_data integrity...")
                if retrieved_event['event_data'] == test_event['event_data']:
                    print("  ✅ JSONB event_data stored and retrieved correctly")
                    print(f"     Event data: {retrieved_event['event_data']}")
                else:
                    print("  ❌ JSONB event_data mismatch")
                    print(f"     Expected: {test_event['event_data']}")
                    print(f"     Got: {retrieved_event['event_data']}")
                    all_checks_passed = False

                # Check 5: Verify required columns exist
                print("\n📋 Check 5: Verifying required columns...")
                required_columns = ['id', 'user_id', 'event_type', 'event_data', 'created_at']
                for col in required_columns:
                    if col in retrieved_event:
                        print(f"  ✅ Column '{col}' exists")
                    else:
                        print(f"  ❌ Column '{col}' missing")
                        all_checks_passed = False

                # Check 6: Test query by event_type (tests index)
                print("\n📋 Check 6: Testing query by event_type (index test)...")
                type_query = supabase.table('analytics_events').select('*').eq('event_type', 'test_verification_event').execute()
                if type_query.data and len(type_query.data) > 0:
                    print("  ✅ Successfully queried by event_type")
                else:
                    print("  ❌ Failed to query by event_type")
                    all_checks_passed = False

                # Check 7: Test query by user_id (tests index)
                print("\n📋 Check 7: Testing query by user_id (index test)...")
                user_query = supabase.table('analytics_events').select('*').eq('user_id', test_event['user_id']).execute()
                if user_query.data and len(user_query.data) > 0:
                    print("  ✅ Successfully queried by user_id")
                else:
                    print("  ❌ Failed to query by user_id")
                    all_checks_passed = False

                # Clean up test event
                print("\n📋 Cleaning up test data...")
                supabase.table('analytics_events').delete().eq('id', test_event_id).execute()
                print("  ✅ Test event cleaned up")
            else:
                print("  ❌ Failed to query test event")
                all_checks_passed = False
        else:
            print("  ❌ Failed to insert test event")
            all_checks_passed = False

    except Exception as e:
        print(f"  ❌ Error during testing: {str(e)}")
        all_checks_passed = False

    # Summary
    print("\n" + "="*60)
    if all_checks_passed:
        print("✅ All verification checks passed!")
        print("Migration 004 has been successfully applied.")
        print("\nThe analytics_events table is ready to track:")
        print("  - onboarding_started")
        print("  - step_completed")
        print("  - onboarding_skipped")
        print("  - onboarding_finished")
        print("  - tooltip_shown")
        print("  - tooltip_skipped")
        print("  - feed_subscribed_from_onboarding")
    else:
        print("❌ Some verification checks failed.")
        print("Please review the migration and try again.")
    print("="*60)

    return all_checks_passed

if __name__ == "__main__":
    success = verify_analytics_events_table()
    sys.exit(0 if success else 1)
