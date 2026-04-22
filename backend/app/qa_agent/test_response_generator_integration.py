"""
Integration test for ResponseGenerator with existing QA Agent components.

This test verifies that the ResponseGenerator integrates correctly with
the existing retrieval engine and other components.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Skip config loading for testing
os.environ["SKIP_CONFIG_LOAD"] = "1"

from qa_agent.models import ArticleMatch, ConversationContext, UserProfile
from qa_agent.response_generator import ResponseGenerator


async def test_response_generator_integration():
    """Test ResponseGenerator integration with mock data."""

    # Create test data
    articles = [
        ArticleMatch(
            article_id=str(uuid4()),
            title="Introduction to Machine Learning",
            content_preview="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. This comprehensive guide covers the fundamentals of ML algorithms, supervised and unsupervised learning, and practical applications in various industries.",
            similarity_score=0.95,
            metadata={"category": "AI", "topics": ["machine learning", "algorithms"]},
            url="https://example.com/ml-intro",
        ),
        ArticleMatch(
            article_id=str(uuid4()),
            title="Python for Data Science",
            content_preview="Python has become the go-to language for data science due to its simplicity and powerful libraries. Learn how to use pandas for data manipulation, numpy for numerical computing, and scikit-learn for machine learning implementations.",
            similarity_score=0.88,
            metadata={"category": "Programming", "topics": ["python", "data science"]},
            url="https://example.com/python-data-science",
        ),
    ]

    user_profile = UserProfile(
        user_id=uuid4(),
        reading_history=[uuid4(), uuid4()],
        preferred_topics=["machine learning", "python", "data science"],
        language_preference="en",
        interaction_patterns={"avg_reading_time": 300},
        query_history=["machine learning basics", "python tutorials"],
        satisfaction_scores=[4.5, 4.8, 4.2],
    )

    conversation_context = ConversationContext(
        conversation_id=str(uuid4()),
        user_id=uuid4(),
        turns=[],
        current_topic="machine learning",
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    # Test ResponseGenerator
    generator = ResponseGenerator()

    print("Testing ResponseGenerator with mock OpenAI API...")

    # Mock the OpenAI client to avoid actual API calls
    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    class MockOpenAIClient:
        def __init__(self):
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            # Return different responses based on the prompt content
            messages = kwargs.get("messages", [])
            if any("summary" in msg.get("content", "").lower() for msg in messages):
                return MockResponse(
                    "This article provides a comprehensive introduction to machine learning concepts and practical applications."
                )
            elif any("insight" in msg.get("content", "").lower() for msg in messages):
                return MockResponse(
                    "Machine learning is transforming industries. Python remains the preferred language. Consider exploring deep learning next."
                )
            elif any("recommendation" in msg.get("content", "").lower() for msg in messages):
                return MockResponse(
                    "Explore neural networks. Try hands-on projects. Consider advanced algorithms."
                )
            else:
                return MockResponse("This is a test response from the mock OpenAI client.")

    # Replace the client with our mock
    generator.client = MockOpenAIClient()

    try:
        # Test response generation
        response = await generator.generate_response(
            query="machine learning basics",
            articles=articles,
            context=conversation_context,
            user_profile=user_profile,
        )

        print("✅ Response generated successfully!")
        print(f"   Query: {response.query}")
        print(f"   Articles: {len(response.articles)}")
        print(f"   Insights: {len(response.insights)}")
        print(f"   Recommendations: {len(response.recommendations)}")

        # Verify response structure
        assert response.query == "machine learning basics"
        assert len(response.articles) == 2
        assert len(response.insights) > 0
        assert len(response.recommendations) > 0
        assert response.conversation_id == conversation_context.conversation_id

        # Test article summaries
        for i, article_summary in enumerate(response.articles):
            print(f"   Article {i+1}: {article_summary.title}")
            print(f"   Summary: {article_summary.summary[:100]}...")
            assert len(article_summary.summary) > 0
            assert article_summary.url.startswith("https://")

        # Test insights
        print("   Insights:")
        for insight in response.insights:
            print(f"   - {insight}")

        # Test recommendations
        print("   Recommendations:")
        for rec in response.recommendations:
            print(f"   - {rec}")

        print("✅ All integration tests passed!")

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_response_generator_integration())
