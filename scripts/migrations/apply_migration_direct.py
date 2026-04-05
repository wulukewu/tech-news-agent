#!/usr/bin/env python3
"""
Apply migration directly to Supabase database using psycopg2.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the user_preferences table migration."""
    
    # Get Supabase URL
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url:
        print("❌ Error: SUPABASE_URL must be set in .env")
        return False
    
    # Extract project reference from URL
    # Format: https://PROJECT_REF.supabase.co
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    # Construct database URL
    # Supabase database URL format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    db_password = os.getenv('SUPABASE_DB_PASSWORD', '')
    
    if not db_password:
        print("❌ Error: SUPABASE_DB_PASSWORD must be set in .env")
        print("You can find this in your Supabase project settings under Database > Connection string")
        return False
    
    db_url = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    # Read the migration SQL file
    migration_file = Path(__file__).parent / '002_create_user_preferences_table.sql'
    
    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    try:
        import psycopg2
        
        print("📝 Applying user_preferences table migration...")
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute the SQL
        cursor.execute(sql_content)
        conn.commit()
        
        print("✓ Migration applied successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except ImportError:
        print("❌ Error: psycopg2 not installed. Install it with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
