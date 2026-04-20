"""
Quiet Hours Schema Definitions

This module defines Pydantic schemas for quiet hours API endpoints.
"""

from datetime import time
from typing import List, Optional

from pydantic import BaseModel, Field


class QuietHoursSettings(BaseModel):
    """Quiet hours settings response model."""

    id: Optional[str] = None
    user_id: Optional[str] = None
    start_time: str = Field(..., description="Start time in HH:MM:SS format")
    end_time: str = Field(..., description="End time in HH:MM:SS format")
    timezone: str = Field(..., description="IANA timezone identifier")
    weekdays: List[int] = Field(..., description="List of weekdays (1=Monday, 7=Sunday)")
    enabled: bool = Field(..., description="Whether quiet hours are enabled")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "e43dfb57-2326-481d-826d-987c5fb1bda8",
                "user_id": "1de9880b-47e4-450c-83a0-46ec25b84790",
                "start_time": "22:00:00",
                "end_time": "08:00:00",
                "timezone": "Asia/Taipei",
                "weekdays": [1, 2, 3, 4, 5, 6, 7],
                "enabled": False,
                "created_at": "2026-04-20T15:09:37.379034+00:00",
                "updated_at": "2026-04-20T15:09:37.379034+00:00",
            }
        }


class UpdateQuietHoursRequest(BaseModel):
    """Request model for updating quiet hours settings."""

    start_time: Optional[time] = Field(None, description="Start time for quiet hours")
    end_time: Optional[time] = Field(None, description="End time for quiet hours")
    timezone: Optional[str] = Field(None, description="IANA timezone identifier")
    weekdays: Optional[List[int]] = Field(None, description="List of weekdays (1=Monday, 7=Sunday)")
    enabled: Optional[bool] = Field(None, description="Whether quiet hours are enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "22:00:00",
                "end_time": "08:00:00",
                "timezone": "Asia/Taipei",
                "weekdays": [1, 2, 3, 4, 5, 6, 7],
                "enabled": True,
            }
        }


class QuietHoursStatusResponse(BaseModel):
    """Response model for quiet hours status check."""

    is_in_quiet_hours: bool
    quiet_hours: Optional[dict] = None
    next_notification_time: Optional[str] = None
    current_time: str
    message: str


class CreateDefaultQuietHoursRequest(BaseModel):
    """Request model for creating default quiet hours."""

    timezone: str = Field(default="UTC", description="IANA timezone identifier")

    class Config:
        json_schema_extra = {"example": {"timezone": "Asia/Taipei"}}
