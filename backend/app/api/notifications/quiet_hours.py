"""
Notification API Endpoints

This module provides API endpoints for managing user notification settings
and preferences, including the new personalized notification frequency system.
"""

import logging
import zoneinfo
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.core.errors import ValidationError
from app.schemas.quiet_hours import (
    CreateDefaultQuietHoursRequest,
    QuietHoursSettings,
    QuietHoursStatusResponse,
    UpdateQuietHoursRequest,
)
from app.schemas.responses import SuccessResponse, success_response
from app.services.quiet_hours_service import QuietHoursService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


router = APIRouter()


@router.get("/quiet-hours", response_model=SuccessResponse[QuietHoursSettings])
async def get_quiet_hours(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get user's quiet hours settings

    Returns the user's quiet hours configuration including time range,
    timezone, weekdays, and enabled status.
    """
    try:
        supabase = SupabaseService()
        quiet_hours_service = QuietHoursService(supabase)

        user_id = current_user["user_id"]  # Already a UUID object

        quiet_hours = await quiet_hours_service.get_quiet_hours(user_id)

        if not quiet_hours:
            # Create default quiet hours if none exist
            quiet_hours = await quiet_hours_service.create_default_quiet_hours(user_id)

        logger.info(f"Retrieved quiet hours for user {user_id}")

        return success_response(quiet_hours.to_dict())

    except Exception as e:
        logger.error(
            f"Error getting quiet hours for user {current_user['user_id']}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="無法載入勿擾時段設定")


@router.put("/quiet-hours", response_model=SuccessResponse[QuietHoursSettings])
async def update_quiet_hours(
    updates: UpdateQuietHoursRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Update user's quiet hours settings

    Updates the user's quiet hours configuration. Only provided fields
    will be updated, others will remain unchanged.
    """
    try:
        supabase = SupabaseService()
        quiet_hours_service = QuietHoursService(supabase)

        user_id = current_user["user_id"]  # Already a UUID object

        # Update quiet hours
        updated_quiet_hours = await quiet_hours_service.update_quiet_hours(
            user_id=user_id,
            start_time=updates.start_time,
            end_time=updates.end_time,
            timezone=updates.timezone,
            weekdays=updates.weekdays,
            enabled=updates.enabled,
        )

        logger.info(f"Updated quiet hours for user {user_id}")

        return success_response(updated_quiet_hours.to_dict())

    except ValidationError as e:
        logger.warning(
            f"Validation error updating quiet hours for user {current_user['user_id']}: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error updating quiet hours for user {current_user['user_id']}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="無法更新勿擾時段設定")


@router.get("/quiet-hours/status", response_model=SuccessResponse[QuietHoursStatusResponse])
async def get_quiet_hours_status(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Check current quiet hours status

    Returns whether the current time is within the user's quiet hours,
    along with the next available notification time if applicable.
    """
    try:
        supabase = SupabaseService()
        quiet_hours_service = QuietHoursService(supabase)

        user_id = current_user["user_id"]  # Already a UUID object
        current_time = datetime.utcnow()

        # Check if currently in quiet hours
        is_in_quiet_hours, quiet_hours = await quiet_hours_service.is_in_quiet_hours(
            user_id, current_time
        )

        # Get next notification time if in quiet hours
        next_notification_time = None
        if is_in_quiet_hours:
            next_time = await quiet_hours_service.get_next_notification_time(user_id, current_time)
            next_notification_time = next_time.isoformat() if next_time else None

        # Format current time in user's timezone
        if quiet_hours and quiet_hours.timezone:
            try:
                user_tz = zoneinfo.ZoneInfo(quiet_hours.timezone)
                if current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=timezone.utc)
                local_time = current_time.astimezone(user_tz)
                current_time_str = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            except zoneinfo.ZoneInfoNotFoundError:
                current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Create status message
        if not quiet_hours or not quiet_hours.enabled:
            message = "勿擾時段未啟用"
        elif is_in_quiet_hours:
            message = "目前在勿擾時段內，通知將被暫停"
        else:
            message = "目前不在勿擾時段內，可以發送通知"

        status_response = QuietHoursStatusResponse(
            is_in_quiet_hours=is_in_quiet_hours,
            quiet_hours=quiet_hours.to_dict() if quiet_hours else None,
            next_notification_time=next_notification_time,
            current_time=current_time_str,
            message=message,
        )

        logger.info(f"Retrieved quiet hours status for user {user_id}: {is_in_quiet_hours}")

        return success_response(status_response.dict())

    except Exception as e:
        logger.error(
            f"Error getting quiet hours status for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入勿擾時段狀態")


@router.post("/quiet-hours/default", response_model=SuccessResponse[QuietHoursSettings])
async def create_default_quiet_hours(
    request: CreateDefaultQuietHoursRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Create default quiet hours settings

    Creates default quiet hours settings for the user (22:00-08:00, disabled by default).
    This is useful for new users or when resetting quiet hours to defaults.
    """
    try:
        supabase = SupabaseService()
        quiet_hours_service = QuietHoursService(supabase)

        user_id = current_user["user_id"]  # Already a UUID object

        # Create default quiet hours
        quiet_hours = await quiet_hours_service.create_default_quiet_hours(
            user_id=user_id, timezone=request.timezone
        )

        logger.info(f"Created default quiet hours for user {user_id}")

        return success_response(quiet_hours.to_dict())

    except Exception as e:
        logger.error(
            f"Error creating default quiet hours for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法創建預設勿擾時段設定")


@router.delete("/quiet-hours", response_model=SuccessResponse[dict])
async def delete_quiet_hours(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Delete user's quiet hours settings

    Removes all quiet hours settings for the user. This effectively
    disables quiet hours functionality.
    """
    try:
        supabase = SupabaseService()
        quiet_hours_service = QuietHoursService(supabase)

        user_id = current_user["user_id"]  # Already a UUID object

        # Delete quiet hours
        await quiet_hours_service.delete_quiet_hours(user_id)

        logger.info(f"Deleted quiet hours for user {user_id}")

        return success_response({"message": "勿擾時段設定已刪除"})

    except Exception as e:
        logger.error(
            f"Error deleting quiet hours for user {current_user['user_id']}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="無法刪除勿擾時段設定")


# Technical Depth API Endpoints
