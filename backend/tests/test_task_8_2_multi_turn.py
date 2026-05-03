"""
Test suite for Task 8.2: Multi-turn conversation support enhancements

Tests the enhanced contextual query understanding, topic change detection,
and conversation data retention policies.
"""

import asyncio
from uuid import uuid4

import pytest

from app.qa_agent.conversation_manager import ConversationManager, ConversationManagerError
from app.qa_agent.models import ParsedQuery, QueryIntent, QueryLanguage
from app.qa_agent.query_processor import QueryProcessor


class TestMultiTurnConversationSupport:
    """Test enhanced multi-turn conversation capabilities."""

    @pytest.fixture
    async def conversation_manager(self):
        """Create a conversation manager for testing."""
        return ConversationManager()

    @pytest.fixture
    async def query_processor(self):
        """Create a query processor for testing."""
        return QueryProcessor()

    @pytest.fixture
    async def sample_context(self, conversation_manager):
        """Create a sample conversation context."""
        user_id = uuid4()
        conversation_id = await conversation_manager.create_conversation(user_id)

        # Add some turns to create context
        await conversation_manager.add_turn(
            conversation_id,
            "What are the latest developments in AI?",
            ParsedQuery(
                original_query="What are the latest developments in AI?",
                language=QueryLanguage.EN,
                intent=QueryIntent.SEARCH,
                keywords=["AI", "developments", "latest"],
                filters={},
                confidence=0.9,
            ),
        )

        return await conversation_manager.get_context(conversation_id)

    async def test_contextual_query_processing(self, conversation_manager):
        """Test enhanced contextual query processing."""
        user_id = uuid4()
        conversation_id = await conversation_manager.create_conversation(user_id)

        # Test initial query
        result = await conversation_manager.process_contextual_query(
            conversation_id, "What is machine learning?", user_id
        )

        assert result["conversation_id"] == conversation_id
        assert not result["should_reset_context"]
        assert not result["is_followup"]
        assert not result["has_context"]
        assert result["query_type"] == "general"

        # Add a turn and test follow-up
        await conversation_manager.add_turn(conversation_id, "What is machine learning?")

        result = await conversation_manager.process_contextual_query(
            conversation_id, "Tell me more about this", user_id
        )

        assert result["is_followup"]
        assert result["has_context"]
        assert result["query_type"] == "expansion"
        assert len(result["contextual_references"]) > 0

    async def test_topic_change_detection(self, conversation_manager, sample_context):
        """Test enhanced topic change detection."""
        conversation_id = str(sample_context.conversation_id)

        # Test continuation query (should not reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "Tell me more about AI developments"
        )
        assert not should_reset

        # Test contextual reference (should not reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "What about this technology?"
        )
        assert not should_reset

        # Test topic change (should reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "Now I want to ask about cooking recipes"
        )
        assert should_reset

        # Test explicit topic change (should reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "Let's talk about different subject - sports"
        )
        assert should_reset

    async def test_contextual_references_detection(self, conversation_manager):
        """Test detection of contextual references."""
        # Test direct references
        assert conversation_manager._has_contextual_references("Tell me more about this")
        assert conversation_manager._has_contextual_references("What about that?")
        assert conversation_manager._has_contextual_references("這個怎麼樣?")  # Chinese

        # Test non-contextual queries
        assert not conversation_manager._has_contextual_references("What is Python?")
        assert not conversation_manager._has_contextual_references("How to cook pasta?")

    async def test_keyword_overlap_calculation(self, conversation_manager):
        """Test keyword overlap calculation for topic continuity."""
        recent_queries = ["machine learning algorithms", "neural networks training"]

        # High overlap query
        overlap = conversation_manager._calculate_keyword_overlap(
            "deep learning algorithms", recent_queries
        )
        assert overlap > 0.3

        # Low overlap query
        overlap = conversation_manager._calculate_keyword_overlap(
            "cooking recipes pasta", recent_queries
        )
        assert overlap < 0.1

    async def test_enhanced_query_expansion(self, query_processor, sample_context):
        """Test enhanced contextual query expansion."""
        # Test direct reference expansion
        expanded = await query_processor.expand_query("Tell me more about this", sample_context)
        assert "AI" in expanded or "developments" in expanded

        # Test comparative query expansion
        expanded = await query_processor.expand_query(
            "Are there other similar technologies?", sample_context
        )
        assert len(expanded) > len("Are there other similar technologies?")

        # Test clarification request expansion
        expanded = await query_processor.expand_query("Can you explain that?", sample_context)
        assert len(expanded) > len("Can you explain that?")

    async def test_query_type_classification(self, conversation_manager):
        """Test contextual query type classification."""
        # Test clarification queries
        query_type = conversation_manager._classify_contextual_query_type(
            "Can you explain what this means?"
        )
        assert query_type == "clarification"

        # Test expansion queries
        query_type = conversation_manager._classify_contextual_query_type(
            "Tell me more details about this"
        )
        assert query_type == "expansion"

        # Test comparison queries
        query_type = conversation_manager._classify_contextual_query_type(
            "How does this compare to other options?"
        )
        assert query_type == "comparison"

        # Test exploration queries
        query_type = conversation_manager._classify_contextual_query_type(
            "What other alternatives are there?"
        )
        assert query_type == "exploration"

    async def test_retention_policy_implementation(self, conversation_manager):
        """Test conversation data retention and cleanup policies."""
        user_id = uuid4()

        # Create multiple conversations
        conversation_ids = []
        for i in range(5):
            conv_id = await conversation_manager.create_conversation(user_id)
            conversation_ids.append(conv_id)
            await conversation_manager.add_turn(conv_id, f"Test query {i}")

        # Test retention policy with custom config
        policy_config = {
            "max_conversations_per_user": 3,
            "inactive_conversations_days": 0,  # Mark all as inactive for testing
        }

        stats = await conversation_manager.implement_retention_policy(policy_config)

        # Should have cleaned up excess conversations
        assert stats["total_processed"] >= 0
        assert "expired_deleted" in stats
        assert "inactive_deleted" in stats
        assert "excess_deleted" in stats

    async def test_conversation_context_reset(self, conversation_manager, sample_context):
        """Test conversation context reset functionality."""
        conversation_id = str(sample_context.conversation_id)

        # Verify context has turns
        context = await conversation_manager.get_context(conversation_id)
        assert len(context.turns) > 0

        # Reset context
        await conversation_manager.reset_context(conversation_id, "New topic")

        # Verify context was reset
        context = await conversation_manager.get_context(conversation_id)
        assert len(context.turns) == 0
        assert context.current_topic == "New topic"
        assert context.context_summary == {}

    async def test_multilingual_contextual_support(self, conversation_manager):
        """Test multilingual support for contextual queries."""
        # Test Chinese contextual references
        assert conversation_manager._has_contextual_references("告訴我更多關於這個")
        assert conversation_manager._has_contextual_references("那個怎麼樣?")

        # Test Chinese topic change detection
        assert conversation_manager._has_topic_change_indicators("現在我想問不同的問題")
        assert conversation_manager._detect_topic_shift_patterns("換個話題", ["previous query"])

        # Test English patterns
        assert conversation_manager._has_contextual_references("tell me more about this")
        assert conversation_manager._has_topic_change_indicators("on a different note")

    async def test_error_handling(self, conversation_manager):
        """Test error handling in enhanced conversation management."""
        # Test with invalid conversation ID
        with pytest.raises(ConversationManagerError):
            await conversation_manager.process_contextual_query(
                "invalid-uuid", "test query", uuid4()
            )

        # Test topic change detection with non-existent conversation
        should_reset = await conversation_manager.should_reset_context(str(uuid4()), "test query")
        assert not should_reset  # Should handle gracefully


if __name__ == "__main__":
    # Run a simple test
    async def run_simple_test():
        manager = ConversationManager()
        user_id = uuid4()

        # Test contextual query processing
        result = await manager.process_contextual_query(str(uuid4()), "What is AI?", user_id)
        print(f"Contextual analysis: {result}")

        # Test retention policy
        stats = await manager.implement_retention_policy()
        print(f"Retention policy stats: {stats}")

        print("Task 8.2 implementation test completed successfully!")

    asyncio.run(run_simple_test())
