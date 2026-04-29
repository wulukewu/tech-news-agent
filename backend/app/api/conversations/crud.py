"""
Conversations API Router

Provides REST endpoints for managing conversation threads and their messages.

Endpoints:
  GET    /api/conversations              - List conversations (paginated, filtered)
  POST   /api/conversations              - Create a new conversation
  GET    /api/conversations/search       - Full-text search across conversations
  GET    /api/conversations/{id}         - Get a single conversation with metadata
  PATCH  /api/conversations/{id}         - Update conversation metadata
  DELETE /api/conversations/{id}         - Delete a conversation
  GET    /api/conversations/{id}/messages - Get messages for a conversation
  POST   /api/conversations/{id}/messages - Add a message to a conversation
  GET    /api/conversations/{id}/export  - Export a conversation

Validates: Requirements 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 9.1, 9.2, 9.3
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.core.errors import DatabaseError, NotFoundError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationFilters, ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.responses import (
    PaginatedResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from app.services.conversation_search import ConversationSearchService, SearchFilters
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_supabase() -> SupabaseService:
    return SupabaseService(validate_connection=False)


def _get_repos(svc: SupabaseService = Depends(_get_supabase)):
    client = svc.client
    return ConversationRepository(client), MessageRepository(client)

    # ---------------------------------------------------------------------------
    # GET /api/conversations/insights
    # ---------------------------------------------------------------------------

    tags: list[str] = Field(default_factory=list, description="Initial tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class AddMessageRequest(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")
    platform: str = Field("web", description="Source platform: 'web' or 'discord'")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationSummaryOut(BaseModel):
    id: str
    title: str = "Untitled Conversation"
    summary: Optional[str] = None
    platform: str
    tags: list[str]
    is_archived: bool
    is_favorite: bool
    created_at: str
    last_message_at: str
    message_count: int
    metadata: dict[str, Any]


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    platform: str
    metadata: dict[str, Any]
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _conv_to_out(conv) -> ConversationSummaryOut:
    created_at = getattr(conv, "created_at", None) or conv.last_message_at
    return ConversationSummaryOut(
        id=str(conv.id),
        title=conv.title,
        summary=conv.summary,
        platform=conv.platform,
        tags=conv.tags or [],
        is_archived=conv.is_archived,
        is_favorite=conv.is_favorite,
        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
        last_message_at=(
            conv.last_message_at.isoformat()
            if hasattr(conv.last_message_at, "isoformat")
            else str(conv.last_message_at)
        ),
        message_count=conv.message_count,
        metadata=getattr(conv, "metadata", None) or {},
    )


def _msg_to_out(msg) -> MessageOut:
    return MessageOut(
        id=str(msg.id),
        conversation_id=str(msg.conversation_id),
        role=msg.role,
        content=msg.content,
        platform=msg.platform,
        metadata=msg.metadata or {},
        created_at=(
            msg.created_at.isoformat()
            if hasattr(msg.created_at, "isoformat")
            else str(msg.created_at)
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/conversations
# ---------------------------------------------------------------------------


router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[ConversationSummaryOut],
    summary="List conversations",
)
async def list_conversations(
    platform: Optional[str] = Query(None, description="Filter by platform: 'web' or 'discord'"),
    is_archived: Optional[bool] = Query(False, description="Filter by archived status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    tags: Optional[str] = Query(None, description="Comma-separated tag list"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """List conversations for the authenticated user with optional filtering."""
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

        if search:
            # Use search service for full-text search
            svc = ConversationSearchService(conv_repo, msg_repo)
            filters = SearchFilters(
                platform=platform,
                is_archived=is_archived,
                is_favorite=is_favorite,
                tags=tag_list,
            )
            results = await svc.search_conversations(
                user_id=user_id, query=search, filters=filters, limit=limit, offset=offset
            )
            items = [
                ConversationSummaryOut(
                    id=r.conversation_id,
                    title=r.title,
                    summary=r.summary,
                    platform=r.platform,
                    tags=r.tags,
                    is_archived=r.is_archived,
                    is_favorite=r.is_favorite,
                    created_at=r.last_message_at.isoformat(),
                    last_message_at=r.last_message_at.isoformat(),
                    message_count=r.message_count,
                    metadata={},
                )
                for r in results
            ]
            return paginated_response(
                items=items,
                total_count=len(items),
                page=(offset // limit) + 1,
                page_size=limit,
            )

        filters = ConversationFilters(
            platform=platform,
            is_archived=is_archived,
            is_favorite=is_favorite,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
        summaries = await conv_repo.list_conversations(user_id=user_id, filters=filters)
        items = [_conv_to_out(s) for s in summaries]

        return paginated_response(
            items=items,
            total_count=len(items),
            page=(offset // limit) + 1,
            page_size=limit,
        )

    except DatabaseError as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


# ---------------------------------------------------------------------------
# POST /api/conversations
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=SuccessResponse[ConversationSummaryOut],
    status_code=201,
    summary="Create a conversation",
)
async def create_conversation(
    body: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Create a new conversation for the authenticated user."""
    conv_repo, _ = repos
    user_id = current_user["user_id"]

    title = (
        body.title or f"New Conversation {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    )

    try:
        conv = await conv_repo.create_conversation(
            user_id=user_id,
            title=title,
            platform=body.platform,
            tags=body.tags,
            metadata=body.metadata,
        )
        return success_response(_conv_to_out(conv))
    except DatabaseError as e:
        logger.error("Failed to create conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create conversation")


# ---------------------------------------------------------------------------
# GET /api/conversations/search
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=SuccessResponse[list[ConversationSummaryOut]],
    summary="Search conversations",
)
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query"),
    platform: Optional[str] = Query(None),
    is_archived: Optional[bool] = Query(False),
    is_favorite: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Search conversations by keyword across titles and message content."""
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    try:
        svc = ConversationSearchService(conv_repo, msg_repo)
        filters = SearchFilters(
            platform=platform,
            is_archived=is_archived,
            is_favorite=is_favorite,
        )
        results = await svc.search_conversations(
            user_id=user_id, query=q, filters=filters, limit=limit, offset=offset
        )
        items = [
            ConversationSummaryOut(
                id=r.conversation_id,
                title=r.title,
                summary=r.summary,
                platform=r.platform,
                tags=r.tags,
                is_archived=r.is_archived,
                is_favorite=r.is_favorite,
                created_at=r.last_message_at.isoformat(),
                last_message_at=r.last_message_at.isoformat(),
                message_count=r.message_count,
                metadata={},
            )
            for r in results
        ]
        return success_response(items)
    except DatabaseError as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


# ---------------------------------------------------------------------------
# GET /api/conversations/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}",
    response_model=SuccessResponse[ConversationSummaryOut],
    summary="Get a conversation",
)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Get a single conversation by ID (ownership enforced)."""
    conv_repo, _ = repos
    user_id = current_user["user_id"]

    try:
        conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return success_response(_conv_to_out(conv))
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error("Failed to get conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


# ---------------------------------------------------------------------------
# PATCH /api/conversations/{id}
# ---------------------------------------------------------------------------


@router.patch(
    "/{conversation_id}",
    response_model=SuccessResponse[ConversationSummaryOut],
    summary="Update a conversation",
)
async def update_conversation(
    conversation_id: str,
    body: UpdateConversationRequest,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Update conversation metadata (title, tags, favorite, archive status)."""
    conv_repo, _ = repos
    user_id = current_user["user_id"]

    updates: dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.summary is not None:
        updates["summary"] = body.summary
    if body.tags is not None:
        updates["tags"] = body.tags
    if body.is_favorite is not None:
        updates["is_favorite"] = body.is_favorite
    if body.is_archived is not None:
        updates["is_archived"] = body.is_archived
    if body.metadata is not None:
        updates["metadata"] = body.metadata

    if not updates:
        # Nothing to update — return current state
        conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return success_response(_conv_to_out(conv))

    try:
        conv = await conv_repo.update_conversation(
            conversation_id=conversation_id, user_id=user_id, updates=updates
        )
        return success_response(_conv_to_out(conv))
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except DatabaseError as e:
        logger.error("Failed to update conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update conversation")


# ---------------------------------------------------------------------------
# DELETE /api/conversations/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{conversation_id}",
    response_model=SuccessResponse[dict],
    summary="Delete a conversation",
)
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Permanently delete a conversation and all its messages."""
    conv_repo, _ = repos
    user_id = current_user["user_id"]

    try:
        deleted = await conv_repo.delete_conversation(
            conversation_id=conversation_id, user_id=user_id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return success_response({"deleted": True, "id": conversation_id})
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error("Failed to delete conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


# ---------------------------------------------------------------------------
# GET /api/conversations/{id}/messages
# ---------------------------------------------------------------------------
