"""
Feed and Subscription Pydantic Schemas

This module defines the Pydantic models for feed and subscription-related
API requests and responses.
"""

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from uuid import UUID


class FeedResponse(BaseModel):
    """
    Feed response model with subscription status
    
    Used by GET /api/feeds endpoint to return feed information
    along with the user's subscription status.
    """
    id: UUID = Field(..., description="Feed UUID")
    name: str = Field(..., description="Feed name")
    url: HttpUrl = Field(..., description="RSS/Atom feed URL")
    category: str = Field(..., description="Feed category")
    is_subscribed: bool = Field(..., description="Whether the user is subscribed to this feed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "category": "Tech News",
                "is_subscribed": True
            }
        }
    )


class SubscriptionToggleRequest(BaseModel):
    """
    Request model for toggling subscription status
    
    Used by POST /api/subscriptions/toggle endpoint.
    """
    feed_id: UUID = Field(..., description="Feed UUID to toggle subscription for")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feed_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class SubscriptionToggleResponse(BaseModel):
    """
    Response model for subscription toggle operation
    
    Returns the feed ID and the new subscription status.
    """
    feed_id: UUID = Field(..., description="Feed UUID")
    is_subscribed: bool = Field(..., description="New subscription status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feed_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_subscribed": True
            }
        }
    )
