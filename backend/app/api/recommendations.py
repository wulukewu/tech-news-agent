"""
Recommendation API Endpoints

This module provides API endpoints for managing recommended feeds and
personalized article recommendations based on user ratings.

Requirements: 2.1, 2.6, 4.1, 3.1-3.10
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.core.errors import ServiceError
from app.repositories.article import ArticleRepository
from app.repositories.feed import FeedRepository
from app.repositories.reading_list import ReadingListRepository
from app.repositories.user_subscription import UserSubscriptionRepository
from app.schemas.recommendation import (
    ArticleRecommendationsResponse,
    DismissRecommendationRequest,
    RecommendationInteraction,
    RecommendedFeedsResponse,
    RefreshRecommendationsRequest,
)
from app.schemas.responses import SuccessResponse, success_response
from app.services.article_recommendation_service import ArticleRecommendationService
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

        # Initialize repositories
        feed_repo = FeedRepository(supabase.client)
        user_subscription_repo = UserSubscriptionRepository(supabase.client)

        # Initialize service
        recommendation_service = RecommendationService(feed_repo, user_subscription_repo)

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


@router.get("/v1/recommendations", response_model=SuccessResponse[ArticleRecommendationsResponse])
async def get_article_recommendations(
    limit: int = 10, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get personalized article recommendations based on user ratings

    Validates: Requirements 3.1, 3.2, 3.6
    """
    try:
        supabase = SupabaseService()

        # Initialize repositories
        article_repo = ArticleRepository(supabase.client)
        reading_list_repo = ReadingListRepository(supabase.client)

        # Initialize service
        recommendation_service = ArticleRecommendationService(article_repo, reading_list_repo)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Get recommendations
        recommendations = await recommendation_service.get_recommendations(user_uuid, limit)

        logger.info(
            f"Retrieved {len(recommendations.recommendations)} recommendations for user {current_user['user_id']}"
        )

        return success_response(recommendations)

    except ServiceError as e:
        logger.error(
            f"Failed to get article recommendations for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="載入推薦時發生錯誤")
    except Exception as e:
        logger.error(
            f"Unexpected error getting article recommendations for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post(
    "/v1/recommendations/refresh", response_model=SuccessResponse[ArticleRecommendationsResponse]
)
async def refresh_article_recommendations(
    request: RefreshRecommendationsRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Refresh recommendations to generate new suggestions

    Validates: Requirement 3.5
    """
    try:
        supabase = SupabaseService()

        # Initialize repositories
        article_repo = ArticleRepository(supabase.client)
        reading_list_repo = ReadingListRepository(supabase.client)

        # Initialize service
        recommendation_service = ArticleRecommendationService(article_repo, reading_list_repo)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Refresh recommendations
        recommendations = await recommendation_service.refresh_recommendations(user_uuid, request)

        logger.info(
            f"Refreshed recommendations for user {current_user['user_id']}, got {len(recommendations.recommendations)} new recommendations"
        )

        return success_response(recommendations)

    except ServiceError as e:
        logger.error(
            f"Failed to refresh recommendations for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="重新載入推薦失敗")
    except Exception as e:
        logger.error(
            f"Unexpected error refreshing recommendations for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/v1/recommendations/dismiss")
async def dismiss_recommendation(
    request: DismissRecommendationRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Dismiss a recommendation

    Validates: Requirement 3.7
    """
    try:
        supabase = SupabaseService()

        # Initialize repositories
        article_repo = ArticleRepository(supabase.client)
        reading_list_repo = ReadingListRepository(supabase.client)

        # Initialize service
        recommendation_service = ArticleRecommendationService(article_repo, reading_list_repo)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Dismiss recommendation
        await recommendation_service.dismiss_recommendation(user_uuid, request)

        logger.info(
            f"Dismissed recommendation {request.recommendation_id} for user {current_user['user_id']}"
        )

        return success_response({"message": "推薦已忽略"})

    except ServiceError as e:
        logger.error(
            f"Failed to dismiss recommendation for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="忽略推薦失敗")
    except Exception as e:
        logger.error(
            f"Unexpected error dismissing recommendation for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/v1/recommendations/track")
async def track_recommendation_interaction(
    interaction: RecommendationInteraction, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Track recommendation interaction for analytics

    Validates: Requirement 3.8
    """
    try:
        supabase = SupabaseService()

        # Initialize repositories
        article_repo = ArticleRepository(supabase.client)
        reading_list_repo = ReadingListRepository(supabase.client)

        # Initialize service
        recommendation_service = ArticleRecommendationService(article_repo, reading_list_repo)

        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])

        # Track interaction
        await recommendation_service.track_interaction(user_uuid, interaction)

        return success_response({"message": "互動已記錄"})

    except Exception as e:
        logger.warning(
            f"Failed to track recommendation interaction for user {current_user['user_id']}: {e!s}"
        )
        # Don't fail the request for analytics tracking errors
        return success_response({"message": "互動記錄失敗，但不影響功能"})
