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
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.auth import get_current_user
from app.schemas.responses import SuccessResponse, success_response
from app.services.supabase_service import SupabaseService

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

    if re.search(r"[?？]|什麼|怎麼|如何|有沒有|推薦|介紹|解釋|告訴我|幫我找|最近.*文章|有什麼.*關於", text, re.IGNORECASE):
        return "question"
    if re.search(r"我喜歡|我不喜歡|我想看|我偏好|我對.*感興趣|不想看|希望多|希望少", text, re.IGNORECASE):
        return "preference"
    return "other"


async def _store_preference(user_id: str, content: str) -> None:
    """Store a preference statement in dm_conversations for learning."""
    try:
        supabase = _get_supabase()
        supabase.client.table("dm_conversations").insert(
            {"user_id": user_id, "content": content}
        ).execute()
    except Exception as e:
        logger.warning("Failed to store preference: %s", e)


async def _search_articles_by_query(query: str) -> List[ArticleSummaryResponse]:
    """Shared article search used by both web chat and DM handler."""
    import re

    keywords = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*|[\u4e00-\u9fff]{2,}", query)
    stop = {"最近", "有什麼", "有沒有", "文章", "介紹", "告訴", "幫我", "什麼", "怎麼", "如何", "推薦"}
    keywords = [k for k in keywords if k.lower() not in stop and len(k) > 1][:3]

    if not keywords:
        return []

    filters = ",".join(f"title.ilike.%{kw}%,ai_summary.ilike.%{kw}%" for kw in keywords)
    try:
        from app.services.supabase_service import SupabaseService as _SS

        supabase = _SS()
        resp = (
            supabase.client.table("articles")
            .select("id, title, url, ai_summary, tinkering_index, published_at")
            .or_(filters)
            .order("published_at", desc=True)
            .limit(5)
            .execute()
        )
        results = []
        for row in resp.data or []:
            results.append(
                ArticleSummaryResponse(
                    article_id=str(row["id"]),
                    title=row.get("title") or "",
                    summary=(row.get("ai_summary") or "")[:300],
                    url=row.get("url") or "",
                    relevance_score=0.9,
                    reading_time=max(2, len(row.get("ai_summary") or "") // 200),
                    key_insights=[],
                    published_at=row.get("published_at"),
                    category="",
                )
            )
        return results
    except Exception as e:
        logger.warning("Article search failed: %s", e)
        return []


def _get_supabase() -> SupabaseService:
    """Return a SupabaseService instance (validates=False to avoid blocking)."""
    return SupabaseService(validate_connection=False)


async def _create_conversation_in_db(user_id: str, title: Optional[str] = None) -> str:
    """
    Create a new conversation row in Supabase and return its ID.
    Uses fallback approach if conversations table doesn't exist.
    """
    conversation_id = str(uuid4())

    try:
        # Try to use the conversations table
        supabase = _get_supabase()
        now = datetime.utcnow().isoformat()
        expires_at = (datetime.utcnow() + timedelta(days=_CONVERSATION_EXPIRY_DAYS)).isoformat()

        initial_context: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "turns": [],
            "current_topic": None,
            "created_at": now,
            "last_updated": now,
        }

        row: Dict[str, Any] = {
            "id": conversation_id,
            "user_id": user_id,
            "context": initial_context,
            "created_at": now,
            "last_updated": now,
            "expires_at": expires_at,
            "platform": "web",
            "tags": [],
            "is_archived": False,
            "is_favorite": False,
            "message_count": 0,
            "last_message_at": now,
            "metadata": {},
        }
        if title:
            row["title"] = title

        result = supabase.client.table("conversations").insert(row).execute()

        logger.info(f"Successfully created conversation {conversation_id} in database")
        return conversation_id

    except Exception as e:
        # If conversations table doesn't exist or other DB error, just return the ID
        logger.warning(f"Failed to create conversation in database, using fallback: {e}")
        logger.info(f"Generated fallback conversation ID: {conversation_id}")
        return conversation_id


async def _save_messages_to_db(
    conversation_id: str,
    user_query: str,
    qa_response: Optional["QAQueryResponse"],
) -> None:
    """
    Save the user query and assistant response as rows in conversation_messages.
    Also updates the conversation title (from query) and message_count.
    """
    try:
        supabase = _get_supabase()
        now = datetime.utcnow().isoformat()

        messages_to_insert = [
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": user_query,
                "platform": "web",
                "metadata": {},
                "created_at": now,
            }
        ]

        if qa_response is not None:
            # Build a readable assistant reply from the structured response
            assistant_content = _qa_response_to_text(qa_response)
            messages_to_insert.append(
                {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": assistant_content,
                    "platform": "web",
                    "metadata": {
                        "articles": [a.dict() for a in qa_response.articles],
                        "insights": qa_response.insights,
                        "recommendations": qa_response.recommendations,
                        "response_time": qa_response.response_time,
                    },
                    "created_at": now,
                }
            )

        supabase.client.table("conversation_messages").insert(messages_to_insert).execute()

        # Update conversation: set title from first query if not set, bump message_count
        existing = (
            supabase.client.table("conversations")
            .select("title, message_count")
            .eq("id", conversation_id)
            .execute()
        )
        if existing.data:
            current_title = existing.data[0].get("title")
            current_count = existing.data[0].get("message_count") or 0
            updates: Dict[str, Any] = {
                "message_count": current_count + len(messages_to_insert),
                "last_message_at": now,
                "last_updated": now,
            }
            if not current_title:
                # Use the query as the title (truncated)
                updates["title"] = user_query[:100]
            supabase.client.table("conversations").update(updates).eq(
                "id", conversation_id
            ).execute()

    except Exception as e:
        logger.warning(f"Failed to save messages to conversation_messages: {e}")


async def _process_query_with_intent(
    user_id: str, query: str, conversation_id: str
) -> "QAQueryResponse":
    """
    Detect intent, store preferences, and run article search if needed.
    Returns a QAQueryResponse with the intent field set.
    """
    intent = _detect_intent(query)

    if intent == "preference":
        await _store_preference(user_id, query)
        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[
                "✅ 已記錄你的偏好！這會幫助我推薦更適合你的文章。",
                "使用 /update_profile 指令（Discord）或前往「偏好設定」更新你的偏好摘要。",
            ],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=0.0,
            intent="preference",
        )

    if intent == "other":
        await _store_preference(user_id, query)
        return QAQueryResponse(
            query=query,
            articles=[],
            insights=["已記錄 👍"],
            recommendations=["試試問我問題，例如「最近有什麼 AI 文章？」", "或告訴我你的偏好，例如「我喜歡系統設計」"],
            conversation_id=conversation_id,
            response_time=0.0,
            intent="other",
        )

    # intent == "question" — search articles directly (same as DM)
    import time

    start = time.time()
    articles = await _search_articles_by_query(query)

    insights: List[str] = []
    recommendations: List[str] = []
    if not articles:
        insights = ["找不到相關文章。試試換個關鍵字，或先訂閱更多 RSS 來源。"]
        recommendations = ["使用 /add_feed 訂閱更多 RSS 來源", "試試不同的關鍵字"]

    return QAQueryResponse(
        query=query,
        articles=articles,
        insights=insights,
        recommendations=recommendations,
        conversation_id=conversation_id,
        response_time=round(time.time() - start, 2),
        intent="question",
    )


def _qa_response_to_text(qa_response: "QAQueryResponse") -> str:
    """Convert a QAQueryResponse to a plain-text assistant message for storage."""
    parts = []
    if qa_response.articles:
        titles = [a.title for a in qa_response.articles[:3]]
        parts.append("相關文章：" + "、".join(titles))
    if qa_response.insights:
        parts.append("洞察：" + " ".join(qa_response.insights[:2]))
    if qa_response.recommendations:
        parts.append("延伸閱讀：" + "、".join(qa_response.recommendations[:3]))
    return "\n".join(parts) if parts else "（已處理您的查詢）"


async def _get_conversation_from_db(conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a conversation row from Supabase.

    Returns the context dict if found and owned by user_id, else None.
    """
    supabase = _get_supabase()
    result = (
        supabase.client.table("conversations")
        .select("id, user_id, context, created_at, last_updated, expires_at")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return None

    row = result.data[0]

    # Check expiry
    expires_at_str = row.get("expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                # Expired — delete and return None
                supabase.client.table("conversations").delete().eq("id", conversation_id).execute()
                return None
        except Exception:
            pass  # If we can't parse the date, allow the conversation through

    return row


async def _append_turn_to_db(
    conversation_id: str,
    user_id: str,
    query: str,
    qa_response: Optional[QAQueryResponse],
) -> None:
    """
    Append a new turn to the conversation's context JSONB and update last_updated.
    Enforces the 10-turn limit (Requirement 4.4).
    """
    supabase = _get_supabase()

    # Fetch current context
    result = (
        supabase.client.table("conversations")
        .select("context")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return

    context = result.data[0]["context"]
    if isinstance(context, str):
        context = json.loads(context)

    turns: List[Dict[str, Any]] = context.get("turns", [])

    # Build new turn
    new_turn = {
        "turn_number": len(turns) + 1,
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
    }
    turns.append(new_turn)

    # Enforce 10-turn limit
    if len(turns) > _MAX_TURNS:
        turns = turns[-_MAX_TURNS:]
        # Renumber
        for i, t in enumerate(turns):
            t["turn_number"] = i + 1

    context["turns"] = turns
    context["last_updated"] = datetime.utcnow().isoformat()

    supabase.client.table("conversations").update(
        {
            "context": context,
            "last_updated": datetime.utcnow().isoformat(),
        }
    ).eq("id", conversation_id).execute()


async def _delete_conversation_from_db(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation row. Returns True if a row was deleted."""
    supabase = _get_supabase()
    result = (
        supabase.client.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(result.data)


# ============================================================================
# Helper: convert StructuredResponse → QAQueryResponse
# ============================================================================


def _structured_response_to_schema(response: Any, conversation_id: str) -> QAQueryResponse:
    """Convert a StructuredResponse dataclass to a JSON-serializable QAQueryResponse."""
    articles = []
    for article in getattr(response, "articles", []):
        articles.append(
            ArticleSummaryResponse(
                article_id=str(article.article_id),
                title=article.title,
                summary=article.summary,
                url=str(article.url),
                relevance_score=article.relevance_score,
                reading_time=article.reading_time,
                key_insights=list(getattr(article, "key_insights", [])),
                published_at=getattr(article, "published_at", None),
                category=getattr(article, "category", ""),
            )
        )

    conv_id = str(response.conversation_id) if response.conversation_id else conversation_id

    return QAQueryResponse(
        query=response.query,
        articles=articles,
        insights=list(getattr(response, "insights", [])),
        recommendations=list(getattr(response, "recommendations", [])),
        conversation_id=conv_id,
        response_time=getattr(response, "response_time", 0.0),
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
