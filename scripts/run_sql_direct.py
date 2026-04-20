#!/usr/bin/env python3
"""
Run SQL directly using psycopg2
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_sql_direct.py <migration_file.sql>")
        sys.exit(1)

    migration_file = sys.argv[1]

    # Load environment variables
    load_dotenv()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    # Parse Supabase URL to get database connection info
    parsed_url = urlparse(supabase_url)
    host = parsed_url.hostname

    # Construct PostgreSQL connection string
    # For Supabase, the connection details are:
    # Host: db.<project-ref>.supabase.co
    # Port: 5432
    # Database: postgres
    # User: postgres
    # Password: your-database-password (not the API key)

    project_ref = host.split('.')[0] if host else None
    if not project_ref:
        print("❌ Could not extract project reference from Supabase URL")
        sys.exit(1)

    db_host = f"db.{project_ref}.supabase.co"

    print("⚠️  This script requires your Supabase database password (not API key)")
    print("You can find it in your Supabase dashboard under Settings > Database")
    db_password = input("Enter your database password: ")

    if not db_password:
        print("❌ Database password is required")
        sys.exit(1)

    # Read the migration SQL
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"📄 Executing migration: {migration_path.name}")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database="postgres",
            user="postgres",
            password=db_password
        )

        cursor = conn.cursor()

        # Execute the SQL
        cursor.execute(sql_content)
        conn.commit()

        cursor.close()
        conn.close()

        print(f"✅ Migration {migration_path.name} executed successfully")

    except Exception as e:
        print(f"❌ Failed to execute migration {migration_path.name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
