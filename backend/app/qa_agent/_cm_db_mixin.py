"""Mixin extracted from app/qa_agent/conversation_manager.py."""
import logging
from uuid import UUID

from asyncpg import Connection

from app.qa_agent.models import ConversationContext

logger = logging.getLogger(__name__)


class ConversationDbMixin:
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
