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
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
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
            "created_at": (
                conv.created_at.isoformat()
                if hasattr(conv.created_at, "isoformat")
                else str(conv.created_at)
            ),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "platform": m.platform,
                    "created_at": (
                        m.created_at.isoformat()
                        if hasattr(m.created_at, "isoformat")
                        else str(m.created_at)
                    ),
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
            "/",
            f"**Platform:** {conv.platform}",
            f"**Tags:** {', '.join(conv.tags) if conv.tags else 'none'}",
            f"**Messages:** {conv.message_count}",
            "/",
            "---",
            "/",
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
