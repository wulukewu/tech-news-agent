"""
Notification API Endpoints

This module provides API endpoints for managing user notification settings
and preferences, including the new personalized notification frequency system.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.schemas.responses import SuccessResponse, success_response
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


router = APIRouter()


@router.patch("/proactive-frequency", response_model=SuccessResponse[dict])
async def update_proactive_dm_frequency(
    body: dict,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update proactive recommendation DM frequency.

    Body: { "frequency": "daily" | "every_two_days" | "weekly" }
    Requirements: 4.4
    """
    frequency = body.get("frequency")
    if frequency not in PROACTIVE_FREQUENCY_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid frequency. Choose from: {list(PROACTIVE_FREQUENCY_OPTIONS.keys())}",
        )

    hours = PROACTIVE_FREQUENCY_OPTIONS[frequency]
    try:
        supabase = SupabaseService()
        supabase.client.table("users").update({"proactive_dm_frequency_hours": hours}).eq(
            "id", current_user["user_id"]
        ).execute()
    except Exception as exc:
        logger.error("Failed to update proactive_dm_frequency_hours: %s", exc)
        raise HTTPException(status_code=500, detail="無法更新推薦頻率設定")

    return success_response({"frequency": frequency, "cooldown_hours": hours})


@router.get("/proactive-frequency", response_model=SuccessResponse[dict])
async def get_proactive_dm_frequency(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get current proactive recommendation DM frequency setting. Requirements: 4.4"""
    try:
        supabase = SupabaseService()
        resp = (
            supabase.client.table("users")
            .select("proactive_dm_frequency_hours")
            .eq("id", current_user["user_id"])
            .single()
            .execute()
        )
        hours = (resp.data or {}).get("proactive_dm_frequency_hours") or 20
    except Exception as exc:
        logger.error("Failed to get proactive_dm_frequency_hours: %s", exc)
        raise HTTPException(status_code=500, detail="無法取得推薦頻率設定")

    # Reverse-map hours → label
    reverse = {v: k for k, v in PROACTIVE_FREQUENCY_OPTIONS.items()}
    frequency = reverse.get(hours, "daily")
    return success_response({"frequency": frequency, "cooldown_hours": hours})
