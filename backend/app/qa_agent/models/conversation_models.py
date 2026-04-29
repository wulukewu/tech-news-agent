"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.qa_agent.models.article_models import ArticleSummary
from app.qa_agent.models.enums import ConversationStatus, ResponseType
from app.qa_agent.models.query_models import ParsedQuery


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
