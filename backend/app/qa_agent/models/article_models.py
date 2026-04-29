"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ArticleMatch(BaseModel):
    """
    Represents a matched article from semantic search with relevance scoring.

    Requirements: 2.2, 2.3
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    article_id: UUID = Field(..., description="Unique article identifier")

    title: str = Field(..., min_length=1, max_length=2000, description="Article title")

    content_preview: str = Field(..., max_length=1000, description="Preview of article content")

    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Vector similarity score")

    keyword_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Keyword matching score")

    combined_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Combined relevance score"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional article metadata"
    )

    url: HttpUrl = Field(..., description="Article URL")

    published_at: Optional[datetime] = Field(None, description="Article publication date")

    feed_name: str = Field(..., description="Source feed name")

    category: str = Field(..., description="Article category")

    def __init__(self, **data):
        """Initialize ArticleMatch and calculate combined score."""
        super().__init__(**data)
        # Calculate combined score after initialization
        self.combined_score = self.similarity_score * 0.7 + self.keyword_score * 0.3

    def is_relevant(self, threshold: float = 0.5) -> bool:
        """Check if article meets relevance threshold."""
        return self.combined_score >= threshold

    def get_reading_time_estimate(self) -> int:
        """Estimate reading time in minutes based on content preview."""
        # Rough estimate: 200 words per minute
        word_count = len(self.content_preview.split())
        # Extrapolate from preview (assuming preview is ~10% of full article)
        estimated_full_words = word_count * 10
        return max(1, estimated_full_words // 200)


class ArticleSummary(BaseModel):
    """
    Summarized article information for structured responses.

    Requirements: 3.2, 3.3
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    article_id: UUID = Field(..., description="Unique article identifier")

    title: str = Field(..., min_length=1, max_length=2000, description="Article title")

    summary: str = Field(
        ..., min_length=10, max_length=500, description="2-3 sentence article summary"
    )

    url: HttpUrl = Field(..., description="Article URL")

    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to user query")

    reading_time: int = Field(..., ge=1, description="Estimated reading time in minutes")

    key_insights: List[str] = Field(
        default_factory=list, description="Key insights from the article"
    )

    published_at: Optional[datetime] = Field(None, description="Article publication date")

    category: str = Field(..., description="Article category")

    @field_validator("summary")
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Ensure summary is appropriate length (2-3 sentences)."""
        sentences = v.split(".")
        # Remove empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 2:
            raise ValueError("Summary must contain at least 2 sentences")

        if len(sentences) > 4:
            # Truncate to first 3 sentences
            v = ". ".join(sentences[:3]) + "."

        return v

    @field_validator("key_insights")
    @classmethod
    def validate_key_insights(cls, v: List[str]) -> List[str]:
        """Validate key insights list."""
        if not v:
            return []

        # Clean and limit insights
        cleaned = [insight.strip() for insight in v if insight.strip()]
        return cleaned[:5]  # Limit to 5 insights

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        # Convert UUID to string for JSON serialization
        data["article_id"] = str(data["article_id"])
        # Convert HttpUrl to string for JSON serialization
        data["url"] = str(data["url"])
        # Convert datetime to ISO string
        if data.get("published_at"):
            data["published_at"] = data["published_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleSummary":
        """Create from dictionary (JSON deserialization)."""
        # Convert string UUID back to UUID object
        if isinstance(data.get("article_id"), str):
            data["article_id"] = UUID(data["article_id"])

        # Convert ISO string back to datetime
        if isinstance(data.get("published_at"), str):
            data["published_at"] = datetime.fromisoformat(data["published_at"])

        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ArticleSummary":
        """Create from JSON string."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)
