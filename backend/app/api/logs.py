"""
Frontend Logs API Endpoint
Task 9.3: Create backend endpoint for frontend logs

This module provides an API endpoint to receive batched logs from the frontend.

Requirements: 5.4
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.logger import get_logger

router = APIRouter(prefix="/api", tags=["logs"])
logger = get_logger(__name__)


class FrontendLogEntry(BaseModel):
    """Frontend log entry model"""

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    level: str = Field(..., description="Log level (DEBUG, INFO, WARN, ERROR)")
    message: str = Field(..., description="Log message")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    userAgent: str | None = Field(None, description="User agent string")
    url: str | None = Field(None, description="Page URL")
    userId: str | None = Field(None, description="User ID")


class FrontendLogsRequest(BaseModel):
    """Request model for frontend logs"""

    logs: list[FrontendLogEntry] = Field(..., description="Batch of log entries")


class FrontendLogsResponse(BaseModel):
    """Response model for frontend logs"""

    success: bool = Field(..., description="Whether logs were received successfully")
    received_count: int = Field(..., description="Number of logs received")
    message: str = Field(..., description="Response message")


@router.post("/logs", response_model=FrontendLogsResponse)
async def receive_frontend_logs(
    request_body: FrontendLogsRequest, request: Request
) -> FrontendLogsResponse:
    """
    Receive batched logs from frontend

    This endpoint receives batched logs from the frontend logger and processes them
    through the centralized logging system.

    **Validates: Requirement 5.4**

    Args:
        request_body: Batch of frontend log entries
        request: FastAPI request object for context

    Returns:
        FrontendLogsResponse with success status and count

    Raises:
        HTTPException: If log processing fails
    """
    try:
        # Get client IP for logging
        client_ip = request.client.host if request.client else "unknown"

        # Process each log entry
        for log_entry in request_body.logs:
            # Parse log level
            level = log_entry.level.upper()

            # Build log context
            log_context = {
                "source": "frontend",
                "client_ip": client_ip,
                "user_agent": log_entry.userAgent,
                "url": log_entry.url,
                "user_id": log_entry.userId,
                "frontend_timestamp": log_entry.timestamp,
            }

            # Add custom context if provided
            if log_entry.context:
                log_context["frontend_context"] = log_entry.context

            # Log to backend logger with appropriate level
            if level == "DEBUG":
                logger.debug(f"[Frontend] {log_entry.message}", extra=log_context)
            elif level == "INFO":
                logger.info(f"[Frontend] {log_entry.message}", extra=log_context)
            elif level == "WARN":
                logger.warning(f"[Frontend] {log_entry.message}", extra=log_context)
            elif level == "ERROR":
                logger.error(f"[Frontend] {log_entry.message}", extra=log_context)
            else:
                # Default to info for unknown levels
                logger.info(f"[Frontend] {log_entry.message}", extra=log_context)

        # Return success response
        return FrontendLogsResponse(
            success=True,
            received_count=len(request_body.logs),
            message=f"Successfully received {len(request_body.logs)} log entries",
        )

    except Exception as e:
        logger.error(
            f"Error processing frontend logs: {e!s}",
            extra={"error": str(e), "client_ip": client_ip},
        )
        raise HTTPException(status_code=500, detail="Failed to process frontend logs")


@router.get("/logs/health")
async def logs_health_check() -> dict[str, str]:
    """
    Health check endpoint for logs API

    Returns:
        Dict with status message
    """
    return {
        "status": "healthy",
        "service": "frontend-logs",
        "timestamp": datetime.utcnow().isoformat(),
    }
