"""
Test suite for ConversationManager implementation.

Tests conversation context management, 10-turn limit, and data retention policies.
"""

import asyncio
from uuid import UUID, uuid4

import pytest

from app.qa_agent.conversation_manager import ConversationManager, ConversationManagerError
from app.qa_agent.database import get_db_connection
from app.qa_agent.models import (
    ArticleSummary,
    ConversationStatus,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)


class TestConversationManager:
    """Test suite for ConversationManager functionality."""

    @pytest.fixture
    async def conversation_manager(self):
        """Create a ConversationManager instance for testing."""
        return ConversationManager(default_expiry_days=7)

    @pytest.fixture
    async def test_user_id(self):
        """Generate a test user ID."""
        return uuid4()

    @pytest.fixture
    async def sample_parsed_query(self):
        """Create a sample ParsedQuery for testing."""
        return ParsedQuery(
            original_query="What are the latest trends in AI?",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["AI", "trends", "latest"],
            confidence=0.8,
        )

    @pytest.fixture
    async def sample_response(self):
        """Create a sample StructuredResponse for testing."""
        article = ArticleSummary(
            article_id=uuid4(),
            title="AI Trends 2024",
            summary="Latest developments in artificial intelligence.",
            url="https://example.com/ai-trends",
            relevance_score=0.9,
            reading_time=5,
            category="Technology",
        )

        return StructuredResponse(
            query="What are the latest trends in AI?",
            response_type=ResponseType.STRUCTURED,
            articles=[article],
            insights=["AI is rapidly evolving"],
            recommendations=["Read more about machine learning"],
            conversation_id=uuid4(),
            response_time=1.5,
            confidence=0.8,
        )

    async def test_create_conversation(self, conversation_manager, test_user_id):
        """Test creating a new conversation."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        assert conversation_id is not None
        assert isinstance(conversation_id, str)

        # Verify conversation exists
        context = await conversation_manager.get_context(conversation_id)
        assert context is not None
        assert context.user_id == test_user_id
        assert len(context.turns) == 0
        assert context.status == ConversationStatus.ACTIVE

    async def test_add_turn_basic(
        self, conversation_manager, test_user_id, sample_parsed_query, sample_response
    ):
        """Test adding a basic turn to a conversation."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        await conversation_manager.add_turn(
            conversation_id,
            "What are the latest trends in AI?",
            sample_parsed_query,
            sample_response,
        )

        context = await conversation_manager.get_context(conversation_id)
        assert len(context.turns) == 1
        assert context.turns[0].query == "What are the latest trends in AI?"
        assert context.turns[0].parsed_query == sample_parsed_query
        assert context.turns[0].response == sample_response
        assert context.current_topic is not None

    async def test_ten_turn_limit(self, conversation_manager, test_user_id):
        """Test that conversation maintains exactly 10 turns maximum."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Add 15 turns
        for i in range(15):
            query = f"Query number {i + 1}"
            await conversation_manager.add_turn(conversation_id, query)

        context = await conversation_manager.get_context(conversation_id)

        # Should have exactly 10 turns (the most recent ones)
        assert len(context.turns) == 10

        # Verify it's the last 10 turns (6-15)
        for i, turn in enumerate(context.turns):
            expected_query = f"Query number {i + 6}"
            assert turn.query == expected_query
            assert turn.turn_number == i + 1  # Turn numbers should be renumbered 1-10

    async def test_get_context_nonexistent(self, conversation_manager):
        """Test getting context for a non-existent conversation."""
        fake_id = str(uuid4())
        context = await conversation_manager.get_context(fake_id)
        assert context is None

    async def test_get_context_invalid_id(self, conversation_manager):
        """Test getting context with invalid conversation ID format."""
        with pytest.raises(ConversationManagerError):
            await conversation_manager.get_context("invalid-uuid")

    async def test_should_reset_context(self, conversation_manager, test_user_id):
        """Test context reset detection based on topic change."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Add initial turn about AI
        parsed_query = ParsedQuery(
            original_query="Tell me about AI",
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=["AI", "artificial", "intelligence"],
            confidence=0.8,
        )
        await conversation_manager.add_turn(conversation_id, "Tell me about AI", parsed_query)

        # Test related query (should not reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "What about machine learning in AI?"
        )
        assert not should_reset

        # Test unrelated query (should reset)
        should_reset = await conversation_manager.should_reset_context(
            conversation_id, "How do I cook pasta?"
        )
        assert should_reset

    async def test_reset_context(self, conversation_manager, test_user_id):
        """Test manually resetting conversation context."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Add some turns
        for i in range(3):
            await conversation_manager.add_turn(conversation_id, f"Query {i}")

        # Reset context
        await conversation_manager.reset_context(conversation_id, "New Topic")

        context = await conversation_manager.get_context(conversation_id)
        assert len(context.turns) == 0
        assert context.current_topic == "New Topic"
        assert context.context_summary == {}

    async def test_get_user_conversations(self, conversation_manager, test_user_id):
        """Test retrieving all conversations for a user."""
        # Create multiple conversations
        conversation_ids = []
        for i in range(3):
            conv_id = await conversation_manager.create_conversation(test_user_id)
            conversation_ids.append(conv_id)
            await conversation_manager.add_turn(conv_id, f"Query in conversation {i}")

        # Get user conversations
        conversations = await conversation_manager.get_user_conversations(test_user_id)

        assert len(conversations) == 3
        for conv in conversations:
            assert conv.user_id == test_user_id
            assert len(conv.turns) == 1

    async def test_delete_conversation(self, conversation_manager, test_user_id):
        """Test deleting a conversation."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)
        await conversation_manager.add_turn(conversation_id, "Test query")

        # Verify conversation exists
        context = await conversation_manager.get_context(conversation_id)
        assert context is not None

        # Delete conversation
        deleted = await conversation_manager.delete_conversation(conversation_id)
        assert deleted is True

        # Verify conversation is gone
        context = await conversation_manager.get_context(conversation_id)
        assert context is None

        # Try to delete again (should return False)
        deleted = await conversation_manager.delete_conversation(conversation_id)
        assert deleted is False

    async def test_cleanup_expired_conversations(self, conversation_manager, test_user_id):
        """Test cleaning up expired conversations."""
        # Create a conversation
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Manually set expiry to past date
        async with get_db_connection() as conn:
            await conn.execute(
                """
                UPDATE conversations
                SET expires_at = NOW() - INTERVAL '1 day'
                WHERE id = $1
            """,
                UUID(conversation_id),
            )

        # Run cleanup
        deleted_count = await conversation_manager.cleanup_expired_conversations()

        # Should have deleted the expired conversation
        assert deleted_count >= 1

        # Verify conversation is gone
        context = await conversation_manager.get_context(conversation_id)
        assert context is None

    async def test_conversation_stats(self, conversation_manager, test_user_id):
        """Test getting conversation statistics."""
        # Create some conversations
        for i in range(3):
            conv_id = await conversation_manager.create_conversation(test_user_id)
            await conversation_manager.add_turn(conv_id, f"Query {i}")

        stats = await conversation_manager.get_conversation_stats()

        assert "total_conversations" in stats
        assert "active_conversations" in stats
        assert "expired_conversations" in stats
        assert "conversations_by_age" in stats
        assert stats["total_conversations"] >= 3
        assert stats["active_conversations"] >= 3

    async def test_serialization_deserialization(
        self, conversation_manager, test_user_id, sample_parsed_query, sample_response
    ):
        """Test that conversation context is properly serialized and deserialized."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Add a complex turn with all data
        await conversation_manager.add_turn(
            conversation_id, "Complex query with full data", sample_parsed_query, sample_response
        )

        # Retrieve and verify all data is intact
        context = await conversation_manager.get_context(conversation_id)

        assert len(context.turns) == 1
        turn = context.turns[0]

        assert turn.query == "Complex query with full data"
        assert turn.parsed_query is not None
        assert turn.parsed_query.original_query == sample_parsed_query.original_query
        assert turn.parsed_query.keywords == sample_parsed_query.keywords

        assert turn.response is not None
        assert turn.response.query == sample_response.query
        assert len(turn.response.articles) == len(sample_response.articles)
        assert turn.response.articles[0].title == sample_response.articles[0].title

    async def test_conversation_expiry_check(self, conversation_manager, test_user_id):
        """Test that expired conversations are automatically removed when accessed."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Manually expire the conversation
        async with get_db_connection() as conn:
            await conn.execute(
                """
                UPDATE conversations
                SET expires_at = NOW() - INTERVAL '1 hour'
                WHERE id = $1
            """,
                UUID(conversation_id),
            )

        # Try to get context - should return None and delete the conversation
        context = await conversation_manager.get_context(conversation_id)
        assert context is None

        # Verify conversation was actually deleted from database
        async with get_db_connection() as conn:
            exists = await conn.fetchval(
                """
                SELECT EXISTS(SELECT 1 FROM conversations WHERE id = $1)
            """,
                UUID(conversation_id),
            )
            assert not exists

    async def test_error_handling_invalid_operations(self, conversation_manager):
        """Test error handling for invalid operations."""
        fake_id = str(uuid4())

        # Try to add turn to non-existent conversation
        with pytest.raises(ConversationManagerError):
            await conversation_manager.add_turn(fake_id, "Test query")

        # Try to reset non-existent conversation
        with pytest.raises(ConversationManagerError):
            await conversation_manager.reset_context(fake_id)

    async def test_concurrent_access(self, conversation_manager, test_user_id):
        """Test concurrent access to the same conversation."""
        conversation_id = await conversation_manager.create_conversation(test_user_id)

        # Create multiple concurrent tasks adding turns
        async def add_turn_task(i):
            await conversation_manager.add_turn(conversation_id, f"Concurrent query {i}")

        # Run 5 concurrent tasks
        tasks = [add_turn_task(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all turns were added
        context = await conversation_manager.get_context(conversation_id)
        assert len(context.turns) == 5

        # Verify turn numbers are sequential
        for i, turn in enumerate(context.turns):
            assert turn.turn_number == i + 1


# Integration test to run the full test suite
async def run_conversation_manager_tests():
    """Run all conversation manager tests."""
    print("Running ConversationManager tests...")

    # Create test instance
    manager = ConversationManager()
    test_user = uuid4()

    try:
        # Test basic functionality
        print("✓ Testing conversation creation...")
        conv_id = await manager.create_conversation(test_user)

        print("✓ Testing turn addition...")
        await manager.add_turn(conv_id, "Test query")

        print("✓ Testing context retrieval...")
        context = await manager.get_context(conv_id)
        assert context is not None
        assert len(context.turns) == 1

        print("✓ Testing 10-turn limit...")
        for i in range(12):  # Add more than 10 turns
            await manager.add_turn(conv_id, f"Query {i}")

        context = await manager.get_context(conv_id)
        assert len(context.turns) == 10  # Should be limited to 10

        print("✓ Testing conversation deletion...")
        deleted = await manager.delete_conversation(conv_id)
        assert deleted is True

        print("✓ Testing cleanup...")
        cleanup_count = await manager.cleanup_expired_conversations()
        print(f"   Cleaned up {cleanup_count} expired conversations")

        print("✓ All ConversationManager tests passed!")
        return True

    except Exception as e:
        print(f"✗ ConversationManager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the integration test
    result = asyncio.run(run_conversation_manager_tests())
    exit(0 if result else 1)
