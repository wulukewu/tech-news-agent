"""Mixin extracted from app/qa_agent/conversation_manager.py."""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.qa_agent.models import ConversationContext, ParsedQuery

logger = logging.getLogger(__name__)


class ConversationAnalysisMixin:
    def _serialize_context(self, context: ConversationContext) -> Dict[str, Any]:
        """Serialize conversation context to JSON-compatible format."""
        # Convert to dict and handle special types
        data = context.model_dump()

        # Convert UUIDs to strings
        data["conversation_id"] = str(data["conversation_id"])
        data["user_id"] = str(data["user_id"])

        # Convert datetime objects to ISO strings
        for field in ["created_at", "last_updated", "expires_at"]:
            if data.get(field):
                data[field] = data[field].isoformat()

        # Serialize turns
        serialized_turns = []
        for turn in data.get("turns", []):
            turn_data = dict(turn)
            if turn_data.get("timestamp"):
                turn_data["timestamp"] = turn_data["timestamp"].isoformat()

            # Serialize nested objects
            if turn_data.get("parsed_query"):
                pq_data = dict(turn_data["parsed_query"])
                if pq_data.get("processed_at"):
                    pq_data["processed_at"] = pq_data["processed_at"].isoformat()
                turn_data["parsed_query"] = pq_data

            if turn_data.get("response"):
                resp_data = dict(turn_data["response"])
                if resp_data.get("generated_at"):
                    resp_data["generated_at"] = resp_data["generated_at"].isoformat()
                if resp_data.get("conversation_id"):
                    resp_data["conversation_id"] = str(resp_data["conversation_id"])

                # Serialize articles in response
                if resp_data.get("articles"):
                    serialized_articles = []
                    for article in resp_data["articles"]:
                        article_data = dict(article)
                        if article_data.get("article_id"):
                            article_data["article_id"] = str(article_data["article_id"])
                        if article_data.get("url"):
                            article_data["url"] = str(article_data["url"])
                        if article_data.get("published_at"):
                            article_data["published_at"] = article_data["published_at"].isoformat()
                        serialized_articles.append(article_data)
                    resp_data["articles"] = serialized_articles

                turn_data["response"] = resp_data

            serialized_turns.append(turn_data)

        data["turns"] = serialized_turns
        return data

    def _deserialize_context(self, context_data: Dict[str, Any], row: Any) -> ConversationContext:
        """Deserialize conversation context from JSON format."""
        # Convert string UUIDs back to UUID objects
        if isinstance(context_data.get("conversation_id"), str):
            context_data["conversation_id"] = UUID(context_data["conversation_id"])
        if isinstance(context_data.get("user_id"), str):
            context_data["user_id"] = UUID(context_data["user_id"])

        # Use database timestamps if available (more reliable)
        context_data["created_at"] = row["created_at"]
        context_data["last_updated"] = row["last_updated"]
        context_data["expires_at"] = row["expires_at"]

        # Deserialize turns
        if context_data.get("turns"):
            deserialized_turns = []
            for turn_data in context_data["turns"]:
                # Convert timestamp
                if isinstance(turn_data.get("timestamp"), str):
                    turn_data["timestamp"] = datetime.fromisoformat(turn_data["timestamp"])

                # Deserialize parsed_query if present
                if turn_data.get("parsed_query"):
                    pq_data = turn_data["parsed_query"]
                    if isinstance(pq_data.get("processed_at"), str):
                        pq_data["processed_at"] = datetime.fromisoformat(pq_data["processed_at"])
                    turn_data["parsed_query"] = ParsedQuery(**pq_data)

                # Deserialize response if present
                if turn_data.get("response"):
                    resp_data = turn_data["response"]
                    if isinstance(resp_data.get("generated_at"), str):
                        resp_data["generated_at"] = datetime.fromisoformat(
                            resp_data["generated_at"]
                        )
                    if isinstance(resp_data.get("conversation_id"), str):
                        resp_data["conversation_id"] = UUID(resp_data["conversation_id"])

                    # Deserialize articles
                    if resp_data.get("articles"):
                        from app.qa_agent.models import ArticleSummary

                        deserialized_articles = []
                        for article_data in resp_data["articles"]:
                            if isinstance(article_data.get("article_id"), str):
                                article_data["article_id"] = UUID(article_data["article_id"])
                            if isinstance(article_data.get("published_at"), str):
                                article_data["published_at"] = datetime.fromisoformat(
                                    article_data["published_at"]
                                )
                            deserialized_articles.append(ArticleSummary(**article_data))
                        resp_data["articles"] = deserialized_articles

                    turn_data["response"] = StructuredResponse(**resp_data)

                deserialized_turns.append(ConversationTurn(**turn_data))

            context_data["turns"] = deserialized_turns

        return ConversationContext(**context_data)

    def _extract_topic_from_query(self, parsed_query: ParsedQuery) -> Optional[str]:
        """Extract topic from parsed query for conversation context."""
        if parsed_query.keywords:
            # Use the first few keywords as the topic
            return " ".join(parsed_query.keywords[:3])
        return None

    async def _analyze_topic_change(self, context: ConversationContext, new_query: str) -> bool:
        """
        Enhanced topic change detection for Task 8.2.

        Analyzes multiple factors to determine if conversation topic has changed:
        - Keyword overlap analysis
        - Query intent comparison
        - Conversation flow patterns
        - Contextual reference detection

        Args:
            context: Current conversation context
            new_query: New query to analyze

        Returns:
            True if topic change detected, False otherwise
        """
        # If no previous turns, no topic change
        if not context.turns:
            return False

        # Get recent queries for analysis
        recent_queries = context.get_recent_queries(count=3)
        if not recent_queries:
            return False

        # 1. Check for contextual references (indicates continuation)
        if self._has_contextual_references(new_query):
            logger.debug("Contextual references detected, continuing conversation")
            return False

        # 2. Analyze keyword overlap with recent queries
        keyword_overlap = self._calculate_keyword_overlap(new_query, recent_queries)
        if keyword_overlap > 0.3:  # 30% overlap threshold
            logger.debug(f"High keyword overlap ({keyword_overlap:.2f}), continuing conversation")
            return False

        # 3. Check query length and complexity (very short queries are likely follow-ups)
        if len(new_query.strip()) < 15:
            logger.debug("Short query detected, likely follow-up")
            return False

        # 4. Analyze topic shift patterns
        if self._detect_topic_shift_patterns(new_query, recent_queries):
            logger.info("Topic shift pattern detected, resetting context")
            return True

        # 5. Check for explicit topic change indicators
        if self._has_topic_change_indicators(new_query):
            logger.info("Explicit topic change indicators found, resetting context")
            return True

        # Default: continue conversation if no clear topic change
        return False

    def _has_contextual_references(self, query: str) -> bool:
        """
        Check if query contains contextual references indicating continuation.

        Enhanced for Task 8.2 to support Requirements 4.2, 4.3.
        """
        query_lower = query.lower()

        # Contextual reference patterns
        contextual_patterns = {
            "zh": [
                "這個",
                "那個",
                "它",
                "他",
                "她",
                "這些",
                "那些",
                "它們",
                "更多",
                "還有",
                "另外",
                "其他",
                "相關",
                "類似",
                "同樣",
                "告訴我更多",
                "詳細說明",
                "進一步",
                "深入",
                "補充",
            ],
            "en": [
                "this",
                "that",
                "it",
                "they",
                "them",
                "these",
                "those",
                "more",
                "also",
                "another",
                "other",
                "related",
                "similar",
                "same",
                "tell me more",
                "more about",
                "elaborate",
                "further",
                "additional",
                "what about",
                "how about",
                "regarding",
                "concerning",
            ],
        }

        # Check for contextual patterns
        for patterns in contextual_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        return False

    def _calculate_keyword_overlap(self, new_query: str, recent_queries: List[str]) -> float:
        """
        Calculate keyword overlap between new query and recent queries.

        Returns overlap ratio (0.0 to 1.0).
        """
        # Extract meaningful words (length > 2, not common stop words)
        stop_words = {
            "zh": {"的", "了", "在", "是", "有", "和", "與", "或", "但", "如果", "因為", "所以"},
            "en": {
                "the",
                "and",
                "or",
                "but",
                "if",
                "because",
                "so",
                "for",
                "with",
                "from",
                "to",
                "at",
                "by",
            },
        }

        def extract_keywords(text: str) -> set:
            words = set()
            for word in text.lower().split():
                # Remove punctuation and filter
                clean_word = "".join(c for c in word if c.isalnum())
                if (
                    len(clean_word) > 2
                    and clean_word not in stop_words.get("zh", set())
                    and clean_word not in stop_words.get("en", set())
                ):
                    words.add(clean_word)
            return words

        new_keywords = extract_keywords(new_query)
        if not new_keywords:
            return 0.0

        # Calculate overlap with recent queries
        total_overlap = 0.0
        for recent_query in recent_queries:
            recent_keywords = extract_keywords(recent_query)
            if recent_keywords:
                overlap = len(new_keywords.intersection(recent_keywords)) / len(
                    new_keywords.union(recent_keywords)
                )
                total_overlap = max(total_overlap, overlap)

        return total_overlap

    def _detect_topic_shift_patterns(self, new_query: str, recent_queries: List[str]) -> bool:
        """
        Detect patterns that indicate a topic shift.
        """
        query_lower = new_query.lower()

        # Topic shift indicators
        shift_patterns = {
            "zh": [
                "現在我想問",
                "另一個問題",
                "換個話題",
                "不同的問題",
                "新的問題",
                "讓我們談談",
                "我想了解",
                "關於",
                "轉到",
                "切換到",
            ],
            "en": [
                "now i want to ask",
                "different question",
                "change topic",
                "new question",
                "let's talk about",
                "i want to know about",
                "switching to",
                "moving to",
                "on a different note",
                "by the way",
                "speaking of",
            ],
        }

        # Check for shift patterns
        for patterns in shift_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        return False

    def _has_topic_change_indicators(self, query: str) -> bool:
        """
        Check for explicit topic change indicators.
        """
        query_lower = query.lower()

        # Explicit topic change phrases
        change_indicators = {
            "zh": ["新話題", "不同主題", "不同", "另一件事", "順便問", "對了", "現在我想問"],
            "en": [
                "new topic",
                "different subject",
                "different",
                "another thing",
                "by the way",
                "incidentally",
                "now i want to ask",
            ],
        }

        for indicators in change_indicators.values():
            if any(indicator in query_lower for indicator in indicators):
                return True

        return False
