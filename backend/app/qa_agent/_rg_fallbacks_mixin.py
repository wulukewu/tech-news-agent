"""Mixin extracted from app/qa_agent/response_generator.py."""
import logging
from typing import List, Optional

from app.qa_agent.models import (
    ArticleMatch,
    ConversationContext,
    StructuredResponse,
)

logger = logging.getLogger(__name__)


class ResponseFallbacksMixin:
    def _create_empty_response(
        self, query: str, context: Optional[ConversationContext] = None
    ) -> StructuredResponse:
        """
        Create an empty response when no articles are found.

        Args:
            query: Original user query
            context: Optional conversation context

        Returns:
            StructuredResponse with empty results and helpful message
        """
        return StructuredResponse(
            query=query,
            articles=[],
            insights=["No relevant articles found for your query."],
            recommendations=[
                "Try using different keywords or broader search terms.",
                "Check if there are any typos in your query.",
                "Consider exploring related topics in your article library.",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,
        )

    def _create_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
    ) -> StructuredResponse:
        """
        Create a fallback response when LLM generation fails completely.

        Args:
            query: Original user query
            articles: Retrieved articles
            context: Optional conversation context

        Returns:
            StructuredResponse with basic summaries and fallback content
        """
        # Create basic summaries without LLM
        article_summaries = [
            self._create_fallback_summary(article) for article in articles[: self.max_articles]
        ]

        return StructuredResponse(
            query=query,
            articles=article_summaries,
            insights=self._create_fallback_insights(query, articles),
            recommendations=self._create_fallback_recommendations(query, articles),
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,
        )
