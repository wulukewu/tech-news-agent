#!/usr/bin/env python3
"""
Apply SQL migration using Supabase RPC.
This script executes raw SQL through Supabase's database connection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def get_database_url():
    """Construct database URL from Supabase credentials."""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return database_url
    
    if not supabase_url:
        print("❌ Error: SUPABASE_URL or DATABASE_URL must be set in .env")
        return None
    
    # Extract project ref from Supabase URL
    # Format: https://xxxxx.supabase.co
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    # Construct PostgreSQL connection string
    # Note: This requires the database password, which is different from the API key
    print("⚠️  Warning: This script requires DATABASE_URL to be set in .env")
    print("   You can find it in Supabase Dashboard > Settings > Database > Connection string")
    print("   Format: postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres")
    return None

def apply_migration(migration_file: Path):
    """Apply a SQL migration file."""
    
    database_url = get_database_url()
    if not database_url:
        return False
    
    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    try:
        print(f"📝 Applying migration: {migration_file.name}")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute SQL
        cursor.execute(sql_content)
        
        cursor.close()
        conn.close()
        
        print(f"✓ Migration applied successfully: {migration_file.name}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 apply_migration_sql.py <migration_file>")
        print("\nExample:")
        print("  python3 apply_migration_sql.py scripts/migrations/002_create_user_preferences_table.sql")
        sys.exit(1)
    
    migration_file = Path(sys.argv[1])
    success = apply_migration(migration_file)
    sys.exit(0 if success else 1)
