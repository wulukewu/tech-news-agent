"""
Recommendation API Endpoints

This module provides API endpoints for managing recommended feeds,
including querying recommended feeds grouped by category and batch subscription.

Requirements: 2.1, 2.6, 4.1
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.core.errors import ServiceError
from app.schemas.recommendation import RecommendedFeedsResponse
from app.schemas.responses import SuccessResponse, success_response
from app.services.recommendation_service import RecommendationService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/feeds/recommended", response_model=SuccessResponse[RecommendedFeedsResponse])
async def get_recommended_feeds(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get all recommended feeds grouped by category

    Returns a list of recommended feeds sorted by priority, along with
    feeds grouped by category for display in collapsible sections.
    Includes subscription status for the current user.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        RecommendedFeedsResponse: Recommended feeds with category grouping

    Raises:
        HTTPException: 500 when database operation fails

    Requirements: 2.1, 4.1
    """
    try:
        supabase = SupabaseService()
        recommendation_service = RecommendationService(supabase.client)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Get recommended feeds with subscription status
        feeds = await recommendation_service.get_recommended_feeds(user_uuid)

        # Group feeds by category
        grouped_by_category: dict[str, list] = {}
        for feed in feeds:
            category = feed.category
            if category not in grouped_by_category:
                grouped_by_category[category] = []
            grouped_by_category[category].append(feed)

        logger.info(
            f"Retrieved {len(feeds)} recommended feeds for user {current_user['user_id']} "
            f"across {len(grouped_by_category)} categories"
        )

        return success_response(
            RecommendedFeedsResponse(
                feeds=feeds, grouped_by_category=grouped_by_category, total_count=len(feeds)
            )
        )

    except ServiceError as e:
        logger.error(
            f"Failed to get recommended feeds for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法取得推薦來源，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error getting recommended feeds for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")
