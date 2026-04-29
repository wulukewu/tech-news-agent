"""
Message Repository

Data access layer for conversation message entities.
Handles all database operations related to messages, including CRUD,
bulk insertion, paginated queries, search, filtering, and statistics.

Validates: Requirements 1.2, 1.3, 7.2
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.database import ConversationMessage
from app.core.errors import DatabaseError, ErrorCode
from app.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Supporting data structures
# ---------------------------------------------------------------------------


@dataclass
class MessageStats:
    """Statistics summary for messages within a conversation.

    Attributes:
        total_count: Total number of messages in the conversation.
        user_count: Number of messages with role ``"user"``.
        assistant_count: Number of messages with role ``"assistant"``.
        platforms: Distinct platform values found in the conversation.
        first_message_at: Timestamp of the earliest message, or ``None`` if
            the conversation has no messages.
        last_message_at: Timestamp of the most recent message, or ``None`` if
            the conversation has no messages.
    """

    total_count: int
    user_count: int
    assistant_count: int
    platforms: list[str]
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


from app.repositories._msg_search_mixin import MsgSearchMixin


class MessageRepository(MsgSearchMixin):
    """Repository for ConversationMessage entities.

    Provides data access methods for message-related operations including
    full CRUD, bulk insertion, paginated retrieval, text search, platform
    filtering, and conversation-level statistics.

    All methods are async and use the Supabase client directly against the
    ``conversation_messages`` table.

    Validates: Requirements 1.2, 1.3, 7.2
    """

    TABLE = "conversation_messages"
    CONVERSATIONS_TABLE = "conversations"

    def __init__(self, client: Client) -> None:
        """Initialise the repository.

        Args:
            client: An initialised Supabase ``Client`` instance.
        """
        self.client = client
        self.logger = get_logger(f"{__name__}.MessageRepository")

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    async def add_message(
        self,
        conversation_id: UUID | str,
        role: str,
        content: str,
        platform: str = "web",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Insert a single message into a conversation.

        After inserting the message, the parent conversation's
        ``last_message_at`` and ``message_count`` fields are updated
        atomically via a separate update call.

        Args:
            conversation_id: UUID of the owning conversation.
            role: Author role — ``"user"`` or ``"assistant"``.
            content: Text content of the message.
            platform: Source platform (``"web"`` or ``"discord"``).
                Defaults to ``"web"``.
            metadata: Optional arbitrary metadata dict (e.g. attachment
                info, Discord message IDs, format hints).

        Returns:
            The newly created :class:`~app.core.database.ConversationMessage`.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.info(
            "Adding message",
            conversation_id=str(conversation_id),
            role=role,
            platform=platform,
        )

        now = datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content,
            "platform": platform,
            "metadata": metadata or {},
            "created_at": now,
        }

        try:
            response = self.client.table(self.TABLE).insert(data).execute()

            if not response.data:
                raise DatabaseError(
                    "Failed to add message: no data returned",
                    error_code=ErrorCode.DB_QUERY_FAILED,
                    details={"conversation_id": str(conversation_id)},
                )

            message = _map_to_message(response.data[0])

            # Update conversation stats (best-effort; errors are logged but
            # do not cause the overall operation to fail)
            await self._update_conversation_stats(conversation_id, now)

            self.logger.info(
                "Message added",
                message_id=str(message.id),
                conversation_id=str(conversation_id),
            )
            return message

        except DatabaseError:
            raise
        except Exception as exc:
            self.logger.error(
                "Failed to add message",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to add message: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def add_messages_batch(
        self,
        messages: list[dict[str, Any]],
    ) -> list[ConversationMessage]:
        """Bulk-insert multiple messages in a single database round-trip.

        Each element of ``messages`` must contain at minimum:
        ``conversation_id``, ``role``, and ``content``.  Optional keys are
        ``platform`` (defaults to ``"web"``) and ``metadata`` (defaults to
        ``{}``).

        After the bulk insert the parent conversation's ``last_message_at``
        and ``message_count`` are updated for every distinct
        ``conversation_id`` found in the batch.

        Args:
            messages: List of message dicts to insert.

        Returns:
            List of created :class:`~app.core.database.ConversationMessage`
            objects in insertion order.

        Raises:
            DatabaseError: If the database operation fails or ``messages``
                is empty.
        """
        if not messages:
            return []

        self.logger.info("Bulk-inserting messages", count=len(messages))

        now = datetime.now(timezone.utc).isoformat()
        rows: list[dict[str, Any]] = []
        for msg in messages:
            rows.append(
                {
                    "conversation_id": str(msg["conversation_id"]),
                    "role": msg["role"],
                    "content": msg["content"],
                    "platform": msg.get("platform", "web"),
                    "metadata": msg.get("metadata") or {},
                    "created_at": msg.get("created_at", now),
                }
            )

        try:
            response = self.client.table(self.TABLE).insert(rows).execute()

            if not response.data:
                raise DatabaseError(
                    "Failed to bulk-insert messages: no data returned",
                    error_code=ErrorCode.DB_QUERY_FAILED,
                )

            result = [_map_to_message(row) for row in response.data]

            # Update stats for each distinct conversation
            conversation_ids = {str(msg["conversation_id"]) for msg in messages}
            for conv_id in conversation_ids:
                await self._update_conversation_stats(conv_id, now)

            self.logger.info(
                "Bulk-insert complete",
                inserted=len(result),
                conversations=len(conversation_ids),
            )
            return result

        except DatabaseError:
            raise
        except Exception as exc:
            self.logger.error(
                "Failed to bulk-insert messages",
                exc_info=True,
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to bulk-insert messages: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            ) from exc

    async def get_message(
        self,
        message_id: UUID | str,
    ) -> Optional[ConversationMessage]:
        """Retrieve a single message by its primary key.

        Args:
            message_id: UUID of the message to fetch.

        Returns:
            The :class:`~app.core.database.ConversationMessage` if found,
            otherwise ``None``.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug("Fetching message", message_id=str(message_id))

        try:
            response = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("id", str(message_id))
                .limit(1)
                .execute()
            )

            if not response.data:
                self.logger.debug("Message not found", message_id=str(message_id))
                return None

            return _map_to_message(response.data[0])

        except Exception as exc:
            self.logger.error(
                "Failed to fetch message",
                exc_info=True,
                message_id=str(message_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to fetch message: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"message_id": str(message_id)},
                original_error=exc,
            ) from exc

    async def delete_message(
        self,
        message_id: UUID | str,
        conversation_id: UUID | str,
    ) -> bool:
        """Permanently delete a single message.

        Args:
            message_id: UUID of the message to delete.
            conversation_id: UUID of the owning conversation (used as an
                additional safety filter to prevent cross-conversation
                deletions).

        Returns:
            ``True`` if the message was deleted, ``False`` if it was not
            found.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.info(
            "Deleting message",
            message_id=str(message_id),
            conversation_id=str(conversation_id),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .delete()
                .eq("id", str(message_id))
                .eq("conversation_id", str(conversation_id))
                .execute()
            )

            deleted = bool(response.data)
            if deleted:
                self.logger.info(
                    "Message deleted",
                    message_id=str(message_id),
                    conversation_id=str(conversation_id),
                )
            else:
                self.logger.debug(
                    "Message not found for deletion",
                    message_id=str(message_id),
                    conversation_id=str(conversation_id),
                )
            return deleted

        except Exception as exc:
            self.logger.error(
                "Failed to delete message",
                exc_info=True,
                message_id=str(message_id),
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to delete message: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "message_id": str(message_id),
                    "conversation_id": str(conversation_id),
                },
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Paginated queries
    # ------------------------------------------------------------------

    async def get_messages(
        self,
        conversation_id: UUID | str,
        limit: int = 50,
        offset: int = 0,
        ascending: bool = False,
    ) -> list[ConversationMessage]:
        """Retrieve a paginated list of messages for a conversation.

        Args:
            conversation_id: UUID of the conversation.
            limit: Maximum number of messages to return. Defaults to 50.
            offset: Number of messages to skip (for pagination).
                Defaults to 0.
            ascending: When ``True`` messages are returned oldest-first;
                when ``False`` (default) newest-first.

        Returns:
            List of :class:`~app.core.database.ConversationMessage` objects.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Fetching messages",
            conversation_id=str(conversation_id),
            limit=limit,
            offset=offset,
            ascending=ascending,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("conversation_id", str(conversation_id))
                .order("created_at", desc=not ascending)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            messages = [_map_to_message(row) for row in (response.data or [])]
            self.logger.debug(
                "Fetched messages",
                conversation_id=str(conversation_id),
                count=len(messages),
            )
            return messages

        except Exception as exc:
            self.logger.error(
                "Failed to fetch messages",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to fetch messages: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def get_message_count(
        self,
        conversation_id: UUID | str,
    ) -> int:
        """Return the total number of messages in a conversation.

        Args:
            conversation_id: UUID of the conversation.

        Returns:
            Integer count of messages.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Counting messages",
            conversation_id=str(conversation_id),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .select("id", count="exact")
                .eq("conversation_id", str(conversation_id))
                .execute()
            )

            count = (
                response.count
                if hasattr(response, "count") and response.count is not None
                else len(response.data or [])
            )
            self.logger.debug(
                "Message count",
                conversation_id=str(conversation_id),
                count=count,
            )
            return count

        except Exception as exc:
            self.logger.error(
                "Failed to count messages",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to count messages: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Search and filtering
    # ------------------------------------------------------------------
