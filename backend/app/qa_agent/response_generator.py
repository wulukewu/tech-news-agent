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

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings

from .models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    StructuredResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)


class ResponseGeneratorError(Exception):
    """Base exception for response generation errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ResponseGenerator:
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

    async def _generate_article_summaries(
        self, articles: List[ArticleMatch], query: str, user_profile: Optional[UserProfile] = None
    ) -> List[ArticleSummary]:
        """
        Generate 2-3 sentence summaries for each article.

        Args:
            articles: List of articles to summarize
            query: Original user query for context
            user_profile: Optional user profile for personalization

        Returns:
            List of ArticleSummary objects with generated summaries
        """
        summaries = []

        # Process articles concurrently for better performance
        tasks = [
            self._generate_single_summary(article, query, user_profile) for article in articles
        ]

        try:
            summary_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(summary_results):
                if isinstance(result, Exception):
                    logger.warning(
                        f"Failed to generate summary for article {articles[i].article_id}: {result}"
                    )
                    # Create fallback summary
                    summaries.append(self._create_fallback_summary(articles[i]))
                else:
                    summaries.append(result)

        except Exception as e:
            logger.error(f"Batch summary generation failed: {str(e)}")
            # Create fallback summaries for all articles
            summaries = [self._create_fallback_summary(article) for article in articles]

        return summaries

    async def _generate_single_summary(
        self, article: ArticleMatch, query: str, user_profile: Optional[UserProfile] = None
    ) -> ArticleSummary:
        """
        Generate a summary for a single article.

        Args:
            article: Article to summarize
            query: Original user query
            user_profile: Optional user profile

        Returns:
            ArticleSummary with generated content
        """
        try:
            # Determine language preference
            language = (
                "Chinese"
                if user_profile and user_profile.language_preference == "zh"
                else "English"
            )

            # Create prompt for article summarization
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert at creating concise, informative article summaries.
                    Create a 2-3 sentence summary in {language} that:
                    1. Captures the main points relevant to the user's query
                    2. Highlights key insights or findings
                    3. Is clear and engaging for technical readers

                    Focus on information that directly relates to: "{query}"
                    """,
                },
                {
                    "role": "user",
                    "content": f"""Article Title: {article.title}

                    Article Content Preview: {article.content_preview}

                    User Query: {query}

                    Please provide a 2-3 sentence summary that highlights how this article relates to the query.""",
                },
            ]

            summary_text = await self._call_openai_api(messages, max_tokens=200)

            # Extract key insights (simple keyword extraction for now)
            key_insights = self._extract_key_insights(article, summary_text)

            return ArticleSummary(
                article_id=article.article_id,  # Already a UUID
                title=article.title,
                summary=summary_text,
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=article.get_reading_time_estimate(),
                key_insights=key_insights,
                published_at=article.published_at,
                category=article.category,
            )

        except Exception as e:
            logger.warning(
                f"Failed to generate LLM summary for article {article.article_id}: {str(e)}"
            )
            return self._create_fallback_summary(article)

    def _create_fallback_summary(self, article: ArticleMatch) -> ArticleSummary:
        """
        Create a fallback summary when LLM generation fails.

        Args:
            article: Article to create fallback summary for

        Returns:
            ArticleSummary with basic content
        """
        # Use first 2-3 sentences from content preview as fallback
        sentences = article.content_preview.split(". ")

        # Ensure we have at least 2 sentences for validation
        if len(sentences) < 2:
            # If content preview doesn't have enough sentences, create them
            fallback_summary = f"{article.content_preview.rstrip('.')}. This article provides valuable insights on the topic."
        else:
            # Take first 2-3 sentences
            selected_sentences = sentences[:3]
            fallback_summary = ". ".join(selected_sentences)
            if not fallback_summary.endswith("."):
                fallback_summary += "."

        return ArticleSummary(
            article_id=article.article_id,  # Already a UUID
            title=article.title,
            summary=fallback_summary,
            url=article.url,
            relevance_score=article.similarity_score,
            reading_time=article.get_reading_time_estimate(),
            key_insights=[],
            published_at=article.published_at,
            category=article.category,
        )

    def _extract_key_insights(self, article: ArticleMatch, summary: str) -> List[str]:
        """
        Extract key insights from article and summary.

        Args:
            article: Original article
            summary: Generated summary

        Returns:
            List of key insight strings
        """
        insights = []

        # Simple keyword-based insight extraction
        technical_keywords = [
            "algorithm",
            "performance",
            "security",
            "scalability",
            "architecture",
            "framework",
            "library",
            "API",
            "database",
            "cloud",
            "AI",
            "ML",
            "optimization",
            "best practice",
            "pattern",
            "design",
        ]

        content_lower = (article.content_preview + " " + summary).lower()

        for keyword in technical_keywords:
            if keyword in content_lower:
                insights.append(keyword.title())

        return insights[:5]  # Limit to 5 key insights

    async def _generate_insights(
        self,
        query: str,
        articles: List[ArticleMatch],
        user_profile: Optional[UserProfile] = None,
        context: Optional[ConversationContext] = None,
    ) -> List[str]:
        """
        Generate personalized insights based on articles and user profile.

        Enhanced for Requirements 3.4, 8.4: Generate personalized insights based on user reading history

        Args:
            query: Original user query
            articles: Retrieved articles
            user_profile: Optional user profile for personalization
            context: Optional conversation context

        Returns:
            List of insight strings
        """
        try:
            # Determine language preference
            language = (
                "Chinese"
                if user_profile and user_profile.language_preference == "zh"
                else "English"
            )

            # Build enhanced user context based on reading history and preferences
            user_context = ""
            reading_patterns = ""
            if user_profile:
                top_topics = user_profile.get_top_topics(
                    5
                )  # Get more topics for better personalization
                if top_topics:
                    user_context = f"User's main interests: {', '.join(top_topics)}. "

                # Analyze reading history patterns
                if user_profile.reading_history:
                    reading_count = len(user_profile.reading_history)
                    reading_patterns = f"User has read {reading_count} articles. "

                    # Check if user has read similar articles
                    similar_articles = self._find_similar_read_articles(articles, user_profile)
                    if similar_articles:
                        reading_patterns += f"User has previously read {len(similar_articles)} similar articles on this topic. "

                # Include satisfaction patterns
                avg_satisfaction = user_profile.get_average_satisfaction()
                if avg_satisfaction > 0.7:
                    reading_patterns += "User typically finds technical content highly valuable. "
                elif avg_satisfaction < 0.4:
                    reading_patterns += "User prefers more practical, actionable content. "

            # Build conversation context with topic evolution
            conversation_context = ""
            if context and context.turns:
                recent_queries = context.get_recent_queries(3)  # Get more context
                if recent_queries:
                    conversation_context = (
                        f"Recent conversation topics: {', '.join(recent_queries)}. "
                    )

                    # Detect if this is a follow-up or deep-dive query
                    if len(recent_queries) > 1:
                        conversation_context += (
                            "This appears to be a follow-up question for deeper exploration. "
                        )

            # Create enhanced articles context with cross-article analysis
            articles_context = self._create_enhanced_articles_context(articles, user_profile)

            # Generate cross-article insights
            cross_insights = self._analyze_cross_article_patterns(articles, user_profile)

            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert technical analyst specializing in personalized insights. Generate 2-3 highly personalized insights in {language} based on the retrieved articles, user's reading history, and preferences.

                    Insights should:
                    1. Connect patterns across articles and relate to user's known interests
                    2. Build on user's existing knowledge from their reading history
                    3. Highlight practical implications specific to user's expertise level
                    4. Suggest actionable next steps tailored to user's learning patterns
                    5. Reference how this relates to user's previous interests or queries

                    {user_context}{reading_patterns}{conversation_context}

                    Cross-article patterns detected: {cross_insights}""",
                },
                {
                    "role": "user",
                    "content": f"""User Query: {query}

                    Retrieved Articles Analysis:
                    {articles_context}

                    Please provide 2-3 highly personalized insights that:
                    - Connect to the user's established interests and reading patterns
                    - Build upon their existing knowledge base
                    - Offer actionable takeaways specific to their expertise level
                    - Highlight unique connections they might not have considered""",
                },
            ]

            insights_text = await self._call_openai_api(
                messages, max_tokens=400
            )  # More tokens for detailed insights

            # Split insights by lines or bullet points
            insights = [
                insight.strip().lstrip("•-*").strip()
                for insight in insights_text.split("\n")
                if insight.strip()
                and len(insight.strip()) > 15  # Require more substantial insights
            ]

            # Add reading history-based insights if available
            if user_profile and user_profile.reading_history:
                history_insights = self._generate_reading_history_insights(
                    query, articles, user_profile
                )
                insights.extend(history_insights)

            return insights[:3]  # Limit to 3 best insights

        except Exception as e:
            logger.warning(f"Failed to generate enhanced insights: {str(e)}")
            return self._create_fallback_insights(query, articles)

    def _create_fallback_insights(self, query: str, articles: List[ArticleMatch]) -> List[str]:
        """
        Create fallback insights when LLM generation fails.

        Args:
            query: Original user query
            articles: Retrieved articles

        Returns:
            List of basic insight strings
        """
        insights = []

        if articles:
            insights.append(f"Found {len(articles)} relevant articles about your query.")

            # Check for common themes
            titles_text = " ".join([article.title.lower() for article in articles])
            if "security" in titles_text:
                insights.append(
                    "Security considerations appear to be a key theme in these articles."
                )
            if "performance" in titles_text:
                insights.append("Performance optimization is discussed across multiple articles.")
            if "best practice" in titles_text or "best-practice" in titles_text:
                insights.append(
                    "Best practices and recommendations are highlighted in the results."
                )

        return insights[:3]

    def _find_similar_read_articles(
        self, current_articles: List[ArticleMatch], user_profile: UserProfile
    ) -> List[UUID]:
        """
        Find articles from reading history that are similar to current results.

        Args:
            current_articles: Currently retrieved articles
            user_profile: User profile with reading history

        Returns:
            List of similar article IDs from reading history
        """
        similar_articles = []

        # Extract topics and keywords from current articles
        current_topics = set()
        current_keywords = set()

        for article in current_articles:
            # Extract from title and content
            title_words = set(article.title.lower().split())
            content_words = set(article.content_preview.lower().split()[:50])  # First 50 words
            current_keywords.update(title_words)
            current_keywords.update(content_words)

            # Extract from metadata if available
            if article.metadata:
                if "topics" in article.metadata:
                    current_topics.update(article.metadata["topics"])
                if "category" in article.metadata:
                    current_topics.add(article.metadata["category"])

        # For now, return a subset of reading history as similar
        # In a real implementation, this would use vector similarity or topic matching
        if user_profile.reading_history:
            # Return up to 3 recent articles as potentially similar
            return user_profile.reading_history[-3:]

        return similar_articles

    def _create_enhanced_articles_context(
        self, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> str:
        """
        Create enhanced context about articles with cross-references and user relevance.

        Args:
            articles: Retrieved articles
            user_profile: Optional user profile

        Returns:
            Enhanced articles context string
        """
        context_parts = []

        for i, article in enumerate(articles[:3], 1):
            article_context = f"{i}. {article.title}"

            # Add relevance score
            article_context += f" (Relevance: {article.similarity_score:.2f})"

            # Add user-specific context
            if user_profile and user_profile.has_read_article(article.article_id):
                article_context += " [Previously read by user]"

            # Add category/topic if available
            if article.metadata:
                if "category" in article.metadata:
                    article_context += f" [Category: {article.metadata['category']}]"

            # Add content preview
            article_context += f"\n   Summary: {article.content_preview[:150]}..."

            context_parts.append(article_context)

        return "\n\n".join(context_parts)

    def _analyze_cross_article_patterns(
        self, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> str:
        """
        Analyze patterns across multiple articles.

        Args:
            articles: Retrieved articles
            user_profile: Optional user profile

        Returns:
            String describing cross-article patterns
        """
        if len(articles) < 2:
            return "Single article analysis."

        patterns = []

        # Analyze common themes
        all_titles = " ".join([article.title.lower() for article in articles])
        common_terms = [
            "AI",
            "machine learning",
            "security",
            "performance",
            "cloud",
            "API",
            "database",
        ]

        found_terms = [term for term in common_terms if term.lower() in all_titles]
        if found_terms:
            patterns.append(f"Common themes: {', '.join(found_terms)}")

        # Analyze publication recency
        recent_articles = sum(
            1
            for article in articles
            if article.published_at and (datetime.utcnow() - article.published_at).days < 30
        )
        if recent_articles > 1:
            patterns.append(f"{recent_articles} recent articles (last 30 days)")

        # Analyze user familiarity
        if user_profile:
            read_count = sum(
                1 for article in articles if user_profile.has_read_article(article.article_id)
            )
            if read_count > 0:
                patterns.append(f"User has read {read_count} similar articles")

        return "; ".join(patterns) if patterns else "Diverse article collection"

    def _generate_reading_history_insights(
        self, query: str, articles: List[ArticleMatch], user_profile: UserProfile
    ) -> List[str]:
        """
        Generate insights based on user's reading history patterns.

        Args:
            query: Original query
            articles: Current articles
            user_profile: User profile with reading history

        Returns:
            List of reading history-based insights
        """
        insights = []

        # Analyze reading volume
        reading_count = len(user_profile.reading_history)
        if reading_count > 100:
            insights.append(
                "Based on your extensive reading history, this topic aligns with your deep technical interests."
            )
        elif reading_count > 20:
            insights.append(
                "This topic complements your growing knowledge base from previous readings."
            )

        # Analyze topic consistency
        user_topics = set(user_profile.preferred_topics)
        if user_topics:
            # Check if current articles match user's interests
            article_topics = set()
            for article in articles:
                if article.metadata and "topics" in article.metadata:
                    article_topics.update(article.metadata["topics"])

            overlap = user_topics.intersection(article_topics)
            if overlap:
                insights.append(
                    f"This directly relates to your interests in {', '.join(list(overlap)[:2])}."
                )

        # Analyze satisfaction patterns
        avg_satisfaction = user_profile.get_average_satisfaction()
        if avg_satisfaction > 0.7:
            insights.append(
                "Given your high satisfaction with similar content, these articles should provide valuable insights."
            )

        return insights[:2]  # Limit to 2 additional insights

    def _analyze_reading_patterns(self, user_profile: UserProfile) -> str:
        """
        Analyze user's reading patterns for personalized recommendations.

        Args:
            user_profile: User profile with reading history

        Returns:
            String describing reading patterns
        """
        patterns = []

        # Analyze reading volume and frequency
        reading_count = len(user_profile.reading_history)
        if reading_count > 200:
            patterns.append("User is a heavy reader who appreciates comprehensive coverage.")
        elif reading_count > 50:
            patterns.append("User has moderate reading habits and values quality content.")
        elif reading_count > 10:
            patterns.append("User is building their knowledge base and prefers focused content.")

        # Analyze satisfaction patterns
        avg_satisfaction = user_profile.get_average_satisfaction()
        if avg_satisfaction > 0.8:
            patterns.append("User has high standards and appreciates in-depth technical content.")
        elif avg_satisfaction > 0.6:
            patterns.append("User values practical, well-structured content.")
        elif avg_satisfaction < 0.4:
            patterns.append(
                "User prefers concise, actionable content over theoretical discussions."
            )

        # Analyze query patterns
        if len(user_profile.query_history) > 10:
            recent_queries = user_profile.query_history[-5:]
            if any("how to" in query.lower() for query in recent_queries):
                patterns.append("User often seeks practical implementation guidance.")
            if any("best practice" in query.lower() for query in recent_queries):
                patterns.append("User is interested in industry standards and best practices.")

        return " ".join(patterns)

    def _create_extended_reading_context(
        self,
        query: str,
        articles: List[ArticleMatch],
        article_topics: List[str],
        user_profile: Optional[UserProfile] = None,
    ) -> str:
        """
        Create context for extended reading suggestions.

        Args:
            query: Original query
            articles: Retrieved articles
            article_topics: Topics from articles
            user_profile: Optional user profile

        Returns:
            Extended reading context string
        """
        context_parts = []

        # Identify knowledge gaps and expansion opportunities
        if "beginner" in query.lower() or "introduction" in query.lower():
            context_parts.append(
                "User seeking foundational knowledge - suggest progressive learning path"
            )
        elif "advanced" in query.lower() or "expert" in query.lower():
            context_parts.append(
                "User has advanced needs - suggest cutting-edge developments and deep dives"
            )

        # Analyze topic breadth
        unique_topics = set(article_topics)
        if len(unique_topics) > 3:
            context_parts.append("Diverse topics covered - suggest focused specialization paths")
        elif len(unique_topics) <= 2:
            context_parts.append("Narrow topic focus - suggest broader context and related fields")

        # Consider user's expertise level
        if user_profile:
            reading_count = len(user_profile.reading_history)
            if reading_count > 100:
                context_parts.append(
                    "Experienced reader - suggest advanced topics and emerging trends"
                )
            else:
                context_parts.append(
                    "Building expertise - suggest foundational resources and practical guides"
                )

        return "; ".join(context_parts)

    def _generate_topic_expansion_suggestions(
        self, article_topics: List[str], user_profile: Optional[UserProfile] = None
    ) -> str:
        """
        Generate suggestions for topic expansion based on current articles.

        Args:
            article_topics: Topics from current articles
            user_profile: Optional user profile

        Returns:
            Topic expansion suggestions string
        """
        suggestions = []

        # Map topics to related areas
        topic_expansions = {
            "machine learning": ["deep learning", "neural networks", "MLOps", "model deployment"],
            "security": [
                "cybersecurity",
                "encryption",
                "authentication",
                "vulnerability assessment",
            ],
            "cloud": ["containerization", "microservices", "serverless", "DevOps"],
            "database": ["data modeling", "query optimization", "NoSQL", "data warehousing"],
            "API": ["REST design", "GraphQL", "API security", "microservices architecture"],
            "performance": ["optimization", "profiling", "caching", "load balancing"],
            "python": ["frameworks", "async programming", "testing", "packaging"],
            "javascript": ["frameworks", "Node.js", "TypeScript", "web performance"],
        }

        # Find expansion opportunities
        for topic in set(article_topics):
            topic_lower = topic.lower()
            for key, expansions in topic_expansions.items():
                if key in topic_lower:
                    suggestions.extend(expansions[:2])  # Take first 2 expansions

        # Add user-specific expansions
        if user_profile:
            user_topics = set(user_profile.preferred_topics)
            current_topics = set(article_topics)

            # Suggest topics user likes but aren't in current results
            missing_interests = user_topics - current_topics
            if missing_interests:
                suggestions.extend(list(missing_interests)[:2])

        return (
            ", ".join(list(set(suggestions))[:5])
            if suggestions
            else "General technical advancement"
        )

    def _generate_personalized_recommendations(
        self, query: str, articles: List[ArticleMatch], user_profile: UserProfile
    ) -> List[str]:
        """
        Generate personalized recommendations based on user profile.

        Args:
            query: Original query
            articles: Retrieved articles
            user_profile: User profile

        Returns:
            List of personalized recommendation strings
        """
        recommendations = []

        # Recommend based on reading history gaps
        user_topics = set(user_profile.preferred_topics)
        article_topics = set()
        for article in articles:
            if article.metadata and "topics" in article.metadata:
                article_topics.update(article.metadata["topics"])

        # Find complementary topics
        complementary_topics = user_topics - article_topics
        if complementary_topics:
            topic_list = list(complementary_topics)[:2]
            recommendations.append(
                f"Consider exploring {', '.join(topic_list)} to complement this knowledge."
            )

        # Recommend based on satisfaction patterns
        avg_satisfaction = user_profile.get_average_satisfaction()
        if avg_satisfaction > 0.7:
            recommendations.append(
                "Based on your preferences, look for in-depth technical analyses and case studies."
            )
        elif avg_satisfaction < 0.5:
            recommendations.append(
                "Focus on practical tutorials and step-by-step implementation guides."
            )

        # Recommend based on reading volume
        reading_count = len(user_profile.reading_history)
        if reading_count > 100:
            recommendations.append(
                "Explore cutting-edge research papers and emerging technology trends in this area."
            )

        return recommendations[:2]  # Limit to 2 personalized recommendations

    def _prioritize_recommendations_by_interest(
        self, recommendations: List[str], priority_topics: List[str]
    ) -> List[str]:
        """
        Prioritize recommendations based on user's interest topics.

        Args:
            recommendations: List of recommendation strings
            priority_topics: Topics that match user's interests

        Returns:
            Reordered recommendations with user interests prioritized
        """
        if not priority_topics:
            return recommendations

        # Score recommendations based on topic matches
        scored_recs = []
        for rec in recommendations:
            score = 0
            rec_lower = rec.lower()

            # Higher score for recommendations mentioning user's priority topics
            for topic in priority_topics:
                if topic.lower() in rec_lower:
                    score += 2

            # Bonus for actionable language
            if any(word in rec_lower for word in ["explore", "try", "implement", "learn", "study"]):
                score += 1

            scored_recs.append((score, rec))

        # Sort by score (descending) and return recommendations
        scored_recs.sort(key=lambda x: x[0], reverse=True)
        return [rec for score, rec in scored_recs]

    def _rank_articles_by_user_interest(
        self, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[ArticleMatch]:
        """
        Rank articles by combining similarity score with user interest preferences.

        Enhanced for Requirement 8.2: Prioritize articles from user's areas of interest

        Args:
            articles: List of articles to rank
            user_profile: Optional user profile for personalization

        Returns:
            List of articles ranked by combined relevance and user interest
        """
        if not user_profile:
            # Fallback to simple similarity ranking
            return sorted(articles, key=lambda x: x.similarity_score, reverse=True)

        # Calculate enhanced ranking scores
        scored_articles = []
        user_topics = set(topic.lower() for topic in user_profile.preferred_topics)

        for article in articles:
            # Start with base similarity score
            score = article.similarity_score

            # Boost score for user's preferred topics (Requirement 8.2)
            topic_boost = 0.0
            if article.metadata:
                article_topics = set()

                # Extract topics from metadata
                if "topics" in article.metadata:
                    article_topics.update(topic.lower() for topic in article.metadata["topics"])
                if "category" in article.metadata:
                    article_topics.add(article.metadata["category"].lower())

                # Calculate topic overlap boost
                topic_overlap = len(user_topics.intersection(article_topics))
                if topic_overlap > 0:
                    topic_boost = min(0.2, topic_overlap * 0.1)  # Max 0.2 boost

            # Boost for articles user hasn't read (encourage discovery)
            novelty_boost = 0.0
            if not user_profile.has_read_article(article.article_id):
                novelty_boost = 0.05

            # Boost for recent articles (if user prefers current content)
            recency_boost = 0.0
            if article.published_at:
                days_old = (datetime.utcnow() - article.published_at).days
                if days_old < 30:  # Articles from last 30 days
                    recency_boost = 0.03

            # Boost based on user satisfaction patterns
            satisfaction_boost = 0.0
            avg_satisfaction = user_profile.get_average_satisfaction()
            if avg_satisfaction > 0.7:
                # High satisfaction users prefer in-depth content
                if article.metadata and article.metadata.get("technical_level") == "advanced":
                    satisfaction_boost = 0.05
            elif avg_satisfaction < 0.5:
                # Lower satisfaction users prefer practical content
                if "tutorial" in article.title.lower() or "guide" in article.title.lower():
                    satisfaction_boost = 0.05

            # Calculate final score
            final_score = score + topic_boost + novelty_boost + recency_boost + satisfaction_boost
            scored_articles.append((final_score, article))

        # Sort by final score (descending) and return articles
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles]

    async def _generate_recommendations(
        self, query: str, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """
        Generate recommendations for related reading and next steps.

        Enhanced for Requirements 3.5, 8.2: Include "延伸閱讀" (extended reading) suggestions
        with related topic articles and prioritize user's areas of interest

        Args:
            query: Original user query
            articles: Retrieved articles
            user_profile: Optional user profile

        Returns:
            List of recommendation strings
        """
        try:
            # Determine language preference
            language = (
                "Chinese"
                if user_profile and user_profile.language_preference == "zh"
                else "English"
            )

            # Extract topics from articles with enhanced analysis
            article_topics = []
            article_categories = []
            technical_depth = []

            for article in articles:
                if article.metadata:
                    if "topics" in article.metadata:
                        article_topics.extend(article.metadata["topics"])
                    if "category" in article.metadata:
                        article_categories.append(article.metadata["category"])
                    if "technical_level" in article.metadata:
                        technical_depth.append(article.metadata["technical_level"])

            # Build user interest context for prioritization (Requirement 8.2)
            user_interest_context = ""
            priority_topics = []
            if user_profile:
                user_topics = user_profile.get_top_topics(5)
                if user_topics:
                    user_interest_context = f"User's primary interests: {', '.join(user_topics)}. "

                    # Find intersection with current topics for prioritization
                    current_topics = set(article_topics + article_categories)
                    priority_topics = list(set(user_topics).intersection(current_topics))

                    if priority_topics:
                        user_interest_context += (
                            f"High priority areas for this user: {', '.join(priority_topics)}. "
                        )

                # Analyze reading patterns for recommendations
                reading_patterns = self._analyze_reading_patterns(user_profile)
                user_interest_context += reading_patterns

            # Create extended reading context (Requirement 3.5)
            extended_reading_context = self._create_extended_reading_context(
                query, articles, article_topics, user_profile
            )

            # Generate topic expansion suggestions
            topic_expansion = self._generate_topic_expansion_suggestions(
                article_topics, user_profile
            )

            topics_context = (
                f"Current article topics: {', '.join(set(article_topics))}"
                if article_topics
                else ""
            )
            categories_context = (
                f"Categories covered: {', '.join(set(article_categories))}"
                if article_categories
                else ""
            )

            messages = [
                {
                    "role": "system",
                    "content": f"""You are a technical learning advisor specializing in personalized reading recommendations. Generate 2-3 specific "延伸閱讀" (extended reading) recommendations in {language} based on the user's query, retrieved articles, and personal interests.

                    Recommendations should:
                    1. Suggest specific related topics that build on current articles
                    2. Prioritize areas that match user's established interests
                    3. Recommend practical next steps or deeper exploration paths
                    4. Identify complementary knowledge areas that enhance understanding
                    5. Suggest both broader context and deeper technical details
                    6. Include actionable learning paths tailored to user's expertise level

                    {user_interest_context}

                    Extended reading opportunities: {extended_reading_context}
                    Topic expansion suggestions: {topic_expansion}""",
                },
                {
                    "role": "user",
                    "content": f"""User Query: {query}

                    {topics_context}
                    {categories_context}

                    Based on this query and the topics covered, provide 2-3 specific "延伸閱讀" recommendations that:
                    - Build naturally on the current articles
                    - Align with user's interests and reading patterns
                    - Offer both breadth (related topics) and depth (advanced concepts)
                    - Include specific areas or technologies to explore next
                    - Suggest practical applications or case studies to investigate""",
                },
            ]

            recommendations_text = await self._call_openai_api(
                messages, max_tokens=350
            )  # More tokens for detailed recommendations

            # Split recommendations by lines
            recommendations = [
                rec.strip().lstrip("•-*").strip()
                for rec in recommendations_text.split("\n")
                if rec.strip() and len(rec.strip()) > 15  # Require more substantial recommendations
            ]

            # Add personalized recommendations based on user profile
            if user_profile:
                personalized_recs = self._generate_personalized_recommendations(
                    query, articles, user_profile
                )
                recommendations.extend(personalized_recs)

            # Prioritize recommendations based on user interests (Requirement 8.2)
            if user_profile and priority_topics:
                recommendations = self._prioritize_recommendations_by_interest(
                    recommendations, priority_topics
                )

            return recommendations[:3]  # Limit to 3 best recommendations

        except Exception as e:
            logger.warning(f"Failed to generate enhanced recommendations: {str(e)}")
            return self._create_fallback_recommendations(query, articles)

    def _create_fallback_recommendations(
        self, query: str, articles: List[ArticleMatch]
    ) -> List[str]:
        """
        Create fallback recommendations when LLM generation fails.

        Args:
            query: Original user query
            articles: Retrieved articles

        Returns:
            List of basic recommendation strings
        """
        recommendations = []

        if articles:
            recommendations.append(
                "Consider reading the most relevant article first for deeper insights."
            )

            # Check for patterns in metadata
            categories = set()
            for article in articles:
                if article.metadata and "category" in article.metadata:
                    categories.add(article.metadata["category"])

            if categories:
                recommendations.append(
                    f"Explore more articles in these categories: {', '.join(categories)}"
                )

            recommendations.append(
                "Try refining your search with more specific keywords for targeted results."
            )

        return recommendations[:3]

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

    async def generate_summary(self, article: ArticleMatch) -> str:
        """
        Generate a standalone summary for a single article.

        Args:
            article: Article to summarize

        Returns:
            Generated summary text

        Raises:
            ResponseGeneratorError: If summary generation fails
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert at creating concise, informative article summaries.
                    Create a 2-3 sentence summary that captures the main points and key insights.
                    Focus on technical accuracy and practical value for readers.""",
                },
                {
                    "role": "user",
                    "content": f"""Article Title: {article.title}

                    Article Content: {article.content_preview}

                    Please provide a 2-3 sentence summary of this article.""",
                },
            ]

            return await self._call_openai_api(messages, max_tokens=200)

        except Exception as e:
            logger.error(f"Failed to generate summary for article {article.article_id}: {str(e)}")
            raise ResponseGeneratorError(f"Summary generation failed: {str(e)}", e)

    async def generate_insights(
        self, articles: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """
        Generate standalone insights from a list of articles.

        Args:
            articles: List of articles to analyze
            user_profile: Optional user profile for personalization

        Returns:
            List of insight strings

        Raises:
            ResponseGeneratorError: If insight generation fails
        """
        try:
            return await self._generate_insights("", articles, user_profile)
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
            raise ResponseGeneratorError(f"Insight generation failed: {str(e)}", e)


# Singleton instance for dependency injection
_response_generator_instance: Optional[ResponseGenerator] = None


def get_response_generator() -> ResponseGenerator:
    """
    Get or create a singleton ResponseGenerator instance.

    Returns:
        ResponseGenerator instance
    """
    global _response_generator_instance
    if _response_generator_instance is None:
        _response_generator_instance = ResponseGenerator()
    return _response_generator_instance
