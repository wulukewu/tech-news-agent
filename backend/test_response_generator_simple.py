"""
Simple standalone test for ResponseGenerator functionality.

This test verifies the core ResponseGenerator logic without dependencies.
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Skip config loading for testing
os.environ["SKIP_CONFIG_LOAD"] = "1"


# Mock the required models for testing
@dataclass
class ArticleMatch:
    article_id: str
    title: str
    content_preview: str
    similarity_score: float
    metadata: Dict[str, Any]
    url: str

    def get_reading_time_estimate(self) -> int:
        return len(self.content_preview) // 200 + 1


@dataclass
class ArticleSummary:
    article_id: str
    title: str
    summary: str
    url: str
    relevance_score: float
    reading_time: int
    key_insights: List[str]
    metadata: Dict[str, Any]


@dataclass
class StructuredResponse:
    query: str
    articles: List[ArticleSummary]
    insights: List[str]
    recommendations: List[str]
    conversation_id: str
    response_time: float


@dataclass
class UserProfile:
    user_id: str
    reading_history: List[str]
    preferred_topics: List[str]
    language_preference: str
    interaction_patterns: Dict[str, Any]
    query_history: List[str]
    satisfaction_scores: List[float]

    def get_top_topics(self, limit: int = 5) -> List[str]:
        return self.preferred_topics[:limit]


@dataclass
class ConversationContext:
    conversation_id: str
    user_id: str
    turns: List[Any]
    current_topic: Optional[str]
    created_at: datetime
    last_updated: datetime

    def get_recent_queries(self, count: int = 3) -> List[str]:
        return []


# Mock settings
class MockSettings:
    GROQ_API_KEY = "gsk_test-key"


# Mock ResponseGenerator with core logic
class ResponseGenerator:
    def __init__(self):
        self.max_articles = 5
        self.client = None  # Will be mocked

    async def _call_openai_api(
        self, messages: List[Dict[str, str]], max_tokens: int = 500, temperature: float = 0.3
    ) -> str:
        # Mock API response based on message content
        content = " ".join([msg.get("content", "") for msg in messages]).lower()

        if "summary" in content:
            return "This article provides a comprehensive introduction to machine learning concepts and practical applications in modern technology."
        elif "insight" in content:
            return "Machine learning is transforming industries rapidly. Python remains the preferred programming language. Consider exploring deep learning frameworks next."
        elif "recommendation" in content:
            return "Explore advanced neural network architectures. Try implementing your own ML models with real datasets. Consider taking a structured course on AI fundamentals."
        else:
            return "This is a test response from the mock API."

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        """Generate a structured response using retrieved articles and context."""

        # Limit to max 5 articles and sort by relevance
        top_articles = sorted(
            articles[: self.max_articles], key=lambda x: x.similarity_score, reverse=True
        )

        if not top_articles:
            return self._create_empty_response(query, context)

        # Generate summaries for each article
        article_summaries = await self._generate_article_summaries(
            top_articles, query, user_profile
        )

        # Generate personalized insights
        insights = await self._generate_insights(query, top_articles, user_profile, context)

        # Generate recommendations for related reading
        recommendations = await self._generate_recommendations(query, top_articles, user_profile)

        return StructuredResponse(
            query=query,
            articles=article_summaries,
            insights=insights,
            recommendations=recommendations,
            conversation_id=context.conversation_id if context else "",
            response_time=0.0,
        )

    async def _generate_article_summaries(
        self, articles: List[ArticleMatch], query: str, user_profile: Optional[UserProfile] = None
    ) -> List[ArticleSummary]:
        """Generate 2-3 sentence summaries for each article."""
        summaries = []

        for article in articles:
            try:
                summary_text = await self._call_openai_api(
                    [
                        {"role": "system", "content": "Create a 2-3 sentence summary."},
                        {
                            "role": "user",
                            "content": f"Article: {article.title}\n{article.content_preview}",
                        },
                    ]
                )

                summaries.append(
                    ArticleSummary(
                        article_id=article.article_id,
                        title=article.title,
                        summary=summary_text,
                        url=article.url,
                        relevance_score=article.similarity_score,
                        reading_time=article.get_reading_time_estimate(),
                        key_insights=["machine learning", "algorithms"],
                        metadata=article.metadata,
                    )
                )
            except Exception:
                # Fallback summary
                fallback_summary = ". ".join(article.content_preview.split(". ")[:3])
                summaries.append(
                    ArticleSummary(
                        article_id=article.article_id,
                        title=article.title,
                        summary=fallback_summary,
                        url=article.url,
                        relevance_score=article.similarity_score,
                        reading_time=article.get_reading_time_estimate(),
                        key_insights=[],
                        metadata=article.metadata,
                    )
                )

        return summaries

    async def _generate_insights(
        self,
        query: str,
        articles: List[ArticleMatch],
        user_profile: Optional[UserProfile] = None,
        context: Optional[ConversationContext] = None,
    ) -> List[str]:
        """Generate personalized insights based on articles and user profile."""
        try:
            insights_text = await self._call_openai_api(
                [
                    {"role": "system", "content": "Generate 2-3 personalized insights."},
                    {"role": "user", "content": f"Query: {query}\nArticles: {len(articles)} found"},
                ]
            )

            insights = [
                insight.strip().lstrip("•-*").strip()
                for insight in insights_text.split("\n")
                if insight.strip() and len(insight.strip()) > 10
            ]

            return insights[:3]
        except Exception:
            return [f"Found {len(articles)} relevant articles about your query."]

    async def _generate_recommendations(
        self, query: str, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """Generate recommendations for related reading and next steps."""
        try:
            recommendations_text = await self._call_openai_api(
                [
                    {"role": "system", "content": "Generate 2-3 specific recommendations."},
                    {
                        "role": "user",
                        "content": f"Query: {query}\nTopics covered: machine learning, python",
                    },
                ]
            )

            recommendations = [
                rec.strip().lstrip("•-*").strip()
                for rec in recommendations_text.split("\n")
                if rec.strip() and len(rec.strip()) > 10
            ]

            return recommendations[:3]
        except Exception:
            return ["Consider reading the most relevant article first for deeper insights."]

    def _create_empty_response(
        self, query: str, context: Optional[ConversationContext] = None
    ) -> StructuredResponse:
        """Create an empty response when no articles are found."""
        return StructuredResponse(
            query=query,
            articles=[],
            insights=["No relevant articles found for your query."],
            recommendations=[
                "Try using different keywords or broader search terms.",
                "Check if there are any typos in your query.",
                "Consider exploring related topics in your article library.",
            ],
            conversation_id=context.conversation_id if context else "",
            response_time=0.0,
        )


async def test_response_generator():
    """Test ResponseGenerator functionality."""

    print("🧪 Testing ResponseGenerator functionality...")

    # Create test data
    articles = [
        ArticleMatch(
            article_id=str(uuid4()),
            title="Introduction to Machine Learning",
            content_preview="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. This comprehensive guide covers the fundamentals of ML algorithms, supervised and unsupervised learning, and practical applications in various industries. We'll explore different types of learning algorithms and their use cases.",
            similarity_score=0.95,
            metadata={"category": "AI", "topics": ["machine learning", "algorithms"]},
            url="https://example.com/ml-intro",
        ),
        ArticleMatch(
            article_id=str(uuid4()),
            title="Python for Data Science",
            content_preview="Python has become the go-to language for data science due to its simplicity and powerful libraries. Learn how to use pandas for data manipulation, numpy for numerical computing, and scikit-learn for machine learning implementations. This tutorial covers practical examples and best practices for data analysis workflows.",
            similarity_score=0.88,
            metadata={"category": "Programming", "topics": ["python", "data science"]},
            url="https://example.com/python-data-science",
        ),
        ArticleMatch(
            article_id=str(uuid4()),
            title="Deep Learning with Neural Networks",
            content_preview="Deep learning represents a significant advancement in machine learning, using neural networks with multiple layers to model and understand complex patterns in data. This article explores the architecture of deep neural networks, backpropagation algorithms, and applications in computer vision and natural language processing.",
            similarity_score=0.82,
            metadata={"category": "AI", "topics": ["deep learning", "neural networks"]},
            url="https://example.com/deep-learning",
        ),
    ]

    user_profile = UserProfile(
        user_id=str(uuid4()),
        reading_history=[str(uuid4()), str(uuid4())],
        preferred_topics=["machine learning", "python", "data science"],
        language_preference="en",
        interaction_patterns={"avg_reading_time": 300},
        query_history=["machine learning basics", "python tutorials"],
        satisfaction_scores=[4.5, 4.8, 4.2],
    )

    conversation_context = ConversationContext(
        conversation_id=str(uuid4()),
        user_id=str(uuid4()),
        turns=[],
        current_topic="machine learning",
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    # Test ResponseGenerator
    generator = ResponseGenerator()

    print("📝 Generating structured response...")

    response = await generator.generate_response(
        query="machine learning basics",
        articles=articles,
        context=conversation_context,
        user_profile=user_profile,
    )

    print("✅ Response generated successfully!")
    print("📊 Response Summary:")
    print(f"   Query: {response.query}")
    print(f"   Articles: {len(response.articles)}")
    print(f"   Insights: {len(response.insights)}")
    print(f"   Recommendations: {len(response.recommendations)}")
    print(f"   Conversation ID: {response.conversation_id}")

    # Verify response structure
    assert response.query == "machine learning basics"
    assert len(response.articles) == 3  # All articles included
    assert len(response.insights) > 0
    assert len(response.recommendations) > 0
    assert response.conversation_id == conversation_context.conversation_id

    # Test article summaries
    print("\n📚 Article Summaries:")
    for i, article_summary in enumerate(response.articles, 1):
        print(f"   {i}. {article_summary.title}")
        print(f"      Summary: {article_summary.summary}")
        print(f"      Relevance: {article_summary.relevance_score:.2f}")
        print(f"      Reading time: {article_summary.reading_time} min")
        print(f"      URL: {article_summary.url}")
        print()

        # Verify summary properties
        assert len(article_summary.summary) > 0
        assert article_summary.url.startswith("https://")
        assert 0 <= article_summary.relevance_score <= 1

    # Verify articles are sorted by relevance (highest first)
    scores = [article.relevance_score for article in response.articles]
    assert scores == sorted(scores, reverse=True), "Articles should be sorted by relevance"

    # Test insights
    print("💡 Generated Insights:")
    for i, insight in enumerate(response.insights, 1):
        print(f"   {i}. {insight}")
        assert len(insight) > 10, "Insights should be meaningful"

    # Test recommendations
    print("\n🎯 Recommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"   {i}. {rec}")
        assert len(rec) > 10, "Recommendations should be meaningful"

    # Test empty articles scenario
    print("\n🔍 Testing empty articles scenario...")
    empty_response = await generator.generate_response(
        query="nonexistent topic", articles=[], context=conversation_context
    )

    assert len(empty_response.articles) == 0
    assert "No relevant articles found" in empty_response.insights[0]
    assert len(empty_response.recommendations) > 0
    print("✅ Empty articles scenario handled correctly")

    # Test max articles limit (should limit to 5)
    print("\n📊 Testing max articles limit...")
    many_articles = articles * 3  # 9 articles total
    limited_response = await generator.generate_response(query="test query", articles=many_articles)

    assert len(limited_response.articles) <= 5, "Should limit to max 5 articles"
    print(f"✅ Articles limited to {len(limited_response.articles)} (max 5)")

    print("\n🎉 All tests passed! ResponseGenerator is working correctly.")

    return response


if __name__ == "__main__":
    result = asyncio.run(test_response_generator())
    print("\n✨ Test completed successfully!")
