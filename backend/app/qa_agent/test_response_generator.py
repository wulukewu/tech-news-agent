"""
Test module for ResponseGenerator

This module contains unit tests for the ResponseGenerator class to verify
correct functionality of structured response generation.
"""

from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from .models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    StructuredResponse,
    UserProfile,
)
from .response_generator import ResponseGenerator, ResponseGeneratorError, get_response_generator


class TestResponseGenerator:
    """Test cases for ResponseGenerator class."""

    @pytest.fixture
    def response_generator(self):
        """Create a ResponseGenerator instance for testing."""
        return ResponseGenerator()

    @pytest.fixture
    def sample_articles(self):
        """Create sample ArticleMatch objects for testing."""
        return [
            ArticleMatch(
                article_id=str(uuid4()),
                title="Introduction to Machine Learning",
                content_preview="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. This article covers the basics of ML algorithms and their applications.",
                similarity_score=0.95,
                metadata={"category": "AI", "topics": ["machine learning", "algorithms"]},
                url="https://example.com/ml-intro",
            ),
            ArticleMatch(
                article_id=str(uuid4()),
                title="Deep Learning Fundamentals",
                content_preview="Deep learning is a machine learning technique that teaches computers to do what comes naturally to humans: learn by example. This comprehensive guide explores neural networks and their applications.",
                similarity_score=0.88,
                metadata={"category": "AI", "topics": ["deep learning", "neural networks"]},
                url="https://example.com/deep-learning",
            ),
            ArticleMatch(
                article_id=str(uuid4()),
                title="Python for Data Science",
                content_preview="Python has become the go-to language for data science due to its simplicity and powerful libraries. Learn how to use pandas, numpy, and scikit-learn for data analysis.",
                similarity_score=0.82,
                metadata={"category": "Programming", "topics": ["python", "data science"]},
                url="https://example.com/python-data-science",
            ),
        ]

    @pytest.fixture
    def sample_user_profile(self):
        """Create a sample UserProfile for testing."""
        return UserProfile(
            user_id=uuid4(),
            reading_history=[uuid4(), uuid4()],
            preferred_topics=["machine learning", "python", "data science"],
            language_preference="en",
            interaction_patterns={"avg_reading_time": 300},
            query_history=["machine learning basics", "python tutorials"],
            satisfaction_scores=[4.5, 4.8, 4.2],
        )

    @pytest.fixture
    def sample_conversation_context(self):
        """Create a sample ConversationContext for testing."""
        return ConversationContext(
            conversation_id=str(uuid4()),
            user_id=uuid4(),
            turns=[],
            current_topic="machine learning",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )

    def test_response_generator_initialization(self, response_generator):
        """Test ResponseGenerator initializes correctly."""
        assert response_generator is not None
        assert response_generator.max_articles == 5
        assert response_generator.client is not None

    def test_get_response_generator_singleton(self):
        """Test that get_response_generator returns the same instance."""
        generator1 = get_response_generator()
        generator2 = get_response_generator()
        assert generator1 is generator2

    @pytest.mark.asyncio
    async def test_generate_response_with_articles(
        self, response_generator, sample_articles, sample_user_profile, sample_conversation_context
    ):
        """Test generating a structured response with articles."""
        # Mock the OpenAI API calls
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.side_effect = [
                "This article provides a comprehensive introduction to machine learning concepts and algorithms.",
                "Deep learning fundamentals are explained with practical examples and neural network architectures.",
                "Python's data science ecosystem is explored with hands-on examples using popular libraries.",
                "Machine learning and deep learning are transforming industries. Python remains the preferred language for implementation. Consider exploring advanced topics like reinforcement learning.",
                "Explore advanced neural network architectures. Try implementing your own ML models. Consider taking a structured course on AI fundamentals.",
            ]

            response = await response_generator.generate_response(
                query="machine learning basics",
                articles=sample_articles,
                context=sample_conversation_context,
                user_profile=sample_user_profile,
            )

            # Verify response structure
            assert isinstance(response, StructuredResponse)
            assert response.query == "machine learning basics"
            assert len(response.articles) <= 5  # Max 5 articles
            assert len(response.articles) == 3  # All sample articles included
            assert len(response.insights) > 0
            assert len(response.recommendations) > 0
            assert response.conversation_id == sample_conversation_context.conversation_id

            # Verify articles are sorted by relevance
            scores = [article.relevance_score for article in response.articles]
            assert scores == sorted(scores, reverse=True)

            # Verify all articles have summaries
            for article in response.articles:
                assert isinstance(article, ArticleSummary)
                assert len(article.summary) > 0
                assert article.url.startswith("https://")

    @pytest.mark.asyncio
    async def test_generate_response_empty_articles(
        self, response_generator, sample_conversation_context
    ):
        """Test generating response when no articles are found."""
        response = await response_generator.generate_response(
            query="nonexistent topic", articles=[], context=sample_conversation_context
        )

        assert isinstance(response, StructuredResponse)
        assert response.query == "nonexistent topic"
        assert len(response.articles) == 0
        assert "No relevant articles found" in response.insights[0]
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_response_api_failure_fallback(
        self, response_generator, sample_articles
    ):
        """Test fallback behavior when OpenAI API fails."""
        # Mock API to raise an exception
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.side_effect = Exception("API Error")

            response = await response_generator.generate_response(
                query="test query", articles=sample_articles
            )

            # Should still return a valid response with fallback content
            assert isinstance(response, StructuredResponse)
            assert len(response.articles) > 0
            assert len(response.insights) > 0
            assert len(response.recommendations) > 0

            # Fallback summaries should use content preview
            for article in response.articles:
                assert len(article.summary) > 0

    @pytest.mark.asyncio
    async def test_generate_single_summary(
        self, response_generator, sample_articles, sample_user_profile
    ):
        """Test generating summary for a single article."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = (
                "This is a comprehensive guide to machine learning fundamentals."
            )

            summary = await response_generator._generate_single_summary(
                sample_articles[0], "machine learning", sample_user_profile
            )

            assert isinstance(summary, ArticleSummary)
            assert summary.title == sample_articles[0].title
            assert summary.url == sample_articles[0].url
            assert len(summary.summary) > 0
            assert summary.relevance_score == sample_articles[0].similarity_score

    def test_create_fallback_summary(self, response_generator, sample_articles):
        """Test creating fallback summary when LLM fails."""
        fallback = response_generator._create_fallback_summary(sample_articles[0])

        assert isinstance(fallback, ArticleSummary)
        assert fallback.title == sample_articles[0].title
        assert fallback.url == sample_articles[0].url
        assert len(fallback.summary) > 0
        assert fallback.summary.endswith(".")

    def test_extract_key_insights(self, response_generator, sample_articles):
        """Test extracting key insights from article content."""
        insights = response_generator._extract_key_insights(
            sample_articles[0],
            "This article covers machine learning algorithms and performance optimization.",
        )

        assert isinstance(insights, list)
        assert len(insights) <= 5
        # Should find 'algorithm' and 'performance' keywords
        insight_text = " ".join(insights).lower()
        assert "algorithm" in insight_text or "performance" in insight_text

    @pytest.mark.asyncio
    async def test_generate_insights_with_user_profile(
        self, response_generator, sample_articles, sample_user_profile
    ):
        """Test generating insights with user profile personalization."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = "Machine learning is evolving rapidly. Python remains essential. Consider exploring deep learning next."

            insights = await response_generator._generate_insights(
                "machine learning", sample_articles, sample_user_profile
            )

            assert isinstance(insights, list)
            assert len(insights) <= 3
            assert all(len(insight) > 10 for insight in insights)

    def test_create_fallback_insights(self, response_generator, sample_articles):
        """Test creating fallback insights when LLM fails."""
        insights = response_generator._create_fallback_insights("machine learning", sample_articles)

        assert isinstance(insights, list)
        assert len(insights) <= 3
        assert len(insights) > 0
        assert "Found" in insights[0] and "articles" in insights[0]

    @pytest.mark.asyncio
    async def test_generate_recommendations(
        self, response_generator, sample_articles, sample_user_profile
    ):
        """Test generating recommendations for further reading."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = (
                "Explore neural networks. Try hands-on projects. Consider advanced algorithms."
            )

            recommendations = await response_generator._generate_recommendations(
                "machine learning", sample_articles, sample_user_profile
            )

            assert isinstance(recommendations, list)
            assert len(recommendations) <= 3
            assert all(len(rec) > 10 for rec in recommendations)

    def test_create_fallback_recommendations(self, response_generator, sample_articles):
        """Test creating fallback recommendations when LLM fails."""
        recommendations = response_generator._create_fallback_recommendations(
            "machine learning", sample_articles
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_summary_standalone(self, response_generator, sample_articles):
        """Test generating standalone summary for single article."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = (
                "Comprehensive machine learning introduction with practical examples."
            )

            summary = await response_generator.generate_summary(sample_articles[0])

            assert isinstance(summary, str)
            assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_generate_summary_api_failure(self, response_generator, sample_articles):
        """Test standalone summary generation with API failure."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.side_effect = Exception("API Error")

            with pytest.raises(ResponseGeneratorError):
                await response_generator.generate_summary(sample_articles[0])

    @pytest.mark.asyncio
    async def test_generate_insights_standalone(
        self, response_generator, sample_articles, sample_user_profile
    ):
        """Test generating standalone insights."""
        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = "Key insight about machine learning trends."

            insights = await response_generator.generate_insights(
                sample_articles, sample_user_profile
            )

            assert isinstance(insights, list)
            assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_max_articles_limit(self, response_generator):
        """Test that response generator limits articles to maximum of 5."""
        # Create 10 articles
        many_articles = []
        for i in range(10):
            many_articles.append(
                ArticleMatch(
                    article_id=str(uuid4()),
                    title=f"Article {i}",
                    content_preview=f"Content for article {i}",
                    similarity_score=0.9 - (i * 0.05),  # Decreasing scores
                    metadata={},
                    url=f"https://example.com/article-{i}",
                )
            )

        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = "Test response"

            response = await response_generator.generate_response(
                query="test query", articles=many_articles
            )

            # Should limit to 5 articles
            assert len(response.articles) == 5

            # Should be sorted by relevance (highest first)
            scores = [article.relevance_score for article in response.articles]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_language_preference_handling(self, response_generator, sample_articles):
        """Test handling of different language preferences."""
        # Test Chinese preference
        chinese_profile = UserProfile(
            user_id=uuid4(),
            reading_history=[],
            preferred_topics=[],
            language_preference="zh",
            interaction_patterns={},
            query_history=[],
            satisfaction_scores=[],
        )

        with patch.object(response_generator, "_call_openai_api") as mock_api:
            mock_api.return_value = "Chinese response"

            response = await response_generator.generate_response(
                query="test query", articles=sample_articles[:1], user_profile=chinese_profile
            )

            # Verify API was called with Chinese language instruction
            assert mock_api.called
            call_args = mock_api.call_args_list[0][0][0]  # First call, first arg (messages)
            system_message = call_args[0]["content"]
            assert "Chinese" in system_message
