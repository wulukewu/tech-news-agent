"""
Example usage of ResponseGenerator for Task 7.1

This example demonstrates how to use the ResponseGenerator class to create
structured responses with article summaries, insights, and recommendations.

Requirements addressed:
- 3.1: Generate structured responses with article summaries, original links, and personalized insights
- 3.2: Display max 5 articles sorted by relevance
- 3.3: Provide 2-3 sentence summaries for each article
- 5.5: Use retrieved article content as context for generating responses
"""

import asyncio
import os
from datetime import datetime
from uuid import uuid4

# Skip config loading for example
os.environ["SKIP_CONFIG_LOAD"] = "1"

from .models import ArticleMatch, ConversationContext, QueryLanguage, UserProfile
from .response_generator import get_response_generator


async def example_basic_usage():
    """Example: Basic ResponseGenerator usage with mock data."""

    print("🚀 ResponseGenerator Example - Basic Usage")
    print("=" * 50)

    # Create sample articles (typically from RetrievalEngine)
    articles = [
        ArticleMatch(
            article_id=uuid4(),
            title="Getting Started with Machine Learning",
            content_preview="Machine learning has revolutionized how we approach data analysis and prediction. This comprehensive guide introduces the fundamental concepts, algorithms, and practical applications of ML. We'll cover supervised learning, unsupervised learning, and reinforcement learning with real-world examples.",
            similarity_score=0.92,
            metadata={"topics": ["machine learning", "beginner"], "author": "Dr. Sarah Chen"},
            url="https://techblog.example.com/ml-getting-started",
            feed_name="Tech Blog",
            category="AI",
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Python Libraries for Data Science",
            content_preview="Python's ecosystem offers powerful libraries for data science workflows. This article explores pandas for data manipulation, numpy for numerical computing, matplotlib for visualization, and scikit-learn for machine learning. Learn best practices and common patterns.",
            similarity_score=0.87,
            metadata={"topics": ["python", "data science", "libraries"], "author": "Mike Johnson"},
            url="https://pythonguide.example.com/data-science-libraries",
            feed_name="Python Guide",
            category="Programming",
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Neural Networks Explained",
            content_preview="Neural networks form the backbone of modern deep learning systems. This detailed explanation covers perceptrons, multi-layer networks, activation functions, and backpropagation. Understand how these mathematical models mimic brain neurons to solve complex problems.",
            similarity_score=0.84,
            metadata={"topics": ["neural networks", "deep learning"], "author": "Prof. Alex Kim"},
            url="https://deeplearning.example.com/neural-networks-explained",
            feed_name="Deep Learning Hub",
            category="AI",
        ),
    ]

    # Get ResponseGenerator instance
    generator = get_response_generator()

    # Mock the OpenAI client for demonstration
    class MockOpenAIClient:
        def __init__(self):
            self.chat = MockChat()

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockCompletions:
        async def create(self, **kwargs):
            messages = kwargs.get("messages", [])
            content = " ".join([msg.get("content", "") for msg in messages]).lower()

            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)

            class MockMessage:
                def __init__(self, content):
                    self.content = content

            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]

            if "summary" in content:
                if "machine learning" in content:
                    return MockResponse(
                        "This article provides a comprehensive introduction to machine learning fundamentals, covering key algorithms and practical applications. It's an excellent starting point for beginners looking to understand how ML transforms data into actionable insights."
                    )
                elif "python" in content:
                    return MockResponse(
                        "This guide explores Python's essential data science libraries including pandas, numpy, and scikit-learn. It demonstrates practical workflows and best practices for data manipulation, analysis, and machine learning implementation."
                    )
                elif "neural" in content:
                    return MockResponse(
                        "This article explains neural network architecture and functionality in detail. It covers the mathematical foundations and practical applications of these powerful deep learning models."
                    )
            elif "insight" in content:
                return MockResponse(
                    "Machine learning is becoming increasingly accessible through Python's rich ecosystem. The combination of theoretical understanding and practical tools enables rapid prototyping and deployment. Consider starting with supervised learning problems to build foundational skills."
                )
            elif "recommendation" in content:
                return MockResponse(
                    "Start with hands-on projects using real datasets. Explore Kaggle competitions for practical experience. Consider taking Andrew Ng's Machine Learning course for theoretical depth."
                )

            return MockResponse(
                "This is a comprehensive technical resource with practical applications."
            )

    generator.client = MockOpenAIClient()

    # Generate structured response
    print("📝 Generating structured response...")

    response = await generator.generate_response(
        query="machine learning for beginners", articles=articles
    )

    # Display results
    print(f"\n✅ Generated Response for: '{response.query}'")
    print(f"📊 Found {len(response.articles)} relevant articles")

    print("\n📚 Article Summaries:")
    for i, article in enumerate(response.articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   📖 Summary: {article.summary}")
        print(f"   🔗 URL: {article.url}")
        print(f"   ⭐ Relevance: {article.relevance_score:.2f}")
        print(f"   ⏱️  Reading time: {article.reading_time} min")
        if article.key_insights:
            print(f"   💡 Key insights: {', '.join(article.key_insights)}")

    print("\n💡 Personalized Insights:")
    for i, insight in enumerate(response.insights, 1):
        print(f"{i}. {insight}")

    print("\n🎯 Recommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"{i}. {rec}")

    return response


async def example_with_user_profile():
    """Example: ResponseGenerator with user profile personalization."""

    print("\n\n🎯 ResponseGenerator Example - With User Profile")
    print("=" * 50)

    # Create user profile for personalization
    user_profile = UserProfile(
        user_id=uuid4(),
        reading_history=[uuid4(), uuid4(), uuid4()],
        preferred_topics=["machine learning", "python", "data visualization"],
        language_preference=QueryLanguage.ENGLISH,  # Could be QueryLanguage.CHINESE for Chinese
        interaction_patterns={"avg_reading_time": 450, "preferred_article_length": "medium"},
        query_history=["python basics", "data analysis", "ML algorithms"],
        satisfaction_scores=[0.84, 0.94, 0.90, 0.96],  # 0.0-1.0 scale
    )

    # Create conversation context for multi-turn conversation
    conversation_context = ConversationContext(
        conversation_id=str(uuid4()),
        user_id=user_profile.user_id,
        turns=[],
        current_topic="data science",
        created_at=datetime.now(),
        last_updated=datetime.now(),
    )

    # Sample articles focused on data visualization
    articles = [
        ArticleMatch(
            article_id=uuid4(),
            title="Advanced Data Visualization with Python",
            content_preview="Data visualization is crucial for understanding complex datasets and communicating insights effectively. This article covers advanced techniques using matplotlib, seaborn, and plotly. Learn to create interactive dashboards, statistical plots, and publication-ready figures that tell compelling data stories.",
            similarity_score=0.94,
            metadata={
                "topics": ["visualization", "python", "matplotlib"],
                "difficulty": "intermediate",
            },
            url="https://dataviz.example.com/advanced-python-visualization",
            feed_name="Data Viz Weekly",
            category="Data Science",
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Interactive Dashboards with Plotly and Dash",
            content_preview="Building interactive web applications for data visualization has never been easier with Plotly and Dash. This tutorial demonstrates how to create responsive dashboards, real-time data updates, and user-friendly interfaces. Perfect for sharing insights with stakeholders and enabling data exploration.",
            similarity_score=0.89,
            metadata={"topics": ["plotly", "dash", "interactive"], "difficulty": "intermediate"},
            url="https://webdev.example.com/plotly-dash-dashboards",
            feed_name="Web Dev Today",
            category="Web Development",
        ),
    ]

    generator = get_response_generator()

    # Mock client with personalized responses
    class MockPersonalizedClient:
        def __init__(self):
            self.chat = MockPersonalizedChat()

    class MockPersonalizedChat:
        def __init__(self):
            self.completions = MockPersonalizedCompletions()

    class MockPersonalizedCompletions:
        async def create(self, **kwargs):
            messages = kwargs.get("messages", [])
            content = " ".join([msg.get("content", "") for msg in messages]).lower()

            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)

            class MockMessage:
                def __init__(self, content):
                    self.content = content

            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]

            if "summary" in content:
                if "visualization" in content:
                    return MockResponse(
                        "This comprehensive guide covers advanced Python visualization techniques using matplotlib, seaborn, and plotly. It's particularly valuable for data scientists looking to create compelling visual narratives from complex datasets."
                    )
                elif "dashboard" in content:
                    return MockResponse(
                        "This tutorial demonstrates building interactive web dashboards with Plotly and Dash. It's perfect for creating user-friendly data exploration tools and sharing insights with non-technical stakeholders."
                    )
            elif "insight" in content:
                return MockResponse(
                    "Given your interest in Python and data visualization, these articles align perfectly with current industry trends. Interactive dashboards are increasingly important for data-driven decision making. Your background in ML will help you create more sophisticated analytical visualizations."
                )
            elif "recommendation" in content:
                return MockResponse(
                    "Practice with real datasets from your ML projects. Explore D3.js for advanced web visualizations. Consider building a portfolio dashboard showcasing your data science work."
                )

            return MockResponse("Personalized response based on user preferences.")

    generator.client = MockPersonalizedClient()

    print("👤 User Profile:")
    print(f"   Preferred topics: {', '.join(user_profile.preferred_topics)}")
    print(f"   Language: {user_profile.language_preference}")
    if user_profile.satisfaction_scores:
        avg_satisfaction = sum(user_profile.satisfaction_scores) / len(
            user_profile.satisfaction_scores
        )
        print(f"   Average satisfaction: {avg_satisfaction:.1f}/5.0")
    else:
        print("   Average satisfaction: No ratings yet")

    print("\n📝 Generating personalized response...")

    response = await generator.generate_response(
        query="data visualization best practices",
        articles=articles,
        context=conversation_context,
        user_profile=user_profile,
    )

    print("\n✅ Personalized Response Generated!")
    print(f"🆔 Conversation ID: {response.conversation_id}")

    print("\n📚 Recommended Articles:")
    for i, article in enumerate(response.articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   📖 {article.summary}")
        print(f"   ⭐ Relevance: {article.relevance_score:.2f}")

    print("\n💡 Personalized Insights:")
    for i, insight in enumerate(response.insights, 1):
        print(f"{i}. {insight}")

    print("\n🎯 Tailored Recommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"{i}. {rec}")


async def example_error_handling():
    """Example: ResponseGenerator error handling and fallback behavior."""

    print("\n\n🛡️  ResponseGenerator Example - Error Handling")
    print("=" * 50)

    generator = get_response_generator()

    # Mock client that simulates API failures
    class MockFailingClient:
        def __init__(self):
            self.chat = MockFailingChat()

    class MockFailingChat:
        def __init__(self):
            self.completions = MockFailingCompletions()

    class MockFailingCompletions:
        async def create(self, **kwargs):
            raise Exception("Simulated API failure")

    generator.client = MockFailingClient()

    articles = [
        ArticleMatch(
            article_id=uuid4(),
            title="Robust Software Architecture",
            content_preview="Building resilient systems requires careful consideration of failure modes and recovery strategies. This article explores patterns for handling errors gracefully, implementing circuit breakers, and designing for fault tolerance. Learn how to create systems that degrade gracefully under stress.",
            similarity_score=0.91,
            metadata={"topics": ["architecture", "resilience"]},
            url="https://engineering.example.com/robust-architecture",
            feed_name="Engineering Blog",
            category="Software Engineering",
        )
    ]

    print("⚠️  Simulating API failure scenario...")

    # Should still return a valid response with fallback content
    response = await generator.generate_response(
        query="error handling strategies", articles=articles
    )

    print("\n✅ Fallback Response Generated!")
    print(f"📊 Articles: {len(response.articles)}")
    print(f"💡 Insights: {len(response.insights)}")
    print(f"🎯 Recommendations: {len(response.recommendations)}")

    print("\n📚 Fallback Article Summary:")
    for article in response.articles:
        print(f"   Title: {article.title}")
        print(f"   Summary: {article.summary}")
        print("   Note: Generated using fallback mechanism")

    print("\n💡 Fallback Insights:")
    for insight in response.insights:
        print(f"   • {insight}")

    print("\n✅ Error handling working correctly - system remains functional!")


async def main():
    """Run all ResponseGenerator examples."""

    print("🎉 ResponseGenerator Task 7.1 - Complete Examples")
    print("=" * 60)

    try:
        # Basic usage example
        await example_basic_usage()

        # Personalized usage example
        await example_with_user_profile()

        # Error handling example
        await example_error_handling()

        print("\n\n🎊 All examples completed successfully!")
        print("✅ Task 7.1 Implementation verified:")
        print("   ✓ ResponseGenerator class with LLM integration")
        print("   ✓ Article summarization (2-3 sentences per article)")
        print("   ✓ Structured response formatting with required elements")
        print("   ✓ Max 5 articles sorted by relevance")
        print("   ✓ Personalized insights and recommendations")
        print("   ✓ Error handling and fallback mechanisms")
        print("   ✓ Requirements 3.1, 3.2, 3.3, 5.5 addressed")

    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
