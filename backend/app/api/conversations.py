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

import io
import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
from app.services.smart_conversation import SmartConversationService
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


@router.get(
    "/insights",
    response_model=SuccessResponse[dict],
    summary="Get conversation insights and analytics",
)
async def get_conversation_insights(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Analyze user's conversation history and generate insights.

    Provides topic distribution, activity metrics, interest areas, knowledge gaps,
    and personalized learning suggestions.

    Validates: Requirements 6.1, 6.3, 6.4, 6.5
    """
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    try:
        smart_service = SmartConversationService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
        )

        insights = await smart_service.analyse_conversations(
            user_id=user_id,
            days=days,
        )

        return success_response(
            {
                "topic_distribution": insights.topic_distribution,
                "active_days": insights.active_days,
                "avg_messages_per_day": insights.avg_messages_per_day,
                "top_tags": insights.top_tags,
                "knowledge_gaps": insights.knowledge_gaps,
                "interest_areas": insights.interest_areas,
                "learning_suggestions": insights.learning_suggestions,
                "trend_summary": insights.trend_summary,
                "generated_at": insights.generated_at.isoformat(),
            }
        )
    except Exception as e:
        logger.error("Failed to generate insights", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title (auto-generated if omitted)")
    platform: str = Field("web", description="Source platform: 'web' or 'discord'")
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
        last_message_at=conv.last_message_at.isoformat()
        if hasattr(conv.last_message_at, "isoformat")
        else str(conv.last_message_at),
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
        created_at=msg.created_at.isoformat()
        if hasattr(msg.created_at, "isoformat")
        else str(msg.created_at),
    )


# ---------------------------------------------------------------------------
# GET /api/conversations
# ---------------------------------------------------------------------------


@router.get(
    "",
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
    "",
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


@router.get(
    "/{conversation_id}/messages",
    response_model=SuccessResponse[list[MessageOut]],
    summary="Get messages",
)
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ascending: bool = Query(True, description="Sort order: True = oldest first"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Get paginated messages for a conversation (ownership enforced via conversation lookup)."""
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    # Verify ownership
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        messages = await msg_repo.get_messages(
            conversation_id=conversation_id, limit=limit, offset=offset, ascending=ascending
        )
        return success_response([_msg_to_out(m) for m in messages])
    except DatabaseError as e:
        logger.error("Failed to get messages", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/messages
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/messages",
    response_model=SuccessResponse[MessageOut],
    status_code=201,
    summary="Add a message",
)
async def add_message(
    conversation_id: str,
    body: AddMessageRequest,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Add a new message to a conversation."""
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    # Verify ownership
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.role not in ("user", "assistant"):
        raise HTTPException(status_code=422, detail="role must be 'user' or 'assistant'")
    if body.platform not in ("web", "discord"):
        raise HTTPException(status_code=422, detail="platform must be 'web' or 'discord'")

    try:
        msg = await msg_repo.add_message(
            conversation_id=conversation_id,
            role=body.role,
            content=body.content,
            platform=body.platform,
            metadata=body.metadata,
        )
        return success_response(_msg_to_out(msg))
    except DatabaseError as e:
        logger.error("Failed to add message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add message")


# ---------------------------------------------------------------------------
# GET /api/conversations/{id}/export
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}/export",
    summary="Export a conversation",
)
async def export_conversation(
    conversation_id: str,
    format: str = Query("markdown", description="Export format: 'markdown', 'json'"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Export a conversation in Markdown or JSON format."""
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await msg_repo.get_messages(
        conversation_id=conversation_id, limit=1000, ascending=True
    )

    if format == "json":
        payload = {
            "id": str(conv.id),
            "title": conv.title,
            "platform": conv.platform,
            "tags": conv.tags,
            "created_at": conv.created_at.isoformat()
            if hasattr(conv.created_at, "isoformat")
            else str(conv.created_at),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "platform": m.platform,
                    "created_at": m.created_at.isoformat()
                    if hasattr(m.created_at, "isoformat")
                    else str(m.created_at),
                }
                for m in messages
            ],
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"conversation-{conversation_id[:8]}.json"
    else:
        # Markdown export
        lines = [
            f"# {conv.title}",
            "",
            f"**Platform:** {conv.platform}",
            f"**Tags:** {', '.join(conv.tags) if conv.tags else 'none'}",
            f"**Messages:** {conv.message_count}",
            "",
            "---",
            "",
        ]
        for msg in messages:
            ts = (
                msg.created_at.strftime("%Y-%m-%d %H:%M")
                if hasattr(msg.created_at, "strftime")
                else str(msg.created_at)
            )
            role_label = "**User**" if msg.role == "user" else "**Assistant**"
            lines.append(f"{role_label} _{ts}_")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        content = "\n".join(lines)
        media_type = "text/markdown"
        filename = f"conversation-{conversation_id[:8]}.md"

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/generate-title
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/generate-title",
    response_model=SuccessResponse[dict],
    summary="Generate a title for a conversation",
)
async def generate_conversation_title(
    conversation_id: str,
    persist: bool = Query(True, description="Whether to save the generated title to the database"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Generate an intelligent title for a conversation based on its content.

    Uses the SmartConversationService to analyze the first few messages and
    generate a concise, meaningful title in the same language as the conversation.

    Validates: Requirement 3.2
    """
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    # Verify ownership
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        # Initialize the smart conversation service
        smart_service = SmartConversationService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
        )

        # Generate the title
        title = await smart_service.generate_title(
            conversation_id=conversation_id,
            user_id=user_id,
            persist=persist,
        )

        return success_response(
            {
                "title": title,
                "persisted": persist,
                "conversation_id": conversation_id,
            }
        )
    except Exception as e:
        logger.error("Failed to generate title", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate title: {str(e)}")


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/generate-summary
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/generate-summary",
    response_model=SuccessResponse[dict],
    summary="Generate a summary for a conversation",
)
async def generate_conversation_summary(
    conversation_id: str,
    persist: bool = Query(
        True, description="Whether to save the generated summary to the database"
    ),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Generate an intelligent summary and key insights for a conversation.

    Validates: Requirement 6.2
    """
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    # Verify ownership
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        smart_service = SmartConversationService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
        )

        summary = await smart_service.generate_summary(
            conversation_id=conversation_id,
            user_id=user_id,
            persist=persist,
        )

        return success_response(
            {
                "summary": summary,
                "persisted": persist,
                "conversation_id": conversation_id,
            }
        )
    except Exception as e:
        logger.error("Failed to generate summary", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


# ---------------------------------------------------------------------------
# GET /api/conversations/{id}/related
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}/related",
    response_model=SuccessResponse[list[dict]],
    summary="Get related conversations",
)
async def get_related_conversations(
    conversation_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Find conversations related to the given one based on tags and content similarity.

    Validates: Requirements 3.5, 6.4
    """
    conv_repo, msg_repo = repos
    user_id = current_user["user_id"]

    # Verify ownership
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        smart_service = SmartConversationService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
        )

        related = await smart_service.get_related_conversations(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
        )

        return success_response(
            [
                {
                    "conversation_id": str(r.conversation_id),
                    "title": r.title,
                    "similarity_score": r.similarity_score,
                    "shared_tags": r.shared_tags,
                    "reason": r.reason,
                }
                for r in related
            ]
        )
    except Exception as e:
        logger.error("Failed to get related conversations", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get related conversations: {str(e)}"
        )


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/share
# ---------------------------------------------------------------------------

import secrets
from datetime import timedelta

# In-memory share token store: token -> {conversation_id, user_id, expires_at}
# In production this should be persisted to the database.
_share_tokens: dict[str, dict] = {}


class CreateShareRequest(BaseModel):
    expires_in_hours: int = Field(24, ge=1, le=720, description="Token TTL in hours (max 30 days)")


class ShareTokenOut(BaseModel):
    token: str
    share_url: str
    expires_at: str


@router.post(
    "/{conversation_id}/share",
    response_model=SuccessResponse[ShareTokenOut],
    status_code=201,
    summary="Create a share link",
)
async def create_share_link(
    conversation_id: str,
    body: CreateShareRequest,
    current_user: dict = Depends(get_current_user),
    repos=Depends(_get_repos),
):
    """Create a time-limited public share link for a conversation."""
    conv_repo, _ = repos
    user_id = current_user["user_id"]

    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=body.expires_in_hours)

    _share_tokens[token] = {
        "conversation_id": conversation_id,
        "user_id": str(user_id),
        "expires_at": expires_at,
    }

    return success_response(
        ShareTokenOut(
            token=token,
            share_url=f"/api/shared/{token}",
            expires_at=expires_at.isoformat(),
        )
    )


# ---------------------------------------------------------------------------
# GET /api/shared/{token}  (public endpoint — no auth required)
# ---------------------------------------------------------------------------


@router.get(
    "/shared/{token}",
    response_model=SuccessResponse[dict],
    summary="Access a shared conversation",
    tags=["conversations"],
)
async def get_shared_conversation(
    token: str,
    repos=Depends(_get_repos),
):
    """Access a shared conversation via its public token (no authentication required)."""
    entry = _share_tokens.get(token)
    if entry is None:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    if datetime.now(timezone.utc) > entry["expires_at"]:
        del _share_tokens[token]
        raise HTTPException(status_code=410, detail="Share link has expired")

    conv_repo, msg_repo = repos
    conv = await conv_repo.get_conversation(
        conversation_id=entry["conversation_id"],
        user_id=entry["user_id"],
    )
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await msg_repo.get_messages(
        conversation_id=entry["conversation_id"], limit=500, ascending=True
    )

    return success_response(
        {
            "conversation": _conv_to_out(conv).model_dump(),
            "messages": [_msg_to_out(m).model_dump() for m in messages],
            "expires_at": entry["expires_at"].isoformat(),
        }
    )
