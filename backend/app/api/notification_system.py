"""
Notification System API

This module provides API endpoints for monitoring and managing the integrated
personalized notification system.

Requirements: All requirements integration monitoring
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.auth import get_current_user
from app.repositories.user import User
from app.services.notification_monitoring import get_notification_monitoring_service
from app.services.notification_system_integration import (
    get_notification_system_integration,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_notification_system_health():
    """
    Get comprehensive notification system health status.

    Returns:
        Dict: System health information across all components
    """
    try:
        integration_service = get_notification_system_integration()
        if not integration_service:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "Notification system integration not available",
                    "components": {},
                },
            )

        health = await integration_service.get_system_health()

        # Determine HTTP status code based on health
        status_code = 200
        if health.get("overall_status") == "unhealthy":
            status_code = 503
        elif health.get("overall_status") == "degraded":
            status_code = 200  # Still operational, just degraded

        return JSONResponse(status_code=status_code, content=health)

    except Exception as e:
        logger.error(f"Failed to get notification system health: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "components": {},
            },
        )


@router.get("/metrics")
async def get_notification_system_metrics():
    """
    Get current notification system metrics.

    Returns:
        Dict: Current system metrics and performance data
    """
    try:
        monitoring_service = get_notification_monitoring_service()
        if not monitoring_service:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Notification monitoring service not available",
                    "metrics": {},
                },
            )

        metrics = await monitoring_service.get_current_metrics()
        return JSONResponse(status_code=200, content=metrics)

    except Exception as e:
        logger.error(f"Failed to get notification system metrics: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "metrics": {},
            },
        )


@router.get("/metrics/history")
async def get_notification_metrics_history(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to retrieve")
):
    """
    Get historical notification system metrics.

    Args:
        hours: Number of hours of history to retrieve (1-24)

    Returns:
        List[Dict]: Historical metrics data
    """
    try:
        monitoring_service = get_notification_monitoring_service()
        if not monitoring_service:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Notification monitoring service not available",
                    "history": [],
                },
            )

        history = await monitoring_service.get_metrics_history(hours=hours)
        return JSONResponse(
            status_code=200,
            content={
                "history": history,
                "hours": hours,
                "total_records": len(history),
            },
        )

    except Exception as e:
        logger.error(f"Failed to get notification metrics history: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "history": [],
            },
        )


@router.get("/report")
async def get_notification_system_report():
    """
    Get comprehensive notification system report.

    Returns:
        Dict: Comprehensive system status and performance report
    """
    try:
        monitoring_service = get_notification_monitoring_service()
        if not monitoring_service:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Notification monitoring service not available",
                    "report": {},
                },
            )

        report = await monitoring_service.get_system_report()
        return JSONResponse(status_code=200, content=report)

    except Exception as e:
        logger.error(f"Failed to get notification system report: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "report": {},
            },
        )


@router.get("/user/{user_id}/status")
async def get_user_notification_status(
    user_id: str, current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive notification status for a specific user.

    Args:
        user_id: User ID to get status for
        current_user: Current authenticated user

    Returns:
        Dict: User's notification status and configuration
    """
    try:
        # Validate user ID format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Check if user can access this information
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        integration_service = get_notification_system_integration()
        if not integration_service:
            raise HTTPException(
                status_code=503, detail="Notification system integration not available"
            )

        status = await integration_service.get_user_notification_status(user_uuid)
        return JSONResponse(status_code=200, content=status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user notification status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/schedule")
async def schedule_user_notifications(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Manually schedule notifications for a user.

    Args:
        user_id: User ID to schedule notifications for
        current_user: Current authenticated user

    Returns:
        Dict: Scheduling result
    """
    try:
        # Validate user ID format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Check if user can access this information
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        integration_service = get_notification_system_integration()
        if not integration_service:
            raise HTTPException(
                status_code=503, detail="Notification system integration not available"
            )

        success = await integration_service.schedule_user_notifications(user_uuid)

        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Notifications scheduled successfully",
                    "user_id": user_id,
                },
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to schedule notifications",
                    "user_id": user_id,
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule user notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{user_id}/schedule")
async def cancel_user_notifications(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Cancel scheduled notifications for a user.

    Args:
        user_id: User ID to cancel notifications for
        current_user: Current authenticated user

    Returns:
        Dict: Cancellation result
    """
    try:
        # Validate user ID format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Check if user can access this information
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        integration_service = get_notification_system_integration()
        if not integration_service:
            raise HTTPException(
                status_code=503, detail="Notification system integration not available"
            )

        success = await integration_service.cancel_user_notifications(user_uuid)

        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Notifications cancelled successfully",
                    "user_id": user_id,
                },
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to cancel notifications",
                    "user_id": user_id,
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel user notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_system_resources():
    """
    Manually trigger system resource cleanup.

    This endpoint is typically used for maintenance operations.

    Returns:
        Dict: Cleanup results
    """
    try:
        integration_service = get_notification_system_integration()
        if not integration_service:
            raise HTTPException(
                status_code=503, detail="Notification system integration not available"
            )

        cleanup_results = await integration_service.cleanup_system_resources()

        status_code = 200 if cleanup_results.get("overall_success", False) else 500

        return JSONResponse(status_code=status_code, content=cleanup_results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup system resources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/test-notification")
async def send_test_notification(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Send a test notification to a user.

    Args:
        user_id: User ID to send test notification to
        current_user: Current authenticated user

    Returns:
        Dict: Test notification result
    """
    try:
        # Validate user ID format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Check if user can access this information
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        integration_service = get_notification_system_integration()
        if not integration_service:
            raise HTTPException(
                status_code=503, detail="Notification system integration not available"
            )

        # Send test notification
        results = await integration_service.send_user_notification(
            user_id=user_uuid, notification_type="test", subject="Test Notification", articles=None
        )

        # Analyze results
        successful_channels = [r.channel for r in results if r.success]
        failed_channels = [r.channel for r in results if not r.success]

        return JSONResponse(
            status_code=200,
            content={
                "success": len(successful_channels) > 0,
                "message": "Test notification sent",
                "user_id": user_id,
                "results": {
                    "successful_channels": successful_channels,
                    "failed_channels": failed_channels,
                    "total_channels": len(results),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
