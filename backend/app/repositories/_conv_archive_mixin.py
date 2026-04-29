"""Mixin extracted from repository."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)


class ConvArchiveMixin:
    async def archive_inactive_conversations(
        self,
        user_id: UUID | str,
        days_threshold: int = 30,
    ) -> int:
        """Archive conversations that have had no activity for ``days_threshold`` days.

        A conversation is considered inactive when its ``last_message_at``
        timestamp is older than ``days_threshold`` days ago.  Only
        non-archived conversations are considered.

        Args:
            user_id: UUID of the user whose conversations to check.
            days_threshold: Number of days of inactivity before archiving.
                Defaults to 30.

        Returns:
            The number of conversations that were archived.

        Raises:
            DatabaseError: If the database operation fails.

        Validates: Requirement 1.4
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        cutoff_iso = cutoff.isoformat()

        self.logger.info(
            "Archiving inactive conversations",
            user_id=str(user_id),
            days_threshold=days_threshold,
            cutoff=cutoff_iso,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update({"is_archived": True})
                .eq("user_id", str(user_id))
                .eq("is_archived", False)
                .lt("last_message_at", cutoff_iso)
                .execute()
            )

            archived_count = len(response.data) if response.data else 0
            self.logger.info(
                "Archived inactive conversations",
                user_id=str(user_id),
                archived_count=archived_count,
                days_threshold=days_threshold,
            )
            return archived_count

        except Exception as exc:
            self.logger.error(
                "Failed to archive inactive conversations",
                exc_info=True,
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to archive inactive conversations: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"user_id": str(user_id), "days_threshold": days_threshold},
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_to_conversation(row: dict[str, Any]) -> Conversation:
        """Map a raw Supabase row dict to a :class:`~app.core.database.Conversation`.

        Args:
            row: Dictionary returned by the Supabase client.

        Returns:
            A validated :class:`~app.core.database.Conversation` instance.
        """
        return Conversation(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            title=row.get("title") or "Untitled Conversation",
            summary=row.get("summary"),
            platform=row.get("platform", "web"),
            tags=row.get("tags") or [],
            is_archived=row.get("is_archived", False),
            is_favorite=row.get("is_favorite", False),
            created_at=_parse_datetime(row["created_at"]),
            last_message_at=_parse_datetime(row["last_message_at"]),
            message_count=row.get("message_count", 0),
            metadata=row.get("metadata") or {},
        )

    @staticmethod
    def _map_to_summary(row: dict[str, Any]) -> ConversationSummary:
        """Map a raw Supabase row dict to a :class:`ConversationSummary`.

        Args:
            row: Dictionary returned by the Supabase client (may be a partial
                select with only summary fields).

        Returns:
            A validated :class:`ConversationSummary` instance.
        """
        return ConversationSummary(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            title=row.get("title") or "Untitled Conversation",
            summary=row.get("summary"),
            platform=row.get("platform", "web"),
            created_at=_parse_datetime(row["created_at"]) if row.get("created_at") else None,
            last_message_at=_parse_datetime(row["last_message_at"]),
            message_count=row.get("message_count", 0),
            tags=row.get("tags") or [],
            is_favorite=row.get("is_favorite", False),
            is_archived=row.get("is_archived", False),
            metadata=row.get("metadata") or {},
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


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
        # Handle both 'Z' suffix and '+00:00' offset
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    raise ValueError(f"Cannot parse datetime from value: {value!r}")
