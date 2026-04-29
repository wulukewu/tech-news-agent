"""
Notification API Endpoints

This module provides API endpoints for managing user notification settings
and preferences, including the new personalized notification frequency system.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.schemas.notification_history import (
    CreateNotificationRecordRequest,
    NotificationChannelsResponse,
    NotificationHistoryResponse,
    NotificationStatsResponse,
    NotificationStatusesResponse,
)
from app.schemas.responses import SuccessResponse, success_response

logger = logging.getLogger(__name__)

router = APIRouter()


router = APIRouter()


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


# ── Proactive Recommendation Frequency ───────────────────────────────────────

PROACTIVE_FREQUENCY_OPTIONS = {
    "daily": 20,  # ~every day (20h cooldown)
    "every_two_days": 44,
    "weekly": 164,
}
