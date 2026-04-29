"""Fallback response methods for QAAgentController."""
import logging
from typing import List, Optional

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ResponseType,
    StructuredResponse,
)

logger = logging.getLogger(__name__)


class FallbacksMixin:
    """Mixin providing fallback response creation methods."""

    def _create_error_response(
        self,
        query: str,
        error_message: str,
        suggestions: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        response_time: float = 0.0,
    ) -> StructuredResponse:
        """Create an error response for invalid queries."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=[error_message],
            recommendations=suggestions or [],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_timeout_response(
        self, query: str, conversation_id: Optional[str], response_time: float
    ) -> StructuredResponse:
        """Create a timeout response."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=["Request timed out. Please try a simpler query or try again later."],
            recommendations=[
                "Try breaking your question into smaller parts",
                "Use more specific keywords",
                "Try again in a moment",
            ],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_fallback_response(
        self,
        query: str,
        conversation_id: Optional[str],
        response_time: float,
        error: Exception,
    ) -> StructuredResponse:
        """Create a fallback response when processing fails."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=[
                "I'm having trouble processing your request right now.",
                "Please try rephrasing your question or try again later.",
            ],
            recommendations=[
                "Try using different keywords",
                "Make your question more specific",
                "Check back in a few minutes",
            ],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_timeout_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
    ) -> StructuredResponse:
        """
        Create a fallback response when response generation times out.

        Implements Requirement 9.4: Provide partial results and explain situation when query times out.
        """
        # Create basic article summaries without LLM
        basic_summaries = []
        for article in articles[:3]:  # Limit to 3 for timeout scenario
            summary = ArticleSummary(
                article_id=article.article_id,
                title=article.title,
                summary=self._create_basic_summary(article),
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=article.get_reading_time_estimate(),
                published_at=article.published_at,
                category=article.category,
            )
            basic_summaries.append(summary)

        # Create timeout-specific insights
        timeout_insights = [
            f"Found {len(articles)} relevant articles but detailed analysis timed out.",
            "Here are the most relevant articles with basic summaries:",
        ]

        # Add article titles for quick reference
        if basic_summaries:
            timeout_insights.append(
                "Articles: " + ", ".join([f'"{s.title}"' for s in basic_summaries[:3]])
            )

        return StructuredResponse(
            query=query,
            response_type=ResponseType.PARTIAL,  # Indicates partial results
            articles=basic_summaries,
            insights=timeout_insights,
            recommendations=[
                "Try a more specific query for faster results",
                "Break complex questions into simpler parts",
                "The articles above contain relevant information",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.6,
        )

    def _create_search_results_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
        error_message: str,
    ) -> StructuredResponse:
        """
        Create a fallback response providing search results list when generation fails.

        Implements Requirement 9.2: Provide search results list as alternative when generation fails.
        """
        # Convert articles to basic summaries
        search_results = []
        for article in articles[:5]:  # Show up to 5 results
            summary = ArticleSummary(
                article_id=article.article_id,
                title=article.title,
                summary=self._create_basic_summary(article),
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=article.get_reading_time_estimate(),
                published_at=article.published_at,
                category=article.category,
            )
            search_results.append(summary)

        # Create informative insights about the search results
        insights = [
            f"I found {len(articles)} articles related to your query but couldn't generate detailed insights.",
            "Here are the search results with basic information:",
        ]

        # Add relevance information
        if search_results:
            insights.append(
                f'Most relevant: "{search_results[0].title}" (relevance: {search_results[0].relevance_score:.2f})'
            )

        return StructuredResponse(
            query=query,
            response_type=ResponseType.SEARCH_RESULTS,  # Indicates search results fallback
            articles=search_results,
            insights=insights,
            recommendations=[
                "Click on the article links above to read the full content",
                "Try rephrasing your question for better AI analysis",
                "The articles are sorted by relevance to your query",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.4,  # Lower confidence for fallback
        )

    def _create_basic_summary(self, article: ArticleMatch) -> str:
        """
        Create a basic summary from article content without LLM.

        This is used when LLM-based summarization fails or times out.
        """
        # Use the content preview if available
        if hasattr(article, "content_preview") and article.content_preview:
            preview = article.content_preview
        else:
            # Fallback to metadata or title
            preview = article.metadata.get("description", "") or article.title

        # Truncate to reasonable length
        if len(preview) > 200:
            preview = preview[:197] + "..."

        return preview or "Article content available at the provided link."

    def _create_error_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
        error_message: str,
    ) -> StructuredResponse:
        """
        Create a fallback response when response generation fails completely.

        This is used when even the search results fallback fails.
        """
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],  # No articles if we can't process them at all
            insights=[
                "I'm having trouble processing your request right now.",
                f"Found {len(articles)} potentially relevant articles but couldn't analyze them.",
                "Please try rephrasing your question or try again later.",
            ],
            recommendations=[
                "Try using more specific keywords",
                "Break down complex questions into simpler parts",
                "Check back in a few minutes",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.1,  # Very low confidence for error state
        )

    # Component health check methods
