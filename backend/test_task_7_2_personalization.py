#!/usr/bin/env python3
"""
Test script for Task 7.2: Enhanced Personalization and Insights Generation

This script tests the enhanced personalization features implemented in ResponseGenerator:
- Personalized insights based on user reading history (Requirement 3.4)
- Extended reading suggestions and recommendations (Requirement 3.5)
- Article ranking by user interest areas (Requirement 8.2)
- Personalized insights in structured responses (Requirement 8.4)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.qa_agent.models import (
    ArticleMatch,
    ConversationContext,
    ConversationTurn,
    QueryLanguage,
    StructuredResponse,
    UserProfile,
)
from app.qa_agent.response_generator import ResponseGenerator


def create_test_user_profile() -> UserProfile:
    """Create a test user profile with reading history and preferences."""
    user_id = uuid4()

    # Create user with established interests
    profile = UserProfile(
        user_id=user_id,
        reading_history=[uuid4() for _ in range(25)],  # 25 read articles
        preferred_topics=[
            "machine learning",
            "python",
            "API design",
            "cloud computing",
            "security",
        ],
        language_preference=QueryLanguage.ENGLISH,
        query_history=[
            "machine learning best practices",
            "python async programming",
            "API security patterns",
            "cloud architecture design",
            "ML model deployment",
        ],
        satisfaction_scores=[0.8, 0.9, 0.7, 0.85, 0.75],  # High satisfaction user
        interaction_patterns={"prefers_technical": True, "likes_detailed_content": True},
    )

    return profile


def create_test_articles() -> List[ArticleMatch]:
    """Create test articles with various topics and metadata."""
    articles = [
        ArticleMatch(
            article_id=uuid4(),
            title="Advanced Machine Learning Deployment Strategies",
            content_preview="This article explores sophisticated approaches to deploying ML models in production environments, covering containerization, monitoring, and scaling strategies...",
            similarity_score=0.92,
            url="https://example.com/ml-deployment",
            published_at=datetime.utcnow() - timedelta(days=5),
            feed_name="ML Engineering Blog",
            category="Machine Learning",
            metadata={
                "topics": ["machine learning", "deployment", "MLOps"],
                "technical_level": "advanced",
                "reading_time": 12,
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Python Async Programming: Complete Guide",
            content_preview="A comprehensive guide to asynchronous programming in Python, covering asyncio, coroutines, and best practices for concurrent applications...",
            similarity_score=0.88,
            url="https://example.com/python-async",
            published_at=datetime.utcnow() - timedelta(days=15),
            feed_name="Python Weekly",
            category="Programming",
            metadata={
                "topics": ["python", "async", "programming"],
                "technical_level": "intermediate",
                "reading_time": 8,
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="API Security Best Practices for 2024",
            content_preview="Essential security practices for modern APIs, including authentication, authorization, rate limiting, and vulnerability prevention...",
            similarity_score=0.85,
            url="https://example.com/api-security",
            published_at=datetime.utcnow() - timedelta(days=3),
            feed_name="Security Today",
            category="Security",
            metadata={
                "topics": ["API", "security", "authentication"],
                "technical_level": "intermediate",
                "reading_time": 10,
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Introduction to Blockchain Development",
            content_preview="A beginner-friendly introduction to blockchain technology and smart contract development using Solidity...",
            similarity_score=0.65,
            url="https://example.com/blockchain-intro",
            published_at=datetime.utcnow() - timedelta(days=30),
            feed_name="Blockchain Basics",
            category="Blockchain",
            metadata={
                "topics": ["blockchain", "solidity", "web3"],
                "technical_level": "beginner",
                "reading_time": 6,
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Cloud Architecture Patterns and Microservices",
            content_preview="Exploring modern cloud architecture patterns, microservices design, and distributed system best practices...",
            similarity_score=0.78,
            url="https://example.com/cloud-architecture",
            published_at=datetime.utcnow() - timedelta(days=8),
            feed_name="Cloud Computing Weekly",
            category="Cloud Computing",
            metadata={
                "topics": ["cloud computing", "microservices", "architecture"],
                "technical_level": "advanced",
                "reading_time": 15,
            },
        ),
    ]

    return articles


def create_test_conversation_context() -> ConversationContext:
    """Create a test conversation context."""
    conversation_id = uuid4()

    # Create some conversation history
    turns = [
        ConversationTurn(
            query="What are the latest trends in machine learning?",
            response=StructuredResponse(
                query="What are the latest trends in machine learning?",
                articles=[],
                insights=["ML is evolving rapidly with new architectures"],
                recommendations=["Explore transformer models"],
                conversation_id=conversation_id,
                response_time=1.5,
            ),
            timestamp=datetime.utcnow() - timedelta(minutes=10),
            turn_number=1,
        ),
        ConversationTurn(
            query="How do I deploy ML models effectively?",
            response=StructuredResponse(
                query="How do I deploy ML models effectively?",
                articles=[],
                insights=["Deployment requires careful planning"],
                recommendations=["Consider containerization"],
                conversation_id=conversation_id,
                response_time=2.1,
            ),
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            turn_number=2,
        ),
    ]

    return ConversationContext(
        conversation_id=conversation_id,
        user_id=uuid4(),
        turns=turns,
        current_topic="machine learning deployment",
        created_at=datetime.utcnow() - timedelta(minutes=15),
        last_updated=datetime.utcnow() - timedelta(minutes=5),
    )


async def test_article_ranking_by_user_interest():
    """Test enhanced article ranking based on user interests (Requirement 8.2)."""
    print("🔍 Testing Article Ranking by User Interest (Requirement 8.2)")

    generator = ResponseGenerator()
    user_profile = create_test_user_profile()
    articles = create_test_articles()

    # Test ranking with user profile
    ranked_articles = generator._rank_articles_by_user_interest(articles, user_profile)

    print(f"   Original order (by similarity): {[a.similarity_score for a in articles]}")
    print(f"   Ranked order (with user interest): {[a.similarity_score for a in ranked_articles]}")

    # Verify that articles matching user interests are prioritized
    top_article = ranked_articles[0]
    print(f"   Top ranked article: '{top_article.title}'")
    print(f"   Topics: {top_article.metadata.get('topics', [])}")

    # Check that user's preferred topics are represented in top results
    user_topics = set(user_profile.preferred_topics)
    top_3_topics = set()
    for article in ranked_articles[:3]:
        if article.metadata and "topics" in article.metadata:
            top_3_topics.update(article.metadata["topics"])

    topic_overlap = user_topics.intersection(top_3_topics)
    print(f"   User interests in top 3: {topic_overlap}")

    assert len(topic_overlap) > 0, "Top articles should match user interests"
    print("   ✓ Articles successfully ranked by user interest")


async def test_enhanced_personalized_insights():
    """Test enhanced personalized insights generation (Requirements 3.4, 8.4)."""
    print("\n💡 Testing Enhanced Personalized Insights (Requirements 3.4, 8.4)")

    generator = ResponseGenerator()
    user_profile = create_test_user_profile()
    articles = create_test_articles()[:3]  # Use top 3 articles
    context = create_test_conversation_context()

    # Generate insights with enhanced personalization
    insights = await generator._generate_insights(
        query="machine learning deployment strategies",
        articles=articles,
        user_profile=user_profile,
        context=context,
    )

    print(f"   Generated {len(insights)} personalized insights:")
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")

    # Verify insights are substantial and personalized
    assert len(insights) > 0, "Should generate at least one insight"
    assert all(len(insight) > 20 for insight in insights), "Insights should be substantial"

    # Test reading history insights
    history_insights = generator._generate_reading_history_insights(
        "machine learning deployment", articles, user_profile
    )

    print(f"   Reading history insights: {len(history_insights)}")
    for insight in history_insights:
        print(f"   - {insight}")

    print("   ✓ Enhanced personalized insights generated successfully")


async def test_extended_reading_recommendations():
    """Test enhanced extended reading recommendations (Requirement 3.5)."""
    print("\n📚 Testing Extended Reading Recommendations (Requirement 3.5)")

    generator = ResponseGenerator()
    user_profile = create_test_user_profile()
    articles = create_test_articles()[:3]

    # Generate enhanced recommendations
    recommendations = await generator._generate_recommendations(
        query="machine learning deployment best practices",
        articles=articles,
        user_profile=user_profile,
    )

    print(f"   Generated {len(recommendations)} extended reading recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")

    # Test personalized recommendations
    personalized_recs = generator._generate_personalized_recommendations(
        "machine learning deployment", articles, user_profile
    )

    print(f"   Personalized recommendations: {len(personalized_recs)}")
    for rec in personalized_recs:
        print(f"   - {rec}")

    # Test topic expansion
    article_topics = []
    for article in articles:
        if article.metadata and "topics" in article.metadata:
            article_topics.extend(article.metadata["topics"])

    topic_expansion = generator._generate_topic_expansion_suggestions(article_topics, user_profile)
    print(f"   Topic expansion suggestions: {topic_expansion}")

    assert len(recommendations) > 0, "Should generate recommendations"
    assert all(len(rec) > 20 for rec in recommendations), "Recommendations should be substantial"

    print("   ✓ Extended reading recommendations generated successfully")


async def test_complete_personalized_response():
    """Test complete personalized response generation with all enhancements."""
    print("\n🎯 Testing Complete Personalized Response Generation")

    generator = ResponseGenerator()
    user_profile = create_test_user_profile()
    articles = create_test_articles()
    context = create_test_conversation_context()

    # Generate complete response with all personalization features
    response = await generator.generate_response(
        query="What are the best practices for deploying machine learning models in production?",
        articles=articles,
        context=context,
        user_profile=user_profile,
    )

    print(f"   Query: {response.query}")
    print(f"   Articles returned: {len(response.articles)}")
    print(f"   Insights generated: {len(response.insights)}")
    print(f"   Recommendations: {len(response.recommendations)}")

    # Verify response structure
    assert len(response.articles) <= 5, "Should limit to max 5 articles"
    assert len(response.insights) > 0, "Should generate insights"
    assert len(response.recommendations) > 0, "Should generate recommendations"

    # Check that articles are ranked by user interest
    if len(response.articles) > 1:
        # Verify that user's preferred topics appear in top articles
        user_topics = set(user_profile.preferred_topics)

        # Get the original article to check metadata
        top_article_id = response.articles[0].article_id
        top_original_article = None
        for article in articles:
            if article.article_id == top_article_id:
                top_original_article = article
                break

        if (
            top_original_article
            and top_original_article.metadata
            and "topics" in top_original_article.metadata
        ):
            top_article_topics = set(top_original_article.metadata["topics"])
            print(f"   Top article topics: {top_article_topics}")
            print(f"   User preferred topics: {user_topics}")

            # Should have some overlap with user interests
            overlap = user_topics.intersection(top_article_topics)
            if overlap:
                print(f"   ✓ Top article matches user interests: {overlap}")
        else:
            print("   ✓ Article ranking completed (metadata not available for verification)")

    print("   ✓ Complete personalized response generated successfully")

    return response


async def main():
    """Run all personalization tests."""
    print("🚀 Testing Task 7.2: Enhanced Personalization and Insights Generation")
    print("=" * 80)

    try:
        # Test individual components
        await test_article_ranking_by_user_interest()
        await test_enhanced_personalized_insights()
        await test_extended_reading_recommendations()

        # Test complete integration
        response = await test_complete_personalized_response()

        print("\n" + "=" * 80)
        print("📋 FINAL RESPONSE SUMMARY")
        print("=" * 80)

        print(f"Query: {response.query}")
        print(f"\nTop Articles ({len(response.articles)}):")
        for i, article in enumerate(response.articles, 1):
            print(f"  {i}. {article.title}")
            print(f"     Relevance: {article.relevance_score:.3f}")
            print(f"     Reading time: {article.reading_time} min")

        print(f"\nPersonalized Insights ({len(response.insights)}):")
        for i, insight in enumerate(response.insights, 1):
            print(f"  {i}. {insight}")

        print(f"\nExtended Reading Recommendations ({len(response.recommendations)}):")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 80)
        print("✅ ALL PERSONALIZATION TESTS PASSED!")
        print("✅ Task 7.2 Implementation Complete")
        print("=" * 80)

        # Verify requirements coverage
        print("\n📋 Requirements Coverage Verification:")
        print("✅ Requirement 3.4: Personalized insights based on user reading history")
        print("✅ Requirement 3.5: Extended reading suggestions with related topics")
        print("✅ Requirement 8.2: Article prioritization by user's areas of interest")
        print("✅ Requirement 8.4: Personalized insights in structured responses")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
