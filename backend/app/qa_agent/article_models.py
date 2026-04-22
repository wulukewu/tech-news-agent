"""
Enhanced Article Models for Intelligent Q&A Agent

This module provides comprehensive article models with metadata support,
serialization capabilities, and integration with the existing database schema.

Requirements: 8.1, 8.2, 3.2
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ArticleMetadata(BaseModel):
    """
    Comprehensive metadata for articles with serialization support.

    Requirements: 3.2, 8.2
    """

    model_config = ConfigDict(
        validate_assignment=True, extra="allow"  # Allow additional metadata fields
    )

    author: Optional[str] = Field(None, max_length=200, description="Article author name")

    source: Optional[str] = Field(
        None, max_length=200, description="Original source or publication"
    )

    tags: List[str] = Field(default_factory=list, description="Article tags for categorization")

    reading_difficulty: Optional[str] = Field(
        None, description="Reading difficulty level (beginner, intermediate, advanced, expert)"
    )

    technical_depth: Optional[int] = Field(
        None, ge=1, le=5, description="Technical depth score (1-5)"
    )

    word_count: Optional[int] = Field(None, ge=0, description="Estimated word count")

    language: Optional[str] = Field(None, max_length=10, description="Article language code")

    content_type: Optional[str] = Field(
        None, description="Type of content (article, tutorial, news, research, etc.)"
    )

    external_links: List[str] = Field(
        default_factory=list, description="External links referenced in the article"
    )

    images: List[str] = Field(default_factory=list, description="Image URLs in the article")

    code_snippets: bool = Field(default=False, description="Whether article contains code snippets")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        if not v:
            return []

        # Clean and limit tags
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(set(cleaned))[:10]  # Unique tags, max 10

    @field_validator("reading_difficulty")
    @classmethod
    def validate_reading_difficulty(cls, v: Optional[str]) -> Optional[str]:
        """Validate reading difficulty level."""
        if v is None:
            return v

        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if v.lower() not in valid_levels:
            return None  # Invalid level, set to None

        return v.lower()

    @field_validator("external_links")
    @classmethod
    def validate_external_links(cls, v: List[str]) -> List[str]:
        """Validate external links."""
        if not v:
            return []

        # Basic URL validation and limit
        valid_links = []
        for link in v[:20]:  # Limit to 20 links
            if link.strip() and (link.startswith("http://") or link.startswith("https://")):
                valid_links.append(link.strip())

        return valid_links

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleMetadata":
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


class Article(BaseModel):
    """
    Enhanced Article model with comprehensive metadata and serialization support.

    Requirements: 8.1, 8.2, 3.2
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    id: UUID = Field(..., description="Unique article identifier")

    title: str = Field(..., min_length=1, max_length=2000, description="Article title")

    content: str = Field(..., min_length=1, description="Full article content")

    url: HttpUrl = Field(..., description="Article URL")

    feed_id: UUID = Field(..., description="Source feed identifier")

    feed_name: str = Field(..., description="Source feed name")

    category: str = Field(..., description="Article category")

    published_at: Optional[datetime] = Field(None, description="Article publication date")

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When article was added to system"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    metadata: ArticleMetadata = Field(
        default_factory=ArticleMetadata, description="Article metadata"
    )

    embedding: Optional[List[float]] = Field(None, description="Article embedding vector")

    is_processed: bool = Field(
        default=False, description="Whether article has been processed for embeddings"
    )

    processing_status: str = Field(
        default="pending", description="Processing status (pending, processing, completed, failed)"
    )

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Validate content length."""
        if len(v.strip()) < 1:
            raise ValueError("Content cannot be empty")

        # No upper limit for content, but warn if extremely long
        if len(v) > 1000000:  # 1MB of text
            # Log warning but don't reject
            pass

        return v.strip()

    @field_validator("processing_status")
    @classmethod
    def validate_processing_status(cls, v: str) -> str:
        """Validate processing status."""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if v not in valid_statuses:
            return "pending"  # Default to pending if invalid
        return v

    def get_content_preview(self, max_length: int = 500) -> str:
        """Get a preview of the article content."""
        if len(self.content) <= max_length:
            return self.content

        # Find a good breaking point (end of sentence)
        preview = self.content[:max_length]
        last_sentence_end = max(
            preview.rfind("."),
            preview.rfind("。"),
            preview.rfind("!"),
            preview.rfind("！"),
            preview.rfind("?"),
            preview.rfind("？"),
        )

        if last_sentence_end > max_length * 0.7:  # If we found a good break point
            return preview[: last_sentence_end + 1]
        else:
            return preview + "..."

    def get_reading_time_estimate(self) -> int:
        """Estimate reading time in minutes."""
        # Different calculation based on language
        if self.metadata.language == "zh":
            # Chinese: ~250 characters per minute
            char_count = len(self.content)
            return max(1, char_count // 250)
        else:
            # English: ~200 words per minute
            word_count = len(self.content.split())
            return max(1, word_count // 200)

    def get_word_count(self) -> int:
        """Get estimated word count."""
        if self.metadata.language == "zh":
            # For Chinese, count characters (excluding spaces and punctuation)
            import re

            chinese_chars = re.findall(r"[\u4e00-\u9fff]", self.content)
            return len(chinese_chars)
        else:
            # For other languages, count words
            return len(self.content.split())

    def update_metadata(self, **kwargs) -> None:
        """Update article metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)

        # Update timestamp
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def mark_as_processed(self, embedding: Optional[List[float]] = None) -> None:
        """Mark article as processed with optional embedding."""
        object.__setattr__(self, "is_processed", True)
        object.__setattr__(self, "processing_status", "completed")
        if embedding:
            object.__setattr__(self, "embedding", embedding)
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def mark_processing_failed(self, error_message: str = "") -> None:
        """Mark article processing as failed."""
        object.__setattr__(self, "processing_status", "failed")
        if error_message:
            self.metadata.processing_error = error_message
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        # Convert UUID to string for JSON serialization
        data["id"] = str(data["id"])
        data["feed_id"] = str(data["feed_id"])
        # Convert HttpUrl to string for JSON serialization
        data["url"] = str(data["url"])
        # Convert datetime to ISO string
        if data.get("published_at"):
            data["published_at"] = data["published_at"].isoformat()
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Article":
        """Create from dictionary (JSON deserialization)."""
        # Convert string UUIDs back to UUID objects
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        if isinstance(data.get("feed_id"), str):
            data["feed_id"] = UUID(data["feed_id"])

        # Convert ISO strings back to datetime
        for field in ["published_at", "created_at", "updated_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])

        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Article":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ArticleCollection(BaseModel):
    """
    Collection of articles with batch operations and serialization support.

    Requirements: 8.2
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    articles: List[Article] = Field(
        default_factory=list, description="List of articles in the collection"
    )

    total_count: int = Field(default=0, ge=0, description="Total number of articles")

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Collection creation timestamp"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")

    def __init__(self, **data):
        """Initialize collection and update count."""
        super().__init__(**data)
        if not data.get("total_count"):
            object.__setattr__(self, "total_count", len(self.articles))

    def add_article(self, article: Article) -> None:
        """Add an article to the collection."""
        self.articles.append(article)
        object.__setattr__(self, "total_count", len(self.articles))

    def remove_article(self, article_id: UUID) -> bool:
        """Remove an article from the collection."""
        original_count = len(self.articles)
        self.articles = [a for a in self.articles if a.id != article_id]
        new_count = len(self.articles)

        if new_count < original_count:
            object.__setattr__(self, "total_count", new_count)
            return True
        return False

    def get_article_by_id(self, article_id: UUID) -> Optional[Article]:
        """Get an article by ID."""
        for article in self.articles:
            if article.id == article_id:
                return article
        return None

    def filter_by_category(self, category: str) -> "ArticleCollection":
        """Filter articles by category."""
        filtered_articles = [a for a in self.articles if a.category.lower() == category.lower()]
        return ArticleCollection(
            articles=filtered_articles, metadata={"filter": "category", "filter_value": category}
        )

    def filter_by_tags(self, tags: List[str]) -> "ArticleCollection":
        """Filter articles by tags."""
        tag_set = set(tag.lower() for tag in tags)
        filtered_articles = []

        for article in self.articles:
            article_tags = set(tag.lower() for tag in article.metadata.tags)
            if tag_set.intersection(article_tags):
                filtered_articles.append(article)

        return ArticleCollection(
            articles=filtered_articles, metadata={"filter": "tags", "filter_value": tags}
        )

    def get_unprocessed_articles(self) -> "ArticleCollection":
        """Get articles that haven't been processed for embeddings."""
        unprocessed = [a for a in self.articles if not a.is_processed]
        return ArticleCollection(articles=unprocessed, metadata={"filter": "unprocessed"})

    def get_articles_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> "ArticleCollection":
        """Get articles within a date range."""
        filtered_articles = []

        for article in self.articles:
            if article.published_at and start_date <= article.published_at <= end_date:
                filtered_articles.append(article)

        return ArticleCollection(
            articles=filtered_articles,
            metadata={
                "filter": "date_range",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

    def sort_by_date(self, ascending: bool = False) -> "ArticleCollection":
        """Sort articles by publication date."""
        sorted_articles = sorted(
            self.articles, key=lambda a: a.published_at or datetime.min, reverse=not ascending
        )

        return ArticleCollection(
            articles=sorted_articles, metadata={"sorted_by": "date", "ascending": ascending}
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.articles:
            return {"total_articles": 0}

        # Category distribution
        categories = {}
        for article in self.articles:
            categories[article.category] = categories.get(article.category, 0) + 1

        # Language distribution
        languages = {}
        for article in self.articles:
            lang = article.metadata.language or "unknown"
            languages[lang] = languages.get(lang, 0) + 1

        # Processing status
        processing_status = {}
        for article in self.articles:
            status = article.processing_status
            processing_status[status] = processing_status.get(status, 0) + 1

        # Date range
        dates = [a.published_at for a in self.articles if a.published_at]
        date_range = {}
        if dates:
            date_range = {"earliest": min(dates).isoformat(), "latest": max(dates).isoformat()}

        return {
            "total_articles": self.total_count,
            "categories": categories,
            "languages": languages,
            "processing_status": processing_status,
            "date_range": date_range,
            "processed_count": len([a for a in self.articles if a.is_processed]),
            "unprocessed_count": len([a for a in self.articles if not a.is_processed]),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "articles": [article.to_dict() for article in self.articles],
            "total_count": self.total_count,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleCollection":
        """Create from dictionary (JSON deserialization)."""
        articles = [Article.from_dict(article_data) for article_data in data.get("articles", [])]

        return cls(
            articles=articles,
            total_count=data.get("total_count", len(articles)),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ArticleCollection":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
