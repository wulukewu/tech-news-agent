"""
Reminder Settings API - 讀寫用戶的智能提醒設定
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.services.reminder_service import get_reminder_stats
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reminders", tags=["reminders"])

_DEFAULTS = {
    "reminder_enabled": True,
    "reminder_on_add": True,
    "reminder_on_rate": True,
    "reminder_cooldown_hours": 4,
    "reminder_min_similarity": 0.72,
}


class ReminderSettings(BaseModel):
    reminder_enabled: bool = True
    reminder_on_add: bool = True
    reminder_on_rate: bool = True
    reminder_cooldown_hours: int = Field(default=4, ge=0, le=72)
    reminder_min_similarity: float = Field(default=0.72, ge=0.5, le=0.99)


async def _get_prefs_row(supabase: SupabaseService, user_id: str) -> dict:
    """讀取 user_notification_preferences，欄位不存在時回傳 defaults"""
    try:
        cols = "id," + ",".join(_DEFAULTS.keys())
        r = (
            supabase.client.table("user_notification_preferences")
            .select(cols)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if r.data:
            return {k: r.data.get(k, v) for k, v in _DEFAULTS.items()}
    except Exception:
        pass
    return dict(_DEFAULTS)


@router.get("/settings", response_model=ReminderSettings)
async def get_reminder_settings(current_user: dict[str, Any] = Depends(get_current_user)):
    supabase = SupabaseService()
    data = await _get_prefs_row(supabase, current_user["user_id"])
    return ReminderSettings(**data)


@router.put("/settings", response_model=ReminderSettings)
async def update_reminder_settings(
    body: ReminderSettings,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    supabase = SupabaseService()
    user_id = current_user["user_id"]

    try:
        supabase.client.table("user_notification_preferences").update(body.model_dump()).eq(
            "user_id", user_id
        ).execute()
    except Exception as e:
        # 欄位不存在（migration 未執行）
        if "column" in str(e).lower() or "schema" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Reminder settings columns not yet migrated. Run migrations/007_add_reminder_settings.sql in Supabase.",
            )
        raise HTTPException(status_code=500, detail=str(e))

    return body


@router.get("/stats")
async def get_reminder_statistics(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """獲取用戶的提醒統計數據"""
    user_id = current_user["user_id"]

    try:
        stats = await get_reminder_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get reminder stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder statistics")


@router.post("/test")
async def test_reminder(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """發送測試提醒給用戶"""
    import asyncio

    from app.services.reminder_service import send_similar_articles_reminder

    discord_id = current_user["discord_id"]

    try:
        # 找一篇用戶最近加入 reading list 的文章作為測試
        supabase = SupabaseService()
        user_id = current_user["user_id"]

        recent_article = (
            supabase.client.table("reading_list")
            .select("article_id")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )

        if not recent_article.data:
            raise HTTPException(status_code=404, detail="No articles in reading list to test with")

        article_id = recent_article.data["article_id"]

        # 異步發送測試提醒
        asyncio.create_task(send_similar_articles_reminder(discord_id, article_id, "added"))

        return {"message": "Test reminder sent! Check your Discord DM."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test reminder")


class FeedbackRequest(BaseModel):
    article_id: str
    feedback: str = Field(..., pattern="^(accurate|inaccurate|not_interested)$")


@router.post("/feedback")
async def submit_reminder_feedback(
    body: FeedbackRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """用戶對推薦文章的反饋"""
    from app.services.reminder_service import record_user_feedback

    user_id = current_user["user_id"]

    try:
        await record_user_feedback(user_id, body.article_id, body.feedback)
        return {"message": "Feedback recorded successfully"}
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/history")
async def get_reminder_history(
    limit: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """獲取用戶的提醒歷史記錄"""
    user_id = current_user["user_id"]
    supabase = SupabaseService()

    try:
        history = (
            supabase.client.table("reminder_logs")
            .select(
                """
                sent_at,
                trigger_type,
                similarity_score,
                clicked_at,
                user_feedback,
                trigger_article:articles!trigger_article_id(title),
                recommended_article:articles!recommended_article_id(title, url)
            """
            )
            .eq("user_id", user_id)
            .order("sent_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {"history": history.data or []}

    except Exception as e:
        logger.error(f"Failed to get reminder history: {e}")
        # 如果表不存在，返回空歷史
        return {"history": []}
