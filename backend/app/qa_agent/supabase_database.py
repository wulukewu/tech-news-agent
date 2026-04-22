"""
Supabase-based database implementation for QA Agent.
Uses Supabase REST API instead of direct PostgreSQL connection.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class SupabaseDatabaseManager:
    """
    Database manager that uses Supabase REST API for QA Agent operations.
    This is a fallback when direct PostgreSQL connection is not available.
    """

    def __init__(self):
        self._supabase_service: Optional[SupabaseService] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the Supabase database manager."""
        if self._is_initialized:
            logger.warning("Supabase database manager already initialized")
            return

        logger.info("Initializing Supabase database manager for QA Agent")

        try:
            self._supabase_service = SupabaseService()

            # Test connection
            await self._test_connection()

            self._is_initialized = True
            logger.info("Supabase database manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase database manager: {e}", exc_info=True)
            raise

    async def _test_connection(self) -> None:
        """Test the Supabase connection."""
        try:
            # Try to query a simple table to test connection
            result = self._supabase_service.client.table("users").select("id").limit(1).execute()
            logger.info("Supabase connection test successful")
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a 'connection' (actually returns the Supabase service).
        This maintains compatibility with the original database interface.
        """
        if not self._is_initialized or not self._supabase_service:
            raise Exception("Supabase database manager not initialized")

        yield self._supabase_service

    async def create_conversation(self, user_id: str, context: Dict[str, Any]) -> str:
        """Create a new conversation record."""
        try:
            result = (
                self._supabase_service.client.table("conversations")
                .insert(
                    {
                        "user_id": user_id,
                        "context": context,
                        "current_topic": context.get("topic"),
                        "turn_count": 0,
                    }
                )
                .execute()
            )

            if result.data:
                conversation_id = result.data[0]["id"]
                logger.info(f"Created conversation {conversation_id} for user {user_id}")
                return conversation_id
            else:
                raise Exception("No data returned from conversation creation")

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation by ID and user ID."""
        try:
            result = (
                self._supabase_service.client.table("conversations")
                .select("*")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None

    async def update_conversation(self, conversation_id: str, context: Dict[str, Any]) -> bool:
        """Update conversation context."""
        try:
            result = (
                self._supabase_service.client.table("conversations")
                .update(
                    {
                        "context": context,
                        "current_topic": context.get("topic"),
                        "turn_count": context.get("turn_count", 0),
                        "last_updated": "now()",
                    }
                )
                .eq("id", conversation_id)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            return False

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        try:
            result = (
                self._supabase_service.client.table("conversations")
                .delete()
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = {
            "healthy": False,
            "supabase_initialized": self._is_initialized,
            "error": None,
        }

        if not self._is_initialized:
            health_status["error"] = "Supabase database manager not initialized"
            return health_status

        try:
            await self._test_connection()
            health_status["healthy"] = True
        except Exception as e:
            health_status["error"] = str(e)

        return health_status

    async def close(self) -> None:
        """Close the database manager."""
        if self._supabase_service:
            logger.info("Closing Supabase database manager")
            self._supabase_service = None
            self._is_initialized = False


# Global instance
_supabase_db_manager: Optional[SupabaseDatabaseManager] = None


async def get_supabase_database_manager() -> SupabaseDatabaseManager:
    """Get the global Supabase database manager instance."""
    global _supabase_db_manager

    if _supabase_db_manager is None:
        _supabase_db_manager = SupabaseDatabaseManager()
        await _supabase_db_manager.initialize()

    return _supabase_db_manager


async def close_supabase_database_manager() -> None:
    """Close the global Supabase database manager instance."""
    global _supabase_db_manager

    if _supabase_db_manager:
        await _supabase_db_manager.close()
        _supabase_db_manager = None
