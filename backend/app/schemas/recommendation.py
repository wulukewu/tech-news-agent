"""
Recommendation Pydantic Schemas

This module defines the Pydantic models for recommendation-related
API requests and responses.

Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer


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
    description: str | None = Field(None, description="User-facing description of the feed content")
    is_recommended: bool = Field(..., description="Whether this feed is recommended for new users")
    recommendation_priority: int = Field(
        ..., description="Priority for ordering (higher = more important)"
    )
    is_subscribed: bool = Field(
        default=False, description="Whether the current user is subscribed to this feed"
    )

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
                "is_subscribed": False,
            }
        },
    )


class RecommendedFeedsResponse(BaseModel):
    """
    Response model for recommended feeds endpoint

    Returns both a flat list and grouped by category.
    """

    feeds: list[RecommendedFeed] = Field(
        ..., description="All recommended feeds sorted by priority"
    )
    grouped_by_category: dict[str, list[RecommendedFeed]] = Field(
        ..., description="Feeds grouped by category, each group sorted by priority"
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
                        "is_subscribed": False,
                    }
                ],
                "grouped_by_category": {"AI": [], "Web Development": [], "Security": []},
                "total_count": 20,
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
        default=0, ge=0, description="Priority for ordering (0-1000, higher = more important)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"is_recommended": True, "recommendation_priority": 100}}
    )


class FeedsByCategoryResponse(BaseModel):
    """
    Response model for feeds grouped by category

    Used by subscription page to display feeds in collapsible sections.
    """

    category: str = Field(..., description="Category name")
    feeds: list[RecommendedFeed] = Field(
        ..., description="Feeds in this category sorted by priority"
    )
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
                        "is_subscribed": False,
                    }
                ],
                "feed_count": 5,
            }
        }
    )


# Article Recommendation Schemas


class ArticleRecommendation(BaseModel):
    """
    Article recommendation model

    Represents a recommended article based on user ratings and preferences.
    """

    id: str = Field(..., description="Recommendation ID")
    article_id: UUID = Field(..., description="Article UUID")
    title: str = Field(..., description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    feed_name: str = Field(..., description="Source feed name", serialization_alias="feedName")
    category: str = Field(..., description="Article category")
    published_at: datetime | None = Field(
        None, description="Publication date", serialization_alias="publishedAt"
    )
    tinkering_index: int = Field(
        ...,
        ge=1,
        le=5,
        description="Technical complexity (1-5)",
        serialization_alias="tinkeringIndex",
    )
    ai_summary: str | None = Field(
        None, description="AI-generated summary", serialization_alias="aiSummary"
    )
    reason: str = Field(..., description="AI-generated recommendation reason")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recommendation confidence score")
    generated_at: datetime = Field(
        ..., description="When recommendation was generated", serialization_alias="generatedAt"
    )
    dismissed: bool = Field(default=False, description="Whether user dismissed this recommendation")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @field_serializer("published_at", "generated_at")
    def serialize_datetime(self, value: datetime | None, _info) -> str | None:
        """Serialize datetime to ISO 8601 format"""
        return value.isoformat() if value else None


class ArticleRecommendationsResponse(BaseModel):
    """
    Response model for article recommendations endpoint
    """

    recommendations: list[ArticleRecommendation] = Field(
        ..., description="List of recommended articles"
    )
    total_count: int = Field(
        ..., description="Total number of recommendations", serialization_alias="totalCount"
    )
    has_sufficient_data: bool = Field(
        ...,
        description="Whether user has enough rating data",
        serialization_alias="hasSufficientData",
    )
    min_ratings_required: int = Field(
        ...,
        description="Minimum ratings needed for recommendations",
        serialization_alias="minRatingsRequired",
    )
    user_rating_count: int = Field(
        ..., description="User's current rating count", serialization_alias="userRatingCount"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class RefreshRecommendationsRequest(BaseModel):
    """
    Request model for refreshing recommendations
    """

    limit: int | None = Field(
        default=10, ge=1, le=50, description="Maximum number of recommendations"
    )


class DismissRecommendationRequest(BaseModel):
    """
    Request model for dismissing a recommendation
    """

    recommendation_id: str = Field(
        ..., description="ID of recommendation to dismiss", serialization_alias="recommendationId"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class RecommendationInteraction(BaseModel):
    """
    Model for tracking recommendation interactions
    """

    recommendation_id: str = Field(
        ..., description="Recommendation ID", serialization_alias="recommendationId"
    )
    interaction_type: str = Field(
        ..., description="Type of interaction (view, click, dismiss, refresh)"
    )
    timestamp: datetime = Field(..., description="When interaction occurred")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime, _info) -> str:
        """Serialize timestamp to ISO 8601 format"""
        return value.isoformat()
