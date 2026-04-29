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

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.responses import (
    SuccessResponse,
    success_response,
)
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
