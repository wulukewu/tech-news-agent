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

logger = logging.getLogger(__name__)

router = APIRouter()


router = APIRouter()


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
