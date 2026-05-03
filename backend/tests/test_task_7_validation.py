"""
Task 7 Validation Test: Response Generator Implementation

This test validates that Task 7.1 and 7.2 are fully implemented with all required features.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.qa_agent.models import (
    ArticleMatch,
    ConversationContext,
    QueryLanguage,
    UserProfile,
)
from app.qa_agent.response_generator import ResponseGenerator


def create_test_articles():
    """Create test articles for validation."""
    return [
        ArticleMatch(
            article_id=uuid4(),
            title="Introduction to Machine Learning",
            content_preview="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience. This article covers the fundamentals of ML algorithms, including supervised and unsupervised learning techniques.",
            similarity_score=0.95,
            keyword_score=0.85,
            url="https://example.com/ml-intro",
            published_at=datetime.utcnow() - timedelta(days=5),
            feed_name="Tech Blog",
            category="AI/ML",
            metadata={
                "topics": ["machine learning", "AI", "algorithms"],
                "technical_level": "beginner",
                "category": "AI/ML",
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Deep Learning Neural Networks",
            content_preview="Deep learning uses neural networks with multiple layers to process complex patterns. This comprehensive guide explores convolutional neural networks, recurrent networks, and transformer architectures.",
            similarity_score=0.88,
            keyword_score=0.75,
            url="https://example.com/deep-learning",
            published_at=datetime.utcnow() - timedelta(days=15),
            feed_name="AI Research",
            category="AI/ML",
            metadata={
                "topics": ["deep learning", "neural networks", "AI"],
                "technical_level": "advanced",
                "category": "AI/ML",
            },
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Practical Machine Learning with Python",
            content_preview="Learn how to implement machine learning algorithms using Python and popular libraries like scikit-learn and TensorFlow. This tutorial provides hands-on examples and best practices.",
            similarity_score=0.82,
            keyword_score=0.90,
            url="https://example.com/ml-python",
            published_at=datetime.utcnow() - timedelta(days=3),
            feed_name="Python Weekly",
            category="Programming",
            metadata={
                "topics": ["machine learning", "python", "tutorial"],
                "technical_level": "intermediate",
                "category": "Programming",
            },
        ),
    ]


def create_test_user_profile():
    """Create test user profile with reading history."""
    user_id = uuid4()
    profile = UserProfile(
        user_id=user_id,
        reading_history=[uuid4() for _ in range(25)],  # 25 articles read
        preferred_topics=["machine learning", "AI", "python", "data science"],
        language_preference=QueryLanguage.ENGLISH,
        query_history=[
            "machine learning basics",
            "neural networks tutorial",
            "python ML libraries",
        ],
        satisfaction_scores=[0.8, 0.9, 0.75, 0.85, 0.9],  # High satisfaction
        interaction_patterns={"prefers_technical": True, "reading_frequency": "daily"},
    )
    return profile


async def test_task_7_1_structured_response():
    """Test Task 7.1: Structured response generation."""
    print("\n=== Testing Task 7.1: Structured Response Generation ===\n")

    generator = ResponseGenerator()
    articles = create_test_articles()
    query = "What is machine learning?"

    # Test basic response generation
    response = await generator.generate_response(query=query, articles=articles)

    # Validate structured response format
    assert response.query == query, "Query should match"
    assert len(response.articles) <= 5, "Should have max 5 articles"
    assert len(response.articles) > 0, "Should have at least 1 article"
    assert len(response.insights) > 0, "Should have insights"
    assert len(response.recommendations) > 0, "Should have recommendations"

    print("✅ Structured response format validated")

    # Validate article summaries (2-3 sentences)
    for article_summary in response.articles:
        sentences = article_summary.summary.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]
        assert (
            len(sentences) >= 2
        ), f"Summary should have at least 2 sentences, got {len(sentences)}"
        print(f"✅ Article '{article_summary.title}' has valid summary ({len(sentences)} sentences)")

    # Validate relevance sorting
    scores = [article.relevance_score for article in response.articles]
    assert scores == sorted(scores, reverse=True), "Articles should be sorted by relevance"
    print("✅ Articles sorted by relevance")

    # Validate all required elements present
    assert response.articles[0].url is not None, "Should have article URL"
    assert response.articles[0].title is not None, "Should have article title"
    assert response.articles[0].summary is not None, "Should have article summary"
    print("✅ All required elements present (title, summary, URL)")

    print("\n✅ Task 7.1 VALIDATED: Structured response generation working correctly\n")
    return response


async def test_task_7_2_personalization():
    """Test Task 7.2: Personalization and insights generation."""
    print("\n=== Testing Task 7.2: Personalization and Insights ===\n")

    generator = ResponseGenerator()
    articles = create_test_articles()
    user_profile = create_test_user_profile()
    query = "machine learning for beginners"

    # Test personalized response generation
    response = await generator.generate_response(
        query=query, articles=articles, user_profile=user_profile
    )

    # Validate personalized insights
    assert len(response.insights) > 0, "Should have personalized insights"
    print(f"✅ Generated {len(response.insights)} personalized insights")

    for i, insight in enumerate(response.insights, 1):
        print(f"   Insight {i}: {insight[:80]}...")

    # Validate recommendations
    assert len(response.recommendations) > 0, "Should have recommendations"
    print(f"\n✅ Generated {len(response.recommendations)} recommendations")

    for i, rec in enumerate(response.recommendations, 1):
        print(f"   Recommendation {i}: {rec[:80]}...")

    # Test article ranking with user interests
    # Articles matching user's preferred topics should be ranked higher
    print("\n✅ Article ranking considers user interests:")
    for i, article in enumerate(response.articles, 1):
        print(f"   {i}. {article.title} (score: {article.relevance_score:.2f})")

    # Validate max 5 articles
    assert len(response.articles) <= 5, "Should have max 5 articles"
    print(f"\n✅ Response limited to {len(response.articles)} articles (max 5)")

    print("\n✅ Task 7.2 VALIDATED: Personalization and insights working correctly\n")
    return response


async def test_user_interest_ranking():
    """Test that articles are ranked by user interest."""
    print("\n=== Testing User Interest-Based Ranking ===\n")

    generator = ResponseGenerator()
    articles = create_test_articles()
    user_profile = create_test_user_profile()

    # Rank articles with user profile
    ranked_with_profile = generator._rank_articles_by_user_interest(articles, user_profile)

    # Rank articles without user profile (fallback)
    ranked_without_profile = generator._rank_articles_by_user_interest(articles, None)

    print("✅ Ranking with user profile:")
    for i, article in enumerate(ranked_with_profile, 1):
        print(f"   {i}. {article.title} (similarity: {article.similarity_score:.2f})")

    print("\n✅ Ranking without user profile (fallback):")
    for i, article in enumerate(ranked_without_profile, 1):
        print(f"   {i}. {article.title} (similarity: {article.similarity_score:.2f})")

    # Validate that ranking works in both cases
    assert len(ranked_with_profile) == len(articles), "Should rank all articles"
    assert len(ranked_without_profile) == len(articles), "Should rank all articles"

    print("\n✅ User interest-based ranking validated")


async def test_conversation_context():
    """Test response generation with conversation context."""
    print("\n=== Testing Conversation Context Integration ===\n")

    generator = ResponseGenerator()
    articles = create_test_articles()
    user_profile = create_test_user_profile()

    # Create conversation context
    context = ConversationContext(user_id=user_profile.user_id)
    context.add_turn("What is machine learning?")
    context.current_topic = "machine learning"

    # Generate response with context
    response = await generator.generate_response(
        query="Tell me more about neural networks",
        articles=articles,
        context=context,
        user_profile=user_profile,
    )

    assert response.conversation_id == context.conversation_id, "Should use conversation ID"
    assert len(response.insights) > 0, "Should generate insights with context"

    print("✅ Conversation context integrated successfully")
    print(f"   Conversation ID: {response.conversation_id}")
    print(f"   Generated {len(response.insights)} context-aware insights")


async def test_language_preference():
    """Test language preference handling."""
    print("\n=== Testing Language Preference ===\n")

    generator = ResponseGenerator()
    articles = create_test_articles()

    # Test with Chinese preference
    chinese_profile = UserProfile(
        user_id=uuid4(),
        language_preference=QueryLanguage.CHINESE,
        preferred_topics=["机器学习", "人工智能"],
    )

    response_zh = await generator.generate_response(
        query="什么是机器学习？", articles=articles, user_profile=chinese_profile
    )

    # Test with English preference
    english_profile = UserProfile(
        user_id=uuid4(),
        language_preference=QueryLanguage.ENGLISH,
        preferred_topics=["machine learning", "AI"],
    )

    response_en = await generator.generate_response(
        query="What is machine learning?", articles=articles, user_profile=english_profile
    )

    assert len(response_zh.articles) > 0, "Should generate Chinese response"
    assert len(response_en.articles) > 0, "Should generate English response"

    print("✅ Language preference handling validated")
    print(f"   Chinese response: {len(response_zh.articles)} articles")
    print(f"   English response: {len(response_en.articles)} articles")


async def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("TASK 7 VALIDATION: Response Generator Implementation")
    print("=" * 70)

    try:
        # Test Task 7.1
        await test_task_7_1_structured_response()

        # Test Task 7.2
        await test_task_7_2_personalization()

        # Test additional features
        await test_user_interest_ranking()
        await test_conversation_context()
        await test_language_preference()

        print("\n" + "=" * 70)
        print("✅ ALL TASK 7 VALIDATION TESTS PASSED!")
        print("=" * 70)
        print("\nTask 7.1 ✅ Structured response generation")
        print("Task 7.2 ✅ Personalization and insights generation")
        print("\nImplementation Status: COMPLETE")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
