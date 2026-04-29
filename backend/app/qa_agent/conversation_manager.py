"""
Conversation Manager for Intelligent Q&A Agent

This module implements conversation context management with persistent storage,
maintaining conversation history with a 10-turn limit and automatic cleanup.

Requirements: 4.1, 4.4, 10.2
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.qa_agent.database import get_db_connection
from app.qa_agent.models import (
    ConversationContext,
    ParsedQuery,
    StructuredResponse,
)

logger = logging.getLogger(__name__)


from app.qa_agent._cm_analysis_mixin import ConversationAnalysisMixin
from app.qa_agent._cm_db_mixin import ConversationDbMixin
from app.qa_agent._cm_retention_mixin import ConversationRetentionMixin


class ConversationManagerError(Exception):
    """Raised when conversation management operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ConversationManager(
    ConversationDbMixin, ConversationAnalysisMixin, ConversationRetentionMixin
):
    """
    Manages conversation context and state across multiple turns.

    Provides persistent storage of conversation history with automatic cleanup
    and maintains the 10-turn limit as specified in requirements.

    Requirements: 4.1, 4.4, 10.2
    """

    def __init__(self, default_expiry_days: int = 7):
        """
        Initialize the conversation manager.

        Args:
            default_expiry_days: Default number of days before conversations expire
        """
        self.default_expiry_days = default_expiry_days
        self.max_turns = 10  # Requirement 4.4: Keep most recent 10 turns

    async def create_conversation(self, user_id: UUID) -> str:
        """
        Create a new conversation for a user.

        Args:
            user_id: The user identifier

        Returns:
            The conversation ID as a string

        Raises:
            ConversationManagerError: If conversation creation fails
        """
        try:
            conversation_id = uuid4()
            expires_at = datetime.utcnow() + timedelta(days=self.default_expiry_days)

            # Create initial conversation context
            context = ConversationContext(
                conversation_id=conversation_id, user_id=user_id, expires_at=expires_at
            )

            # Store in database
            await self._store_conversation(context)

            logger.info(f"Created new conversation {conversation_id} for user {user_id}")
            return str(conversation_id)

        except Exception as e:
            logger.error(f"Failed to create conversation for user {user_id}: {e}", exc_info=True)
            raise ConversationManagerError(f"Failed to create conversation: {e}", original_error=e)

    async def add_turn(
        self,
        conversation_id: str,
        query: str,
        parsed_query: Optional[ParsedQuery] = None,
        response: Optional[StructuredResponse] = None,
    ) -> None:
        """
        Add a new turn to an existing conversation.

        Automatically maintains the 10-turn limit by removing older turns.

        Args:
            conversation_id: The conversation identifier
            query: The user query for this turn
            parsed_query: Optional parsed query information
            response: Optional system response

        Raises:
            ConversationManagerError: If turn addition fails
        """
        try:
            # Load existing conversation
            context = await self.get_context(conversation_id)
            if not context:
                raise ConversationManagerError(f"Conversation {conversation_id} not found")

            # Add the turn (this automatically handles the 10-turn limit)
            context.add_turn(query, parsed_query, response)

            # Update topic if this is a new conversation or topic has changed
            if not context.current_topic and parsed_query:
                context.current_topic = self._extract_topic_from_query(parsed_query)

            # Store updated conversation
            await self._store_conversation(context)

            logger.debug(
                f"Added turn to conversation {conversation_id}, total turns: {len(context.turns)}"
            )

        except ConversationManagerError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to add turn to conversation {conversation_id}: {e}", exc_info=True
            )
            raise ConversationManagerError(f"Failed to add turn: {e}", original_error=e)

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context by ID.

        Args:
            conversation_id: The conversation identifier

        Returns:
            ConversationContext if found, None otherwise

        Raises:
            ConversationManagerError: If context retrieval fails
        """
        try:
            conversation_uuid = UUID(conversation_id)

            async with get_db_connection() as conn:
                # First ensure the conversations table exists
                await self._ensure_conversations_table(conn)

                # Retrieve conversation data
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, context, created_at, last_updated, expires_at
                    FROM conversations
                    WHERE id = $1
                """,
                    conversation_uuid,
                )

                if not row:
                    logger.debug(f"Conversation {conversation_id} not found")
                    return None

                # Check if conversation has expired
                if row["expires_at"] and datetime.utcnow() > row["expires_at"]:
                    logger.info(f"Conversation {conversation_id} has expired, removing")
                    await self._delete_conversation(conn, conversation_uuid)
                    return None

                # Deserialize context from JSONB
                context_data = row["context"]
                context = self._deserialize_context(context_data, row)

                logger.debug(
                    f"Retrieved conversation {conversation_id} with {len(context.turns)} turns"
                )
                return context

        except ValueError as e:
            logger.error(f"Invalid conversation ID format: {conversation_id}")
            raise ConversationManagerError(f"Invalid conversation ID: {e}")
        except Exception as e:
            logger.error(
                f"Failed to get context for conversation {conversation_id}: {e}", exc_info=True
            )
            raise ConversationManagerError(
                f"Failed to retrieve conversation context: {e}", original_error=e
            )

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        """
        Determine if conversation context should be reset based on topic change.

        Enhanced for Task 8.2 with improved topic change detection using:
        - Semantic similarity analysis
        - Keyword overlap analysis
        - Query intent comparison
        - Conversation flow analysis

        Args:
            conversation_id: The conversation identifier
            new_query: The new query to evaluate

        Returns:
            True if context should be reset, False otherwise

        Raises:
            ConversationManagerError: If evaluation fails
        """
        try:
            context = await self.get_context(conversation_id)
            if not context:
                return False

            # Enhanced topic change detection
            return await self._analyze_topic_change(context, new_query)

        except Exception as e:
            logger.error(
                f"Failed to evaluate context reset for conversation {conversation_id}: {e}"
            )
            raise ConversationManagerError(
                f"Failed to evaluate context reset: {e}", original_error=e
            )

    async def reset_context(self, conversation_id: str, new_topic: Optional[str] = None) -> None:
        """
        Reset conversation context while preserving the conversation ID.

        Args:
            conversation_id: The conversation identifier
            new_topic: Optional new topic for the conversation

        Raises:
            ConversationManagerError: If context reset fails
        """
        try:
            context = await self.get_context(conversation_id)
            if not context:
                raise ConversationManagerError(f"Conversation {conversation_id} not found")

            # Clear turns and reset topic
            context.turns = []
            context.current_topic = new_topic
            context.context_summary = {}

            # Store updated conversation
            await self._store_conversation(context)

            logger.info(f"Reset context for conversation {conversation_id}")

        except ConversationManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to reset context for conversation {conversation_id}: {e}")
            raise ConversationManagerError(f"Failed to reset context: {e}", original_error=e)

    async def get_user_conversations(
        self, user_id: UUID, limit: int = 10, include_expired: bool = False
    ) -> List[ConversationContext]:
        """
        Get all conversations for a user.

        Args:
            user_id: The user identifier
            limit: Maximum number of conversations to return
            include_expired: Whether to include expired conversations

        Returns:
            List of conversation contexts

        Raises:
            ConversationManagerError: If retrieval fails
        """
        try:
            async with get_db_connection() as conn:
                await self._ensure_conversations_table(conn)

                # Build query based on whether to include expired conversations
                if include_expired:
                    query = """
                        SELECT id, user_id, context, created_at, last_updated, expires_at
                        FROM conversations
                        WHERE user_id = $1
                        ORDER BY last_updated DESC
                        LIMIT $2
                    """
                else:
                    query = """
                        SELECT id, user_id, context, created_at, last_updated, expires_at
                        FROM conversations
                        WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY last_updated DESC
                        LIMIT $2
                    """

                rows = await conn.fetch(query, user_id, limit)

                conversations = []
                for row in rows:
                    try:
                        context = self._deserialize_context(row["context"], row)
                        conversations.append(context)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize conversation {row['id']}: {e}")
                        continue

                logger.debug(f"Retrieved {len(conversations)} conversations for user {user_id}")
                return conversations

        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}", exc_info=True)
            raise ConversationManagerError(
                f"Failed to retrieve user conversations: {e}", original_error=e
            )

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation permanently.

        Args:
            conversation_id: The conversation identifier

        Returns:
            True if conversation was deleted, False if not found

        Raises:
            ConversationManagerError: If deletion fails
        """
        try:
            conversation_uuid = UUID(conversation_id)

            async with get_db_connection() as conn:
                await self._ensure_conversations_table(conn)

                deleted_count = await self._delete_conversation(conn, conversation_uuid)

                if deleted_count > 0:
                    logger.info(f"Deleted conversation {conversation_id}")
                    return True
                else:
                    logger.debug(f"Conversation {conversation_id} not found for deletion")
                    return False

        except ValueError as e:
            logger.error(f"Invalid conversation ID format: {conversation_id}")
            raise ConversationManagerError(f"Invalid conversation ID: {e}")
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise ConversationManagerError(f"Failed to delete conversation: {e}", original_error=e)

    async def cleanup_expired_conversations(self, days: Optional[int] = None) -> int:
        """
        Clean up expired conversations.

        Implements data retention policy as per requirement 10.2.

        Args:
            days: Number of days after which conversations are considered expired.
                  If None, uses the default expiry days.

        Returns:
            Number of conversations deleted

        Raises:
            ConversationManagerError: If cleanup fails
        """
        try:
            cleanup_days = days or self.default_expiry_days

            async with get_db_connection() as conn:
                await self._ensure_conversations_table(conn)

                # Delete conversations that have expired
                deleted_count = await conn.fetchval(
                    """
                    DELETE FROM conversations
                    WHERE expires_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """,
                    cleanup_days,
                )

                deleted_count = deleted_count or 0

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired conversations")
                else:
                    logger.debug("No expired conversations found for cleanup")

                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired conversations: {e}")
            raise ConversationManagerError(
                f"Failed to cleanup conversations: {e}", original_error=e
            )

    async def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about conversations in the system.

        Returns:
            Dictionary containing conversation statistics
        """
        try:
            async with get_db_connection() as conn:
                await self._ensure_conversations_table(conn)

                stats = {}

                # Total conversations
                stats["total_conversations"] = await conn.fetchval(
                    "SELECT COUNT(*) FROM conversations"
                )

                # Active conversations (not expired)
                stats["active_conversations"] = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE expires_at IS NULL OR expires_at > NOW()
                """
                )

                # Expired conversations
                stats["expired_conversations"] = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                """
                )

                # Conversations by age
                stats["conversations_by_age"] = {}
                age_ranges = [
                    ("last_hour", "1 hour"),
                    ("last_day", "1 day"),
                    ("last_week", "7 days"),
                    ("last_month", "30 days"),
                ]

                for label, interval in age_ranges:
                    count = await conn.fetchval(
                        f"""
                        SELECT COUNT(*) FROM conversations
                        WHERE last_updated > NOW() - INTERVAL '{interval}'
                    """
                    )
                    stats["conversations_by_age"][label] = count

                return stats

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {"error": str(e)}

    # Private helper methods


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
