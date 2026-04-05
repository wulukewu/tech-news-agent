"""
Onboarding Pydantic Schemas

This module defines the Pydantic models for onboarding-related
API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime


class OnboardingStatus(BaseModel):
    """
    Onboarding status response model
    
    Used by GET /api/onboarding/status endpoint to return the user's
    current onboarding progress and state.
    """
    onboarding_completed: bool = Field(..., description="Whether user has completed the onboarding flow")
    onboarding_step: Optional[str] = Field(None, description="Current step in onboarding flow (welcome, recommendations, complete)")
    onboarding_skipped: bool = Field(..., description="Whether user skipped the onboarding flow")
    tooltip_tour_completed: bool = Field(..., description="Whether user has completed the tooltip tour")
    should_show_onboarding: bool = Field(..., description="Whether the onboarding modal should be displayed to the user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "onboarding_completed": False,
                "onboarding_step": "welcome",
                "onboarding_skipped": False,
                "tooltip_tour_completed": False,
                "should_show_onboarding": True
            }
        }
    )


class UpdateOnboardingProgressRequest(BaseModel):
    """
    Request model for updating onboarding progress
    
    Used by POST /api/onboarding/progress endpoint.
    """
    step: str = Field(..., description="Onboarding step (welcome, recommendations, complete)")
    completed: bool = Field(..., description="Whether the step is completed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step": "welcome",
                "completed": True
            }
        }
    )


class UserPreferences(BaseModel):
    """
    Complete user preferences model
    
    Represents the full user_preferences table record.
    """
    id: UUID = Field(..., description="Preference record UUID")
    user_id: UUID = Field(..., description="User UUID")
    onboarding_completed: bool = Field(default=False, description="Whether user has completed the onboarding flow")
    onboarding_step: Optional[str] = Field(None, description="Current step in onboarding flow")
    onboarding_skipped: bool = Field(default=False, description="Whether user skipped the onboarding flow")
    onboarding_started_at: Optional[datetime] = Field(None, description="Timestamp when user started onboarding")
    onboarding_completed_at: Optional[datetime] = Field(None, description="Timestamp when user completed onboarding")
    tooltip_tour_completed: bool = Field(default=False, description="Whether user has completed the tooltip tour")
    tooltip_tour_skipped: bool = Field(default=False, description="Whether user skipped the tooltip tour")
    preferred_language: str = Field(default='zh-TW', description="User preferred language code")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "onboarding_completed": False,
                "onboarding_step": "welcome",
                "onboarding_skipped": False,
                "onboarding_started_at": "2024-01-01T00:00:00Z",
                "onboarding_completed_at": None,
                "tooltip_tour_completed": False,
                "tooltip_tour_skipped": False,
                "preferred_language": "zh-TW",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )
