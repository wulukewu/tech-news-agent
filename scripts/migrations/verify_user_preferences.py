#!/usr/bin/env python3
"""
Verify that the user_preferences table exists with all required columns.
This script checks the database schema without modifying it.
"""

import os
import sys
from supabase import create_client, Client

def verify_user_preferences_schema():
    """Verify that user_preferences table exists with all required columns."""
    
    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Try to query the user_preferences table with all columns
        # This will fail if the table or columns don't exist
        result = supabase.table('user_preferences').select(
            'id, user_id, onboarding_completed, onboarding_step, '
            'onboarding_skipped, onboarding_started_at, onboarding_completed_at, '
            'tooltip_tour_completed, tooltip_tour_skipped, preferred_language, '
            'created_at, updated_at'
        ).limit(1).execute()
        
        print("✓ Schema verification successful!")
        print("✓ user_preferences table exists")
        print("✓ All required columns exist:")
        print("  - id, user_id")
        print("  - onboarding_completed, onboarding_step, onboarding_skipped")
        print("  - onboarding_started_at, onboarding_completed_at")
        print("  - tooltip_tour_completed, tooltip_tour_skipped")
        print("  - preferred_language")
        print("  - created_at, updated_at")
        
        # Check if indexes exist by trying to use them
        result_with_filter = supabase.table('user_preferences').select(
            'id'
        ).eq('onboarding_completed', False).limit(1).execute()
        
        print("✓ Indexes appear to be working")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        print("\nThe migration may not have been applied yet.")
        print("Run: ./scripts/migrations/apply_migration.sh scripts/migrations/002_create_user_preferences_table.sql")
        return False

if __name__ == '__main__':
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    success = verify_user_preferences_schema()
    sys.exit(0 if success else 1)
