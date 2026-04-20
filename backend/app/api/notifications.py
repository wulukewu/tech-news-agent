"""
Notification API Endpoints

This module provides API endpoints for managing user notification settings
and preferences, including the new personalized notification frequency system.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.core.errors import ServiceError, ValidationError
from app.core.timezone_converter import TimezoneConverter
from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.schemas.notification import (
    NotificationDeliveryStatus,
    NotificationSettings,
    UpdateNotificationSettingsRequest,
)
from app.schemas.responses import SuccessResponse, success_response
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
    UserNotificationPreferences,
)
from app.services.notification_settings_service import NotificationSettingsService
from app.services.preference_service import PreferenceService
from app.services.supabase_service import SupabaseService
from app.tasks.scheduler import get_dynamic_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/settings", response_model=SuccessResponse[NotificationSettings])
async def get_notification_settings(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get user's notification settings

    Returns the user's notification preferences including DM settings,
    frequency, quiet hours, and feed-specific settings.
    """
    try:
        supabase = SupabaseService()
        service = NotificationSettingsService(supabase)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Get notification settings
        settings = await service.get_notification_settings(user_uuid)

        logger.info(f"Retrieved notification settings for user {current_user['user_id']}")

        return success_response(settings)

    except ServiceError as e:
        logger.error(
            f"Failed to get notification settings for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入通知設定")
    except Exception as e:
        logger.error(
            f"Unexpected error getting notification settings for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.patch("/settings", response_model=SuccessResponse[NotificationSettings])
async def update_notification_settings(
    updates: UpdateNotificationSettingsRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update user's notification settings

    Updates the user's notification preferences. Only provided fields
    will be updated, others will remain unchanged.
    """
    try:
        supabase = SupabaseService()
        service = NotificationSettingsService(supabase)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Update notification settings
        updated_settings = await service.update_notification_settings(user_uuid, updates)

        logger.info(f"Updated notification settings for user {current_user['user_id']}")

        return success_response(updated_settings)

    except ValidationError as e:
        logger.warning(
            f"Validation error updating notification settings for user {current_user['user_id']}: {e!s}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceError as e:
        logger.error(
            f"Failed to update notification settings for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法更新通知設定")
    except Exception as e:
        logger.error(
            f"Unexpected error updating notification settings for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/test")
async def send_test_notification(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Send a test notification

    Sends a test notification to verify the user's notification settings
    are working correctly.
    """
    try:
        supabase = SupabaseService()
        service = NotificationSettingsService(supabase)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Send test notification
        await service.send_test_notification(user_uuid)

        logger.info(f"Sent test notification for user {current_user['user_id']}")

        return success_response({"message": "測試通知已發送"})

    except ValidationError as e:
        logger.warning(
            f"Validation error sending test notification for user {current_user['user_id']}: {e!s}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceError as e:
        logger.error(
            f"Failed to send test notification for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法發送測試通知")
    except Exception as e:
        logger.error(
            f"Unexpected error sending test notification for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.get("/history", response_model=SuccessResponse[NotificationDeliveryStatus])
async def get_notification_history(
    limit: int = 50, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get notification delivery history

    Returns the user's recent notification delivery history including
    success/failure status and timestamps.
    """
    try:
        # For now, return empty history as this feature is not fully implemented
        # In the future, this would query a notification_history table

        history = NotificationDeliveryStatus(
            total_sent=0, total_failed=0, last_sent_at=None, recent_history=[]
        )

        logger.info(f"Retrieved notification history for user {current_user['user_id']}")

        return success_response(history)

    except Exception as e:
        logger.error(
            f"Unexpected error getting notification history for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


# New Personalized Notification Frequency Endpoints


@router.get("/preferences", response_model=SuccessResponse[UserNotificationPreferences])
async def get_notification_preferences(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get user's notification preferences

    Returns the user's personalized notification preferences including frequency,
    timing, timezone, and channel settings.

    Requirements: 6.1, 6.2
    """
    try:
        supabase = SupabaseService()

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Initialize services
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)

        # Get notification preferences (creates defaults if none exist)
        preferences = await preference_service.get_user_preferences(user_uuid)

        logger.info(f"Retrieved notification preferences for user {current_user['user_id']}")

        return success_response(preferences)

    except ServiceError as e:
        logger.error(
            f"Failed to get notification preferences for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入通知偏好設定")
    except Exception as e:
        logger.error(
            f"Unexpected error getting notification preferences for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.put("/preferences", response_model=SuccessResponse[UserNotificationPreferences])
async def update_notification_preferences(
    updates: UpdateUserNotificationPreferencesRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update user's notification preferences

    Updates the user's personalized notification preferences. Only provided fields
    will be updated, others will remain unchanged. Automatically reschedules
    notifications based on new preferences.

    Requirements: 6.3, 6.4, 6.5
    """
    try:
        supabase = SupabaseService()

        # Get user UUID
        user_id = await supabase.get_or_create_user(current_user["discord_id"])

        # Initialize services
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)
        dynamic_scheduler = get_dynamic_scheduler()

        # Update notification preferences with source tracking
        updated_preferences = await preference_service.update_preferences(
            user_id, updates, source="web"
        )

        logger.info(f"Updated notification preferences for user {current_user['user_id']}")

        return success_response(updated_preferences)

    except ValidationError as e:
        logger.warning(
            f"Validation error updating notification preferences for user {current_user['user_id']}: {e!s}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceError as e:
        logger.error(
            f"Failed to update notification preferences for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法更新通知偏好設定")
    except Exception as e:
        logger.error(
            f"Unexpected error updating notification preferences for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.get("/preferences/preview")
async def preview_notification_time(
    frequency: str,
    notification_time: str,
    timezone: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Preview next notification time

    Calculates and returns when the next notification would be sent
    based on the provided preferences.

    Requirements: 6.4
    """
    try:
        # Validate inputs
        valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
        if frequency not in valid_frequencies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}",
            )

        # Calculate next notification time
        next_time = TimezoneConverter.get_next_notification_time(
            frequency=frequency, notification_time=notification_time, timezone=timezone
        )

        if next_time is None:
            return success_response(
                {
                    "next_notification_time": None,
                    "local_time": None,
                    "utc_time": None,
                    "message": "通知已停用",
                }
            )

        # Convert to user's local time for display
        local_time = TimezoneConverter.convert_to_user_time(next_time, timezone)

        return success_response(
            {
                "next_notification_time": next_time.isoformat(),
                "local_time": local_time.isoformat(),
                "utc_time": next_time.isoformat(),
                "message": f"下次通知時間：{local_time.strftime('%Y-%m-%d %H:%M')} ({timezone})",
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid preview parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing notification time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法預覽通知時間")


@router.get("/preferences/timezones")
async def get_supported_timezones():
    """
    Get list of supported timezones

    Returns a list of commonly used IANA timezone identifiers
    for the timezone selector.
    """
    try:
        # Common timezones for the selector
        common_timezones = [
            {"value": "UTC", "label": "UTC", "offset": "+00:00"},
            {"value": "Asia/Taipei", "label": "台北 (Asia/Taipei)", "offset": "+08:00"},
            {"value": "Asia/Tokyo", "label": "東京 (Asia/Tokyo)", "offset": "+09:00"},
            {"value": "Asia/Shanghai", "label": "上海 (Asia/Shanghai)", "offset": "+08:00"},
            {"value": "Asia/Hong_Kong", "label": "香港 (Asia/Hong_Kong)", "offset": "+08:00"},
            {"value": "Asia/Singapore", "label": "新加坡 (Asia/Singapore)", "offset": "+08:00"},
            {"value": "America/New_York", "label": "紐約 (America/New_York)", "offset": "-05:00"},
            {
                "value": "America/Los_Angeles",
                "label": "洛杉磯 (America/Los_Angeles)",
                "offset": "-08:00",
            },
            {"value": "America/Chicago", "label": "芝加哥 (America/Chicago)", "offset": "-06:00"},
            {"value": "Europe/London", "label": "倫敦 (Europe/London)", "offset": "+00:00"},
            {"value": "Europe/Paris", "label": "巴黎 (Europe/Paris)", "offset": "+01:00"},
            {"value": "Europe/Berlin", "label": "柏林 (Europe/Berlin)", "offset": "+01:00"},
            {"value": "Australia/Sydney", "label": "雪梨 (Australia/Sydney)", "offset": "+11:00"},
            {
                "value": "Australia/Melbourne",
                "label": "墨爾本 (Australia/Melbourne)",
                "offset": "+11:00",
            },
        ]

        return success_response({"timezones": common_timezones, "total": len(common_timezones)})

    except Exception as e:
        logger.error(f"Error getting supported timezones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法載入時區列表")


@router.get("/preferences/status")
async def get_notification_status(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get notification scheduling status

    Returns information about the user's current notification scheduling
    status including next scheduled notification and job information.
    """
    try:
        supabase = SupabaseService()

        # Get user UUID
        user_id = await supabase.get_or_create_user(current_user["discord_id"])

        # Get dynamic scheduler
        dynamic_scheduler = get_dynamic_scheduler()

        if not dynamic_scheduler:
            return success_response({"scheduled": False, "message": "動態排程器未啟用"})

        # Get job information
        job_info = await dynamic_scheduler.get_user_job_info(user_id)

        if job_info:
            return success_response(
                {
                    "scheduled": True,
                    "job_id": job_info["job_id"],
                    "next_run_time": job_info["next_run_time"],
                    "message": "通知已排程",
                }
            )
        else:
            return success_response({"scheduled": False, "message": "無排程通知（可能已停用或尚未設定）"})

    except Exception as e:
        logger.error(f"Error getting notification status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法載入通知狀態")
