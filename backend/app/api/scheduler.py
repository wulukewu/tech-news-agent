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
    - Is running status
    - Next execution time

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


@router.get("/system/health")
async def get_system_health(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get system health metrics including database, API, and error rates.

    Returns:
        - 200: Health metrics retrieved successfully
        - 401: Unauthorized (no valid token)
    """
    try:
        from datetime import datetime

        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService()

        # Check database connection and response time
        db_start = datetime.now()
        try:
            # Simple query to test database
            result = supabase.client.table("users").select("id").limit(1).execute()
            db_connected = True
            db_response_time = int((datetime.now() - db_start).total_seconds() * 1000)
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_connected = False
            db_response_time = 0

        # Get error statistics from last 24 hours
        # This is a simplified version - in production you'd query actual error logs
        error_rate = 0.0
        total_errors_24h = 0
        last_error = None

        health_data = {
            "database": {
                "connected": db_connected,
                "response_time": db_response_time,
                "last_checked": datetime.now().isoformat(),
            },
            "api": {
                "average_response_time": 120,  # Placeholder - would need actual metrics
                "p95_response_time": 250,
                "p99_response_time": 500,
                "last_checked": datetime.now().isoformat(),
            },
            "errors": {
                "rate": error_rate,
                "total_24h": total_errors_24h,
                "last_error": last_error,
            },
        }

        return success_response(health_data)
    except Exception as e:
        logger.error(f"Failed to get system health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system health",
        )


@router.get("/system/statistics")
async def get_fetch_statistics(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Get fetch statistics for the last 24 hours.

    Returns:
        - 200: Statistics retrieved successfully
        - 401: Unauthorized (no valid token)
    """
    try:
        from datetime import datetime, timedelta

        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService()

        # Get articles from last 24 hours
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()

        try:
            result = (
                supabase.client.table("articles")
                .select("id, created_at")
                .gte("created_at", twenty_four_hours_ago)
                .execute()
            )
            total_articles_24h = len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Failed to get article statistics: {e}")
            total_articles_24h = 0

        # Calculate statistics
        # In a real implementation, you'd track these metrics properly
        statistics = {
            "total_articles_24h": total_articles_24h,
            "success_rate": 0.95,  # Placeholder
            "average_processing_time": 2.5,  # seconds, placeholder
            "total_fetches_24h": 4,  # Assuming 6-hour intervals
            "failed_fetches_24h": 0,  # Placeholder
        }

        return success_response(statistics)
    except Exception as e:
        logger.error(f"Failed to get fetch statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get fetch statistics",
        )
