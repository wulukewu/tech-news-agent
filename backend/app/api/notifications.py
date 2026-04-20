"""
Notification API Endpoints

This module provides API endpoints for managing user notification settings
and preferences, including the new personalized notification frequency system.
"""

import logging
import zoneinfo
from datetime import datetime, timezone
from typing import Any, Optional

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
from app.schemas.notification_history import (
    CreateNotificationRecordRequest,
    NotificationChannelsResponse,
    NotificationHistoryResponse,
    NotificationStatsResponse,
    NotificationStatusesResponse,
)
from app.schemas.quiet_hours import (
    CreateDefaultQuietHoursRequest,
    QuietHoursSettings,
    QuietHoursStatusResponse,
    UpdateQuietHoursRequest,
)
from app.schemas.responses import SuccessResponse, success_response
from app.schemas.technical_depth import (
    ArticleDepthEstimateRequest,
    ArticleDepthEstimateResponse,
    NotificationFilterCheckRequest,
    NotificationFilterCheckResponse,
    TechnicalDepthFilteringStats,
    TechnicalDepthLevelsResponse,
    TechnicalDepthSettings,
    UpdateTechnicalDepthRequest,
)
from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
    UserNotificationPreferences,
)
from app.services.notification_settings_service import NotificationSettingsService
from app.services.preference_service import PreferenceService
from app.services.quiet_hours_service import QuietHoursService
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

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

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

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

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

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

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

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

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

        # Use the authenticated user's UUID directly
        user_id = current_user["user_id"]

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

        # Use the authenticated user's UUID directly
        user_id = current_user["user_id"]

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


@router.post("/preferences/reschedule")
async def reschedule_user_notification(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Manually trigger user notification rescheduling

    This endpoint allows users to manually trigger the rescheduling of their
    notifications if they appear as "not scheduled" in the frontend.
    """
    try:
        supabase = SupabaseService()

        # Use the authenticated user's UUID directly
        user_id = current_user["user_id"]

        # Get user preferences
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)

        preferences = await preference_service.get_user_preferences(user_id)

        if preferences.frequency == "disabled" or not preferences.dm_enabled:
            return success_response({"success": False, "message": "通知已停用，無需排程"})

        # Get notification system integration
        from app.services.notification_system_integration import get_notification_system_integration

        integration_service = get_notification_system_integration()

        if not integration_service:
            return success_response({"success": False, "message": "通知系統集成未初始化"})

        # Schedule the user notification
        await integration_service.schedule_user_notification(
            user_id, preferences.frequency, preferences.notification_time, preferences.timezone
        )

        logger.info(f"Successfully rescheduled notification for user {current_user['user_id']}")

        return success_response({"success": True, "message": "通知排程已更新"})

    except Exception as e:
        logger.error(f"Error rescheduling notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法更新通知排程")


# Quiet Hours API Endpoints


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


@router.get("/tech-depth", response_model=SuccessResponse[TechnicalDepthSettings])
async def get_tech_depth_settings(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get user's technical depth threshold settings

    Returns the user's technical depth filtering configuration including
    threshold level and enabled status.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        tech_depth_service = TechnicalDepthService()
        user_id = current_user["user_id"]  # Already a UUID object

        settings = await tech_depth_service.get_tech_depth_settings(user_id)

        logger.info(f"Retrieved technical depth settings for user {user_id}")

        return success_response(settings.to_dict())

    except Exception as e:
        logger.error(
            f"Error getting technical depth settings for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入技術深度設定")


@router.put("/tech-depth", response_model=SuccessResponse[TechnicalDepthSettings])
async def update_tech_depth_settings(
    updates: UpdateTechnicalDepthRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Update user's technical depth threshold settings

    Updates the user's technical depth filtering configuration. Only provided
    fields will be updated, others will remain unchanged.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        tech_depth_service = TechnicalDepthService()
        user_id = current_user["user_id"]  # Already a UUID object

        updated_settings = await tech_depth_service.update_tech_depth_settings(
            user_id=user_id, threshold=updates.threshold, enabled=updates.enabled
        )

        logger.info(f"Updated technical depth settings for user {user_id}")

        return success_response(updated_settings.to_dict())

    except ValueError as e:
        logger.warning(
            f"Validation error updating technical depth settings for user {current_user['user_id']}: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error updating technical depth settings for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法更新技術深度設定")


@router.get("/tech-depth/levels", response_model=SuccessResponse[TechnicalDepthLevelsResponse])
async def get_tech_depth_levels():
    """
    Get available technical depth levels

    Returns all available technical depth levels with descriptions
    and numeric values for comparison.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        levels = TechnicalDepthService.get_available_levels()

        response = TechnicalDepthLevelsResponse(levels=levels)

        return success_response(response.dict())

    except Exception as e:
        logger.error(f"Error getting technical depth levels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法載入技術深度等級")


@router.get("/tech-depth/stats", response_model=SuccessResponse[TechnicalDepthFilteringStats])
async def get_tech_depth_filtering_stats(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get technical depth filtering statistics

    Returns statistics about how technical depth filtering affects
    notifications for the current user.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        tech_depth_service = TechnicalDepthService()
        user_id = current_user["user_id"]  # Already a UUID object

        stats = await tech_depth_service.get_filtering_stats(user_id)

        logger.info(f"Retrieved technical depth filtering stats for user {user_id}")

        return success_response(stats)

    except Exception as e:
        user_id_str = str(current_user.get("user_id", "unknown"))
        logger.error(
            f"Error getting technical depth filtering stats for user {user_id_str}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入篩選統計資料")


@router.post("/tech-depth/estimate", response_model=SuccessResponse[ArticleDepthEstimateResponse])
async def estimate_article_tech_depth(
    request: ArticleDepthEstimateRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Estimate technical depth of an article

    Analyzes the provided article content and estimates its technical
    depth level using heuristic-based analysis.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        estimated_depth = TechnicalDepthService.estimate_article_depth(
            content=request.content, title=request.title
        )

        response = ArticleDepthEstimateResponse(
            estimated_depth=estimated_depth,
            confidence=0.7,  # Placeholder confidence score
            reasoning=f"基於內容關鍵字分析，估計為 {estimated_depth} 等級",
        )

        logger.info(
            f"Estimated article depth: {estimated_depth} for user {current_user['user_id']}"
        )

        return success_response(response.dict())

    except Exception as e:
        logger.error(f"Error estimating article technical depth: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法分析文章技術深度")


@router.post(
    "/tech-depth/check-filter", response_model=SuccessResponse[NotificationFilterCheckResponse]
)
async def check_notification_filter(
    request: NotificationFilterCheckRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Check if notification should be sent based on technical depth

    Checks whether a notification should be sent for an article
    based on the user's technical depth filtering settings.
    """
    try:
        from app.services.technical_depth_service import TechnicalDepthService

        tech_depth_service = TechnicalDepthService()
        user_id = current_user["user_id"]  # Already a UUID object

        should_send, reason = await tech_depth_service.should_send_notification(
            user_id=user_id, article_tech_depth=request.article_tech_depth
        )

        user_settings = await tech_depth_service.get_tech_depth_settings(user_id)

        response = NotificationFilterCheckResponse(
            should_send=should_send, reason=reason, user_settings=user_settings.to_dict()
        )

        logger.info(f"Notification filter check for user {user_id}: {should_send} - {reason}")

        return success_response(response.dict())

    except Exception as e:
        logger.error(
            f"Error checking notification filter for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法檢查通知篩選條件")


# Notification History API Endpoints


@router.get("/history", response_model=SuccessResponse[NotificationHistoryResponse])
async def get_notification_history(
    page: int = 1,
    page_size: int = 50,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    days_back: Optional[int] = None,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get notification delivery history

    Returns the user's notification delivery history with pagination
    and filtering options.
    """
    try:
        from app.services.notification_history_service import NotificationHistoryService

        history_service = NotificationHistoryService()
        user_id = current_user["user_id"]  # Already a UUID object

        # Calculate offset
        offset = (page - 1) * page_size

        # Get history records
        records, total_count = await history_service.get_notification_history(
            user_id=user_id,
            limit=page_size,
            offset=offset,
            channel=channel,
            status=status,
            days_back=days_back,
        )

        # Convert to response format
        record_dicts = [record.to_dict() for record in records]
        has_more = offset + len(records) < total_count

        response = NotificationHistoryResponse(
            records=record_dicts,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

        logger.info(f"Retrieved notification history for user {user_id}: {len(records)} records")

        return success_response(response.dict())

    except ValueError as e:
        logger.warning(
            f"Validation error getting notification history for user {current_user['user_id']}: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error getting notification history for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入通知歷史記錄")


@router.get("/history/stats", response_model=SuccessResponse[NotificationStatsResponse])
async def get_notification_stats(
    days_back: int = 30, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get notification statistics

    Returns statistics about notification delivery for the specified time period.
    """
    try:
        from app.services.notification_history_service import NotificationHistoryService

        history_service = NotificationHistoryService()
        user_id = current_user["user_id"]  # Already a UUID object

        stats = await history_service.get_notification_stats(user_id, days_back)

        response = NotificationStatsResponse(**stats)

        logger.info(
            f"Retrieved notification stats for user {user_id}: {stats['total_notifications']} total"
        )

        return success_response(response.dict())

    except Exception as e:
        logger.error(
            f"Error getting notification stats for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法載入通知統計資料")


@router.post("/history/record", response_model=SuccessResponse[dict])
async def create_notification_record(
    request: CreateNotificationRecordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Create a notification history record

    This endpoint is typically used by the notification system to record
    delivery attempts.
    """
    try:
        from app.services.notification_history_service import NotificationHistoryService

        history_service = NotificationHistoryService()
        user_id = current_user["user_id"]  # Already a UUID object

        record = await history_service.record_notification(
            user_id=user_id,
            channel=request.channel,
            status=request.status,
            content=request.content,
            feed_source=request.feed_source,
            error_message=request.error_message,
            sent_at=request.sent_at,
        )

        logger.info(f"Created notification record for user {user_id}: {record.id}")

        return success_response(record.to_dict())

    except ValueError as e:
        logger.warning(
            f"Validation error creating notification record for user {current_user['user_id']}: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error creating notification record for user {current_user['user_id']}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法創建通知記錄")


@router.get("/history/channels", response_model=SuccessResponse[NotificationChannelsResponse])
async def get_notification_channels():
    """
    Get available notification channels

    Returns all available notification delivery channels.
    """
    try:
        from app.services.notification_history_service import NotificationHistoryService

        channels = NotificationHistoryService.get_available_channels()

        response = NotificationChannelsResponse(channels=channels)

        return success_response(response.dict())

    except Exception as e:
        logger.error(f"Error getting notification channels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法載入通知管道列表")


@router.get("/history/statuses", response_model=SuccessResponse[NotificationStatusesResponse])
async def get_notification_statuses():
    """
    Get available notification statuses

    Returns all available notification delivery statuses.
    """
    try:
        from app.services.notification_history_service import NotificationHistoryService

        statuses = NotificationHistoryService.get_available_statuses()

        response = NotificationStatusesResponse(statuses=statuses)

        return success_response(response.dict())

    except Exception as e:
        logger.error(f"Error getting notification statuses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="無法載入通知狀態列表")
