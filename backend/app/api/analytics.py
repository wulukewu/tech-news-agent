"""
Analytics API Endpoints

This module provides API endpoints for tracking and analyzing user onboarding events,
including event logging, completion rates, drop-off rates, and average time per step.

Requirements: 14.1, 14.6, 14.7
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import logging

from app.api.auth import get_current_user
from app.services.supabase_service import SupabaseService
from app.services.analytics_service import AnalyticsService, AnalyticsServiceError
from app.schemas.analytics import (
    LogAnalyticsEventRequest,
    OnboardingCompletionRateResponse,
    DropOffRatesResponse,
    AverageTimePerStepResponse
)
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analytics/event")
@limiter.limit("100/minute")
async def log_analytics_event(
    request: LogAnalyticsEventRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log an analytics event
    
    Records user actions during onboarding for later analysis.
    Rate limited to prevent abuse (100 events per minute per user).
    
    Args:
        request: Request containing event_type and event_data
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 422 when request body is invalid (handled by Pydantic)
        HTTPException: 429 when rate limit exceeded
        HTTPException: 500 when database operation fails
        
    Requirements: 14.1, 14.7
    """
    try:
        supabase = SupabaseService()
        analytics_service = AnalyticsService(supabase.client)
        
        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])
        
        # Log the event
        await analytics_service.log_event(
            user_uuid,
            request.event_type,
            request.event_data
        )
        
        logger.info(
            f"Logged analytics event for user {current_user['user_id']}: "
            f"type={request.event_type}"
        )
        
        return {"message": "事件已記錄"}
        
    except AnalyticsServiceError as e:
        logger.error(
            f"Failed to log analytics event for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="無法記錄事件，請稍後再試"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error logging analytics event for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="系統錯誤，請稍後再試"
        )


@router.get("/analytics/onboarding/completion-rate", response_model=OnboardingCompletionRateResponse)
async def get_onboarding_completion_rate(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get onboarding completion rate for a time period
    
    Calculates the percentage of users who completed onboarding out of
    those who started it within the specified time period.
    
    Args:
        days: Number of days to analyze (default: 30, max: 365)
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        OnboardingCompletionRateResponse: Completion statistics
        
    Raises:
        HTTPException: 500 when database operation fails
        
    Requirements: 14.6
    """
    try:
        supabase = SupabaseService()
        analytics_service = AnalyticsService(supabase.client)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get completion rate
        result = await analytics_service.get_onboarding_completion_rate(
            start_date,
            end_date
        )
        
        logger.info(
            f"Retrieved completion rate for user {current_user['user_id']}: "
            f"{result.completion_rate}% ({result.completed_users}/{result.total_users})"
        )
        
        return result
        
    except AnalyticsServiceError as e:
        logger.error(
            f"Failed to get completion rate for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="無法取得完成率，請稍後再試"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting completion rate for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="系統錯誤，請稍後再試"
        )


@router.get("/analytics/onboarding/drop-off", response_model=DropOffRatesResponse)
async def get_drop_off_rates(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get drop-off rates at each onboarding step
    
    Identifies where users are abandoning the onboarding flow,
    helping to pinpoint areas for improvement.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        DropOffRatesResponse: Drop-off rates per step
        
    Raises:
        HTTPException: 500 when database operation fails
        
    Requirements: 14.7
    """
    try:
        supabase = SupabaseService()
        analytics_service = AnalyticsService(supabase.client)
        
        # Get drop-off rates
        result = await analytics_service.get_drop_off_rates()
        
        logger.info(
            f"Retrieved drop-off rates for user {current_user['user_id']}: "
            f"{len(result.drop_off_by_step)} steps analyzed"
        )
        
        return result
        
    except AnalyticsServiceError as e:
        logger.error(
            f"Failed to get drop-off rates for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="無法取得流失率，請稍後再試"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting drop-off rates for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="系統錯誤，請稍後再試"
        )


@router.get("/analytics/onboarding/average-time", response_model=AverageTimePerStepResponse)
async def get_average_time_per_step(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get average time spent on each onboarding step
    
    Provides insights into which steps take the most time,
    helping to optimize the onboarding flow.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        AverageTimePerStepResponse: Average time per step in seconds
        
    Raises:
        HTTPException: 500 when database operation fails
        
    Requirements: 14.5
    """
    try:
        supabase = SupabaseService()
        analytics_service = AnalyticsService(supabase.client)
        
        # Get average time per step
        result = await analytics_service.get_average_time_per_step()
        
        logger.info(
            f"Retrieved average time per step for user {current_user['user_id']}: "
            f"{len(result.average_time_by_step)} steps analyzed"
        )
        
        return result
        
    except AnalyticsServiceError as e:
        logger.error(
            f"Failed to get average time per step for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="無法取得平均時間，請稍後再試"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting average time per step for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="系統錯誤，請稍後再試"
        )
