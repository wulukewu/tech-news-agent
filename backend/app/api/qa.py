"""
Intelligent Q&A Agent REST API Endpoints

This module provides FastAPI endpoints for the intelligent Q&A system,
supporting single queries, multi-turn conversations, and conversation management.

Conversation persistence uses the existing Supabase client (same as the rest of
the app) rather than the asyncpg pool, which requires a separate direct PostgreSQL
connection that may not be available in all deployment environments.

Requirements: 1.1, 4.1, 4.4, 6.4, 10.3
"""

import json
import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.auth import get_current_user
from app.schemas.responses import SuccessResponse, success_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level limiter — must match the one registered on app.state.limiter in main.py
limiter = Limiter(key_func=get_remote_address)

# Conversation expiry
_CONVERSATION_EXPIRY_DAYS = 7
# Max turns kept in context (Requirement 4.4)
_MAX_TURNS = 10


# ============================================================================
# Request / Response Schemas
# ============================================================================


class QueryRequest(BaseModel):
    """Request body for single Q&A query. Requirements: 1.1"""

    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID to continue an existing conversation"
    )


class CreateConversationRequest(BaseModel):
    """Request body for creating a new conversation. Requirements: 4.1"""

    initial_query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2000,
        description="Optional initial query to process when creating the conversation",
    )


class ContinueConversationRequest(BaseModel):
    """Request body for continuing an existing conversation. Requirements: 4.1, 4.2, 4.3"""

    query: str = Field(
        ..., min_length=1, max_length=2000, description="Follow-up query for the conversation"
    )


class ArticleSummaryResponse(BaseModel):
    """Serializable article summary for API responses."""

    article_id: str
    title: str
    summary: str
    url: str
    relevance_score: float
    reading_time: int
    key_insights: List[str]
    published_at: Optional[datetime]
    category: str


class QAQueryResponse(BaseModel):
    """
    Response for Q&A query endpoints.
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """

    query: str = Field(..., description="Original user query")
    articles: List[ArticleSummaryResponse] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    conversation_id: str = Field(..., description="Associated conversation ID")
    response_time: float = Field(..., description="Response generation time in seconds")
    intent: str = Field(
        default="question", description="Detected intent: question | preference | other"
    )


class ConversationTurnResponse(BaseModel):
    """Serializable conversation turn for API responses."""

    turn_number: int
    query: str
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    """
    Response for conversation history endpoint.
    Requirements: 4.1, 4.4
    """

    conversation_id: str
    user_id: str
    turns: List[ConversationTurnResponse] = Field(default_factory=list)
    current_topic: Optional[str] = None
    created_at: datetime
    last_updated: datetime


class CreateConversationResponse(BaseModel):
    """Response for conversation creation endpoint."""

    conversation_id: str
    query_result: Optional[QAQueryResponse] = None


# ============================================================================
# Supabase-backed conversation helpers
# ============================================================================


def _detect_intent(text: str) -> str:
    """Detect user intent: 'question', 'preference', or 'other'."""
    import re

    if re.search(
        r"[?？]|什麼|怎麼|如何|有沒有|推薦|介紹|解釋|告訴我|幫我找"
        r"|最近.*文章|有什麼.*關於|關於.*文章|哪些.*文章|找.*文章"
        r"|最新|新聞|資訊|教學|文章|新的|有哪些|哪裡|為什麼|誰|何時",
        text,
        re.IGNORECASE,
    ):
        return "question"
    if re.search(r"我喜歡|我不喜歡|我想看|我偏好|我對.*感興趣|不想看|希望多|希望少", text, re.IGNORECASE):
        return "preference"
    return "other"


from app.api._qa_helpers import (
    _append_turn_to_db,
    _create_conversation_in_db,
    _delete_conversation_from_db,
    _get_conversation_from_db,
    _process_query_with_intent,
    _save_messages_to_db,
)


@router.post("/query", response_model=SuccessResponse[QAQueryResponse])
@limiter.limit("20/minute")
async def query(
    request: Request,
    body: QueryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Process a single natural language query and return a structured response.

    Requirements: 1.1, 6.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])

        conv_id = body.conversation_id or str(uuid4())
        result = await _process_query_with_intent(user_id, body.query, conv_id)

        if body.conversation_id:
            try:
                await _append_turn_to_db(body.conversation_id, user_id, body.query, result)
            except Exception as e:
                logger.warning(f"Failed to persist query turn (using fallback mode): {e}")
            try:
                await _save_messages_to_db(body.conversation_id, body.query, result)
            except Exception as e:
                logger.warning(f"Failed to save query messages to DB: {e}")

        return success_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing query for user {current_user['user_id']}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to process query")


@router.post("/conversations", response_model=SuccessResponse[CreateConversationResponse])
@limiter.limit("20/minute")
async def create_conversation(
    request: Request,
    body: CreateConversationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Create a new conversation session.

    Optionally accepts an initial query to process immediately after creation.

    Requirements: 4.1, 6.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])

        # Create conversation row in Supabase
        conversation_id = await _create_conversation_in_db(user_id)

        query_result: Optional[QAQueryResponse] = None
        if body.initial_query:
            try:
                query_result = await _process_query_with_intent(
                    user_id, body.initial_query, conversation_id
                )
                try:
                    await _append_turn_to_db(
                        conversation_id, user_id, body.initial_query, query_result
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist initial turn (fallback mode): {e}")
                try:
                    await _save_messages_to_db(conversation_id, body.initial_query, query_result)
                except Exception as e:
                    logger.warning(f"Failed to save messages to DB: {e}")
            except Exception as e:
                logger.warning(f"Initial query failed, conversation still created: {e}")

        return success_response(
            CreateConversationResponse(
                conversation_id=conversation_id,
                query_result=query_result,
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating conversation for user {current_user['user_id']}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.post(
    "/conversations/{conversation_id}/continue",
    response_model=SuccessResponse[QAQueryResponse],
)
@limiter.limit("20/minute")
async def continue_conversation(
    request: Request,
    conversation_id: str,
    body: ContinueConversationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Continue an existing conversation with a follow-up query.

    Requirements: 4.1, 4.2, 4.3, 4.4, 6.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])

        # Verify conversation exists and belongs to this user
        row = await _get_conversation_from_db(conversation_id, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")

        # Use intent-aware processing
        result = await _process_query_with_intent(user_id, body.query, conversation_id)

        # Persist the turn
        try:
            await _append_turn_to_db(conversation_id, user_id, body.query, result)
        except Exception as e:
            logger.warning(f"Failed to persist follow-up turn: {e}")
        # Save messages to conversation_messages table
        try:
            await _save_messages_to_db(conversation_id, body.query, result)
        except Exception as e:
            logger.warning(f"Failed to save follow-up messages to DB: {e}")

        return success_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error continuing conversation {conversation_id} for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to continue conversation")


@router.get(
    "/conversations/{conversation_id}",
    response_model=SuccessResponse[ConversationHistoryResponse],
)
@limiter.limit("20/minute")
async def get_conversation(
    request: Request,
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve the history of an existing conversation.

    Requirements: 4.1, 4.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])

        row = await _get_conversation_from_db(conversation_id, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")

        context = row["context"]
        if isinstance(context, str):
            context = json.loads(context)

        # Parse turns
        turns = []
        for t in context.get("turns", []):
            try:
                ts = t.get("timestamp", datetime.utcnow().isoformat())
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                turns.append(
                    ConversationTurnResponse(
                        turn_number=t.get("turn_number", 0),
                        query=t.get("query", ""),
                        timestamp=ts,
                    )
                )
            except Exception:
                continue

        # Parse timestamps
        def _parse_ts(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            return datetime.utcnow()

        result = ConversationHistoryResponse(
            conversation_id=conversation_id,
            user_id=user_id,
            turns=turns,
            current_topic=context.get("current_topic"),
            created_at=_parse_ts(row.get("created_at")),
            last_updated=_parse_ts(row.get("last_updated")),
        )
        return success_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving conversation {conversation_id} for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.delete(
    "/conversations/{conversation_id}",
    response_model=SuccessResponse[dict],
)
@limiter.limit("20/minute")
async def delete_conversation(
    request: Request,
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a conversation and all its associated data.

    Requirements: 4.1, 10.3, 10.4
    """
    try:
        user_id = str(current_user["user_id"])

        deleted = await _delete_conversation_from_db(conversation_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")

        return success_response({"message": "Conversation deleted successfully"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting conversation {conversation_id} for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
