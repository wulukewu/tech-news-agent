"""
Test script for database connection and configuration management.

This script can be run to verify that the database connection is working
properly and that pgvector extension is available.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logger import get_logger
from app.qa_agent.database import DatabaseManager, get_database_manager

logger = get_logger(__name__)


async def test_database_connection():
    """Test database connection and basic functionality."""
    logger.info("Starting database connection test")

    try:
        # Test direct DatabaseManager usage
        logger.info("Testing DatabaseManager initialization...")
        db_manager = DatabaseManager()
        await db_manager.initialize()

        # Test health check
        logger.info("Running health check...")
        health = await db_manager.health_check()
        logger.info(f"Health check result: {health}")

        if not health["healthy"]:
            logger.error(f"Database health check failed: {health.get('error')}")
            return False

        # Test basic query execution
        logger.info("Testing query execution...")
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT version()")
            logger.info(f"PostgreSQL version: {result}")

            # Test pgvector functionality
            logger.info("Testing pgvector functionality...")
            distance = await conn.fetchval("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
            logger.info(f"Vector distance test result: {distance}")

        # Test retry mechanism
        logger.info("Testing retry mechanism with invalid query...")
        try:
            await db_manager.execute_with_retry("SELECT * FROM non_existent_table", max_retries=1)
        except Exception as e:
            logger.info(f"Expected error caught: {e}")

        await db_manager.close()

        # Test global manager
        logger.info("Testing global database manager...")
        global_manager = await get_database_manager()
        health = await global_manager.health_check()
        logger.info(f"Global manager health: {health}")

        logger.info("All database tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        return False


async def main():
    """Main test function."""
    logger.info("Database Connection Test")
    logger.info("=" * 50)

    # Display configuration
    logger.info("Configuration:")
    if settings.database_url:
        logger.info(f"  DATABASE_URL: {settings.database_url[:20]}...")
    else:
        logger.info(f"  HOST: {settings.database_host}")
        logger.info(f"  PORT: {settings.database_port}")
        logger.info(f"  DATABASE: {settings.database_name}")
        logger.info(f"  USER: {settings.database_user}")

    logger.info(f"  POOL_MIN_SIZE: {settings.database_pool_min_size}")
    logger.info(f"  POOL_MAX_SIZE: {settings.database_pool_max_size}")
    logger.info("")

    success = await test_database_connection()

    if success:
        logger.info("✅ Database connection test completed successfully")
        return 0
    else:
        logger.error("❌ Database connection test failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
