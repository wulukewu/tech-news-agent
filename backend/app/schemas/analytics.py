"""
Analytics Pydantic Schemas

This module defines the Pydantic models for analytics-related
API requests and responses.

Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LogAnalyticsEventRequest(BaseModel):
    """
    Request model for logging analytics events

    Used by POST /api/analytics/event endpoint.
    """

    event_type: str = Field(
        ..., description="Type of event (onboarding_started, step_completed, etc.)"
    )
    event_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional event metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "onboarding_started",
                "event_data": {"source": "web", "timestamp": "2024-01-01T00:00:00Z"},
            }
        }
    )


class AnalyticsEvent(BaseModel):
    """
    Analytics event model

    Represents a single analytics event record.
    """

    id: UUID = Field(..., description="Event UUID")
    user_id: UUID = Field(..., description="User UUID")
    event_type: str = Field(..., description="Event type")
    event_data: dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    created_at: datetime = Field(..., description="Event timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "event_type": "step_completed",
                "event_data": {"step": "welcome", "time_spent_seconds": 30},
                "created_at": "2024-01-01T00:00:00Z",
            }
        },
    )


class OnboardingCompletionRateResponse(BaseModel):
    """
    Response model for onboarding completion rate

    Used by GET /api/analytics/onboarding/completion-rate endpoint.
    """

    completion_rate: float = Field(..., description="Completion rate as percentage (0-100)")
    total_users: int = Field(..., description="Total number of users who started onboarding")
    completed_users: int = Field(..., description="Number of users who completed onboarding")
    skipped_users: int = Field(..., description="Number of users who skipped onboarding")
    start_date: datetime = Field(..., description="Start date of the analysis period")
    end_date: datetime = Field(..., description="End date of the analysis period")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "completion_rate": 75.5,
                "total_users": 100,
                "completed_users": 75,
                "skipped_users": 15,
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
            }
        }
    )


class DropOffRatesResponse(BaseModel):
    """
    Response model for drop-off rates at each onboarding step

    Used by GET /api/analytics/onboarding/drop-off endpoint.
    """

    drop_off_by_step: dict[str, float] = Field(
        ..., description="Drop-off rate for each step as percentage (0-100)"
    )
    total_started: int = Field(..., description="Total number of users who started onboarding")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "drop_off_by_step": {"welcome": 10.5, "recommendations": 15.2, "complete": 5.0},
                "total_started": 100,
            }
        }
    )


class AverageTimePerStepResponse(BaseModel):
    """
    Response model for average time spent per onboarding step

    Used by GET /api/analytics/onboarding/average-time endpoint.
    """

    average_time_by_step: dict[str, float] = Field(
        ..., description="Average time in seconds for each step"
    )
    total_completions: int = Field(..., description="Total number of completed onboarding flows")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "average_time_by_step": {
                    "welcome": 45.5,
                    "recommendations": 120.3,
                    "complete": 30.0,
                },
                "total_completions": 75,
            }
        }
    )
