"""
Conversation Repository

Data access layer for conversation entities.
Handles all database operations related to conversations, including CRUD,
metadata management (title, tags, favorite, archived status), and
auto-archiving of inactive conversations.

Validates: Requirements 1.1, 1.2, 1.4, 3.4
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from supabase import Client

from app.core.database import Conversation
from app.core.errors import DatabaseError, ErrorCode, NotFoundError
from app.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Supporting Pydantic models
# ---------------------------------------------------------------------------


class ConversationSummary(BaseModel):
    """Lightweight conversation model for list views.

    Contains only the fields needed to render a conversation list item,
    avoiding the overhead of loading full message content.
    """

    id: UUID
    title: str = "Untitled Conversation"
    summary: Optional[str] = None
    platform: str
    created_at: Optional[datetime] = None
    last_message_at: datetime
    message_count: int = 0
    tags: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    is_archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConversationFilters(BaseModel):
    """Filters and pagination options for listing conversations.

    All filter fields are optional.  When ``is_archived`` is not explicitly
    set it defaults to ``False`` so that archived conversations are hidden
    from the default list view.
    """

    platform: Optional[str] = None
    is_archived: Optional[bool] = False  # default: show non-archived only
    is_favorite: Optional[bool] = None
    tags: Optional[list[str]] = None
    limit: int = 20
    offset: int = 0
    order_by: str = "last_message_at"
    ascending: bool = False


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


from app.repositories._conv_archive_mixin import ConvArchiveMixin


class ConversationRepository(ConvArchiveMixin):
    """Repository for Conversation entities.

    Provides data access methods for conversation-related operations including
    full CRUD, metadata management, and automatic archiving of inactive
    conversations.

    All methods are async and use the Supabase client directly (the
    ``conversations`` table does not have a ``deleted_at`` column, so the
    generic soft-delete logic in ``BaseRepository`` is not applicable here).

    Validates: Requirements 1.1, 1.2, 1.4, 3.4
    """

    TABLE = "conversations"

    def __init__(self, client: Client) -> None:
        """Initialise the repository.

        Args:
            client: An initialised Supabase ``Client`` instance.
        """
        self.client = client
        self.logger = get_logger(f"{__name__}.ConversationRepository")

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    async def create_conversation(
        self,
        user_id: UUID | str,
        title: str,
        platform: str = "web",
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Conversation:
        """Create a new conversation record.

        Args:
            user_id: UUID of the owning user.
            title: Human-readable conversation title.
            platform: Source platform (``"web"`` or ``"discord"``).
            tags: Optional list of tag strings.
            metadata: Optional arbitrary metadata dict.

        Returns:
            The newly created :class:`~app.core.database.Conversation`.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.info(
            "Creating conversation",
            user_id=str(user_id),
            platform=platform,
        )

        now = datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "user_id": str(user_id),
            "title": title,
            "platform": platform,
            "tags": tags or [],
            "metadata": metadata or {},
            "is_archived": False,
            "is_favorite": False,
            "message_count": 0,
            "created_at": now,
            "last_message_at": now,
        }

        try:
            response = self.client.table(self.TABLE).insert(data).execute()

            if not response.data:
                raise DatabaseError(
                    "Failed to create conversation: no data returned",
                    error_code=ErrorCode.DB_QUERY_FAILED,
                    details={"user_id": str(user_id)},
                )

            conversation = self._map_to_conversation(response.data[0])
            self.logger.info(
                "Conversation created",
                conversation_id=str(conversation.id),
                user_id=str(user_id),
            )
            return conversation

        except DatabaseError:
            raise
        except Exception as exc:
            self.logger.error(
                "Failed to create conversation",
                exc_info=True,
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to create conversation: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"user_id": str(user_id)},
                original_error=exc,
            ) from exc

    async def get_conversation(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
    ) -> Optional[Conversation]:
        """Retrieve a single conversation by ID, scoped to the given user.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the requesting user (ownership check).

        Returns:
            The :class:`~app.core.database.Conversation` if found and owned
            by ``user_id``, otherwise ``None``.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Fetching conversation",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )

            if not response.data:
                self.logger.debug(
                    "Conversation not found",
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                )
                return None

            return self._map_to_conversation(response.data[0])

        except Exception as exc:
            self.logger.error(
                "Failed to fetch conversation",
                exc_info=True,
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to fetch conversation: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "conversation_id": str(conversation_id),
                    "user_id": str(user_id),
                },
                original_error=exc,
            ) from exc

    async def list_conversations(
        self,
        user_id: UUID | str,
        filters: Optional[ConversationFilters] = None,
    ) -> list[ConversationSummary]:
        """List conversations for a user with optional filtering and pagination.

        Args:
            user_id: UUID of the user whose conversations to list.
            filters: Optional :class:`ConversationFilters` controlling
                pagination, ordering, and field-level filters.

        Returns:
            A list of :class:`ConversationSummary` objects.

        Raises:
            DatabaseError: If the database operation fails.
        """
        if filters is None:
            filters = ConversationFilters()

        self.logger.debug(
            "Listing conversations",
            user_id=str(user_id),
            filters=filters.model_dump(),
        )

        try:
            query = (
                self.client.table(self.TABLE)
                .select(
                    "id, title, summary, platform, created_at, last_message_at, "
                    "message_count, tags, is_favorite, is_archived, metadata"
                )
                .eq("user_id", str(user_id))
            )

            # Apply optional field filters
            if filters.platform is not None:
                query = query.eq("platform", filters.platform)
            if filters.is_archived is not None:
                query = query.eq("is_archived", filters.is_archived)
            if filters.is_favorite is not None:
                query = query.eq("is_favorite", filters.is_favorite)
            if filters.tags:
                # Filter rows whose tags JSONB array contains ALL requested tags
                for tag in filters.tags:
                    query = query.contains("tags", [tag])

            # Ordering
            query = query.order(filters.order_by, desc=not filters.ascending)

            # Pagination
            query = query.limit(filters.limit).offset(filters.offset)

            response = query.execute()

            summaries = [self._map_to_summary(row) for row in (response.data or [])]
            self.logger.debug(
                "Listed conversations",
                user_id=str(user_id),
                count=len(summaries),
            )
            return summaries

        except Exception as exc:
            self.logger.error(
                "Failed to list conversations",
                exc_info=True,
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to list conversations: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"user_id": str(user_id)},
                original_error=exc,
            ) from exc

    async def update_conversation(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        updates: dict[str, Any],
    ) -> Conversation:
        """Update fields on an existing conversation.

        Only the keys present in ``updates`` are modified.  The caller is
        responsible for passing valid field names.

        Args:
            conversation_id: UUID of the conversation to update.
            user_id: UUID of the owning user (ownership check).
            updates: Dictionary of field names to new values.

        Returns:
            The updated :class:`~app.core.database.Conversation`.

        Raises:
            NotFoundError: If the conversation does not exist or is not owned
                by ``user_id``.
            DatabaseError: If the database operation fails.
        """
        self.logger.info(
            "Updating conversation",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            fields=list(updates.keys()),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update(updates)
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data:
                raise NotFoundError(
                    "Conversation not found or access denied",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={
                        "conversation_id": str(conversation_id),
                        "user_id": str(user_id),
                    },
                )

            conversation = self._map_to_conversation(response.data[0])
            self.logger.info(
                "Conversation updated",
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            )
            return conversation

        except (NotFoundError, DatabaseError):
            raise
        except Exception as exc:
            self.logger.error(
                "Failed to update conversation",
                exc_info=True,
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to update conversation: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "conversation_id": str(conversation_id),
                    "user_id": str(user_id),
                },
                original_error=exc,
            ) from exc

    async def delete_conversation(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
    ) -> bool:
        """Permanently delete a conversation and all its messages.

        The ``conversations`` table has ``ON DELETE CASCADE`` on the
        ``conversation_messages`` foreign key, so child rows are removed
        automatically by the database.

        Args:
            conversation_id: UUID of the conversation to delete.
            user_id: UUID of the owning user (ownership check).

        Returns:
            ``True`` if the conversation was deleted, ``False`` if it was not
            found (or not owned by ``user_id``).

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.info(
            "Deleting conversation",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .delete()
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            deleted = bool(response.data)
            if deleted:
                self.logger.info(
                    "Conversation deleted",
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                )
            else:
                self.logger.debug(
                    "Conversation not found for deletion",
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                )
            return deleted

        except Exception as exc:
            self.logger.error(
                "Failed to delete conversation",
                exc_info=True,
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to delete conversation: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={
                    "conversation_id": str(conversation_id),
                    "user_id": str(user_id),
                },
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Metadata management
    # ------------------------------------------------------------------

    async def set_favorite(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        is_favorite: bool,
    ) -> bool:
        """Set or clear the favorite flag on a conversation.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            is_favorite: ``True`` to mark as favorite, ``False`` to unmark.

        Returns:
            ``True`` if the update succeeded, ``False`` if the conversation
            was not found.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Setting favorite flag",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            is_favorite=is_favorite,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update({"is_favorite": is_favorite})
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            return bool(response.data)

        except Exception as exc:
            self.logger.error(
                "Failed to set favorite flag",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to set favorite flag: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def set_archived(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        is_archived: bool,
    ) -> bool:
        """Set or clear the archived flag on a conversation.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            is_archived: ``True`` to archive, ``False`` to unarchive.

        Returns:
            ``True`` if the update succeeded, ``False`` if the conversation
            was not found.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Setting archived flag",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            is_archived=is_archived,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update({"is_archived": is_archived})
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            return bool(response.data)

        except Exception as exc:
            self.logger.error(
                "Failed to set archived flag",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to set archived flag: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def update_tags(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        tags: list[str],
    ) -> bool:
        """Replace the tag list on a conversation.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            tags: New list of tag strings (replaces existing tags).

        Returns:
            ``True`` if the update succeeded, ``False`` if the conversation
            was not found.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Updating tags",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            tags=tags,
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update({"tags": tags})
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            return bool(response.data)

        except Exception as exc:
            self.logger.error(
                "Failed to update tags",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to update tags: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    async def update_title(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        title: str,
    ) -> bool:
        """Update the title of a conversation.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            title: New title string.

        Returns:
            ``True`` if the update succeeded, ``False`` if the conversation
            was not found.

        Raises:
            DatabaseError: If the database operation fails.
        """
        self.logger.debug(
            "Updating title",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )

        try:
            response = (
                self.client.table(self.TABLE)
                .update({"title": title})
                .eq("id", str(conversation_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            return bool(response.data)

        except Exception as exc:
            self.logger.error(
                "Failed to update title",
                exc_info=True,
                conversation_id=str(conversation_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to update title: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"conversation_id": str(conversation_id)},
                original_error=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Auto-archive
    # ------------------------------------------------------------------
