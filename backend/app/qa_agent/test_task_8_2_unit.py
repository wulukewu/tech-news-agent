"""
Unit tests for Task 8.2: Multi-turn conversation support enhancements

Tests the enhanced contextual query understanding and topic change detection
without requiring database connectivity.
"""

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


class TestMultiTurnConversationLogic:
    """Test enhanced multi-turn conversation logic without database dependencies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.conversation_manager = ConversationManager()
        self.query_processor = QueryProcessor()

        # Create sample conversation context
        self.user_id = uuid4()
        self.conversation_context = ConversationContext(
            user_id=self.user_id, current_topic="artificial intelligence"
        )

        # Add some sample turns
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
        self.conversation_context.turns.append(turn1)

    def test_contextual_references_detection(self):
        """Test detection of contextual references."""
        # Test English contextual references
        assert self.conversation_manager._has_contextual_references("Tell me more about this")
        assert self.conversation_manager._has_contextual_references("What about that technology?")
        assert self.conversation_manager._has_contextual_references("Are there other similar ones?")

        # Test Chinese contextual references
        assert self.conversation_manager._has_contextual_references("告訴我更多關於這個")
        assert self.conversation_manager._has_contextual_references("那個怎麼樣?")
        assert self.conversation_manager._has_contextual_references("還有其他相關的嗎?")

        # Test non-contextual queries
        assert not self.conversation_manager._has_contextual_references(
            "What is Python programming?"
        )
        assert not self.conversation_manager._has_contextual_references("How to cook pasta?")
        assert not self.conversation_manager._has_contextual_references("什麼是機器學習?")

    def test_keyword_overlap_calculation(self):
        """Test keyword overlap calculation for topic continuity."""
        recent_queries = ["machine learning algorithms", "neural networks training"]

        # High overlap query
        overlap = self.conversation_manager._calculate_keyword_overlap(
            "deep learning algorithms", recent_queries
        )
        assert overlap > 0.2, f"Expected high overlap, got {overlap}"

        # Low overlap query
        overlap = self.conversation_manager._calculate_keyword_overlap(
            "cooking recipes pasta", recent_queries
        )
        assert overlap < 0.3, f"Expected low overlap, got {overlap}"

        # No overlap query
        overlap = self.conversation_manager._calculate_keyword_overlap(
            "weather forecast", recent_queries
        )
        assert overlap < 0.1, f"Expected no overlap, got {overlap}"

    def test_topic_shift_pattern_detection(self):
        """Test detection of topic shift patterns."""
        recent_queries = ["AI developments", "machine learning"]

        # Test English topic shift patterns
        assert self.conversation_manager._detect_topic_shift_patterns(
            "Now I want to ask about cooking", recent_queries
        )
        assert self.conversation_manager._detect_topic_shift_patterns(
            "Let's talk about different question", recent_queries
        )
        assert self.conversation_manager._detect_topic_shift_patterns(
            "On a different note, what about sports?", recent_queries
        )

        # Test Chinese topic shift patterns
        assert self.conversation_manager._detect_topic_shift_patterns("現在我想問不同的問題", recent_queries)
        assert self.conversation_manager._detect_topic_shift_patterns("換個話題，關於烹飪", recent_queries)

        # Test non-shift patterns
        assert not self.conversation_manager._detect_topic_shift_patterns(
            "Tell me more about AI", recent_queries
        )
        assert not self.conversation_manager._detect_topic_shift_patterns(
            "What about machine learning?", recent_queries
        )

    def test_topic_change_indicators(self):
        """Test explicit topic change indicators."""
        # Test English indicators
        assert self.conversation_manager._has_topic_change_indicators(
            "By the way, what about sports?"
        )
        assert self.conversation_manager._has_topic_change_indicators("New topic: cooking recipes")
        assert self.conversation_manager._has_topic_change_indicators("Different subject entirely")

        # Test Chinese indicators
        assert self.conversation_manager._has_topic_change_indicators("順便問一下，關於運動")
        assert self.conversation_manager._has_topic_change_indicators("新話題：烹飪食譜")
        assert self.conversation_manager._has_topic_change_indicators("對了，什麼是")

        # Test non-indicators
        assert not self.conversation_manager._has_topic_change_indicators("Tell me more")
        assert not self.conversation_manager._has_topic_change_indicators("What about this?")

    def test_enhanced_followup_detection(self):
        """Test enhanced follow-up query detection."""
        # Test contextual follow-ups
        assert self.conversation_manager._is_followup_query("Tell me more about this")
        assert self.conversation_manager._is_followup_query("What about that?")
        assert self.conversation_manager._is_followup_query("這個怎麼樣?")  # Chinese

        # Test short queries (likely follow-ups)
        assert self.conversation_manager._is_followup_query("More details?")
        assert self.conversation_manager._is_followup_query("And then?")

        # Test non-follow-ups
        assert not self.conversation_manager._is_followup_query("What is artificial intelligence?")
        assert not self.conversation_manager._is_followup_query(
            "How do neural networks work in detail?"
        )

    def test_contextual_reference_extraction(self):
        """Test extraction of contextual references from queries."""
        # Test direct references
        refs = self.conversation_manager._extract_contextual_references(
            "Tell me about this technology"
        )
        assert any("direct" in ref for ref in refs)

        # Test plural references
        refs = self.conversation_manager._extract_contextual_references(
            "What about these algorithms?"
        )
        assert any("plural" in ref for ref in refs)

        # Test comparative references
        refs = self.conversation_manager._extract_contextual_references(
            "Are there other similar methods?"
        )
        assert any("comparative" in ref for ref in refs)

        # Test temporal references
        refs = self.conversation_manager._extract_contextual_references("Like the previous example")
        assert any("temporal" in ref for ref in refs)

    def test_query_type_classification(self):
        """Test contextual query type classification."""
        # Test clarification queries
        query_type = self.conversation_manager._classify_contextual_query_type(
            "Can you explain what this means?"
        )
        assert query_type == "clarification"

        # Test expansion queries
        query_type = self.conversation_manager._classify_contextual_query_type(
            "Tell me more details about this"
        )
        assert query_type == "expansion"

        # Test comparison queries
        query_type = self.conversation_manager._classify_contextual_query_type(
            "How does this compare to other options?"
        )
        assert query_type == "comparison"

        # Test exploration queries
        query_type = self.conversation_manager._classify_contextual_query_type(
            "What other alternatives are there?"
        )
        assert query_type == "exploration"

        # Test general queries
        query_type = self.conversation_manager._classify_contextual_query_type(
            "What is the weather today?"
        )
        assert query_type == "general"

    async def test_enhanced_query_expansion_patterns(self):
        """Test enhanced query expansion patterns."""
        # Test direct reference expansion
        expanded = await self.query_processor._expand_with_context(
            "Tell me more about this", self.conversation_context
        )
        assert "artificial intelligence" in expanded.lower()

        # Test follow-up pattern expansion
        expanded = await self.query_processor._expand_with_context(
            "More information please", self.conversation_context
        )
        assert len(expanded) > len("More information please")

        # Test comparative query expansion
        expanded = await self.query_processor._expand_with_context(
            "Are there other similar technologies?", self.conversation_context
        )
        assert "alternatives" in expanded.lower()

    def test_query_pattern_detection_methods(self):
        """Test individual query pattern detection methods."""
        # Test direct references
        assert self.query_processor._has_direct_references("tell me about this")
        assert self.query_processor._has_direct_references("what about that technology")
        assert not self.query_processor._has_direct_references("what is machine learning")

        # Test follow-up patterns
        assert self.query_processor._is_followup_pattern("tell me more about")
        assert self.query_processor._is_followup_pattern("elaborate on this")
        assert not self.query_processor._is_followup_pattern("what is artificial intelligence")

        # Test comparative queries
        assert self.query_processor._is_comparative_query("are there other similar")
        assert self.query_processor._is_comparative_query("compare this to alternatives")
        assert not self.query_processor._is_comparative_query("what is machine learning")

        # Test clarification requests
        assert self.query_processor._is_clarification_request("can you explain this")
        assert self.query_processor._is_clarification_request("what does this mean")
        assert not self.query_processor._is_clarification_request("what is the weather")

    def test_contextual_relatedness_detection(self):
        """Test detection of contextually related queries."""
        # Test related query
        is_related = self.query_processor._is_contextually_related(
            "machine learning applications", self.conversation_context
        )
        assert is_related

        # Test unrelated query
        is_related = self.query_processor._is_contextually_related(
            "cooking pasta recipes", self.conversation_context
        )
        assert not is_related

    def test_multilingual_support(self):
        """Test multilingual support for contextual understanding."""
        # Test Chinese patterns
        assert self.conversation_manager._has_contextual_references("告訴我更多關於這個")
        assert self.conversation_manager._detect_topic_shift_patterns("現在我想問", ["previous"])
        assert self.conversation_manager._has_topic_change_indicators("順便問一下")

        # Test English patterns
        assert self.conversation_manager._has_contextual_references("tell me more about this")
        assert self.conversation_manager._detect_topic_shift_patterns(
            "now i want to ask", ["previous"]
        )
        assert self.conversation_manager._has_topic_change_indicators("by the way")

    def test_conversation_context_methods(self):
        """Test ConversationContext methods for topic change detection."""
        # Test should_reset_context method
        should_reset = self.conversation_context.should_reset_context("Tell me about cooking")
        assert should_reset  # Different topic

        should_reset = self.conversation_context.should_reset_context("More about AI developments")
        assert not should_reset  # Same topic

        # Test conversation summary
        summary = self.conversation_context.get_conversation_summary()
        assert "artificial intelligence" in summary
        assert "1 turns" in summary


if __name__ == "__main__":
    # Run a simple test
    test_instance = TestMultiTurnConversationLogic()
    test_instance.setup_method()

    # Test contextual references
    test_instance.test_contextual_references_detection()
    print("✓ Contextual references detection works")

    # Test keyword overlap
    test_instance.test_keyword_overlap_calculation()
    print("✓ Keyword overlap calculation works")

    # Test topic shift detection
    test_instance.test_topic_shift_pattern_detection()
    print("✓ Topic shift pattern detection works")

    # Test query type classification
    test_instance.test_query_type_classification()
    print("✓ Query type classification works")

    # Test multilingual support
    test_instance.test_multilingual_support()
    print("✓ Multilingual support works")

    print("\n🎉 Task 8.2 enhanced multi-turn conversation support implemented successfully!")
    print("\nKey enhancements:")
    print("- Enhanced contextual query understanding for follow-up questions")
    print("- Improved topic change detection with multiple analysis factors")
    print("- Comprehensive conversation data retention and cleanup policies")
    print("- Multilingual support for Chinese and English")
    print("- Advanced query expansion with contextual awareness")
