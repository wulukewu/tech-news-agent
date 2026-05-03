"""
Example usage of the QA Agent Database Connection Manager.

This module demonstrates how to use the database connection manager
in the intelligent QA agent system.
"""

import asyncio
import logging

from app.qa_agent.database import get_database_manager, get_db_connection
from app.qa_agent.db_utils import QADatabaseUtils

logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example of basic database operations."""
    print("=== Basic Database Usage Example ===")

    # Get the global database manager
    db_manager = await get_database_manager()

    # Perform health check
    health = await db_manager.health_check()
    print(f"Database health: {health}")

    # Use connection context manager
    async with get_db_connection() as conn:
        # Basic query
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version}")

        # Test pgvector functionality
        try:
            distance = await conn.fetchval("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
            print(f"Vector distance calculation: {distance}")
        except Exception as e:
            print(f"pgvector test failed: {e}")


async def example_retry_mechanism():
    """Example of using the retry mechanism."""
    print("\n=== Retry Mechanism Example ===")

    db_manager = await get_database_manager()

    try:
        # This will fail but demonstrate retry logic
        result = await db_manager.execute_with_retry(
            "SELECT * FROM non_existent_table", max_retries=2
        )
    except Exception as e:
        print(f"Expected error after retries: {e}")


async def example_utility_functions():
    """Example of using utility functions."""
    print("\n=== Utility Functions Example ===")

    # Get table statistics
    stats = await QADatabaseUtils.get_table_stats()
    print(f"Table statistics: {stats}")

    # Test vector operations
    vector_test = await QADatabaseUtils.test_vector_operations()
    print(f"Vector operations test: {vector_test}")

    # Get database info
    db_info = await QADatabaseUtils.get_database_info()
    print(f"Database info: {db_info}")


async def example_vector_operations():
    """Example of vector operations for QA agent."""
    print("\n=== Vector Operations Example ===")

    async with get_db_connection() as conn:
        try:
            # Create a temporary table for demonstration
            await conn.execute(
                """
                CREATE TEMP TABLE temp_embeddings (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(3)
                )
            """
            )

            # Insert some sample embeddings
            sample_data = [
                ("Hello world", [0.1, 0.2, 0.3]),
                ("Goodbye world", [0.4, 0.5, 0.6]),
                ("Machine learning", [0.7, 0.8, 0.9]),
            ]

            for content, embedding in sample_data:
                await conn.execute(
                    "INSERT INTO temp_embeddings (content, embedding) VALUES ($1, $2)",
                    content,
                    embedding,
                )

            # Perform similarity search
            query_embedding = [0.2, 0.3, 0.4]
            results = await conn.fetch(
                """
                SELECT content, embedding <-> $1 as distance
                FROM temp_embeddings
                ORDER BY distance
                LIMIT 3
            """,
                query_embedding,
            )

            print("Similarity search results:")
            for row in results:
                print(f"  {row['content']}: distance = {row['distance']:.4f}")

        except Exception as e:
            print(f"Vector operations example failed: {e}")


async def main():
    """Main example function."""
    print("QA Agent Database Connection Examples")
    print("=" * 50)

    try:
        await example_basic_usage()
        await example_retry_mechanism()
        await example_utility_functions()
        await example_vector_operations()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        logger.error(f"Example execution failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run examples
    asyncio.run(main())
