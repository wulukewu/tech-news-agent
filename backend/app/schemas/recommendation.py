"""
Recommendation Pydantic Schemas

This module defines the Pydantic models for recommendation-related
API requests and responses.

Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
"""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional, Dict, List
from datetime import datetime


class RecommendedFeed(BaseModel):
    """
    Recommended feed response model
    
    Represents a feed with recommendation metadata.
    Used by GET /api/feeds/recommended endpoint.
    """
    id: UUID = Field(..., description="Feed UUID")
    name: str = Field(..., description="Feed name")
    url: str = Field(..., description="Feed RSS URL")
    category: str = Field(..., description="Feed category (AI, Web Development, Security, etc.)")
    description: Optional[str] = Field(None, description="User-facing description of the feed content")
    is_recommended: bool = Field(..., description="Whether this feed is recommended for new users")
    recommendation_priority: int = Field(..., description="Priority for ordering (higher = more important)")
    is_subscribed: bool = Field(default=False, description="Whether the current user is subscribed to this feed")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Hacker News",
                "url": "https://news.ycombinator.com/rss",
                "category": "Tech News",
                "description": "最熱門的科技新聞和討論",
                "is_recommended": True,
                "recommendation_priority": 100,
                "is_subscribed": False
            }
        }
    )


class RecommendedFeedsResponse(BaseModel):
    """
    Response model for recommended feeds endpoint
    
    Returns both a flat list and grouped by category.
    """
    feeds: List[RecommendedFeed] = Field(..., description="All recommended feeds sorted by priority")
    grouped_by_category: Dict[str, List[RecommendedFeed]] = Field(
        ..., 
        description="Feeds grouped by category, each group sorted by priority"
    )
    total_count: int = Field(..., description="Total number of recommended feeds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feeds": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Hacker News",
                        "url": "https://news.ycombinator.com/rss",
                        "category": "Tech News",
                        "description": "最熱門的科技新聞和討論",
                        "is_recommended": True,
                        "recommendation_priority": 100,
                        "is_subscribed": False
                    }
                ],
                "grouped_by_category": {
                    "AI": [],
                    "Web Development": [],
                    "Security": []
                },
                "total_count": 20
            }
        }
    )


class UpdateRecommendationStatusRequest(BaseModel):
    """
    Request model for updating feed recommendation status
    
    Used by admin endpoints to manage recommended feeds.
    """
    is_recommended: bool = Field(..., description="Whether the feed should be recommended")
    recommendation_priority: int = Field(
        default=0, 
        ge=0,
        description="Priority for ordering (0-1000, higher = more important)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_recommended": True,
                "recommendation_priority": 100
            }
        }
    )


class FeedsByCategoryResponse(BaseModel):
    """
    Response model for feeds grouped by category
    
    Used by subscription page to display feeds in collapsible sections.
    """
    category: str = Field(..., description="Category name")
    feeds: List[RecommendedFeed] = Field(..., description="Feeds in this category sorted by priority")
    feed_count: int = Field(..., description="Number of feeds in this category")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "AI",
                "feeds": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "OpenAI Blog",
                        "url": "https://openai.com/blog/rss",
                        "category": "AI",
                        "description": "OpenAI 官方部落格",
                        "is_recommended": True,
                        "recommendation_priority": 95,
                        "is_subscribed": False
                    }
                ],
                "feed_count": 5
            }
        }
    )
