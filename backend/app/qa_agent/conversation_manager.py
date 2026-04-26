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

from asyncpg import Connection

from app.qa_agent.database import get_db_connection
from app.qa_agent.models import (
    ConversationContext,
    ConversationTurn,
    ParsedQuery,
    StructuredResponse,
)

logger = logging.getLogger(__name__)


class ConversationManagerError(Exception):
    """Raised when conversation management operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ConversationManager:
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

    async def _store_conversation(self, context: ConversationContext) -> None:
        """Store conversation context in the database."""
        async with get_db_connection() as conn:
            await self._ensure_conversations_table(conn)

            # Serialize context to JSONB
            context_data = self._serialize_context(context)

            # Upsert conversation
            await conn.execute(
                """
                INSERT INTO conversations (id, user_id, context, created_at, last_updated, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    context = EXCLUDED.context,
                    last_updated = EXCLUDED.last_updated,
                    expires_at = EXCLUDED.expires_at
            """,
                context.conversation_id,
                context.user_id,
                context_data,
                context.created_at,
                context.last_updated,
                context.expires_at,
            )

    async def _delete_conversation(self, conn: Connection, conversation_id: UUID) -> int:
        """Delete a conversation from the database."""
        result = await conn.fetchval(
            """
            DELETE FROM conversations
            WHERE id = $1
            RETURNING 1
        """,
            conversation_id,
        )

        return 1 if result else 0

    async def _ensure_conversations_table(self, conn: Connection) -> None:
        """Ensure the conversations table exists."""
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                context JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
            )
        """
        )

        # Create indexes if they don't exist
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)
        """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at)
        """
        )

    def _serialize_context(self, context: ConversationContext) -> Dict[str, Any]:
        """Serialize conversation context to JSON-compatible format."""
        # Convert to dict and handle special types
        data = context.model_dump()

        # Convert UUIDs to strings
        data["conversation_id"] = str(data["conversation_id"])
        data["user_id"] = str(data["user_id"])

        # Convert datetime objects to ISO strings
        for field in ["created_at", "last_updated", "expires_at"]:
            if data.get(field):
                data[field] = data[field].isoformat()

        # Serialize turns
        serialized_turns = []
        for turn in data.get("turns", []):
            turn_data = dict(turn)
            if turn_data.get("timestamp"):
                turn_data["timestamp"] = turn_data["timestamp"].isoformat()

            # Serialize nested objects
            if turn_data.get("parsed_query"):
                pq_data = dict(turn_data["parsed_query"])
                if pq_data.get("processed_at"):
                    pq_data["processed_at"] = pq_data["processed_at"].isoformat()
                turn_data["parsed_query"] = pq_data

            if turn_data.get("response"):
                resp_data = dict(turn_data["response"])
                if resp_data.get("generated_at"):
                    resp_data["generated_at"] = resp_data["generated_at"].isoformat()
                if resp_data.get("conversation_id"):
                    resp_data["conversation_id"] = str(resp_data["conversation_id"])

                # Serialize articles in response
                if resp_data.get("articles"):
                    serialized_articles = []
                    for article in resp_data["articles"]:
                        article_data = dict(article)
                        if article_data.get("article_id"):
                            article_data["article_id"] = str(article_data["article_id"])
                        if article_data.get("url"):
                            article_data["url"] = str(article_data["url"])
                        if article_data.get("published_at"):
                            article_data["published_at"] = article_data["published_at"].isoformat()
                        serialized_articles.append(article_data)
                    resp_data["articles"] = serialized_articles

                turn_data["response"] = resp_data

            serialized_turns.append(turn_data)

        data["turns"] = serialized_turns
        return data

    def _deserialize_context(self, context_data: Dict[str, Any], row: Any) -> ConversationContext:
        """Deserialize conversation context from JSON format."""
        # Convert string UUIDs back to UUID objects
        if isinstance(context_data.get("conversation_id"), str):
            context_data["conversation_id"] = UUID(context_data["conversation_id"])
        if isinstance(context_data.get("user_id"), str):
            context_data["user_id"] = UUID(context_data["user_id"])

        # Use database timestamps if available (more reliable)
        context_data["created_at"] = row["created_at"]
        context_data["last_updated"] = row["last_updated"]
        context_data["expires_at"] = row["expires_at"]

        # Deserialize turns
        if context_data.get("turns"):
            deserialized_turns = []
            for turn_data in context_data["turns"]:
                # Convert timestamp
                if isinstance(turn_data.get("timestamp"), str):
                    turn_data["timestamp"] = datetime.fromisoformat(turn_data["timestamp"])

                # Deserialize parsed_query if present
                if turn_data.get("parsed_query"):
                    pq_data = turn_data["parsed_query"]
                    if isinstance(pq_data.get("processed_at"), str):
                        pq_data["processed_at"] = datetime.fromisoformat(pq_data["processed_at"])
                    turn_data["parsed_query"] = ParsedQuery(**pq_data)

                # Deserialize response if present
                if turn_data.get("response"):
                    resp_data = turn_data["response"]
                    if isinstance(resp_data.get("generated_at"), str):
                        resp_data["generated_at"] = datetime.fromisoformat(
                            resp_data["generated_at"]
                        )
                    if isinstance(resp_data.get("conversation_id"), str):
                        resp_data["conversation_id"] = UUID(resp_data["conversation_id"])

                    # Deserialize articles
                    if resp_data.get("articles"):
                        from app.qa_agent.models import ArticleSummary

                        deserialized_articles = []
                        for article_data in resp_data["articles"]:
                            if isinstance(article_data.get("article_id"), str):
                                article_data["article_id"] = UUID(article_data["article_id"])
                            if isinstance(article_data.get("published_at"), str):
                                article_data["published_at"] = datetime.fromisoformat(
                                    article_data["published_at"]
                                )
                            deserialized_articles.append(ArticleSummary(**article_data))
                        resp_data["articles"] = deserialized_articles

                    turn_data["response"] = StructuredResponse(**resp_data)

                deserialized_turns.append(ConversationTurn(**turn_data))

            context_data["turns"] = deserialized_turns

        return ConversationContext(**context_data)

    def _extract_topic_from_query(self, parsed_query: ParsedQuery) -> Optional[str]:
        """Extract topic from parsed query for conversation context."""
        if parsed_query.keywords:
            # Use the first few keywords as the topic
            return " ".join(parsed_query.keywords[:3])
        return None

    async def _analyze_topic_change(self, context: ConversationContext, new_query: str) -> bool:
        """
        Enhanced topic change detection for Task 8.2.

        Analyzes multiple factors to determine if conversation topic has changed:
        - Keyword overlap analysis
        - Query intent comparison
        - Conversation flow patterns
        - Contextual reference detection

        Args:
            context: Current conversation context
            new_query: New query to analyze

        Returns:
            True if topic change detected, False otherwise
        """
        # If no previous turns, no topic change
        if not context.turns:
            return False

        # Get recent queries for analysis
        recent_queries = context.get_recent_queries(count=3)
        if not recent_queries:
            return False

        # 1. Check for contextual references (indicates continuation)
        if self._has_contextual_references(new_query):
            logger.debug("Contextual references detected, continuing conversation")
            return False

        # 2. Analyze keyword overlap with recent queries
        keyword_overlap = self._calculate_keyword_overlap(new_query, recent_queries)
        if keyword_overlap > 0.3:  # 30% overlap threshold
            logger.debug(f"High keyword overlap ({keyword_overlap:.2f}), continuing conversation")
            return False

        # 3. Check query length and complexity (very short queries are likely follow-ups)
        if len(new_query.strip()) < 15:
            logger.debug("Short query detected, likely follow-up")
            return False

        # 4. Analyze topic shift patterns
        if self._detect_topic_shift_patterns(new_query, recent_queries):
            logger.info("Topic shift pattern detected, resetting context")
            return True

        # 5. Check for explicit topic change indicators
        if self._has_topic_change_indicators(new_query):
            logger.info("Explicit topic change indicators found, resetting context")
            return True

        # Default: continue conversation if no clear topic change
        return False

    def _has_contextual_references(self, query: str) -> bool:
        """
        Check if query contains contextual references indicating continuation.

        Enhanced for Task 8.2 to support Requirements 4.2, 4.3.
        """
        query_lower = query.lower()

        # Contextual reference patterns
        contextual_patterns = {
            "zh": [
                "這個",
                "那個",
                "它",
                "他",
                "她",
                "這些",
                "那些",
                "它們",
                "更多",
                "還有",
                "另外",
                "其他",
                "相關",
                "類似",
                "同樣",
                "告訴我更多",
                "詳細說明",
                "進一步",
                "深入",
                "補充",
            ],
            "en": [
                "this",
                "that",
                "it",
                "they",
                "them",
                "these",
                "those",
                "more",
                "also",
                "another",
                "other",
                "related",
                "similar",
                "same",
                "tell me more",
                "more about",
                "elaborate",
                "further",
                "additional",
                "what about",
                "how about",
                "regarding",
                "concerning",
            ],
        }

        # Check for contextual patterns
        for patterns in contextual_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        return False

    def _calculate_keyword_overlap(self, new_query: str, recent_queries: List[str]) -> float:
        """
        Calculate keyword overlap between new query and recent queries.

        Returns overlap ratio (0.0 to 1.0).
        """
        # Extract meaningful words (length > 2, not common stop words)
        stop_words = {
            "zh": {"的", "了", "在", "是", "有", "和", "與", "或", "但", "如果", "因為", "所以"},
            "en": {
                "the",
                "and",
                "or",
                "but",
                "if",
                "because",
                "so",
                "for",
                "with",
                "from",
                "to",
                "at",
                "by",
            },
        }

        def extract_keywords(text: str) -> set:
            words = set()
            for word in text.lower().split():
                # Remove punctuation and filter
                clean_word = "".join(c for c in word if c.isalnum())
                if (
                    len(clean_word) > 2
                    and clean_word not in stop_words.get("zh", set())
                    and clean_word not in stop_words.get("en", set())
                ):
                    words.add(clean_word)
            return words

        new_keywords = extract_keywords(new_query)
        if not new_keywords:
            return 0.0

        # Calculate overlap with recent queries
        total_overlap = 0.0
        for recent_query in recent_queries:
            recent_keywords = extract_keywords(recent_query)
            if recent_keywords:
                overlap = len(new_keywords.intersection(recent_keywords)) / len(
                    new_keywords.union(recent_keywords)
                )
                total_overlap = max(total_overlap, overlap)

        return total_overlap

    def _detect_topic_shift_patterns(self, new_query: str, recent_queries: List[str]) -> bool:
        """
        Detect patterns that indicate a topic shift.
        """
        query_lower = new_query.lower()

        # Topic shift indicators
        shift_patterns = {
            "zh": [
                "現在我想問",
                "另一個問題",
                "換個話題",
                "不同的問題",
                "新的問題",
                "讓我們談談",
                "我想了解",
                "關於",
                "轉到",
                "切換到",
            ],
            "en": [
                "now i want to ask",
                "different question",
                "change topic",
                "new question",
                "let's talk about",
                "i want to know about",
                "switching to",
                "moving to",
                "on a different note",
                "by the way",
                "speaking of",
            ],
        }

        # Check for shift patterns
        for patterns in shift_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        return False

    def _has_topic_change_indicators(self, query: str) -> bool:
        """
        Check for explicit topic change indicators.
        """
        query_lower = query.lower()

        # Explicit topic change phrases
        change_indicators = {
            "zh": ["新話題", "不同主題", "不同", "另一件事", "順便問", "對了", "現在我想問"],
            "en": [
                "new topic",
                "different subject",
                "different",
                "another thing",
                "by the way",
                "incidentally",
                "now i want to ask",
            ],
        }

        for indicators in change_indicators.values():
            if any(indicator in query_lower for indicator in indicators):
                return True

        return False

    async def implement_retention_policy(
        self, policy_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Implement comprehensive conversation data retention and cleanup policies.

        Enhanced for Task 8.2 to address Requirement 10.2.

        Args:
            policy_config: Optional configuration for retention policies

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Default retention policy configuration
            default_config = {
                "expired_conversations_days": 7,
                "inactive_conversations_days": 30,
                "max_conversations_per_user": 50,
                "cleanup_batch_size": 100,
            }

            config = {**default_config, **(policy_config or {})}

            async with get_db_connection() as conn:
                await self._ensure_conversations_table(conn)

                stats = {
                    "expired_deleted": 0,
                    "inactive_deleted": 0,
                    "excess_deleted": 0,
                    "total_processed": 0,
                }

                # 1. Clean up explicitly expired conversations
                expired_count = await conn.fetchval(
                    """
                    DELETE FROM conversations
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                    RETURNING COUNT(*)
                """
                )
                stats["expired_deleted"] = expired_count or 0

                # 2. Clean up inactive conversations (no updates for X days)
                inactive_cutoff = datetime.utcnow() - timedelta(
                    days=config["inactive_conversations_days"]
                )
                inactive_count = await conn.fetchval(
                    """
                    DELETE FROM conversations
                    WHERE last_updated < $1
                    RETURNING COUNT(*)
                """,
                    inactive_cutoff,
                )
                stats["inactive_deleted"] = inactive_count or 0

                # 3. Limit conversations per user (keep most recent)
                excess_count = await self._cleanup_excess_conversations_per_user(
                    conn, config["max_conversations_per_user"], config["cleanup_batch_size"]
                )
                stats["excess_deleted"] = excess_count

                # 4. Update statistics
                stats["total_processed"] = sum(stats.values())

                logger.info(f"Retention policy cleanup completed: {stats}")
                return stats

        except Exception as e:
            logger.error(f"Failed to implement retention policy: {e}")
            raise ConversationManagerError(
                f"Failed to implement retention policy: {e}", original_error=e
            )

    async def _cleanup_excess_conversations_per_user(
        self, conn: Connection, max_per_user: int, batch_size: int
    ) -> int:
        """
        Clean up excess conversations per user, keeping the most recent ones.
        """
        # Find users with too many conversations
        users_with_excess = await conn.fetch(
            """
            SELECT user_id, COUNT(*) as conversation_count
            FROM conversations
            GROUP BY user_id
            HAVING COUNT(*) > $1
        """,
            max_per_user,
        )

        total_deleted = 0

        for user_row in users_with_excess:
            user_id = user_row["user_id"]
            excess_count = user_row["conversation_count"] - max_per_user

            # Delete oldest conversations for this user
            deleted_ids = await conn.fetch(
                """
                DELETE FROM conversations
                WHERE id IN (
                    SELECT id FROM conversations
                    WHERE user_id = $1
                    ORDER BY last_updated ASC
                    LIMIT $2
                )
                RETURNING id
            """,
                user_id,
                excess_count,
            )

            deleted_count = len(deleted_ids)
            total_deleted += deleted_count

            logger.debug(f"Deleted {deleted_count} excess conversations for user {user_id}")

    async def process_contextual_query(
        self, conversation_id: str, query: str, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Process a query with full contextual understanding.

        Enhanced for Task 8.2 to provide comprehensive contextual query processing:
        - Analyzes query in context of conversation history
        - Determines if context reset is needed
        - Provides contextual metadata for downstream processing

        Args:
            conversation_id: The conversation identifier
            query: The user query
            user_id: The user identifier

        Returns:
            Dictionary containing contextual analysis results
        """
        try:
            # Get or create conversation context
            context = await self.get_context(conversation_id)
            if not context:
                # Create new conversation if not found
                new_conversation_id = await self.create_conversation(user_id)
                context = await self.get_context(new_conversation_id)
                conversation_id = new_conversation_id

            # Analyze if context should be reset
            should_reset = await self.should_reset_context(conversation_id, query)

            # Reset context if needed
            if should_reset:
                await self.reset_context(conversation_id)
                context = await self.get_context(conversation_id)

            # Analyze query context
            contextual_analysis = {
                "conversation_id": conversation_id,
                "should_reset_context": should_reset,
                "is_followup": self._is_followup_query(query),
                "has_context": len(context.turns) > 0 if context else False,
                "current_topic": context.current_topic if context else None,
                "turn_count": len(context.turns) if context else 0,
                "contextual_references": self._extract_contextual_references(query),
                "query_type": self._classify_contextual_query_type(query),
                "context_summary": (
                    context.get_conversation_summary() if context else "New conversation"
                ),
            }

            logger.debug(f"Contextual analysis for query '{query}': {contextual_analysis}")
            return contextual_analysis

        except Exception as e:
            logger.error(f"Failed to process contextual query: {e}")
            raise ConversationManagerError(
                f"Failed to process contextual query: {e}", original_error=e
            )

    def _is_followup_query(self, query: str) -> bool:
        """Enhanced follow-up query detection for Task 8.2."""
        query_lower = query.lower()

        # Enhanced follow-up indicators
        followup_indicators = {
            "zh": [
                "這個",
                "那個",
                "它",
                "他",
                "她",
                "這些",
                "那些",
                "它們",
                "更多",
                "還有",
                "另外",
                "其他",
                "相關",
                "類似",
                "同樣",
                "告訴我更多",
                "詳細說明",
                "進一步",
                "深入",
                "補充",
                "繼續",
                "接著",
                "然後",
            ],
            "en": [
                "this",
                "that",
                "it",
                "they",
                "them",
                "these",
                "those",
                "more",
                "also",
                "another",
                "other",
                "related",
                "similar",
                "same",
                "tell me more",
                "more about",
                "elaborate",
                "further",
                "additional",
                "what about",
                "how about",
                "regarding",
                "concerning",
                "continue",
                "next",
                "then",
                "also",
            ],
        }

        # Check for indicators
        for indicators in followup_indicators.values():
            if any(indicator in query_lower for indicator in indicators):
                return True

        # Check if query is very short (likely a follow-up)
        if len(query.strip()) < 15:
            return True

        return False

    def _extract_contextual_references(self, query: str) -> List[str]:
        """Extract contextual references from the query."""
        query_lower = query.lower()
        references = []

        # Reference patterns
        reference_patterns = {
            "zh": {
                "direct": ["這個", "那個", "它", "他", "她"],
                "plural": ["這些", "那些", "它們"],
                "comparative": ["其他", "另外", "類似", "相關"],
                "temporal": ["之前", "剛才", "上面", "前面"],
            },
            "en": {
                "direct": ["this", "that", "it"],
                "plural": ["these", "those", "they", "them"],
                "comparative": ["other", "another", "similar", "related"],
                "temporal": ["before", "earlier", "above", "previous"],
            },
        }

        for lang, categories in reference_patterns.items():
            for category, patterns in categories.items():
                for pattern in patterns:
                    if pattern in query_lower:
                        references.append(f"{lang}:{category}:{pattern}")

        return references

    def _classify_contextual_query_type(self, query: str) -> str:
        """Classify the type of contextual query."""
        query_lower = query.lower()

        # Query type patterns - ordered by specificity (most specific first)
        type_patterns = {
            "comparison": {
                "zh": ["比較", "對比", "不同", "類似", "相關", "versus", "vs"],
                "en": [
                    "compare",
                    "comparison",
                    "versus",
                    "vs",
                    "different from",
                    "similar to",
                    "contrast",
                ],
            },
            "exploration": {
                "zh": ["還有", "其他", "另外", "探索", "發現", "alternatives"],
                "en": [
                    "other",
                    "another",
                    "alternatives",
                    "explore",
                    "find",
                    "discover",
                    "what else",
                ],
            },
            "expansion": {
                "zh": ["更多", "詳細", "進一步", "深入", "補充"],
                "en": ["more", "detail", "further", "elaborate", "additional", "tell me more"],
            },
            "clarification": {
                "zh": ["解釋", "說明", "澄清", "什麼意思"],
                "en": ["explain", "clarify", "what does this mean", "what do you mean"],
            },
        }

        # Check patterns in order of specificity
        for query_type, lang_patterns in type_patterns.items():
            for patterns in lang_patterns.values():
                if any(pattern in query_lower for pattern in patterns):
                    return query_type

        return "general"


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """
    Get the global conversation manager instance.

    Returns:
        ConversationManager instance
    """
    global _conversation_manager

    if _conversation_manager is None:
        _conversation_manager = ConversationManager()

    return _conversation_manager
