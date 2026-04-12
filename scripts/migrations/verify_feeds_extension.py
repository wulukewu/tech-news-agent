#!/usr/bin/env python3
"""
Verification script for Migration 003: Extend feeds table for recommendations
Task 1.2: 擴展 feeds 表格

This script verifies that:
1. New columns exist in feeds table (is_recommended, recommendation_priority, description, updated_at)
2. Indexes are created (idx_feeds_is_recommended, idx_feeds_recommendation_priority)
3. Trigger is created (update_feeds_updated_at)
4. Column types and defaults are correct
"""

import os
import sys
from supabase import create_client, Client

def verify_feeds_extension():
    """Verify the feeds table extension migration"""

    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False

    supabase: Client = create_client(supabase_url, supabase_key)

    print("🔍 Verifying Migration 003: Extend feeds table for recommendations\n")

    all_checks_passed = True

    # Check 1: Verify new columns exist
    print("📋 Check 1: Verifying new columns in feeds table...")
    try:
        result = supabase.rpc('exec_sql', {
            'query': """
                SELECT
                    column_name,
                    data_type,
                    column_default,
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = 'feeds'
                AND column_name IN ('is_recommended', 'recommendation_priority', 'description', 'updated_at')
                ORDER BY column_name;
            """
        }).execute()

        expected_columns = {
            'is_recommended': {'data_type': 'boolean', 'default': 'false'},
            'recommendation_priority': {'data_type': 'integer', 'default': '0'},
            'description': {'data_type': 'text', 'default': None},
            'updated_at': {'data_type': 'timestamp with time zone', 'default': 'now()'}
        }

        found_columns = {row['column_name']: row for row in result.data}

        for col_name, expected in expected_columns.items():
            if col_name in found_columns:
                col_info = found_columns[col_name]
                print(f"  ✅ Column '{col_name}' exists")
                print(f"     Type: {col_info['data_type']}")
                print(f"     Default: {col_info['column_default']}")
            else:
                print(f"  ❌ Column '{col_name}' not found")
                all_checks_passed = False

    except Exception as e:
        print(f"  ❌ Error checking columns: {e}")
        all_checks_passed = False

    # Check 2: Verify indexes exist
    print("\n📋 Check 2: Verifying indexes...")
    try:
        result = supabase.rpc('exec_sql', {
            'query': """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = 'feeds'
                AND indexname IN ('idx_feeds_is_recommended', 'idx_feeds_recommendation_priority')
                ORDER BY indexname;
            """
        }).execute()

        expected_indexes = ['idx_feeds_is_recommended', 'idx_feeds_recommendation_priority']
        found_indexes = [row['indexname'] for row in result.data]

        for idx_name in expected_indexes:
            if idx_name in found_indexes:
                print(f"  ✅ Index '{idx_name}' exists")
            else:
                print(f"  ❌ Index '{idx_name}' not found")
                all_checks_passed = False

    except Exception as e:
        print(f"  ❌ Error checking indexes: {e}")
        all_checks_passed = False

    # Check 3: Verify trigger exists
    print("\n📋 Check 3: Verifying trigger...")
    try:
        result = supabase.rpc('exec_sql', {
            'query': """
                SELECT
                    trigger_name,
                    event_manipulation,
                    action_timing
                FROM information_schema.triggers
                WHERE event_object_table = 'feeds'
                AND trigger_name = 'update_feeds_updated_at';
            """
        }).execute()

        if result.data:
            trigger = result.data[0]
            print(f"  ✅ Trigger 'update_feeds_updated_at' exists")
            print(f"     Event: {trigger['event_manipulation']}")
            print(f"     Timing: {trigger['action_timing']}")
        else:
            print(f"  ❌ Trigger 'update_feeds_updated_at' not found")
            all_checks_passed = False

    except Exception as e:
        print(f"  ❌ Error checking trigger: {e}")
        all_checks_passed = False

    # Check 4: Test functionality
    print("\n📋 Check 4: Testing functionality...")
    try:
        # Try to query feeds with new columns
        result = supabase.table('feeds').select(
            'id, name, is_recommended, recommendation_priority, description, updated_at'
        ).limit(1).execute()

        print(f"  ✅ Can query feeds table with new columns")

    except Exception as e:
        print(f"  ❌ Error querying feeds table: {e}")
        all_checks_passed = False

    # Summary
    print("\n" + "="*60)
    if all_checks_passed:
        print("✅ All verification checks passed!")
        print("Migration 003 has been successfully applied.")
    else:
        print("❌ Some verification checks failed.")
        print("Please review the migration and try again.")
    print("="*60)

    return all_checks_passed

if __name__ == "__main__":
    success = verify_feeds_extension()
    sys.exit(0 if success else 1)
