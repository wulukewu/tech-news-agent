"""
Response Generator for Intelligent Q&A Agent

This module implements the ResponseGenerator class that creates structured responses
using retrieved articles and conversation context. It integrates with LLM services
to generate article summaries and personalized insights.

Requirements addressed:
- 3.1: Generate structured responses with article summaries, original links, and personalized insights
- 3.2: Display max 5 articles sorted by relevance
- 3.3: Provide 2-3 sentence summaries for each article
- 5.5: Use retrieved article content as context for generating responses
"""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings

from .models import (
    ArticleMatch,
    ConversationContext,
    StructuredResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)


from app.qa_agent._rg_fallbacks_mixin import ResponseFallbacksMixin
from app.qa_agent._rg_recommendations_mixin import RecommendationsMixin
from app.qa_agent._rg_summaries_mixin import SummariesMixin


class ResponseGeneratorError(Exception):
    """Base exception for response generation errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ResponseGenerator(SummariesMixin, RecommendationsMixin, ResponseFallbacksMixin):
    """
    Generates structured responses using retrieved articles and LLM integration.

    This class is responsible for:
    - Creating article summaries (2-3 sentences each)
    - Generating personalized insights based on user profile
    - Formatting structured responses with all required elements
    - Handling LLM API failures gracefully with fallback mechanisms
    """

    def __init__(self):
        """Initialize the ResponseGenerator with Groq client (OpenAI-compatible)."""
        try:
            self.settings = get_settings()
            api_key = self.settings.groq_api_key
        except Exception:
            # Fallback for testing when config is not loaded
            api_key = "gsk_test-key"

        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1", api_key=api_key, timeout=30.0
        )
        self.model = "llama-3.3-70b-versatile"
        self.max_articles = 5  # Requirement 3.2: Display max 5 articles

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def _call_openai_api(
        self, messages: List[Dict[str, str]], max_tokens: int = 500, temperature: float = 0.3
    ) -> str:
        """
        Call OpenAI API with retry logic.

        Args:
            messages: List of message dictionaries for the conversation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated text response

        Raises:
            ResponseGeneratorError: If API call fails after retries
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30.0,
            )

            if not response.choices or not response.choices[0].message.content:
                raise ResponseGeneratorError("Empty response from Groq API")

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}")
            raise ResponseGeneratorError(f"LLM API call failed: {str(e)}", e)

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        """
        Generate a structured response using retrieved articles and context.

        Enhanced for Requirements 8.2, 8.4: Prioritize articles from user's areas of interest
        and include personalized insights based on user preferences

        Args:
            query: The user's original query
            articles: List of retrieved articles (will be limited to max 5)
            context: Optional conversation context for multi-turn conversations
            user_profile: Optional user profile for personalization

        Returns:
            StructuredResponse with summaries, insights, and recommendations

        Raises:
            ResponseGeneratorError: If response generation fails
        """
        try:
            # Enhanced article ranking with user preference prioritization (Requirement 8.2)
            ranked_articles = self._rank_articles_by_user_interest(articles, user_profile)

            # Limit to max 5 articles (Requirement 3.2)
            top_articles = ranked_articles[: self.max_articles]

            if not top_articles:
                return self._create_empty_response(query, context)

            # Generate summaries for each article with enhanced personalization
            article_summaries = await self._generate_article_summaries(
                top_articles, query, user_profile
            )

            # Generate enhanced personalized insights (Requirements 3.4, 8.4)
            insights = await self._generate_insights(query, top_articles, user_profile, context)

            # Generate enhanced recommendations for related reading (Requirement 3.5)
            recommendations = await self._generate_recommendations(
                query, top_articles, user_profile
            )

            return StructuredResponse(
                query=query,
                articles=article_summaries,
                insights=insights,
                recommendations=recommendations,
                conversation_id=context.conversation_id if context else uuid4(),
                response_time=0.0,  # Will be set by the controller
            )

        except Exception as e:
            logger.error(f"Response generation failed for query '{query}': {str(e)}")
            # Fallback to basic response without LLM-generated content
            return self._create_fallback_response(query, articles, context)
