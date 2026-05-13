"""Mixin: metadata update methods for ConversationRepository.

Covers set_favorite, set_archived, update_tags, update_title —
all follow the same single-field update pattern.
"""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DatabaseError, ErrorCode
from app.core.logger import get_logger

logger = get_logger(__name__)


class ConvMetadataMixin:
    """Single-field metadata updates for conversations."""

    async def _update_field(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        field: str,
        value: object,
        op_name: str,
    ) -> bool:
        """Generic single-field update helper."""
        self.logger.debug(
            f"{op_name}",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )
        try:
            response = (
                self.client.table(self.TABLE)
                .update({field: value})
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            return bool(response.data)
        except Exception as exc:
            self.logger.error(
                f"Failed to {op_name}",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to {op_name}: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def set_favorite(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        is_favorite: bool,
    ) -> bool:
        """Set or clear the favorite flag on a conversation."""
        return await self._update_field(
            conversation_id, user_id, "is_favorite", is_favorite, "set favorite flag"
        )

    async def set_archived(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        is_archived: bool,
    ) -> bool:
        """Set or clear the archived flag on a conversation."""
        return await self._update_field(
            conversation_id, user_id, "is_archived", is_archived, "set archived flag"
        )

    async def update_tags(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        tags: list[str],
    ) -> bool:
        """Replace the tag list on a conversation."""
        return await self._update_field(conversation_id, user_id, "tags", tags, "update tags")

    async def update_title(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        title: str,
    ) -> bool:
        """Update the title of a conversation."""
        return await self._update_field(conversation_id, user_id, "title", title, "update title")
