"""
Database utilities for the Intelligent Q&A Agent.

This module provides common database operations and utilities
for the QA agent system.
"""

import logging
from typing import Any, Dict

from app.qa_agent.database import get_db_connection

logger = logging.getLogger(__name__)


class QADatabaseUtils:
    """Utility class for common QA agent database operations."""

    @staticmethod
    async def ensure_tables_exist() -> None:
        """
        Ensure that all required tables for the QA agent exist.

        This function checks for the existence of required tables and creates
        them if they don't exist. It's safe to call multiple times.
        """
        async with get_db_connection() as conn:
            # Check if article_embeddings table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'article_embeddings'
                )
            """
            )

            if not table_exists:
                logger.warning(
                    "article_embeddings table does not exist. "
                    "Please run the database migration script first."
                )
            else:
                logger.info("Required QA agent tables verified")

    @staticmethod
    async def get_table_stats() -> Dict[str, Any]:
        """
        Get statistics about QA agent related tables.

        Returns:
            Dictionary containing table statistics
        """
        stats = {}

        async with get_db_connection() as conn:
            try:
                # Get article count
                article_count = await conn.fetchval("SELECT COUNT(*) FROM articles")
                stats["articles_count"] = article_count

                # Get embedding count if table exists
                embedding_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'article_embeddings'
                    )
                """
                )

                if embedding_exists:
                    embedding_count = await conn.fetchval("SELECT COUNT(*) FROM article_embeddings")
                    stats["embeddings_count"] = embedding_count
                else:
                    stats["embeddings_count"] = 0
                    stats["embeddings_table_exists"] = False

                # Get conversation count if table exists
                conversation_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'conversations'
                    )
                """
                )

                if conversation_exists:
                    conversation_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
                    stats["conversations_count"] = conversation_count
                else:
                    stats["conversations_count"] = 0
                    stats["conversations_table_exists"] = False

            except Exception as e:
                logger.error(f"Error getting table stats: {e}")
                stats["error"] = str(e)

        return stats

    @staticmethod
    async def test_vector_operations() -> Dict[str, Any]:
        """
        Test basic vector operations to ensure pgvector is working correctly.

        Returns:
            Dictionary containing test results
        """
        results = {
            "vector_extension_available": False,
            "basic_vector_ops": False,
            "similarity_search": False,
            "error": None,
        }

        try:
            async with get_db_connection() as conn:
                # Test vector extension
                extension_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                results["vector_extension_available"] = extension_exists

                if not extension_exists:
                    results["error"] = "pgvector extension not installed"
                    return results

                # Test basic vector operations
                await conn.fetchval("SELECT '[1,2,3]'::vector")
                results["basic_vector_ops"] = True

                # Test similarity operations
                distance = await conn.fetchval("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
                results["similarity_search"] = True
                results["test_distance"] = float(distance)

        except Exception as e:
            logger.error(f"Vector operations test failed: {e}")
            results["error"] = str(e)

        return results

    @staticmethod
    async def cleanup_expired_conversations(days: int = 7) -> int:
        """
        Clean up expired conversations older than specified days.

        Args:
            days: Number of days after which conversations are considered expired

        Returns:
            Number of conversations deleted
        """
        try:
            async with get_db_connection() as conn:
                # Check if conversations table exists
                table_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'conversations'
                    )
                """
                )

                if not table_exists:
                    logger.info("Conversations table does not exist, skipping cleanup")
                    return 0

                # Delete expired conversations
                deleted_count = await conn.fetchval(
                    """
                    DELETE FROM conversations
                    WHERE expires_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """,
                    days,
                )

                if deleted_count and deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired conversations")

                return deleted_count or 0

        except Exception as e:
            logger.error(f"Error cleaning up conversations: {e}")
            return 0

    @staticmethod
    async def get_database_info() -> Dict[str, Any]:
        """
        Get comprehensive database information for monitoring and debugging.

        Returns:
            Dictionary containing database information
        """
        info = {}

        try:
            async with get_db_connection() as conn:
                # PostgreSQL version
                version = await conn.fetchval("SELECT version()")
                info["postgresql_version"] = version

                # Database name and size
                db_name = await conn.fetchval("SELECT current_database()")
                info["database_name"] = db_name

                # Check extensions
                extensions = await conn.fetch(
                    "SELECT extname, extversion FROM pg_extension ORDER BY extname"
                )
                info["extensions"] = {ext["extname"]: ext["extversion"] for ext in extensions}

                # Connection info
                info["current_user"] = await conn.fetchval("SELECT current_user")
                info["current_schema"] = await conn.fetchval("SELECT current_schema()")

                # Server settings relevant to performance
                settings_query = """
                    SELECT name, setting, unit
                    FROM pg_settings
                    WHERE name IN (
                        'max_connections', 'shared_buffers', 'work_mem',
                        'maintenance_work_mem', 'effective_cache_size'
                    )
                """
                settings_result = await conn.fetch(settings_query)
                info["server_settings"] = {
                    row["name"]: f"{row['setting']}{row['unit'] or ''}" for row in settings_result
                }

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info["error"] = str(e)

        return info
