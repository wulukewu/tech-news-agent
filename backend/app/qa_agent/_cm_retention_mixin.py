"""Mixin extracted from app/qa_agent/conversation_manager.py."""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from asyncpg import Connection

logger = logging.getLogger(__name__)


class ConversationRetentionMixin:
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
