"""
Onboarding API Endpoints

This module provides API endpoints for managing user onboarding progress,
including status queries, progress updates, completion, skip, and reset functionality.

Requirements: 1.4, 1.5, 1.6, 10.3, 10.6
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.core.errors import ServiceError
from app.schemas.onboarding import OnboardingStatus, UpdateOnboardingProgressRequest
from app.schemas.responses import SuccessResponse, success_response
from app.services.onboarding_service import OnboardingService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/onboarding/status", response_model=SuccessResponse[OnboardingStatus])
async def get_onboarding_status(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get the current user's onboarding status

    Returns the user's onboarding progress, including completion status,
    current step, skip status, and whether the onboarding modal should be shown.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        OnboardingStatus: Current onboarding state

    Raises:
        HTTPException: 500 when database operation fails

    Requirements: 1.4, 10.3, 10.4
    """
    try:
        supabase = SupabaseService()
        onboarding_service = OnboardingService(supabase.client)

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

        # Get onboarding status
        status = await onboarding_service.get_onboarding_status(user_uuid)

        logger.info(
            f"Retrieved onboarding status for user {current_user['user_id']}: "
            f"completed={status.onboarding_completed}, should_show={status.should_show_onboarding}"
        )

        return success_response(status)

    except ServiceError as e:
        logger.error(
            f"Failed to get onboarding status for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法取得引導進度，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error getting onboarding status for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/onboarding/progress")
async def update_onboarding_progress(
    request: UpdateOnboardingProgressRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update the user's onboarding progress

    Records the user's current step in the onboarding flow and whether
    the step is completed. Sets onboarding_started_at on first step.

    Args:
        request: Request containing step name and completion status
        current_user: Current authenticated user (injected by dependency)

    Returns:
        Success message

    Raises:
        HTTPException: 422 when request body is invalid (handled by Pydantic)
        HTTPException: 500 when database operation fails

    Requirements: 1.4, 10.3
    """
    try:
        supabase = SupabaseService()
        onboarding_service = OnboardingService(supabase.client)

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

        # Update progress
        await onboarding_service.update_onboarding_progress(
            user_uuid, request.step, request.completed
        )

        logger.info(
            f"Updated onboarding progress for user {current_user['user_id']}: "
            f"step={request.step}, completed={request.completed}"
        )

        return success_response({"message": "引導進度已更新"})

    except ServiceError as e:
        logger.error(
            f"Failed to update onboarding progress for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法更新引導進度，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error updating onboarding progress for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/onboarding/complete")
async def mark_onboarding_completed(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Mark the user's onboarding as completed

    Sets onboarding_completed to true and records the completion timestamp.
    After this, the onboarding modal will not be shown again.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        Success message

    Raises:
        HTTPException: 500 when database operation fails

    Requirements: 1.5, 10.3
    """
    try:
        supabase = SupabaseService()
        onboarding_service = OnboardingService(supabase.client)

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

        # Mark as completed
        await onboarding_service.mark_onboarding_completed(user_uuid)

        logger.info(f"Marked onboarding as completed for user {current_user['user_id']}")

        return success_response({"message": "引導已完成"})

    except ServiceError as e:
        logger.error(
            f"Failed to mark onboarding completed for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法完成引導，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error marking onboarding completed for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/onboarding/skip")
async def mark_onboarding_skipped(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Mark the user's onboarding as skipped

    Sets onboarding_skipped to true so the onboarding modal won't be shown again
    unless the user manually triggers it from settings.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        Success message

    Raises:
        HTTPException: 500 when database operation fails

    Requirements: 1.6, 1.7, 10.3
    """
    try:
        supabase = SupabaseService()
        onboarding_service = OnboardingService(supabase.client)

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

        # Mark as skipped
        await onboarding_service.mark_onboarding_skipped(user_uuid)

        logger.info(f"Marked onboarding as skipped for user {current_user['user_id']}")

        return success_response({"message": "已跳過引導"})

    except ServiceError as e:
        logger.error(
            f"Failed to mark onboarding skipped for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法跳過引導，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error marking onboarding skipped for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")


@router.post("/onboarding/reset")
async def reset_onboarding(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Reset the user's onboarding state

    Clears all onboarding flags and timestamps, allowing the user to go through
    the onboarding flow again. Typically triggered from user settings.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        Success message

    Raises:
        HTTPException: 500 when database operation fails

    Requirements: 10.6, 10.7
    """
    try:
        supabase = SupabaseService()
        onboarding_service = OnboardingService(supabase.client)

        # Use the authenticated user's UUID directly
        user_uuid = current_user["user_id"]

        # Reset onboarding
        await onboarding_service.reset_onboarding(user_uuid)

        logger.info(f"Reset onboarding for user {current_user['user_id']}")

        return success_response({"message": "引導已重置"})

    except ServiceError as e:
        logger.error(
            f"Failed to reset onboarding for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="無法重置引導，請稍後再試")
    except Exception as e:
        logger.error(
            f"Unexpected error resetting onboarding for user {current_user['user_id']}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")
