"""
Example usage of QAAgentController

This example demonstrates how to use the QAAgentController for:
- Single query processing
- Multi-turn conversations
- Error handling
- Performance monitoring
- System health checks
"""

import asyncio
import time
from uuid import uuid4

from .models import QueryLanguage, UserProfile
from .qa_agent_controller import QAAgentController


async def example_single_query():
    """Example of processing a single query."""
    print("=== Single Query Example ===")

    # Initialize the controller (uses real components)
    controller = QAAgentController()

    # Create a user profile for personalization
    user_profile = UserProfile(
        user_id=uuid4(),
        preferred_topics=["AI", "Machine Learning", "Deep Learning", "Technology"],
        language_preference=QueryLanguage.ENGLISH,
    )

    user_id = str(user_profile.user_id)
    query = "What are the latest developments in artificial intelligence?"

    print(f"User ID: {user_id}")
    print(f"Query: {query}")
    print(f"User interests: {', '.join(user_profile.preferred_topics)}")

    try:
        start_time = time.time()

        response = await controller.process_query(
            user_id=user_id,
            query=query,
            user_profile=user_profile,
        )

        end_time = time.time()

        print(f"\n✅ Response generated in {end_time - start_time:.2f} seconds")
        print(f"Response type: {response.response_type}")
        print(f"Conversation ID: {response.conversation_id}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Number of articles: {len(response.articles)}")
        print(f"Number of insights: {len(response.insights)}")
        print(f"Number of recommendations: {len(response.recommendations)}")

        # Display articles
        if response.articles:
            print("\n📚 Articles found:")
            for i, article in enumerate(response.articles, 1):
                print(f"  {i}. {article.title}")
                print(f"     Relevance: {article.relevance_score:.2f}")
                print(f"     Reading time: {article.reading_time} min")
                print(f"     Summary: {article.summary[:100]}...")
                print()

        # Display insights
        if response.insights:
            print("💡 Insights:")
            for insight in response.insights:
                print(f"  • {insight}")
            print()

        # Display recommendations
        if response.recommendations:
            print("🔍 Recommendations:")
            for rec in response.recommendations:
                print(f"  • {rec}")
            print()

        return response

    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return None


async def example_multi_turn_conversation():
    """Example of a multi-turn conversation."""
    print("\n=== Multi-turn Conversation Example ===")

    controller = QAAgentController()

    user_profile = UserProfile(
        user_id=uuid4(),
        preferred_topics=["Programming", "Software Development", "Python"],
        language_preference=QueryLanguage.ENGLISH,
    )

    user_id = str(user_profile.user_id)
    conversation_id = None

    # Conversation turns
    queries = [
        "What is Python programming?",
        "What are the main features of Python?",
        "How does Python compare to Java?",
        "Can you recommend some Python learning resources?",
    ]

    print(f"User ID: {user_id}")
    print("Starting conversation...\n")

    for i, query in enumerate(queries, 1):
        print(f"Turn {i}: {query}")

        try:
            start_time = time.time()

            if conversation_id:
                # Continue existing conversation
                response = await controller.continue_conversation(
                    user_id=user_id,
                    query=query,
                    conversation_id=conversation_id,
                    user_profile=user_profile,
                )
            else:
                # Start new conversation
                response = await controller.process_query(
                    user_id=user_id,
                    query=query,
                    user_profile=user_profile,
                )
                conversation_id = str(response.conversation_id)

            end_time = time.time()

            print(f"  ✅ Response in {end_time - start_time:.2f}s")
            print(f"  Articles: {len(response.articles)}")
            print(f"  Confidence: {response.confidence:.2f}")

            if response.insights:
                print(f"  Key insight: {response.insights[0][:80]}...")

            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()

    # Get conversation history
    if conversation_id:
        print("📜 Conversation History:")
        history = await controller.get_conversation_history(user_id, conversation_id)
        if history:
            print(f"  Conversation ID: {history.conversation_id}")
            print(f"  Total turns: {len(history.turns)}")
            print(f"  Current topic: {history.current_topic or 'Not set'}")
            print(f"  Created: {history.created_at}")
            print(f"  Last updated: {history.last_updated}")
        else:
            print("  No history found")


async def example_error_handling():
    """Example of error handling scenarios."""
    print("\n=== Error Handling Examples ===")

    controller = QAAgentController()
    user_id = str(uuid4())

    # Test cases for different error scenarios
    test_cases = [
        ("", "Empty query"),
        ("   ", "Whitespace only query"),
        ("a" * 3000, "Very long query"),
        ("What is AI?", "Normal query (should work)"),
    ]

    for query, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")

        try:
            start_time = time.time()

            response = await controller.process_query(
                user_id=user_id,
                query=query,
            )

            end_time = time.time()

            print(f"  ✅ Response type: {response.response_type}")
            print(f"  Time: {end_time - start_time:.2f}s")
            print(f"  Confidence: {response.confidence:.2f}")

            if response.insights:
                print(f"  Message: {response.insights[0][:80]}...")

        except Exception as e:
            print(f"  ❌ Exception: {e}")


async def example_performance_monitoring():
    """Example of performance monitoring."""
    print("\n=== Performance Monitoring Example ===")

    controller = QAAgentController()
    user_id = str(uuid4())

    # Test multiple queries to measure performance
    queries = [
        "What is machine learning?",
        "Explain neural networks",
        "What are the benefits of cloud computing?",
        "How does blockchain work?",
        "What is quantum computing?",
    ]

    response_times = []
    successful_queries = 0

    print(f"Testing {len(queries)} queries for performance...")

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")

        try:
            start_time = time.time()

            response = await controller.process_query(
                user_id=user_id,
                query=query,
            )

            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)

            if response.response_type.value != "error":
                successful_queries += 1

            print(f"  Time: {response_time:.2f}s")
            print(f"  Type: {response.response_type}")
            print(f"  Articles: {len(response.articles)}")

            # Check if within 3-second requirement
            if response_time <= 3.0:
                print("  ✅ Within performance requirement")
            else:
                print("  ⚠️  Exceeds 3-second requirement")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Performance summary
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print("\n📊 Performance Summary:")
        print(f"  Successful queries: {successful_queries}/{len(queries)}")
        print(f"  Average response time: {avg_time:.2f}s")
        print(f"  Fastest response: {min_time:.2f}s")
        print(f"  Slowest response: {max_time:.2f}s")
        print(
            f"  Within 3s requirement: {sum(1 for t in response_times if t <= 3.0)}/{len(response_times)}"
        )


async def example_system_health():
    """Example of system health monitoring."""
    print("\n=== System Health Monitoring Example ===")

    controller = QAAgentController()

    print("Checking system health...")

    try:
        health = await controller.get_system_health()

        print("\n🏥 System Health Report:")
        print(f"  Overall health: {health['overall_health']:.2f}")
        print(f"  Status: {health['status']}")
        print(f"  Timestamp: {health['timestamp']}")

        if "components" in health:
            print("\n🔧 Component Status:")
            for component, status in health["components"].items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {component}: {'Healthy' if status else 'Unhealthy'}")

        if "healthy_components" in health and "total_components" in health:
            print("\n📈 Summary:")
            print(
                f"  Healthy components: {health['healthy_components']}/{health['total_components']}"
            )

        # Recommendations based on health
        if health["overall_health"] >= 0.8:
            print("  💚 System is operating normally")
        elif health["overall_health"] >= 0.5:
            print("  💛 System is degraded - some components may need attention")
        else:
            print("  ❤️  System is unhealthy - immediate attention required")

    except Exception as e:
        print(f"❌ Health check failed: {e}")


async def example_conversation_management():
    """Example of conversation management operations."""
    print("\n=== Conversation Management Example ===")

    controller = QAAgentController()
    user_id = str(uuid4())

    print(f"User ID: {user_id}")

    # Create a conversation
    print("\n1. Creating conversation...")
    response = await controller.process_query(
        user_id=user_id,
        query="What is artificial intelligence?",
    )

    conversation_id = str(response.conversation_id)
    print(f"   Created conversation: {conversation_id}")

    # Add more turns
    print("\n2. Adding conversation turns...")
    queries = [
        "What are the main types of AI?",
        "How is AI used in healthcare?",
    ]

    for query in queries:
        await controller.continue_conversation(
            user_id=user_id,
            query=query,
            conversation_id=conversation_id,
        )
        print(f"   Added turn: {query}")

    # Get conversation history
    print("\n3. Retrieving conversation history...")
    history = await controller.get_conversation_history(user_id, conversation_id)

    if history:
        print(f"   Conversation has {len(history.turns)} turns")
        print(f"   Current topic: {history.current_topic or 'Not set'}")
        print(f"   Status: {history.status}")

        # Show recent queries
        recent_queries = history.get_recent_queries(3)
        if recent_queries:
            print("   Recent queries:")
            for i, query in enumerate(recent_queries, 1):
                print(f"     {i}. {query}")

    # Delete conversation
    print("\n4. Deleting conversation...")
    deleted = await controller.delete_conversation(user_id, conversation_id)

    if deleted:
        print("   ✅ Conversation deleted successfully")

        # Verify deletion
        history_after = await controller.get_conversation_history(user_id, conversation_id)
        if history_after is None:
            print("   ✅ Confirmed: conversation no longer exists")
        else:
            print("   ⚠️  Warning: conversation still exists after deletion")
    else:
        print("   ❌ Failed to delete conversation")


async def main():
    """Run all examples."""
    print("🤖 QA Agent Controller Examples")
    print("=" * 50)

    try:
        # Run examples
        await example_single_query()
        await example_multi_turn_conversation()
        await example_error_handling()
        await example_performance_monitoring()
        await example_system_health()
        await example_conversation_management()

        print("\n🎉 All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
