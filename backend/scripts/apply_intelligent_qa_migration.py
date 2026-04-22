#!/usr/bin/env python3
"""
Apply Intelligent Q&A Agent Database Migration

This script provides instructions and verification for applying the database schema
migration for the intelligent Q&A agent. The SQL must be executed manually in
Supabase Dashboard due to security restrictions.

Usage:
    python backend/scripts/apply_intelligent_qa_migration.py

Requirements:
    - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables
    - PostgreSQL database with pgvector extension capability
    - Existing base schema (users, articles, feeds tables)
    - Access to Supabase Dashboard SQL Editor

Validates: Requirements 5.1, 7.1, 10.1
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import load_settings
from app.core.logger import get_logger
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


async def show_migration_instructions():
    """Show instructions for applying the migration manually."""
    migration_file = Path(__file__).parent / "migrations" / "007_create_intelligent_qa_schema.sql"

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    print("\n" + "=" * 80)
    print("INTELLIGENT Q&A AGENT DATABASE MIGRATION")
    print("=" * 80)
    print()
    print("Due to security restrictions, the migration SQL must be executed manually.")
    print("Please follow these steps:")
    print()
    print("1. Open Supabase Dashboard (https://supabase.com/dashboard)")
    print("2. Navigate to your project")
    print("3. Go to SQL Editor")
    print("4. Copy and paste the following SQL migration:")
    print()
    print(f"   File: {migration_file}")
    print()
    print("5. Execute the SQL in the editor")
    print("6. Run the verification script to confirm success:")
    print("   python backend/scripts/verify_intelligent_qa_schema.py")
    print()
    print("=" * 80)
    print("MIGRATION SQL CONTENT:")
    print("=" * 80)

    # Display the SQL content
    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(sql_content)
    print()
    print("=" * 80)
    print("END OF MIGRATION SQL")
    print("=" * 80)
    print()

    return True


async def verify_prerequisites():
    """Verify that prerequisites are met."""
    logger.info("Checking prerequisites...")

    try:
        # Initialize settings and services
        settings = load_settings()
        logger.info("✓ Settings loaded successfully")

        supabase_service = SupabaseService()
        logger.info("✓ Supabase service initialized")

        # Test basic connectivity
        async with supabase_service:
            # Try to query existing tables to verify connectivity
            try:
                result = supabase_service.client.table("users").select("id").limit(1).execute()
                logger.info("✓ Database connectivity verified")
            except Exception as e:
                logger.warning(f"Database connectivity test failed: {str(e)}")
                logger.warning("This may be normal if using service role key restrictions")

        return True

    except Exception as e:
        logger.error(f"Prerequisites check failed: {str(e)}")
        return False


async def main():
    """Main function to show migration instructions."""
    logger.info("Starting intelligent Q&A agent database migration setup...")

    # Check required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the migration.")
        return 1

    # Verify prerequisites
    if not await verify_prerequisites():
        logger.error("Prerequisites check failed. Please resolve issues before proceeding.")
        return 1

    # Show migration instructions
    success = await show_migration_instructions()

    if success:
        print()
        print("📋 NEXT STEPS:")
        print("1. Execute the SQL above in Supabase Dashboard")
        print("2. Run verification: python backend/scripts/verify_intelligent_qa_schema.py")
        print("3. If verification passes, the schema is ready for use!")
        print()
        return 0
    else:
        logger.error("Failed to show migration instructions.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
