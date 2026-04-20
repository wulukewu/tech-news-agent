"""
Technical Depth Schema Definitions

This module defines Pydantic schemas for technical depth API endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TechnicalDepthSettings(BaseModel):
    """Technical depth settings response model."""

    user_id: str
    threshold: str = Field(..., description="Technical depth threshold level")
    enabled: bool = Field(..., description="Whether technical depth filtering is enabled")
    threshold_description: Optional[str] = Field(
        None, description="Human-readable description of the threshold"
    )
    threshold_numeric: Optional[int] = Field(
        None, description="Numeric value of the threshold for comparison"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "1de9880b-47e4-450c-83a0-46ec25b84790",
                "threshold": "intermediate",
                "enabled": True,
                "threshold_description": "中等 - 需要一定技術背景，包含實作細節",
                "threshold_numeric": 2,
            }
        }


class UpdateTechnicalDepthRequest(BaseModel):
    """Request model for updating technical depth settings."""

    threshold: Optional[str] = Field(
        None, description="Technical depth threshold level (basic, intermediate, advanced, expert)"
    )
    enabled: Optional[bool] = Field(
        None, description="Whether technical depth filtering is enabled"
    )

    class Config:
        json_schema_extra = {"example": {"threshold": "intermediate", "enabled": True}}


class TechnicalDepthLevel(BaseModel):
    """Technical depth level information."""

    value: str
    label: str
    description: str
    numeric_value: int


class TechnicalDepthLevelsResponse(BaseModel):
    """Response model for available technical depth levels."""

    levels: List[dict]


class TechnicalDepthFilteringStats(BaseModel):
    """Response model for technical depth filtering statistics."""

    enabled: bool
    threshold: Optional[str] = None
    threshold_description: Optional[str] = None
    threshold_numeric: Optional[int] = None
    message: str
    error: Optional[str] = None


class ArticleDepthEstimateRequest(BaseModel):
    """Request model for estimating article technical depth."""

    content: str = Field(..., description="Article content")
    title: Optional[str] = Field(None, description="Article title")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This article covers advanced algorithms and performance optimization techniques",
                "title": "Advanced Algorithm Optimization",
            }
        }


class ArticleDepthEstimateResponse(BaseModel):
    """Response model for article depth estimation."""

    estimated_depth: str
    confidence: float
    reasoning: str


class NotificationFilterCheckRequest(BaseModel):
    """Request model for checking notification filter."""

    article_tech_depth: str = Field(..., description="Technical depth level of the article")

    class Config:
        json_schema_extra = {"example": {"article_tech_depth": "advanced"}}


class NotificationFilterCheckResponse(BaseModel):
    """Response model for notification filter check."""

    should_send: bool
    reason: str
    user_settings: dict
