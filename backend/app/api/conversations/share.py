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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.responses import (
    SuccessResponse,
    success_response,
)
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class CreateShareRequest(BaseModel):
    expires_in_hours: int = Field(24, ge=1, le=720, description="Token TTL in hours (max 30 days)")


class ShareTokenOut(BaseModel):
    token: str
    share_url: str
    expires_at: str


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
