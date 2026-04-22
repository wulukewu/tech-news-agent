"""
Intelligent Q&A Agent REST API Endpoints

This module provides FastAPI endpoints for the intelligent Q&A system,
supporting single queries, multi-turn conversations, and conversation management.

Requirements: 1.1, 4.1, 4.4, 6.4, 10.3
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.auth import get_current_user
from app.qa_agent.conversation_manager import ConversationManager
from app.qa_agent.qa_agent_controller import QAAgentController
from app.schemas.responses import SuccessResponse, success_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level limiter — must match the one registered on app.state.limiter in main.py
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Request / Response Schemas
# ============================================================================


class QueryRequest(BaseModel):
    """
    Request body for single Q&A query.

    Requirements: 1.1
    """

    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID to continue an existing conversation"
    )


class CreateConversationRequest(BaseModel):
    """
    Request body for creating a new conversation.

    Requirements: 4.1
    """

    initial_query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2000,
        description="Optional initial query to process when creating the conversation",
    )


class ContinueConversationRequest(BaseModel):
    """
    Request body for continuing an existing conversation with a follow-up query.

    Requirements: 4.1, 4.2, 4.3
    """

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

    Wraps StructuredResponse fields into a JSON-serializable format.

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """

    query: str = Field(..., description="Original user query")
    articles: List[ArticleSummaryResponse] = Field(
        default_factory=list, description="Relevant articles (max 5)"
    )
    insights: List[str] = Field(
        default_factory=list, description="Personalized insights based on user profile"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Related reading suggestions"
    )
    conversation_id: str = Field(..., description="Associated conversation ID")
    response_time: float = Field(..., description="Response generation time in seconds")


class ConversationTurnResponse(BaseModel):
    """Serializable conversation turn for API responses."""

    turn_number: int
    query: str
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    """
    Response for conversation history endpoint.

    Wraps ConversationContext fields into a JSON-serializable format.

    Requirements: 4.1, 4.4
    """

    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User identifier")
    turns: List[ConversationTurnResponse] = Field(
        default_factory=list, description="Conversation turns"
    )
    current_topic: Optional[str] = Field(None, description="Current conversation topic")
    created_at: datetime = Field(..., description="When conversation was created")
    last_updated: datetime = Field(..., description="Last update timestamp")


class CreateConversationResponse(BaseModel):
    """Response for conversation creation endpoint."""

    conversation_id: str = Field(..., description="Newly created conversation ID")
    query_result: Optional[QAQueryResponse] = Field(
        None, description="Result of initial query if provided"
    )


# ============================================================================
# Helper utilities
# ============================================================================


def _structured_response_to_dict(response, conversation_id: str) -> QAQueryResponse:
    """
    Convert a StructuredResponse dataclass to a QAQueryResponse schema.

    Args:
        response: StructuredResponse instance from QAAgentController
        conversation_id: Conversation ID string (fallback if response has none)

    Returns:
        QAQueryResponse ready for serialization
    """
    articles = []
    for article in response.articles:
        articles.append(
            ArticleSummaryResponse(
                article_id=str(article.article_id),
                title=article.title,
                summary=article.summary,
                url=str(article.url),
                relevance_score=article.relevance_score,
                reading_time=article.reading_time,
                key_insights=article.key_insights,
                published_at=article.published_at,
                category=article.category,
            )
        )

    conv_id = str(response.conversation_id) if response.conversation_id else conversation_id

    return QAQueryResponse(
        query=response.query,
        articles=articles,
        insights=response.insights,
        recommendations=response.recommendations,
        conversation_id=conv_id,
        response_time=response.response_time,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/query", response_model=SuccessResponse[QAQueryResponse])
@limiter.limit("20/minute")
async def query(
    request: Request,
    body: QueryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Process a single natural language query and return a structured response.

    Supports optional conversation_id to continue an existing conversation.
    If no conversation_id is provided, a new conversation is created automatically.

    Requirements: 1.1, 6.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])
        controller = QAAgentController()

        response = await controller.process_query(
            user_id=user_id,
            query=body.query,
            conversation_id=body.conversation_id,
        )

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to process query")

        result = _structured_response_to_dict(response, body.conversation_id or "")
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
        user_uuid = current_user["user_id"]  # UUID object

        conversation_manager = ConversationManager()
        conversation_id = await conversation_manager.create_conversation(user_uuid)

        query_result = None
        if body.initial_query:
            controller = QAAgentController(conversation_manager=conversation_manager)
            response = await controller.process_query(
                user_id=user_id,
                query=body.initial_query,
                conversation_id=conversation_id,
            )
            if response is not None:
                query_result = _structured_response_to_dict(response, conversation_id)

        result = CreateConversationResponse(
            conversation_id=conversation_id,
            query_result=query_result,
        )
        return success_response(result)

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

    Maintains conversation context across multiple turns (up to 10 turns).

    Requirements: 4.1, 4.2, 4.3, 4.4, 6.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])
        controller = QAAgentController()

        # Verify conversation exists and belongs to this user
        context = await controller.get_conversation_history(user_id, conversation_id)
        if context is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or access denied",
            )

        response = await controller.continue_conversation(
            user_id=user_id,
            query=body.query,
            conversation_id=conversation_id,
        )

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to process follow-up query")

        result = _structured_response_to_dict(response, conversation_id)
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

    Returns conversation turns and metadata. Only the conversation owner can access it.

    Requirements: 4.1, 4.4, 10.3
    """
    try:
        user_id = str(current_user["user_id"])
        controller = QAAgentController()

        context = await controller.get_conversation_history(user_id, conversation_id)
        if context is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or access denied",
            )

        turns = [
            ConversationTurnResponse(
                turn_number=turn.turn_number,
                query=turn.query,
                timestamp=turn.timestamp,
            )
            for turn in context.turns
        ]

        result = ConversationHistoryResponse(
            conversation_id=str(context.conversation_id),
            user_id=str(context.user_id),
            turns=turns,
            current_topic=context.current_topic,
            created_at=context.created_at,
            last_updated=context.last_updated,
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

    Only the conversation owner can delete it. This operation is irreversible.

    Requirements: 4.1, 10.3, 10.4
    """
    try:
        user_id = str(current_user["user_id"])
        controller = QAAgentController()

        deleted = await controller.delete_conversation(user_id, conversation_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or access denied",
            )

        return success_response({"message": "Conversation deleted successfully"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting conversation {conversation_id} for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
