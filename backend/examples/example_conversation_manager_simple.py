"""
Simple example usage of ConversationManager without database dependency.

This demonstrates the core functionality using the mock implementation.
"""

import asyncio
from uuid import uuid4

from app.qa_agent.models import (
    ArticleSummary,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)
from app.qa_agent.test_conversation_manager_mock import MockConversationManager


async def simple_conversation_demo():
    """Simple demonstration of ConversationManager functionality."""
    print("=== Simple ConversationManager Demo ===\n")

    # Use mock manager for demonstration
    manager = MockConversationManager()
    user_id = uuid4()

    print(f"Demo user ID: {user_id}\n")

    # Create a conversation
    print("1. Creating conversation...")
    conv_id = await manager.create_conversation(user_id)
    print(f"   Created: {conv_id}\n")

    # Add some turns
    print("2. Adding conversation turns...")

    queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Can you explain neural networks?",
        "What about deep learning?",
        "Tell me about AI applications",
    ]

    for i, query in enumerate(queries, 1):
        # Create parsed query
        parsed_query = ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.lower().split()[:3],
            confidence=0.8 + (i * 0.02),
        )

        # Create sample article
        article = ArticleSummary(
            article_id=uuid4(),
            title=f"Article about {query.split()[2] if len(query.split()) > 2 else 'AI'}",
            summary=f"This article explains {query.lower()}. It covers the fundamental concepts and practical applications. The content is designed for both beginners and experts.",
            url=f"https://example.com/article-{i}",
            relevance_score=0.9 - (i * 0.05),
            reading_time=5 + i,
            category="Technology",
        )

        # Create response
        response = StructuredResponse(
            query=query,
            response_type=ResponseType.STRUCTURED,
            articles=[article],
            insights=[f"Key insight about {query.split()[2] if len(query.split()) > 2 else 'AI'}"],
            recommendations=[
                f"Learn more about {query.split()[-1] if query.split() else 'technology'}"
            ],
            conversation_id=uuid4(),
            response_time=1.0 + (i * 0.1),
            confidence=0.85,
        )

        await manager.add_turn(conv_id, query, parsed_query, response)
        print(f"   Turn {i}: {query}")

    print()

    # Show conversation state
    print("3. Current conversation state...")
    context = await manager.get_context(conv_id)
    print(f"   Turns: {len(context.turns)}")
    print(f"   Topic: {context.current_topic}")
    print(f"   Status: {context.status}")
    print(f"   Created: {context.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 10-turn limit
    print("4. Testing 10-turn limit...")
    print("   Adding 8 more turns...")

    for i in range(6, 14):
        await manager.add_turn(conv_id, f"Follow-up question {i}")

    context = await manager.get_context(conv_id)
    print(f"   After adding more turns: {len(context.turns)} turns")
    print(f"   First turn: {context.turns[0].query}")
    print(f"   Last turn: {context.turns[-1].query}")
    print("   (Shows only most recent 10 turns)\n")

    # Test context reset
    print("5. Testing context reset...")

    # Check if unrelated query would reset context
    should_reset = await manager.should_reset_context(conv_id, "How do I cook pasta?")
    print(f"   Unrelated query should reset: {should_reset}")

    if should_reset:
        await manager.reset_context(conv_id, "Cooking")
        context = await manager.get_context(conv_id)
        print(f"   After reset - turns: {len(context.turns)}, topic: {context.current_topic}")

    print()

    # Show final state
    print("6. Final conversation summary...")
    context = await manager.get_context(conv_id)
    summary = context.get_conversation_summary()
    print(f"   Summary: {summary}")
    print(f"   Is active: {context.is_active()}")
    print(f"   Recent queries: {context.get_recent_queries(3)}")

    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(simple_conversation_demo())
