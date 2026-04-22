"""
Example usage of ConversationManager for the Intelligent Q&A Agent.

This script demonstrates how to use the ConversationManager class for
managing conversation context and maintaining conversation history.
"""

import asyncio
from uuid import uuid4

from app.qa_agent.conversation_manager import get_conversation_manager
from app.qa_agent.models import (
    ArticleSummary,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)


async def demonstrate_conversation_manager():
    """Demonstrate ConversationManager functionality."""
    print("=== ConversationManager Usage Examples ===\n")

    # Get the conversation manager
    manager = get_conversation_manager()

    # Create a test user
    user_id = uuid4()
    print(f"Created test user: {user_id}\n")

    # Example 1: Create a new conversation
    print("1. Creating a new conversation...")
    conversation_id = await manager.create_conversation(user_id)
    print(f"   Created conversation: {conversation_id}\n")

    # Example 2: Add turns to the conversation
    print("2. Adding turns to the conversation...")

    # First turn - asking about AI
    parsed_query_1 = ParsedQuery(
        original_query="What are the latest developments in artificial intelligence?",
        language=QueryLanguage.ENGLISH,
        intent=QueryIntent.SEARCH,
        keywords=["AI", "artificial intelligence", "developments", "latest"],
        confidence=0.9,
    )

    # Create a sample response
    article_1 = ArticleSummary(
        article_id=uuid4(),
        title="AI Breakthroughs in 2024",
        summary="Recent advances in AI include improved language models, better computer vision, and more efficient training methods. These developments are reshaping various industries.",
        url="https://example.com/ai-breakthroughs-2024",
        relevance_score=0.95,
        reading_time=8,
        category="Technology",
    )

    response_1 = StructuredResponse(
        query="What are the latest developments in artificial intelligence?",
        response_type=ResponseType.STRUCTURED,
        articles=[article_1],
        insights=[
            "AI development is accelerating rapidly in 2024",
            "Language models are becoming more efficient and capable",
        ],
        recommendations=[
            "Consider reading about transformer architectures",
            "Look into recent papers on AI safety",
        ],
        conversation_id=uuid4(),
        response_time=2.1,
        confidence=0.9,
    )

    await manager.add_turn(
        conversation_id, parsed_query_1.original_query, parsed_query_1, response_1
    )
    print(f"   Added turn 1: {parsed_query_1.original_query}")

    # Second turn - follow-up question
    parsed_query_2 = ParsedQuery(
        original_query="Can you tell me more about the language model improvements?",
        language=QueryLanguage.ENGLISH,
        intent=QueryIntent.CLARIFICATION,
        keywords=["language model", "improvements", "more"],
        confidence=0.8,
    )

    await manager.add_turn(conversation_id, parsed_query_2.original_query, parsed_query_2)
    print(f"   Added turn 2: {parsed_query_2.original_query}")

    # Third turn - different topic
    parsed_query_3 = ParsedQuery(
        original_query="What about computer vision advances?",
        language=QueryLanguage.ENGLISH,
        intent=QueryIntent.EXPLORATION,
        keywords=["computer vision", "advances"],
        confidence=0.85,
    )

    await manager.add_turn(conversation_id, parsed_query_3.original_query, parsed_query_3)
    print(f"   Added turn 3: {parsed_query_3.original_query}\n")

    # Example 3: Retrieve conversation context
    print("3. Retrieving conversation context...")
    context = await manager.get_context(conversation_id)
    if context:
        print(f"   Conversation ID: {context.conversation_id}")
        print(f"   User ID: {context.user_id}")
        print(f"   Number of turns: {len(context.turns)}")
        print(f"   Current topic: {context.current_topic}")
        print(f"   Status: {context.status}")
        print(f"   Created: {context.created_at}")
        print(f"   Last updated: {context.last_updated}")

        print("\n   Turn details:")
        for i, turn in enumerate(context.turns, 1):
            print(f"     Turn {i}: {turn.query}")
            if turn.parsed_query:
                print(f"       Intent: {turn.parsed_query.intent}")
                print(f"       Keywords: {turn.parsed_query.keywords}")
            if turn.response:
                print(f"       Response articles: {len(turn.response.articles)}")
    print()

    # Example 4: Test context reset detection
    print("4. Testing context reset detection...")

    # Related query (should not reset)
    should_reset = await manager.should_reset_context(
        conversation_id, "What about neural network architectures in AI?"
    )
    print(f"   Related query should reset context: {should_reset}")

    # Unrelated query (should reset)
    should_reset = await manager.should_reset_context(
        conversation_id, "How do I cook a perfect steak?"
    )
    print(f"   Unrelated query should reset context: {should_reset}\n")

    # Example 5: Demonstrate 10-turn limit
    print("5. Demonstrating 10-turn limit...")

    # Add many turns to test the limit
    for i in range(4, 15):  # Add turns 4-14 (11 more turns)
        query = f"Follow-up question number {i}"
        await manager.add_turn(conversation_id, query)

    # Check the context again
    context = await manager.get_context(conversation_id)
    print(f"   After adding many turns, conversation has {len(context.turns)} turns")
    print(f"   First turn query: {context.turns[0].query}")
    print(f"   Last turn query: {context.turns[-1].query}")
    print("   (Should show only the most recent 10 turns)\n")

    # Example 6: Get user conversations
    print("6. Getting all user conversations...")

    # Create another conversation for the same user
    conversation_id_2 = await manager.create_conversation(user_id)
    await manager.add_turn(conversation_id_2, "Another conversation topic")

    user_conversations = await manager.get_user_conversations(user_id)
    print(f"   User has {len(user_conversations)} conversations")
    for i, conv in enumerate(user_conversations, 1):
        print(f"     Conversation {i}: {len(conv.turns)} turns, topic: {conv.current_topic}")
    print()

    # Example 7: Reset conversation context
    print("7. Resetting conversation context...")
    await manager.reset_context(conversation_id, "New Topic After Reset")

    context = await manager.get_context(conversation_id)
    print(f"   After reset - turns: {len(context.turns)}, topic: {context.current_topic}\n")

    # Example 8: Get conversation statistics
    print("8. Getting conversation statistics...")
    stats = await manager.get_conversation_stats()
    print(f"   Total conversations: {stats.get('total_conversations', 0)}")
    print(f"   Active conversations: {stats.get('active_conversations', 0)}")
    print(f"   Expired conversations: {stats.get('expired_conversations', 0)}")

    if "conversations_by_age" in stats:
        print("   Conversations by age:")
        for period, count in stats["conversations_by_age"].items():
            print(f"     {period}: {count}")
    print()

    # Example 9: Cleanup and deletion
    print("9. Cleaning up conversations...")

    # Delete one conversation
    deleted = await manager.delete_conversation(conversation_id_2)
    print(f"   Deleted conversation 2: {deleted}")

    # Run cleanup for expired conversations
    cleanup_count = await manager.cleanup_expired_conversations()
    print(f"   Cleaned up {cleanup_count} expired conversations")

    # Final stats
    final_stats = await manager.get_conversation_stats()
    print(f"   Final total conversations: {final_stats.get('total_conversations', 0)}\n")

    print("=== ConversationManager demonstration completed ===")


async def demonstrate_error_handling():
    """Demonstrate error handling in ConversationManager."""
    print("\n=== Error Handling Examples ===\n")

    manager = get_conversation_manager()

    # Example 1: Invalid conversation ID
    print("1. Testing invalid conversation ID...")
    try:
        context = await manager.get_context("invalid-uuid-format")
        print("   This should not print")
    except Exception as e:
        print(f"   Caught expected error: {type(e).__name__}: {e}")

    # Example 2: Non-existent conversation
    print("\n2. Testing non-existent conversation...")
    fake_id = str(uuid4())
    context = await manager.get_context(fake_id)
    print(f"   Context for non-existent conversation: {context}")

    # Example 3: Adding turn to non-existent conversation
    print("\n3. Testing add turn to non-existent conversation...")
    try:
        await manager.add_turn(fake_id, "This should fail")
        print("   This should not print")
    except Exception as e:
        print(f"   Caught expected error: {type(e).__name__}: {e}")

    print("\n=== Error handling demonstration completed ===")


async def main():
    """Main function to run all examples."""
    try:
        await demonstrate_conversation_manager()
        await demonstrate_error_handling()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
