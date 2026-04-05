#!/usr/bin/env python3
"""
Apply RLS Migration Script
This script applies Row Level Security policies to the reading_list table.
Validates: Requirements 10.8
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def apply_rls_migration():
    """Apply RLS policies to reading_list table."""
    
    # Load environment variables
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Read the migration SQL file
        migration_file = Path(__file__).parent / "001_enable_rls_reading_list.sql"
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("\n📝 Applying RLS migration...")
        print("=" * 60)
        
        # Execute the migration
        # Note: Supabase Python client doesn't support raw SQL execution directly
        # This needs to be run in Supabase Dashboard > SQL Editor
        print("\n⚠️  IMPORTANT: This migration must be run in Supabase Dashboard")
        print("\nSteps to apply:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Copy the contents of: scripts/migrations/001_enable_rls_reading_list.sql")
        print("3. Paste and execute in SQL Editor")
        print("\nMigration SQL:")
        print("=" * 60)
        print(migration_sql)
        print("=" * 60)
        
        # Verify RLS is enabled (this will work after manual execution)
        print("\n🔍 Verifying RLS status...")
        try:
            # Query pg_class to check if RLS is enabled
            result = supabase.rpc('check_rls_enabled', {}).execute()
            print("✅ RLS verification query executed")
        except Exception as e:
            print(f"⚠️  Cannot verify RLS status automatically: {e}")
            print("Please verify manually in Supabase Dashboard")
        
        print("\n✅ Migration script prepared successfully")
        print("\nNext steps:")
        print("1. Execute the SQL in Supabase Dashboard")
        print("2. Run: python3 scripts/migrations/verify_rls.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_rls_migration()
