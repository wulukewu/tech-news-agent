"""
Scheduler API endpoints for manual trigger and status monitoring.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.schemas.responses import success_response
from app.tasks.scheduler import background_fetch_job, get_scheduler_health

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scheduler/trigger")
async def trigger_scheduler_manually(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Manually trigger the background fetch job.

    This endpoint allows authenticated users to manually trigger the scheduler
    to fetch new articles immediately, without waiting for the scheduled time.

    The job runs asynchronously in the background and returns immediately.

    Returns:
        - 202: Job triggered successfully
        - 401: Unauthorized (no valid token)
    """
    try:
        logger.info(f"Manual scheduler trigger requested by user {current_user['discord_id']}")

        # Import asyncio to run the job in the background
        import asyncio

        # Create a background task to run the job
        asyncio.create_task(background_fetch_job())

        return success_response(
            {
                "status": "triggered",
                "message": "Scheduler job has been triggered manually and is running in the background.",
            }
        )
    except Exception as e:
        logger.error(f"Failed to trigger scheduler manually: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger scheduler"
        )


@router.get("/scheduler/status")
async def get_scheduler_status(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get the current status of the scheduler.

    Returns detailed information about the last execution, including:
    - Last execution time
    - Articles processed
    - Failed operations
    - Health status

    Returns:
        - 200: Status retrieved successfully
        - 401: Unauthorized (no valid token)
    """
    try:
        health_data = await get_scheduler_health()

        return success_response(health_data)
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status",
        )
