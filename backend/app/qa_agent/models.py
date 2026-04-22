"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class QueryIntent(str, Enum):
    """
    Enumeration of possible query intents for natural language processing.

    Requirements: 1.1, 1.2
    """

    SEARCH = "search"  # General search query
    QUESTION = "question"  # Direct question
    COMPARISON = "comparison"  # Comparing topics/articles
    SUMMARY = "summary"  # Request for summary
    RECOMMENDATION = "recommendation"  # Request for recommendations
    CLARIFICATION = "clarification"  # Follow-up clarification
    EXPLORATION = "exploration"  # Deep dive into topic
    UNKNOWN = "unknown"  # Unable to determine intent


class QueryLanguage(str, Enum):
    """
    Supported languages for query processing.

    Requirements: 1.2
    """

    CHINESE = "zh"
    ENGLISH = "en"
    AUTO_DETECT = "auto"


class ResponseType(str, Enum):
    """
    Types of responses the system can generate.

    Requirements: 3.1, 9.2, 9.4
    """

    STRUCTURED = "structured"  # Full structured response
    SIMPLE = "simple"  # Simple text response
    ERROR = "error"  # Error response
    CLARIFICATION = "clarification"  # Clarification request
    PARTIAL = "partial"  # Partial results due to timeout (Requirement 9.4)
    SEARCH_RESULTS = "search_results"  # Search results fallback (Requirement 9.2)


class ConversationStatus(str, Enum):
    """
    Status of conversation sessions.

    Requirements: 4.1
    """

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CLOSED = "closed"


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


class StructuredResponse(BaseModel):
    """
    Complete structured response containing articles, insights, and recommendations.

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    query: str = Field(..., description="Original user query")

    response_type: ResponseType = Field(
        default=ResponseType.STRUCTURED, description="Type of response"
    )

    articles: List[ArticleSummary] = Field(
        default_factory=list, max_length=5, description="Relevant articles (max 5)"
    )

    insights: List[str] = Field(
        default_factory=list, description="Personalized insights based on user profile"
    )

    recommendations: List[str] = Field(
        default_factory=list, description="Related reading suggestions"
    )

    conversation_id: UUID = Field(..., description="Associated conversation ID")

    response_time: float = Field(..., ge=0.0, description="Response generation time in seconds")

    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in response quality"
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the response was generated"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional response metadata"
    )

    @field_validator("articles")
    @classmethod
    def validate_articles_order(cls, v: List[ArticleSummary]) -> List[ArticleSummary]:
        """Ensure articles are sorted by relevance score."""
        return sorted(v, key=lambda x: x.relevance_score, reverse=True)

    @field_validator("insights")
    @classmethod
    def validate_insights(cls, v: List[str]) -> List[str]:
        """Validate insights list."""
        if not v:
            return []

        cleaned = [insight.strip() for insight in v if insight.strip()]
        return cleaned[:10]  # Limit to 10 insights

    @field_validator("recommendations")
    @classmethod
    def validate_recommendations(cls, v: List[str]) -> List[str]:
        """Validate recommendations list."""
        if not v:
            return []

        cleaned = [rec.strip() for rec in v if rec.strip()]
        return cleaned[:10]  # Limit to 10 recommendations

    def is_successful(self) -> bool:
        """Check if response contains useful content."""
        return (
            self.response_type == ResponseType.STRUCTURED
            and len(self.articles) > 0
            and self.confidence > 0.3
        )

    def get_article_count(self) -> int:
        """Get number of articles in response."""
        return len(self.articles)

    def get_top_article(self) -> Optional[ArticleSummary]:
        """Get the most relevant article."""
        return self.articles[0] if self.articles else None


class ConversationTurn(BaseModel):
    """
    Represents a single turn in a conversation.

    Requirements: 4.1, 4.2
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    turn_number: int = Field(..., ge=1, description="Turn number in conversation")

    query: str = Field(..., min_length=1, description="User query for this turn")

    parsed_query: Optional[ParsedQuery] = Field(None, description="Parsed query information")

    response: Optional[StructuredResponse] = Field(
        None, description="System response for this turn"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When this turn occurred"
    )

    context_used: Dict[str, Any] = Field(
        default_factory=dict, description="Context information used for this turn"
    )


class ConversationContext(BaseModel):
    """
    Maintains conversation state and context across multiple turns.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    conversation_id: UUID = Field(
        default_factory=uuid4, description="Unique conversation identifier"
    )

    user_id: UUID = Field(..., description="User identifier")

    turns: List[ConversationTurn] = Field(
        default_factory=list, max_length=10, description="Conversation turns (max 10)"
    )

    current_topic: Optional[str] = Field(None, description="Current conversation topic")

    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE, description="Conversation status"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When conversation was created"
    )

    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    expires_at: Optional[datetime] = Field(None, description="When conversation expires")

    context_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Summarized context information"
    )

    @field_validator("turns")
    @classmethod
    def validate_turns_limit(cls, v: List[ConversationTurn]) -> List[ConversationTurn]:
        """Ensure turns list doesn't exceed limit."""
        if len(v) > 10:
            # Keep only the most recent 10 turns
            return v[-10:]
        return v

    def __init__(self, **data):
        """Initialize ConversationContext and set timestamps."""
        super().__init__(**data)
        # Set last_updated after initialization to avoid recursion
        object.__setattr__(self, "last_updated", datetime.utcnow())

    def add_turn(
        self,
        query: str,
        parsed_query: Optional[ParsedQuery] = None,
        response: Optional[StructuredResponse] = None,
    ) -> ConversationTurn:
        """Add a new turn to the conversation."""
        turn_number = len(self.turns) + 1

        turn = ConversationTurn(
            turn_number=turn_number, query=query, parsed_query=parsed_query, response=response
        )

        self.turns.append(turn)

        # Keep only last 10 turns
        if len(self.turns) > 10:
            self.turns = self.turns[-10:]
            # Renumber turns
            for i, turn in enumerate(self.turns, 1):
                turn.turn_number = i

        # Manually update timestamp to avoid recursion
        object.__setattr__(self, "last_updated", datetime.utcnow())
        return turn

    def get_recent_queries(self, count: int = 3) -> List[str]:
        """Get recent queries for context."""
        recent_turns = self.turns[-count:] if len(self.turns) >= count else self.turns
        return [turn.query for turn in recent_turns]

    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation."""
        if not self.turns:
            return "New conversation"

        if self.current_topic:
            return f"Discussion about {self.current_topic} ({len(self.turns)} turns)"

        return f"Conversation with {len(self.turns)} turns"

    def should_reset_context(self, new_query: str) -> bool:
        """Determine if context should be reset based on topic change."""
        if not self.turns or not self.current_topic:
            return False

        # Enhanced topic change detection
        new_query_words = set(word.lower() for word in new_query.split() if len(word) > 2)
        topic_words = set(word.lower() for word in self.current_topic.split() if len(word) > 2)

        # If there are no meaningful words in either, don't reset
        if not new_query_words or not topic_words:
            return False

        # Check for direct word overlap
        common_words = new_query_words.intersection(topic_words)
        if len(common_words) > 0:
            return False  # Has common words, don't reset

        # Check for semantic relatedness using domain knowledge
        ai_related_terms = {
            "artificial",
            "intelligence",
            "ai",
            "machine",
            "learning",
            "ml",
            "deep",
            "neural",
            "network",
            "algorithm",
            "model",
            "data",
            "science",
            "automation",
            "robot",
            "nlp",
            "computer",
            "vision",
            "processing",
            "natural",
            "language",
            "applications",
            "developments",
        }

        tech_related_terms = {
            "technology",
            "software",
            "programming",
            "development",
            "system",
            "application",
            "platform",
            "framework",
            "tool",
            "solution",
            "innovation",
            "digital",
        }

        # Check if both query and topic contain related terms
        query_ai_terms = new_query_words.intersection(ai_related_terms)
        topic_ai_terms = topic_words.intersection(ai_related_terms)

        if query_ai_terms and topic_ai_terms:
            return False  # Both are AI-related, don't reset

        query_tech_terms = new_query_words.intersection(tech_related_terms)
        topic_tech_terms = topic_words.intersection(tech_related_terms)

        if query_tech_terms and topic_tech_terms:
            return False  # Both are tech-related, don't reset

        # If no semantic relationship found, reset context
        return True

    def is_expired(self) -> bool:
        """Check if conversation has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE and not self.is_expired()


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
