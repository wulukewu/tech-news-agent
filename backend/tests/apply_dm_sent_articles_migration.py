"""
Helper script to apply dm_sent_articles migration for testing.
This script applies the migration directly using Supabase client.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def apply_dm_sent_articles_migration():
    """Apply migration to create dm_sent_articles table."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False
    
    if "dummy" in url.lower() or "dummy" in key.lower():
        print("⚠️  Skipping migration: Using dummy credentials")
        return False
    
    client = create_client(url, key)
    
    # Check if table already exists
    try:
        result = client.table('dm_sent_articles').select('id').limit(1).execute()
        print("✅ dm_sent_articles table already exists")
        return True
    except Exception as e:
        print(f"📝 Table doesn't exist yet, will create it: {e}")
    
    print("📝 Applying dm_sent_articles migration...")
    
    # Read migration SQL
    migration_path = 'scripts/migrations/003_create_dm_sent_articles_table.sql'
    if not os.path.exists(migration_path):
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    # Execute SQL using Supabase RPC
    try:
        # Note: This requires a custom RPC function in Supabase
        # For now, we'll print instructions
        print("\n⚠️  Note: This migration requires manual application via Supabase SQL Editor")
        print("\nPlease run the following SQL in Supabase SQL Editor:")
        print("=" * 80)
        print(sql)
        print("=" * 80)
        print("\nAfter applying the SQL, run the tests again.")
        return False
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        return False

if __name__ == '__main__':
    apply_dm_sent_articles_migration()
