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
from app.schemas.notification import (
    NotificationSettings,
    UpdateNotificationSettingsRequest,
)
from app.schemas.responses import SuccessResponse, success_response
from app.services.notification_settings_service import NotificationSettingsService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


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


# New Personalized Notification Frequency Endpoints
