"""Mixin extracted from repository."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)


class MsgSearchMixin:
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
