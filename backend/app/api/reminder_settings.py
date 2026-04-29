"""
Reminder Settings API - 讀寫用戶的智能提醒設定
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
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
    reminder_cooldown_hours: int = Field(default=4, ge=1, le=72)
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
