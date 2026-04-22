"""
Tests for QA Agent Data Models

This module contains comprehensive tests for all QA agent data models,
including validation, serialization, and business logic.

Requirements: 1.1, 3.1, 4.1
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ConversationStatus,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    StructuredResponse,
    UserProfile,
    validate_embedding_vector,
    validate_query_text,
    validate_similarity_score,
)
from app.qa_agent.validators import (
    ArticleValidator,
    ConversationValidator,
    QueryValidator,
    ResponseValidator,
    UserProfileValidator,
)


class TestParsedQuery:
    """Test cases for ParsedQuery model."""

    def test_valid_parsed_query_creation(self):
        """Test creating a valid ParsedQuery."""
        query = ParsedQuery(
            original_query="What are the latest AI developments?",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["AI", "developments", "latest"],
            confidence=0.8,
        )

        assert query.original_query == "What are the latest AI developments?"
        assert query.language == QueryLanguage.ENGLISH
        assert query.intent == QueryIntent.SEARCH
        assert query.keywords == ["AI", "developments", "latest"]
        assert query.confidence == 0.8
        assert query.is_valid()
        assert not query.requires_clarification()

    def test_parsed_query_validation(self):
        """Test ParsedQuery validation methods."""
        # Valid query
        valid_query = ParsedQuery(
            original_query="機器學習的最新進展",
            language=QueryLanguage.CHINESE,
            intent=QueryIntent.QUESTION,
            keywords=["機器學習", "進展"],
            confidence=0.7,
        )
        assert valid_query.is_valid()

        # Invalid query - low confidence
        invalid_query = ParsedQuery(
            original_query="unclear query",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.UNKNOWN,
            keywords=[],
            confidence=0.2,
        )
        assert not invalid_query.is_valid()
        assert invalid_query.requires_clarification()

    def test_keywords_validation(self):
        """Test keywords validation and cleaning."""
        query = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["  keyword1  ", "keyword2", "", "keyword1", "keyword3"],
            confidence=0.5,
        )

        # Should remove empty strings, duplicates, and strip whitespace
        expected_keywords = ["keyword1", "keyword2", "keyword3"]
        assert query.keywords == expected_keywords

    def test_filters_validation(self):
        """Test filters validation."""
        valid_filters = {
            "time_range": {"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:59"},
            "categories": ["AI", "ML"],
            "technical_depth": 3,
        }

        query = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            filters=valid_filters,
            confidence=0.5,
        )

        assert "time_range" in query.filters
        assert "categories" in query.filters
        assert "technical_depth" in query.filters

    def test_invalid_query_text(self):
        """Test validation of invalid query text."""
        with pytest.raises(PydanticValidationError):
            ParsedQuery(
                original_query="",  # Empty query
                language=QueryLanguage.ENGLISH,
                intent=QueryIntent.SEARCH,
                confidence=0.5,
            )

        with pytest.raises(PydanticValidationError):
            ParsedQuery(
                original_query="x" * 2001,  # Too long
                language=QueryLanguage.ENGLISH,
                intent=QueryIntent.SEARCH,
                confidence=0.5,
            )


class TestArticleMatch:
    """Test cases for ArticleMatch model."""

    def test_valid_article_match_creation(self):
        """Test creating a valid ArticleMatch."""
        article = ArticleMatch(
            article_id=uuid4(),
            title="Test Article",
            content_preview="This is a test article about AI developments.",
            similarity_score=0.85,
            keyword_score=0.7,
            url="https://example.com/article",
            feed_name="Tech News",
            category="AI",
        )

        assert article.title == "Test Article"
        assert article.similarity_score == 0.85
        assert article.keyword_score == 0.7
        assert article.combined_score > 0  # Should be calculated automatically
        assert article.is_relevant()

    def test_combined_score_calculation(self):
        """Test automatic combined score calculation."""
        article = ArticleMatch(
            article_id=uuid4(),
            title="Test Article",
            content_preview="Test content",
            similarity_score=0.8,
            keyword_score=0.6,
            url="https://example.com/article",
            feed_name="Test Feed",
            category="Test",
        )

        # Combined score should be weighted average: 0.8 * 0.7 + 0.6 * 0.3 = 0.74
        expected_score = 0.8 * 0.7 + 0.6 * 0.3
        assert abs(article.combined_score - expected_score) < 0.01

    def test_relevance_threshold(self):
        """Test relevance threshold checking."""
        high_relevance = ArticleMatch(
            article_id=uuid4(),
            title="Highly Relevant",
            content_preview="Very relevant content",
            similarity_score=0.9,
            keyword_score=0.8,
            url="https://example.com/high",
            feed_name="Test Feed",
            category="Test",
        )

        low_relevance = ArticleMatch(
            article_id=uuid4(),
            title="Low Relevance",
            content_preview="Not very relevant",
            similarity_score=0.3,
            keyword_score=0.2,
            url="https://example.com/low",
            feed_name="Test Feed",
            category="Test",
        )

        assert high_relevance.is_relevant(threshold=0.5)
        assert not low_relevance.is_relevant(threshold=0.5)

    def test_reading_time_estimate(self):
        """Test reading time estimation."""
        article = ArticleMatch(
            article_id=uuid4(),
            title="Test Article",
            content_preview="This is a test preview with about twenty words to estimate reading time properly.",
            similarity_score=0.8,
            url="https://example.com/article",
            feed_name="Test Feed",
            category="Test",
        )

        reading_time = article.get_reading_time_estimate()
        assert reading_time >= 1  # Should be at least 1 minute
        assert isinstance(reading_time, int)


class TestArticleSummary:
    """Test cases for ArticleSummary model."""

    def test_valid_article_summary_creation(self):
        """Test creating a valid ArticleSummary."""
        summary = ArticleSummary(
            article_id=uuid4(),
            title="AI Breakthrough",
            summary="This article discusses recent AI breakthroughs. It covers new developments in machine learning. The implications for the future are significant.",
            url="https://example.com/ai-breakthrough",
            relevance_score=0.9,
            reading_time=5,
            category="AI",
        )

        assert summary.title == "AI Breakthrough"
        assert len(summary.summary.split(".")) >= 2  # At least 2 sentences
        assert summary.relevance_score == 0.9
        assert summary.reading_time == 5

    def test_summary_validation(self):
        """Test summary content validation."""
        # Valid summary with 3 sentences
        valid_summary = ArticleSummary(
            article_id=uuid4(),
            title="Test Article",
            summary="First sentence. Second sentence. Third sentence.",
            url="https://example.com/test",
            relevance_score=0.8,
            reading_time=3,
            category="Test",
        )
        assert len(valid_summary.summary.split(".")) == 4  # 3 sentences + empty string

        # Invalid summary - too short
        with pytest.raises(PydanticValidationError):
            ArticleSummary(
                article_id=uuid4(),
                title="Test",
                summary="Too short",  # Less than 10 characters
                url="https://example.com/test",
                relevance_score=0.8,
                reading_time=3,
                category="Test",
            )

    def test_key_insights_validation(self):
        """Test key insights validation."""
        summary = ArticleSummary(
            article_id=uuid4(),
            title="Test Article",
            summary="This is a valid summary with proper length and structure. It contains multiple sentences.",
            url="https://example.com/test",
            relevance_score=0.8,
            reading_time=3,
            category="Test",
            key_insights=[
                "Insight 1",
                "Insight 2",
                "",
                "Insight 3",
            ],  # Empty string should be removed
        )

        # Should remove empty insights
        assert len(summary.key_insights) == 3
        assert "" not in summary.key_insights


class TestStructuredResponse:
    """Test cases for StructuredResponse model."""

    def test_valid_structured_response_creation(self):
        """Test creating a valid StructuredResponse."""
        articles = [
            ArticleSummary(
                article_id=uuid4(),
                title="Article 1",
                summary="First article summary with proper length and content. It provides valuable insights.",
                url="https://example.com/1",
                relevance_score=0.9,
                reading_time=5,
                category="AI",
            ),
            ArticleSummary(
                article_id=uuid4(),
                title="Article 2",
                summary="Second article summary with different content. It offers additional perspectives.",
                url="https://example.com/2",
                relevance_score=0.8,
                reading_time=3,
                category="ML",
            ),
        ]

        response = StructuredResponse(
            query="What are the latest AI developments?",
            articles=articles,
            insights=["AI is rapidly evolving", "Machine learning shows promise"],
            recommendations=["Read more about neural networks", "Explore deep learning"],
            conversation_id=uuid4(),
            response_time=1.5,
            confidence=0.85,
        )

        assert response.query == "What are the latest AI developments?"
        assert len(response.articles) == 2
        assert response.is_successful()
        assert response.get_article_count() == 2
        assert response.get_top_article().relevance_score == 0.9  # Should be sorted by relevance

    def test_articles_sorting(self):
        """Test that articles are automatically sorted by relevance."""
        articles = [
            ArticleSummary(
                article_id=uuid4(),
                title="Lower Relevance",
                summary="Article with lower relevance score. Still contains useful information.",
                url="https://example.com/low",
                relevance_score=0.6,
                reading_time=3,
                category="Test",
            ),
            ArticleSummary(
                article_id=uuid4(),
                title="Higher Relevance",
                summary="Article with higher relevance score. Contains more targeted information.",
                url="https://example.com/high",
                relevance_score=0.9,
                reading_time=4,
                category="Test",
            ),
        ]

        response = StructuredResponse(
            query="test query", articles=articles, conversation_id=uuid4(), response_time=1.0
        )

        # Should be sorted by relevance (highest first)
        assert response.articles[0].relevance_score == 0.9
        assert response.articles[1].relevance_score == 0.6

    def test_response_success_criteria(self):
        """Test response success criteria."""
        # Successful response
        successful_response = StructuredResponse(
            query="test query",
            articles=[
                ArticleSummary(
                    article_id=uuid4(),
                    title="Test Article",
                    summary="Valid article summary with proper content and length requirements. This contains multiple sentences as required.",
                    url="https://example.com/test",
                    relevance_score=0.8,
                    reading_time=3,
                    category="Test",
                )
            ],
            conversation_id=uuid4(),
            response_time=1.0,
            confidence=0.7,
        )
        assert successful_response.is_successful()

        # Unsuccessful response - no articles
        unsuccessful_response = StructuredResponse(
            query="test query",
            articles=[],
            conversation_id=uuid4(),
            response_time=1.0,
            confidence=0.7,
        )
        assert not unsuccessful_response.is_successful()


class TestConversationContext:
    """Test cases for ConversationContext model."""

    def test_valid_conversation_creation(self):
        """Test creating a valid ConversationContext."""
        user_id = uuid4()
        context = ConversationContext(user_id=user_id)

        assert context.user_id == user_id
        assert context.status == ConversationStatus.ACTIVE
        assert len(context.turns) == 0
        assert context.is_active()
        assert not context.is_expired()

    def test_add_turn(self):
        """Test adding turns to conversation."""
        context = ConversationContext(user_id=uuid4())

        # Add first turn
        turn1 = context.add_turn("What is AI?")
        assert turn1.turn_number == 1
        assert turn1.query == "What is AI?"
        assert len(context.turns) == 1

        # Add second turn
        turn2 = context.add_turn("Tell me more about machine learning")
        assert turn2.turn_number == 2
        assert len(context.turns) == 2

    def test_turn_limit_enforcement(self):
        """Test that conversation enforces 10-turn limit."""
        context = ConversationContext(user_id=uuid4())

        # Add 12 turns
        for i in range(12):
            context.add_turn(f"Query {i + 1}")

        # Should only keep last 10 turns
        assert len(context.turns) == 10
        assert context.turns[0].turn_number == 1  # Should be renumbered
        assert context.turns[-1].query == "Query 12"

    def test_recent_queries(self):
        """Test getting recent queries."""
        context = ConversationContext(user_id=uuid4())

        context.add_turn("First query")
        context.add_turn("Second query")
        context.add_turn("Third query")
        context.add_turn("Fourth query")

        recent = context.get_recent_queries(count=3)
        assert len(recent) == 3
        assert recent == ["Second query", "Third query", "Fourth query"]

    def test_conversation_summary(self):
        """Test conversation summary generation."""
        context = ConversationContext(user_id=uuid4())

        # New conversation
        assert "New conversation" in context.get_conversation_summary()

        # With turns
        context.add_turn("Test query")
        summary = context.get_conversation_summary()
        assert "1 turns" in summary

        # With topic
        context.current_topic = "AI Development"
        summary = context.get_conversation_summary()
        assert "AI Development" in summary

    def test_context_reset_logic(self):
        """Test context reset logic."""
        context = ConversationContext(user_id=uuid4())
        context.current_topic = "artificial intelligence machine learning"

        # Add a turn so the context has conversation history
        context.add_turn("What is artificial intelligence?")

        # Related query - should not reset
        related_query = "What about deep learning algorithms?"
        assert not context.should_reset_context(related_query)

        # Unrelated query - should reset
        unrelated_query = "How to cook pasta?"
        assert context.should_reset_context(unrelated_query)

    def test_expiration(self):
        """Test conversation expiration."""
        context = ConversationContext(user_id=uuid4())

        # Not expired by default
        assert not context.is_expired()
        assert context.is_active()

        # Set expiration in the past
        context.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert context.is_expired()
        assert not context.is_active()


class TestUserProfile:
    """Test cases for UserProfile model."""

    def test_valid_user_profile_creation(self):
        """Test creating a valid UserProfile."""
        user_id = uuid4()
        profile = UserProfile(user_id=user_id)

        assert profile.user_id == user_id
        assert profile.language_preference == QueryLanguage.CHINESE
        assert len(profile.reading_history) == 0
        assert len(profile.preferred_topics) == 0
        assert profile.get_average_satisfaction() == 0.5  # Default neutral

    def test_add_read_article(self):
        """Test adding articles to reading history."""
        profile = UserProfile(user_id=uuid4())
        article_id = uuid4()

        profile.add_read_article(article_id)
        assert article_id in profile.reading_history
        assert profile.has_read_article(article_id)

        # Adding same article again should not duplicate
        profile.add_read_article(article_id)
        assert profile.reading_history.count(article_id) == 1

    def test_reading_history_limit(self):
        """Test reading history size limit."""
        profile = UserProfile(user_id=uuid4())

        # Add more than 1000 articles
        for i in range(1050):
            profile.add_read_article(uuid4())

        # Should keep only last 1000
        assert len(profile.reading_history) == 1000

    def test_add_query_history(self):
        """Test adding queries to history."""
        profile = UserProfile(user_id=uuid4())

        profile.add_query("What is AI?")
        profile.add_query("How does machine learning work?")

        assert len(profile.query_history) == 2
        assert "What is AI?" in profile.query_history

    def test_satisfaction_scores(self):
        """Test satisfaction score management."""
        profile = UserProfile(user_id=uuid4())

        profile.add_satisfaction_score(0.8)
        profile.add_satisfaction_score(0.6)
        profile.add_satisfaction_score(0.9)

        assert len(profile.satisfaction_scores) == 3
        expected_avg = (0.8 + 0.6 + 0.9) / 3
        assert abs(profile.get_average_satisfaction() - expected_avg) < 0.01

        # Invalid scores should be ignored
        profile.add_satisfaction_score(1.5)  # Too high
        profile.add_satisfaction_score(-0.1)  # Too low
        assert len(profile.satisfaction_scores) == 3  # Should remain unchanged

    def test_preferred_topics_validation(self):
        """Test preferred topics validation."""
        profile = UserProfile(
            user_id=uuid4(),
            preferred_topics=["AI", "ML", "  Data Science  ", "", "AI", "Deep Learning"],
        )

        # Should remove empty strings, duplicates, and strip whitespace
        expected_topics = {"AI", "ML", "Data Science", "Deep Learning"}
        assert set(profile.preferred_topics) == expected_topics

    def test_get_top_topics(self):
        """Test getting top preferred topics."""
        profile = UserProfile(
            user_id=uuid4(),
            preferred_topics=[
                "AI",
                "ML",
                "Data Science",
                "Deep Learning",
                "NLP",
                "Computer Vision",
            ],
        )

        top_3 = profile.get_top_topics(limit=3)
        assert len(top_3) == 3
        assert all(topic in profile.preferred_topics for topic in top_3)


class TestValidationUtilities:
    """Test cases for validation utility functions."""

    def test_validate_query_text(self):
        """Test query text validation function."""
        # Valid queries
        assert validate_query_text("What is artificial intelligence?")
        assert validate_query_text("人工智能是什麼？")
        assert validate_query_text("How does ML work?")

        # Invalid queries
        assert not validate_query_text("")
        assert not validate_query_text("   ")
        assert not validate_query_text("!!!")  # Only punctuation
        assert not validate_query_text("x" * 2001)  # Too long

    def test_validate_embedding_vector(self):
        """Test embedding vector validation."""
        # Valid embedding (1536 dimensions)
        valid_embedding = [0.1] * 1536
        assert validate_embedding_vector(valid_embedding)

        # Invalid embeddings
        assert not validate_embedding_vector([])  # Empty
        assert not validate_embedding_vector([0.1] * 100)  # Wrong dimension
        assert not validate_embedding_vector([0.1] * 1535)  # Wrong dimension
        assert not validate_embedding_vector([2.5] * 1536)  # Values out of range
        assert not validate_embedding_vector(["not", "numbers"] * 768)  # Wrong type

    def test_validate_similarity_score(self):
        """Test similarity score validation."""
        # Valid scores
        assert validate_similarity_score(0.0)
        assert validate_similarity_score(0.5)
        assert validate_similarity_score(1.0)
        assert validate_similarity_score(0.85)

        # Invalid scores
        assert not validate_similarity_score(-0.1)
        assert not validate_similarity_score(1.1)
        assert not validate_similarity_score("0.5")  # Wrong type


class TestValidators:
    """Test cases for validator classes."""

    def test_query_validator(self):
        """Test QueryValidator functionality."""
        # Valid query
        valid_query = ParsedQuery(
            original_query="What are the latest AI developments?",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["AI", "developments", "latest"],
            confidence=0.8,
        )

        errors = QueryValidator.validate_parsed_query(valid_query)
        assert len(errors) == 0

        # Test individual validation methods with invalid data
        assert not QueryValidator.validate_query_text("")
        assert not QueryValidator.validate_intent_confidence(QueryIntent.UNKNOWN, 1.5)

    def test_article_validator(self):
        """Test ArticleValidator functionality."""
        valid_article = ArticleMatch(
            article_id=uuid4(),
            title="Test Article",
            content_preview="Valid content preview",
            similarity_score=0.8,
            url="https://example.com/test",
            feed_name="Test Feed",
            category="Test",
        )

        errors = ArticleValidator.validate_article_match(valid_article)
        assert len(errors) == 0

        # Test similarity score validation
        assert ArticleValidator.validate_similarity_score(0.5)
        assert not ArticleValidator.validate_similarity_score(1.5)

    def test_response_validator(self):
        """Test ResponseValidator functionality."""
        valid_response = StructuredResponse(
            query="test query",
            articles=[
                ArticleSummary(
                    article_id=uuid4(),
                    title="Test Article",
                    summary="This is a valid summary with proper length. It contains multiple sentences.",
                    url="https://example.com/test",
                    relevance_score=0.8,
                    reading_time=3,
                    category="Test",
                )
            ],
            conversation_id=uuid4(),
            response_time=1.5,
            confidence=0.7,
        )

        errors = ResponseValidator.validate_structured_response(valid_response)
        assert len(errors) == 0

    def test_conversation_validator(self):
        """Test ConversationValidator functionality."""
        valid_context = ConversationContext(user_id=uuid4())
        valid_context.add_turn("First query")
        valid_context.add_turn("Second query")

        errors = ConversationValidator.validate_conversation_context(valid_context)
        assert len(errors) == 0

        # Test query validation
        assert ConversationValidator.validate_conversation_turn_query("Valid query")
        assert not ConversationValidator.validate_conversation_turn_query("")

    def test_user_profile_validator(self):
        """Test UserProfileValidator functionality."""
        valid_profile = UserProfile(
            user_id=uuid4(), preferred_topics=["AI", "ML"], satisfaction_scores=[0.8, 0.6, 0.9]
        )

        errors = UserProfileValidator.validate_user_profile(valid_profile)
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__])
