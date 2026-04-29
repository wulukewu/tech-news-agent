"""Mixin extracted from app/qa_agent/query_processor.py."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.qa_agent.models import ConversationContext, QueryLanguage
from app.qa_agent.query_processor import QueryValidationResult

logger = logging.getLogger(__name__)


class SuggestionsMixin:
    async def generate_contextual_suggestions(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
        user_profile: Optional["UserProfile"] = None,
    ) -> List[str]:
        """
        Generate context-aware query suggestions.
        Task 4.2 enhancement.

        Args:
            query: Current or partial query
            context: Optional conversation context
            user_profile: Optional user profile for personalization

        Returns:
            List of suggested queries
        """
        language = self._detect_language(query)
        suggestions = []

        # Start with basic template suggestions
        template_suggestions = self.generate_query_suggestions(query, language)
        suggestions.extend(template_suggestions)

        # Add context-based suggestions if available
        if context and context.current_topic:
            topic = context.current_topic
            if language == QueryLanguage.CHINESE:
                suggestions.extend([f"關於{topic}的更多細節", f"{topic}的實際應用", f"{topic}與{query}的關係"])
            else:
                suggestions.extend(
                    [
                        f"More details about {topic}",
                        f"Practical applications of {topic}",
                        f"How {topic} relates to {query}",
                    ]
                )

        # Add user history-based suggestions if available
        if user_profile and user_profile.preferred_topics:
            top_topics = user_profile.get_top_topics(limit=2)
            for topic in top_topics:
                if language == QueryLanguage.CHINESE:
                    suggestions.append(f"{query}在{topic}領域的應用")
                else:
                    suggestions.append(f"{query} in {topic}")

        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion.lower())

        return unique_suggestions[:10]  # Limit to 10 suggestions

    def _is_followup_query(self, query: str) -> bool:
        """
        Determine if query is a follow-up question.

        Args:
            query: Query text

        Returns:
            True if query appears to be a follow-up
        """
        query_lower = query.lower()

        # Follow-up indicators
        followup_indicators = {
            "zh": ["這個", "那個", "它", "他", "她", "更多", "還有", "另外", "其他"],
            "en": ["this", "that", "it", "more", "also", "another", "other", "what about"],
        }

        # Check for indicators
        for indicators in followup_indicators.values():
            if any(indicator in query_lower for indicator in indicators):
                return True

        # Check if query is very short (likely a follow-up)
        if len(query.strip()) < 20:
            return True

        return False

    async def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate query and provide error messages or suggestions.

        Args:
            query: Query text to validate

        Returns:
            QueryValidationResult with validation status and details

        Requirements: 1.5
        """
        # Check if query is empty
        if not query or not query.strip():
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_QUERY,
                error_message="Query cannot be empty",
                suggestions=["Please provide a question or search term"],
            )

        # Check query length
        if len(query) > PerformanceLimits.MAX_QUERY_LENGTH:
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.QUERY_TOO_LONG,
                error_message=f"Query exceeds maximum length of {PerformanceLimits.MAX_QUERY_LENGTH} characters",
                suggestions=[
                    "Please shorten your query",
                    "Try breaking it into multiple questions",
                ],
            )

        # Check if query has meaningful content
        if not re.search(r"[a-zA-Z\u4e00-\u9fff]", query):
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_QUERY,
                error_message="Query must contain letters or characters",
                suggestions=["Please provide a meaningful question"],
            )

        # Parse query to check confidence
        parsed = await self.parse_query(query)

        # Check if query requires clarification
        if parsed.requires_clarification():
            language = parsed.language.value
            clarification_msgs = MessageTemplates.CLARIFICATION_REQUESTS.get(language, [])

            return QueryValidationResult(
                is_valid=True,  # Query is valid but needs clarification
                error_code=None,
                error_message=None,
                suggestions=clarification_msgs,
            )

        # Query is valid
        return QueryValidationResult(is_valid=True)

    def generate_query_suggestions(self, partial_query: str, language: QueryLanguage) -> List[str]:
        """
        Generate query suggestions for unclear or incomplete queries.

        Args:
            partial_query: Incomplete or unclear query
            language: Query language

        Returns:
            List of suggested complete queries

        Requirements: 1.3
        """
        lang_code = language.value

        # Common query templates
        templates = {
            "zh": [
                f"關於{partial_query}的最新文章",
                f"如何{partial_query}",
                f"{partial_query}的教程",
                f"{partial_query}的最佳實踐",
                f"推薦一些{partial_query}相關的文章",
            ],
            "en": [
                f"Latest articles about {partial_query}",
                f"How to {partial_query}",
                f"{partial_query} tutorial",
                f"{partial_query} best practices",
                f"Recommend articles about {partial_query}",
            ],
        }

        return templates.get(lang_code, templates["en"])[:5]

    def _extract_topics(self, query: str, lang_code: str) -> Optional[List[str]]:
        """
        Extract topic/category filters from query.
        Task 4.2 enhancement.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            List of detected topics or None
        """
        query_lower = query.lower()
        topic_keywords = self.topic_keywords.get(lang_code, {})

        detected_topics = []
        for topic, synonyms in topic_keywords.items():
            # Check if topic or any synonym is in query
            if topic.lower() in query_lower:
                detected_topics.append(topic)
            else:
                for synonym in synonyms:
                    if synonym.lower() in query_lower:
                        detected_topics.append(topic)
                        break

        return detected_topics if detected_topics else None

    def _extract_advanced_time_range(
        self, query: str, lang_code: str
    ) -> Optional[Dict[str, datetime]]:
        """
        Extract advanced time range patterns like "between X and Y" or "last N months".
        Task 4.2 enhancement.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            Dictionary with start and end datetime, or None
        """
        query_lower = query.lower()

        # Pattern: "last N months/weeks/days"
        import re

        if lang_code == "zh":
            # Pattern: 最近N個月/週/天
            patterns = [
                (r"最近(\d+)個月", lambda n: timedelta(days=int(n) * 30)),
                (r"最近(\d+)週", lambda n: timedelta(weeks=int(n))),
                (r"最近(\d+)天", lambda n: timedelta(days=int(n))),
                (r"過去(\d+)個月", lambda n: timedelta(days=int(n) * 30)),
                (r"過去(\d+)年", lambda n: timedelta(days=int(n) * 365)),
            ]
        else:
            # Pattern: last N months/weeks/days
            patterns = [
                (r"last (\d+) months?", lambda n: timedelta(days=int(n) * 30)),
                (r"last (\d+) weeks?", lambda n: timedelta(weeks=int(n))),
                (r"last (\d+) days?", lambda n: timedelta(days=int(n))),
                (r"past (\d+) months?", lambda n: timedelta(days=int(n) * 30)),
                (r"past (\d+) years?", lambda n: timedelta(days=int(n) * 365)),
            ]

        for pattern, delta_func in patterns:
            match = re.search(pattern, query_lower)
            if match:
                n = match.group(1)
                delta = delta_func(n)
                end_time = datetime.utcnow()
                start_time = end_time - delta
                return {"start": start_time, "end": end_time}

        # Pattern: "between X and Y" (simplified - would need date parsing library for full support)
        if lang_code == "zh":
            between_pattern = r"(從|在).*?(到|至)"
        else:
            between_pattern = r"between .* and"

        if re.search(between_pattern, query_lower):
            # For now, return a default range
            # In production, this would use a date parsing library like dateutil
            self.logger.info("Detected 'between' time pattern but detailed parsing not implemented")
            # Return last 3 months as default
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)
            return {"start": start_time, "end": end_time}

        return None
