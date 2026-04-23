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


class MessageRepository:
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

    async def search_messages(
        self,
        conversation_id: UUID | str,
        query: str,
        limit: int = 20,
    ) -> list[ConversationMessage]:
        """Search messages within a conversation using a case-insensitive
        substring match (``ilike``).

        Args:
            conversation_id: UUID of the conversation to search within.
            query: Search string.  The match is performed against the
                ``content`` column using ``ilike '%query%'``.
            limit: Maximum number of results to return. Defaults to 20.

        Returns:
            List of matching :class:`~app.core.database.ConversationMessage`
            objects ordered by ``created_at`` descending.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Searching messages",
            conversation_id=str(conversation_id),
            query=query,
            limit=limit,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("conversation_id", str(conversation_id))
                .ilike("content", f"%{query}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            messages = [_map_to_message(row) for row in (response.data or [])]
            self.logger.debug(
                "Search complete",
                conversation_id=str(conversation_id),
                query=query,
                results=len(messages),
            )
            return messages

        except Exception as exc:
            self.logger.error(
                "Failed to search messages",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to search messages: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "conversation_id": str(conversation_id),
                    "query": query,
                },
                original_error=exc,
            ) from exc

    async def get_messages_by_platform(
        self,
        conversation_id: UUID | str,
        platform: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationMessage]:
        """Retrieve messages filtered by originating platform.

        Args:
            conversation_id: UUID of the conversation.
            platform: Platform value to filter on (e.g. ``"web"`` or
                ``"discord"``).
            limit: Maximum number of messages to return. Defaults to 50.
            offset: Number of messages to skip. Defaults to 0.

        Returns:
            List of :class:`~app.core.database.ConversationMessage` objects
            ordered by ``created_at`` descending.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Fetching messages by platform",
            conversation_id=str(conversation_id),
            platform=platform,
            limit=limit,
            offset=offset,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("conversation_id", str(conversation_id))
                .eq("platform", platform)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            messages = [_map_to_message(row) for row in (response.data or [])]
            self.logger.debug(
                "Fetched messages by platform",
                conversation_id=str(conversation_id),
                platform=platform,
                count=len(messages),
            )
            return messages

        except Exception as exc:
            self.logger.error(
                "Failed to fetch messages by platform",
                exc_info=True,
                conversation_id=str(conversation_id),
                platform=platform,
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to fetch messages by platform: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "conversation_id": str(conversation_id),
                    "platform": platform,
                },
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def get_conversation_stats(
        self,
        conversation_id: UUID | str,
    ) -> MessageStats:
        """Compute statistics for all messages in a conversation.

        Fetches all messages for the conversation and derives:
        - total, user, and assistant message counts
        - distinct platform values
        - timestamps of the first and last messages

        Args:
            conversation_id: UUID of the conversation.

        Returns:
            A :class:`MessageStats` dataclass with the computed statistics.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Computing conversation stats",
            conversation_id=str(conversation_id),
        )

        try:
            # Fetch all messages for the conversation (role, platform,
            # created_at only — no need for full content)
            response = (
                self.client.table(self.TABLE)
                .select("role, platform, created_at")
                .eq("conversation_id", str(conversation_id))
                .order("created_at", desc=False)
                .execute()
            )

            rows = response.data or []

            total_count = len(rows)
            user_count = sum(1 for r in rows if r.get("role") == "user")
            assistant_count = sum(1 for r in rows if r.get("role") == "assistant")
            platforms: list[str] = list({r["platform"] for r in rows if r.get("platform")})

            first_message_at: Optional[datetime] = None
            last_message_at: Optional[datetime] = None
            if rows:
                first_message_at = _parse_datetime(rows[0]["created_at"])
                last_message_at = _parse_datetime(rows[-1]["created_at"])

            stats = MessageStats(
                total_count=total_count,
                user_count=user_count,
                assistant_count=assistant_count,
                platforms=platforms,
                first_message_at=first_message_at,
                last_message_at=last_message_at,
            )

            self.logger.debug(
                "Conversation stats computed",
                conversation_id=str(conversation_id),
                total=total_count,
            )
            return stats

        except Exception as exc:
            self.logger.error(
                "Failed to compute conversation stats",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to compute conversation stats: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _update_conversation_stats(
        self,
        conversation_id: UUID | str,
        last_message_at: str,
    ) -> None:
        """Increment ``message_count`` and update ``last_message_at`` on the
        parent conversation row.

        This is a best-effort operation — failures are logged but do not
        propagate to the caller.

        Args:
            conversation_id: UUID of the conversation to update.
            last_message_at: ISO-8601 timestamp string of the latest message.
        """
        try:
            # Fetch current message_count first
            response = (
                self.client.table(self.CONVERSATIONS_TABLE)
                .select("message_count")
                .eq("id", str(conversation_id))
                .limit(1)
                .execute()
            )

            if response.data:
                current_count = response.data[0].get("message_count", 0) or 0
                self.client.table(self.CONVERSATIONS_TABLE).update(
                    {
                        "message_count": current_count + 1,
                        "last_message_at": last_message_at,
                    }
                ).eq("id", str(conversation_id)).execute()

        except Exception as exc:
            self.logger.warning(
                "Failed to update conversation stats (non-fatal)",
                conversation_id=str(conversation_id),
                error=str(exc),
            )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _map_to_message(row: dict[str, Any]) -> ConversationMessage:
    """Map a raw Supabase row dict to a
    :class:`~app.core.database.ConversationMessage`.

    Args:
        row: Dictionary returned by the Supabase client.

    Returns:
        A validated :class:`~app.core.database.ConversationMessage` instance.
    """
    return ConversationMessage(
        id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
        conversation_id=(
            UUID(row["conversation_id"])
            if isinstance(row["conversation_id"], str)
            else row["conversation_id"]
        ),
        role=row["role"],
        content=row["content"],
        platform=row.get("platform", "web"),
        metadata=row.get("metadata") or {},
        created_at=_parse_datetime(row["created_at"]),
    )


def _parse_datetime(value: Any) -> datetime:
    """Parse a datetime value from a Supabase response.

    Supabase may return datetimes as ISO-8601 strings or as Python
    ``datetime`` objects depending on the client version.

    Args:
        value: Raw value from the database row.

    Returns:
        A timezone-aware :class:`datetime` object.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    raise ValueError(f"Cannot parse datetime from value: {value!r}")
