"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.qa_agent.models.enums import QueryLanguage


class UserProfile(BaseModel):
    """
    User profile information for personalization.

    Requirements: 8.1, 8.2, 8.3, 8.4
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    user_id: UUID = Field(..., description="Unique user identifier")

    reading_history: List[UUID] = Field(
        default_factory=list, description="List of read article IDs"
    )

    preferred_topics: List[str] = Field(
        default_factory=list, description="User's preferred topics/categories"
    )

    language_preference: QueryLanguage = Field(
        default=QueryLanguage.CHINESE, description="User's preferred language"
    )

    interaction_patterns: Dict[str, Any] = Field(
        default_factory=dict, description="User interaction patterns and preferences"
    )

    query_history: List[str] = Field(default_factory=list, description="Recent query patterns")

    satisfaction_scores: List[float] = Field(
        default_factory=list, description="Historical satisfaction scores"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Profile creation timestamp"
    )

    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")

    @field_validator("reading_history")
    @classmethod
    def validate_reading_history(cls, v: List[UUID]) -> List[UUID]:
        """Limit reading history size."""
        return v[-1000:] if len(v) > 1000 else v  # Keep last 1000 articles

    @field_validator("preferred_topics")
    @classmethod
    def validate_preferred_topics(cls, v: List[str]) -> List[str]:
        """Validate and clean preferred topics."""
        if not v:
            return []

        # Clean and deduplicate while preserving order
        cleaned = []
        seen = set()
        for topic in v:
            topic = topic.strip()
            if topic and topic not in seen:
                cleaned.append(topic)
                seen.add(topic)

        return cleaned[:20]  # Unique topics, max 20

    @field_validator("query_history")
    @classmethod
    def validate_query_history(cls, v: List[str]) -> List[str]:
        """Limit query history size."""
        return v[-100:] if len(v) > 100 else v  # Keep last 100 queries

    @field_validator("satisfaction_scores")
    @classmethod
    def validate_satisfaction_scores(cls, v: List[float]) -> List[float]:
        """Validate satisfaction scores."""
        valid_scores = [score for score in v if 0.0 <= score <= 1.0]
        return valid_scores[-50:] if len(valid_scores) > 50 else valid_scores

    def add_read_article(self, article_id: UUID) -> None:
        """Add an article to reading history."""
        if article_id not in self.reading_history:
            self.reading_history.append(article_id)
            # Keep only last 1000
            if len(self.reading_history) > 1000:
                self.reading_history = self.reading_history[-1000:]
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def add_query(self, query: str) -> None:
        """Add a query to history."""
        self.query_history.append(query)
        # Keep only last 100
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def add_satisfaction_score(self, score: float) -> None:
        """Add a satisfaction score."""
        if 0.0 <= score <= 1.0:
            self.satisfaction_scores.append(score)
            # Keep only last 50
            if len(self.satisfaction_scores) > 50:
                self.satisfaction_scores = self.satisfaction_scores[-50:]
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def get_average_satisfaction(self) -> float:
        """Calculate average satisfaction score."""
        if not self.satisfaction_scores:
            return 0.5  # Neutral default
        return sum(self.satisfaction_scores) / len(self.satisfaction_scores)

    def get_top_topics(self, limit: int = 5) -> List[str]:
        """Get top preferred topics."""
        return self.preferred_topics[:limit]

    def has_read_article(self, article_id: UUID) -> bool:
        """Check if user has read an article."""
        return article_id in self.reading_history

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        # Convert UUID to string for JSON serialization
        data["user_id"] = str(data["user_id"])
        data["reading_history"] = [str(article_id) for article_id in data["reading_history"]]
        # Convert datetime to ISO string
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create from dictionary (JSON deserialization)."""
        # Convert string UUIDs back to UUID objects
        if isinstance(data.get("user_id"), str):
            data["user_id"] = UUID(data["user_id"])
        if "reading_history" in data:
            data["reading_history"] = [
                UUID(article_id) if isinstance(article_id, str) else article_id
                for article_id in data["reading_history"]
            ]

        # Convert ISO strings back to datetime
        for field in ["created_at", "updated_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])

        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "UserProfile":
        """Create from JSON string."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)


# Validation utilities


def validate_query_text(query: str) -> bool:
    """Validate query text format and content."""
    if not query or not query.strip():
        return False

    # Check length
    if len(query.strip()) > 2000:
        return False

    # Check for basic content (not just punctuation/whitespace)
    import re

    has_content = bool(re.search(r"[a-zA-Z\u4e00-\u9fff]", query))
    return has_content


def validate_embedding_vector(embedding: List[float]) -> bool:
    """Validate embedding vector format."""
    if not embedding:
        return False

    # Check dimension (assuming OpenAI embeddings)
    if len(embedding) != 1536:
        return False

    # Check for valid float values
    try:
        for val in embedding:
            if not isinstance(val, (int, float)) or not (-1.0 <= val <= 1.0):
                return False
    except (TypeError, ValueError):
        return False

    return True


def validate_similarity_score(score: float) -> bool:
    """Validate similarity score range."""
    return isinstance(score, (int, float)) and 0.0 <= score <= 1.0
