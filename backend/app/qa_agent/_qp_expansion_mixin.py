"""Mixin extracted from app/qa_agent/query_processor.py."""
import logging

from app.qa_agent.models import ConversationContext

logger = logging.getLogger(__name__)


class ExpansionMixin:
    async def expand_query(self, query: str, context: ConversationContext) -> str:
        """
        Expand query using conversation context for follow-up questions.
        Enhanced for Task 8.2 with improved contextual understanding.

        Supports Requirements 4.2, 4.3:
        - Combines previous conversation content with new questions
        - Handles context-related queries like "tell me more about this"
        - Provides intelligent query expansion based on conversation history

        Args:
            query: Current query
            context: Conversation context

        Returns:
            Expanded query with context and synonyms

        Requirements: 1.4, 4.2, 4.3
        """
        # If no context or first turn, apply synonym expansion only
        if not context or len(context.turns) == 0:
            return await self._expand_with_synonyms(query)

        # Enhanced contextual query analysis
        expanded_query = await self._expand_with_context(query, context)

        # Apply synonym expansion to the expanded query
        expanded_query = await self._expand_with_synonyms(expanded_query)

        self.logger.info(f"Expanded query: '{query}' -> '{expanded_query}'")
        return expanded_query

    async def _expand_with_context(self, query: str, context: ConversationContext) -> str:
        """
        Enhanced contextual query expansion for Task 8.2.

        Handles various types of contextual queries:
        - Direct references ("this", "that", "it")
        - Follow-up questions ("tell me more", "what about")
        - Comparative queries ("are there other", "similar ones")
        - Clarification requests ("explain further", "more details")
        """
        query_lower = query.lower()

        # 1. Handle direct contextual references
        if self._has_direct_references(query_lower):
            return self._expand_direct_references(query, context)

        # 2. Handle follow-up question patterns
        if self._is_followup_pattern(query_lower):
            return self._expand_followup_query(query, context)

        # 3. Handle comparative/exploratory queries
        if self._is_comparative_query(query_lower):
            return self._expand_comparative_query(query, context)

        # 4. Handle clarification requests
        if self._is_clarification_request(query_lower):
            return self._expand_clarification_request(query, context)

        # 5. For other queries, check if they're contextually related
        if self._is_contextually_related(query, context):
            return self._expand_related_query(query, context)

        # If no contextual expansion needed, return original query
        return query

    def _has_direct_references(self, query_lower: str) -> bool:
        """Check if query has direct references to previous content."""
        direct_refs = {
            "zh": ["這個", "那個", "它", "他", "她", "這些", "那些", "它們"],
            "en": ["this", "that", "it", "they", "them", "these", "those"],
        }

        for refs in direct_refs.values():
            if any(ref in query_lower for ref in refs):
                return True
        return False

    def _expand_direct_references(self, query: str, context: ConversationContext) -> str:
        """Expand queries with direct references using conversation context."""
        if not context.turns:
            return query

        # Get the most recent response for context
        last_turn = context.turns[-1]
        if last_turn.response and last_turn.response.articles:
            # Use the first article's title as reference context
            article_context = last_turn.response.articles[0].title
            return f"{article_context}: {query}"
        elif context.current_topic:
            return f"{context.current_topic}: {query}"
        else:
            # Use the last query as context
            return f"{last_turn.query} {query}"

    def _is_followup_pattern(self, query_lower: str) -> bool:
        """Enhanced follow-up pattern detection."""
        followup_patterns = {
            "zh": [
                "告訴我更多",
                "更多資訊",
                "詳細說明",
                "進一步",
                "深入了解",
                "還有什麼",
                "其他的",
                "更多關於",
                "補充",
                "擴展",
                "更多細節",
            ],
            "en": [
                "tell me more",
                "more about",
                "more information",
                "elaborate",
                "further details",
                "more details",
                "what else",
                "additional",
                "expand on",
                "more on",
                "continue",
                "go deeper",
            ],
        }

        for patterns in followup_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True
        return False

    def _expand_followup_query(self, query: str, context: ConversationContext) -> str:
        """Expand follow-up queries with relevant context."""
        if not context.turns:
            return query

        # Combine with current topic and recent context
        if context.current_topic:
            base_context = context.current_topic
        else:
            # Use keywords from recent queries
            recent_queries = context.get_recent_queries(count=2)
            base_context = " ".join(recent_queries) if recent_queries else ""

        return f"{base_context} {query}" if base_context else query

    def _is_comparative_query(self, query_lower: str) -> bool:
        """Check if query is asking for comparisons or alternatives."""
        comparative_patterns = {
            "zh": [
                "有其他",
                "還有別的",
                "類似的",
                "相關的",
                "比較",
                "對比",
                "不同的",
                "替代的",
                "另外的選擇",
            ],
            "en": [
                "are there other",
                "other similar",
                "alternatives",
                "related ones",
                "compare",
                "comparison",
                "different",
                "alternative",
                "similar to",
            ],
        }

        for patterns in comparative_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True
        return False

    def _expand_comparative_query(self, query: str, context: ConversationContext) -> str:
        """Expand comparative queries with context for better search."""
        if context.current_topic:
            return f"alternatives to {context.current_topic}: {query}"
        elif context.turns:
            last_query = context.turns[-1].query
            return f"alternatives to {last_query}: {query}"
        return query

    def _is_clarification_request(self, query_lower: str) -> bool:
        """Check if query is requesting clarification or explanation."""
        # More specific clarification patterns that indicate contextual clarification
        clarification_patterns = {
            "zh": [
                "解釋這個",
                "說明這個",
                "澄清",
                "詳細說明",
                "具體解釋",
                "什麼意思",
                "能否解釋",
                "怎麼理解",
                "為什麼這樣",
            ],
            "en": [
                "explain this",
                "clarify this",
                "what does this mean",
                "how does this work",
                "can you explain",
                "elaborate on this",
                "break down this",
                "what do you mean",
            ],
        }

        # Check for contextual clarification patterns (not general "what is" questions)
        for patterns in clarification_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        # Additional check for contextual references with clarification intent
        contextual_clarification = [
            "explain that",
            "clarify that",
            "what does that mean",
            "how does that work",
        ]

        return any(pattern in query_lower for pattern in contextual_clarification)

    def _expand_clarification_request(self, query: str, context: ConversationContext) -> str:
        """Expand clarification requests with specific context."""
        if context.current_topic:
            return f"explain {context.current_topic}: {query}"
        elif context.turns:
            # Use the most recent article or topic mentioned
            last_turn = context.turns[-1]
            if last_turn.response and last_turn.response.articles:
                article_title = last_turn.response.articles[0].title
                return f"explain {article_title}: {query}"
        return query

    def _is_contextually_related(self, query: str, context: ConversationContext) -> bool:
        """Check if query is contextually related to ongoing conversation."""
        if not context.current_topic:
            return False

        # Enhanced contextual relatedness detection
        query_words = set(word.lower() for word in query.split() if len(word) > 2)
        topic_words = set(word.lower() for word in context.current_topic.split() if len(word) > 2)

        if not query_words or not topic_words:
            return False

        # Check for direct word overlap
        direct_overlap = len(query_words.intersection(topic_words)) / len(
            query_words.union(topic_words)
        )
        if direct_overlap > 0.1:  # Lower threshold for direct overlap
            return True

        # Check for semantic relatedness using domain knowledge
        ai_related_terms = {
            "artificial",
            "intelligence",
            "ai",
            "machine",
            "learning",
            "ml",
            "deep",
            "neural",
            "network",
            "algorithm",
            "model",
            "data",
            "science",
            "automation",
            "robot",
            "nlp",
            "computer",
            "vision",
            "processing",
            "natural",
            "language",
            "applications",
        }

        tech_related_terms = {
            "technology",
            "software",
            "programming",
            "development",
            "system",
            "application",
            "platform",
            "framework",
            "tool",
            "solution",
            "innovation",
            "digital",
        }

        # Check if both query and topic contain related terms
        query_ai_terms = query_words.intersection(ai_related_terms)
        topic_ai_terms = topic_words.intersection(ai_related_terms)

        if query_ai_terms and topic_ai_terms:
            return True

        query_tech_terms = query_words.intersection(tech_related_terms)
        topic_tech_terms = topic_words.intersection(tech_related_terms)

        if query_tech_terms and topic_tech_terms:
            return True

        return False

    def _expand_related_query(self, query: str, context: ConversationContext) -> str:
        """Expand contextually related queries."""
        if context.current_topic:
            return f"{context.current_topic} {query}"
        return query

    async def _expand_with_synonyms(self, query: str) -> str:
        """
        Expand query with synonyms for better search coverage.
        Task 4.2 enhancement.

        Args:
            query: Original query

        Returns:
            Query with key terms expanded with synonyms
        """
        # Detect language
        language = self._detect_language(query)
        lang_code = language.value

        # Get synonyms for this language
        synonym_dict = self.synonyms.get(lang_code, {})

        # Find and expand key terms
        query_lower = query.lower()
        expanded_terms = []

        for term, synonyms in synonym_dict.items():
            if term in query_lower:
                # Add original term and first synonym
                expanded_terms.append(f"({term} OR {synonyms[0]})")

        # If we found terms to expand, append them to the query
        if expanded_terms:
            expansion = " ".join(expanded_terms)
            return f"{query} {expansion}"

        return query
