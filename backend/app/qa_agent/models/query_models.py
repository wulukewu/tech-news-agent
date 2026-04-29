"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.qa_agent.models.enums import QueryIntent, QueryLanguage


class ParsedQuery(BaseModel):
    """
    Represents a parsed natural language query with extracted intent and metadata.

    Requirements: 1.1, 1.2, 1.4
    """

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    original_query: str = Field(
        ..., min_length=1, max_length=2000, description="Original user query text"
    )

    language: QueryLanguage = Field(..., description="Detected or specified language")

    intent: QueryIntent = Field(..., description="Classified query intent")

    keywords: List[str] = Field(default_factory=list, description="Extracted keywords for search")

    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Extracted filters (time range, category, etc.)"
    )

    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score for intent classification"
    )

    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the query was processed"
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and clean keywords."""
        if not v:
            return []

        # Remove empty strings and duplicates while preserving order
        cleaned = []
        seen = set()
        for keyword in v:
            keyword = keyword.strip()
            if keyword and keyword.lower() not in seen:
                cleaned.append(keyword)
                seen.add(keyword.lower())

        return cleaned[:20]  # Limit to 20 keywords

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter structure."""
        if not v:
            return {}

        # Ensure known filter keys have proper types
        valid_filters = {}

        if "time_range" in v:
            time_range = v["time_range"]
            if isinstance(time_range, dict) and "start" in time_range and "end" in time_range:
                valid_filters["time_range"] = time_range

        if "categories" in v and isinstance(v["categories"], list):
            valid_filters["categories"] = v["categories"][:10]  # Limit categories

        if "technical_depth" in v and isinstance(v["technical_depth"], (int, str)):
            valid_filters["technical_depth"] = v["technical_depth"]

        return valid_filters

    def is_valid(self) -> bool:
        """Check if the parsed query is valid for processing."""
        return (
            len(self.original_query.strip()) > 0
            and self.intent != QueryIntent.UNKNOWN
            and self.confidence > 0.3
        )

    def requires_clarification(self) -> bool:
        """Check if the query requires clarification."""
        return (
            self.confidence < 0.5 or self.intent == QueryIntent.UNKNOWN or len(self.keywords) == 0
        )
