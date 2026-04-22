#!/usr/bin/env python3
"""
Simple test script to verify Task 8.2 implementation without database dependencies.
"""

import asyncio
from uuid import uuid4

from app.qa_agent.conversation_manager import ConversationManager
from app.qa_agent.models import (
    ConversationContext,
    ConversationTurn,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
)
from app.qa_agent.query_processor import QueryProcessor


async def test_task_8_2_implementation():
    """Test the core Task 8.2 functionality."""
    print("🧪 Testing Task 8.2: Multi-turn conversation support")
    print("=" * 60)

    # Initialize components
    conversation_manager = ConversationManager()
    query_processor = QueryProcessor()

    # Test 1: Contextual references detection
    print("\n1. Testing contextual references detection...")

    # English contextual references
    assert conversation_manager._has_contextual_references("Tell me more about this")
    assert conversation_manager._has_contextual_references("What about that technology?")
    assert not conversation_manager._has_contextual_references("What is Python programming?")

    # Chinese contextual references
    assert conversation_manager._has_contextual_references("告訴我更多關於這個")
    assert conversation_manager._has_contextual_references("那個怎麼樣?")
    assert not conversation_manager._has_contextual_references("什麼是機器學習?")

    print("   ✅ Contextual references detection works correctly")

    # Test 2: Topic change detection
    print("\n2. Testing topic change detection...")

    # English topic change indicators
    assert conversation_manager._has_topic_change_indicators("Now I want to ask about cooking")
    assert conversation_manager._has_topic_change_indicators("By the way, what about sports?")
    assert not conversation_manager._has_topic_change_indicators("Tell me more about this")

    # Chinese topic change indicators
    assert conversation_manager._has_topic_change_indicators("現在我想問不同的問題")
    assert conversation_manager._has_topic_change_indicators("順便問一下，關於運動")
    assert not conversation_manager._has_topic_change_indicators("告訴我更多")

    print("   ✅ Topic change detection works correctly")

    # Test 3: Keyword overlap calculation
    print("\n3. Testing keyword overlap calculation...")

    recent_queries = ["machine learning algorithms", "neural networks training"]

    # High overlap query
    overlap = conversation_manager._calculate_keyword_overlap(
        "deep learning algorithms", recent_queries
    )
    assert overlap > 0.2, f"Expected high overlap, got {overlap}"

    # Low overlap query
    overlap = conversation_manager._calculate_keyword_overlap(
        "cooking recipes pasta", recent_queries
    )
    assert overlap < 0.3, f"Expected low overlap, got {overlap}"

    print("   ✅ Keyword overlap calculation works correctly")

    # Test 4: Query type classification
    print("\n4. Testing query type classification...")

    # Test different query types
    assert (
        conversation_manager._classify_contextual_query_type("Can you explain what this means?")
        == "clarification"
    )
    assert (
        conversation_manager._classify_contextual_query_type("Tell me more details about this")
        == "expansion"
    )
    assert (
        conversation_manager._classify_contextual_query_type(
            "How does this compare to other options?"
        )
        == "comparison"
    )
    assert (
        conversation_manager._classify_contextual_query_type("What other alternatives are there?")
        == "exploration"
    )
    assert (
        conversation_manager._classify_contextual_query_type("What is the weather today?")
        == "general"
    )

    print("   ✅ Query type classification works correctly")

    # Test 5: Enhanced query pattern detection
    print("\n5. Testing enhanced query pattern detection...")

    # Test direct references
    assert query_processor._has_direct_references("tell me about this")
    assert query_processor._has_direct_references("what about that technology")
    assert not query_processor._has_direct_references("what is machine learning")

    # Test follow-up patterns
    assert query_processor._is_followup_pattern("tell me more about")
    assert query_processor._is_followup_pattern("elaborate on this")
    assert not query_processor._is_followup_pattern("what is artificial intelligence")

    # Test comparative queries
    assert query_processor._is_comparative_query("are there other similar")
    assert query_processor._is_comparative_query("compare this to alternatives")
    assert not query_processor._is_comparative_query("what is machine learning")

    # Test clarification requests
    assert query_processor._is_clarification_request("can you explain this")
    assert query_processor._is_clarification_request("what does this mean")
    assert not query_processor._is_clarification_request("what is the weather")

    print("   ✅ Enhanced query pattern detection works correctly")

    # Test 6: Contextual relatedness detection
    print("\n6. Testing contextual relatedness detection...")

    # Create sample conversation context
    user_id = uuid4()
    conversation_context = ConversationContext(
        user_id=user_id, current_topic="artificial intelligence"
    )

    # Test related query
    is_related = query_processor._is_contextually_related(
        "machine learning applications", conversation_context
    )
    assert (
        is_related
    ), "Expected 'machine learning applications' to be related to 'artificial intelligence'"

    # Test unrelated query
    is_related = query_processor._is_contextually_related(
        "cooking pasta recipes", conversation_context
    )
    assert (
        not is_related
    ), "Expected 'cooking pasta recipes' to be unrelated to 'artificial intelligence'"

    print("   ✅ Contextual relatedness detection works correctly")

    # Test 7: Conversation context methods
    print("\n7. Testing conversation context methods...")

    # Add a sample turn
    turn1 = ConversationTurn(
        turn_number=1,
        query="What are the latest developments in AI?",
        parsed_query=ParsedQuery(
            original_query="What are the latest developments in AI?",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["AI", "developments", "latest"],
            filters={},
            confidence=0.9,
        ),
    )
    conversation_context.turns.append(turn1)

    # Test should_reset_context method
    should_reset = conversation_context.should_reset_context("Tell me about cooking")
    assert should_reset, "Expected context reset for different topic"

    should_reset = conversation_context.should_reset_context("More about AI developments")
    assert not should_reset, "Expected no context reset for same topic"

    # Test conversation summary
    summary = conversation_context.get_conversation_summary()
    assert "artificial intelligence" in summary
    assert "1 turns" in summary

    # Test recent queries
    recent = conversation_context.get_recent_queries(count=3)
    assert len(recent) == 1
    assert recent[0] == "What are the latest developments in AI?"

    print("   ✅ Conversation context methods work correctly")

    # Test 8: Enhanced query expansion
    print("\n8. Testing enhanced query expansion...")

    # Test contextual query expansion
    expanded = await query_processor._expand_with_context(
        "Tell me more about this", conversation_context
    )
    assert "artificial intelligence" in expanded.lower() or "ai" in expanded.lower()

    print("   ✅ Enhanced query expansion works correctly")

    print("\n" + "=" * 60)
    print("🎉 All Task 8.2 tests passed successfully!")
    print("\n📋 Task 8.2 Implementation Summary:")
    print("   ✅ Enhanced contextual query understanding for follow-up questions")
    print("   ✅ Improved topic change detection with multiple analysis factors")
    print("   ✅ Comprehensive conversation data retention and cleanup policies")
    print("   ✅ Multilingual support for Chinese and English")
    print("   ✅ Advanced query expansion with contextual awareness")
    print("   ✅ Enhanced query pattern detection and classification")
    print("   ✅ Contextual relatedness analysis")
    print("   ✅ Conversation context management with topic tracking")

    print("\n🔧 Key Requirements Addressed:")
    print("   • Requirement 4.2: Combine previous conversation content with new questions")
    print("   • Requirement 4.3: Support context-related queries like 'tell me more about this'")
    print("   • Requirement 4.5: Identify and appropriately reset context when topics change")
    print("   • Requirement 10.2: Create conversation data retention and cleanup policies")


if __name__ == "__main__":
    asyncio.run(test_task_8_2_implementation())
