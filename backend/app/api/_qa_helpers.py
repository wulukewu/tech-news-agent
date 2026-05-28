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

from fastapi import APIRouter
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    """Shared article search used by both web chat and DM handler.

    Uses semantic (vector) search when Voyage API key is configured,
    falls back to keyword ilike search otherwise.
    """
    from app.services.supabase_service import SupabaseService as _SS
    from app.services.voyage_embedding import embed_text

    supabase = _SS()

    # Try semantic search first
    query_embedding = await embed_text(query)
    if query_embedding:
        try:
            resp = supabase.client.rpc(
                "match_articles",
                {
                    "query_embedding": query_embedding,
                    "match_count": 5,
                    "match_threshold": 0.3,
                },
            ).execute()
            if resp.data:
                logger.info(
                    "Vector search returned %d results, top similarity: %.3f",
                    len(resp.data),
                    resp.data[0].get("similarity", 0),
                )
            if resp.data:
                return [
                    ArticleSummaryResponse(
                        article_id=str(row["id"]),
                        title=row.get("title") or "",
                        summary=(row.get("ai_summary") or "")[:300],
                        url=row.get("url") or "",
                        relevance_score=round(float(row.get("similarity", 0.9)), 3),
                        reading_time=max(2, len(row.get("ai_summary") or "") // 200),
                        key_insights=[],
                        published_at=row.get("published_at"),
                        category=row.get("category") or "",
                    )
                    for row in resp.data
                ]
        except Exception as e:
            logger.warning("Vector search failed, falling back to keyword: %s", e)

    # Fallback: keyword ilike search
    import re

    keywords = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*|[\u4e00-\u9fff]{2,}", query)
    stop = {
        "最近",
        "有什麼",
        "有沒有",
        "文章",
        "介紹",
        "告訴",
        "幫我",
        "什麼",
        "怎麼",
        "如何",
        "推薦",
    }
    keywords = [k for k in keywords if k.lower() not in stop and len(k) > 1][:3]

    if not keywords:
        return []

    filters = ",".join(f"title.ilike.%{kw}%,ai_summary.ilike.%{kw}%" for kw in keywords)
    try:
        resp = (
            supabase.client.table("articles")
            .select(
                "id, title, url, ai_summary, actionable_takeaway, tinkering_index, published_at, category, feeds(category)"
            )
            .or_(filters)
            .order("published_at", desc=True)
            .limit(5)
            .execute()
        )
        results = []
        for row in resp.data or []:
            category = row.get("category") or (row.get("feeds") or {}).get("category") or ""
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
                    category=category,
                )
            )
        return results
    except Exception as e:
        logger.warning("Article search failed: %s", e)
        return []


def _get_supabase() -> SupabaseService:
    """Return a SupabaseService instance (validates=False to avoid blocking)."""
    return SupabaseService(validate_connection=False)


async def _create_conversation_in_db(
    user_id: str, title: Optional[str] = None, platform: str = "web"
) -> str:
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
            "platform": platform,
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


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert UUID, datetime, HttpUrl etc to JSON serializable formats."""
    import uuid
    from datetime import datetime

    from pydantic import BaseModel

    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(x) for x in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        try:
            return _make_json_safe(obj.dict())
        except Exception:
            pass
    # Check for Pydantic HttpUrl / Url types
    if hasattr(obj, "host") or type(obj).__name__ in ("HttpUrl", "Url", "UrlConstraints"):
        return str(obj)
    return obj


async def _save_messages_to_db(
    conversation_id: str,
    user_query: str,
    qa_response: Optional["QAQueryResponse"],
    platform: str = "web",
    skip_user_message: bool = False,
) -> None:
    """
    Save the user query and assistant response as rows in conversation_messages.
    Also updates the conversation title (from query) and message_count.
    """
    try:
        from datetime import timedelta

        supabase = _get_supabase()
        now = datetime.utcnow()
        user_ts = now.isoformat()
        assistant_ts = (now + timedelta(milliseconds=1)).isoformat()

        messages_to_insert = []
        if not skip_user_message:
            messages_to_insert.append(
                {
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": user_query,
                    "platform": platform,
                    "metadata": {},
                    "created_at": user_ts,
                }
            )

        if qa_response is not None:
            assistant_content = _qa_response_to_text(qa_response)

            # Construct raw metadata dict safely
            raw_metadata = {
                "articles": [
                    a.model_dump()
                    if hasattr(a, "model_dump")
                    else a.dict()
                    if hasattr(a, "dict")
                    else a
                    for a in qa_response.articles
                ],
                "insights": qa_response.insights,
                "recommendations": qa_response.recommendations,
                "response_time": qa_response.response_time,
                "intent": qa_response.intent,
            }

            messages_to_insert.append(
                {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": assistant_content,
                    "platform": platform,
                    "metadata": _make_json_safe(raw_metadata),
                    "created_at": assistant_ts,
                }
            )

        if messages_to_insert:
            supabase.client.table("conversation_messages").insert(messages_to_insert).execute()

        # Update conversation title and message_count
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
                "last_message_at": assistant_ts,
                "last_updated": assistant_ts,
            }
            if not current_title:
                updates["title"] = user_query[:100]
            supabase.client.table("conversations").update(updates).eq(
                "id", conversation_id
            ).execute()

    except Exception as e:
        logger.warning(f"Failed to save messages to conversation_messages: {e}")


async def _process_query_with_intent(
    user_id: str, query: str, conversation_id: str, platform: str = "web"
) -> "QAQueryResponse":
    """
    Intelligently dispatch and process user query using QAAgentDispatcher.
    """
    import time

    from app.qa_agent.agent_dispatcher import QAAgentDispatcher

    start_time = time.time()
    supabase = _get_supabase()

    # 1. Fetch user's discord_id to fetch active subscriptions
    discord_id = ""
    try:
        user_row = await supabase.get_user_by_id(user_id)
        if user_row:
            discord_id = user_row.get("discord_id") or ""
    except Exception as e:
        logger.warning(f"Failed to fetch discord_id for user {user_id}: {e}")

    # 2. Fetch conversation history turns
    history_turns = []
    try:
        msg_resp = (
            supabase.client.table("conversation_messages")
            .select("role, content, platform")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(10)
            .execute()
        )
        if msg_resp.data:
            for msg in msg_resp.data:
                history_turns.append(
                    {
                        "is_user": msg.get("role") == "user",
                        "content": msg.get("content") or "",
                        "platform": msg.get("platform") or "web",
                    }
                )
    except Exception as e:
        logger.warning(f"Failed to fetch conversation history for {conversation_id}: {e}")

    # 3. Call the dispatcher
    dispatcher = QAAgentDispatcher(supabase_service=supabase)
    dispatch_result = await dispatcher.dispatch(
        user_id=user_id,
        discord_id=discord_id,
        query=query,
        history_turns=history_turns,
        platform=platform,
    )

    action = dispatch_result.get("action", "chat")
    reply_content = dispatch_result.get("reply_content")
    action_args = dispatch_result.get("action_args") or {}

    # 4. Route dispatcher action
    if action == "record_preference":
        # Extract and store preference
        memory = dispatch_result.get("memory_to_record") or query
        await _store_preference(user_id, memory)

        # Trigger background summary update
        from app.services.auto_preference_summary import schedule_preference_summary_update

        try:
            schedule_preference_summary_update(user_id)
        except Exception:
            pass

        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or "✅ 已為您記錄偏好！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="preference",
        )

    elif action == "update_notification_frequency":
        frequency = action_args.get("frequency")
        if frequency in ["daily", "weekly", "monthly", "disabled"]:
            try:
                from app.repositories.user_notification_preferences import (
                    UserNotificationPreferencesRepository,
                )
                from app.schemas.user_notification_preferences import (
                    UpdateUserNotificationPreferencesRequest,
                )
                from app.services.preference_service import PreferenceService

                prefs_repo = UserNotificationPreferencesRepository(supabase.client)
                pref_service = PreferenceService(prefs_repo)
                updates = UpdateUserNotificationPreferencesRequest(frequency=frequency)
                await pref_service.update_preferences(user_id, updates, source="agent")
                logger.info(f"Successfully updated frequency to {frequency} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to update frequency in agent dispatcher: {e}")
                reply_content = "抱歉，設定推送頻率時發生錯誤，請稍後再試。"

        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or f"✅ 已為您將通知頻率更新為：{frequency}！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="preference",
        )

    elif action == "update_timezone":
        timezone = action_args.get("timezone") or "Asia/Taipei"
        try:
            from app.repositories.user_notification_preferences import (
                UserNotificationPreferencesRepository,
            )
            from app.schemas.user_notification_preferences import (
                UpdateUserNotificationPreferencesRequest,
            )
            from app.services.preference_service import PreferenceService

            prefs_repo = UserNotificationPreferencesRepository(supabase.client)
            pref_service = PreferenceService(prefs_repo)
            updates = UpdateUserNotificationPreferencesRequest(timezone=timezone)
            await pref_service.update_preferences(user_id, updates, source="agent")
            logger.info(f"Successfully updated timezone to {timezone} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to update timezone in agent dispatcher: {e}")
            reply_content = "抱歉，設定時區時發生錯誤，請稍後再試。"

        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or f"✅ 已為您將時區更新為：{timezone}！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="preference",
        )

    elif action == "toggle_notifications":
        enabled = action_args.get("enabled")
        if enabled is not None:
            try:
                from app.repositories.user_notification_preferences import (
                    UserNotificationPreferencesRepository,
                )
                from app.schemas.user_notification_preferences import (
                    UpdateUserNotificationPreferencesRequest,
                )
                from app.services.preference_service import PreferenceService

                prefs_repo = UserNotificationPreferencesRepository(supabase.client)
                pref_service = PreferenceService(prefs_repo)
                updates = UpdateUserNotificationPreferencesRequest(dm_enabled=bool(enabled))
                await pref_service.update_preferences(user_id, updates, source="agent")
                logger.info(f"Successfully toggled notifications to {enabled} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to toggle notifications in agent dispatcher: {e}")
                reply_content = "抱歉，切換通知設定時發生錯誤，請稍後再試。"

        status_str = "開啟" if enabled else "關閉"
        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or f"✅ 已為您{status_str}推送通知！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="preference",
        )

    elif action == "subscribe_rss":
        feed_url = action_args.get("feed_url")
        feed_name = action_args.get("feed_name") or "技術來源"
        if feed_url and discord_id:
            try:
                # 1. Look up if feed already exists
                feed_id = await supabase.find_feed_by_url(feed_url)
                if not feed_id:
                    # 2. Create feed first
                    feed_id = await supabase.create_feed(
                        url=feed_url,
                        name=feed_name,
                        category="Technology",
                        created_by=user_id,
                    )
                # 3. Subscribe user to feed
                await supabase.subscribe_to_feed(discord_id, feed_id)
                logger.info(f"Successfully subscribed user {discord_id} to feed {feed_id}")
            except Exception as e:
                logger.error(f"Failed to subscribe user to feed in agent dispatcher: {e}")
                reply_content = f"抱歉，訂閱 RSS 來源時發生錯誤：{e}"
        elif not discord_id:
            reply_content = "請先在 Discord 中註冊以訂閱 RSS 來源！"

        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or f"✅ 已為您成功訂閱 RSS 來源：{feed_name}！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="other",
        )

    elif action == "unsubscribe_rss":
        feed_name = action_args.get("feed_name")
        if feed_name and discord_id:
            try:
                # 1. Fetch user subscriptions
                subs = await supabase.get_user_subscriptions(discord_id)
                matched_sub = None
                for sub in subs:
                    # Case insensitive name search or partial match
                    if (
                        feed_name.lower() in sub.name.lower()
                        or sub.name.lower() in feed_name.lower()
                    ):
                        matched_sub = sub
                        break
                if matched_sub:
                    # 2. Unsubscribe
                    await supabase.unsubscribe_from_feed(discord_id, matched_sub.feed_id)
                    logger.info(
                        f"Successfully unsubscribed user {discord_id} from feed {matched_sub.feed_id}"
                    )
                else:
                    reply_content = f"抱歉，在您的訂閱清單中找不到名為「{feed_name}」的來源。"
            except Exception as e:
                logger.error(f"Failed to unsubscribe user from feed in agent dispatcher: {e}")
                reply_content = "抱歉，取消訂閱時發生錯誤，請稍後再試。"
        elif not discord_id:
            reply_content = "請先在 Discord 中註冊以管理訂閱！"

        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or f"✅ 已為您成功取消訂閱 RSS 來源：{feed_name}！"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="other",
        )

    elif action == "search":
        search_query = dispatch_result.get("search_query") or query
        articles = await _search_articles_by_query(search_query)

        insights = []
        recommendations = []
        if not articles:
            insights = ["找不到相關文章。試試換個關鍵字，或先訂閱更多 RSS 來源。"]
            recommendations = ["使用 /add_feed 訂閱更多 RSS 來源", "試試不同的關鍵字"]
        else:
            insights = [f"已為您搜尋關於「{search_query}」的相關文章："]

        return QAQueryResponse(
            query=query,
            articles=articles,
            insights=insights,
            recommendations=recommendations,
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="question",
        )

    else:  # action == "chat"
        # Just standard conversational chat
        return QAQueryResponse(
            query=query,
            articles=[],
            insights=[reply_content or "你好！有什麼想聊的技術話題嗎？"],
            recommendations=[],
            conversation_id=conversation_id,
            response_time=round(time.time() - start_time, 2),
            intent="other",
        )


def _qa_response_to_text(qa_response: "QAQueryResponse") -> str:
    """Convert a QAQueryResponse to a plain-text assistant message for storage."""
    if not qa_response.articles and qa_response.insights:
        return " ".join(qa_response.insights)

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
