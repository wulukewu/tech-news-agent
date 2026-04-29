"""Mixin extracted from app/qa_agent/response_generator.py."""
import logging
from typing import List, Optional

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    UserProfile,
)

logger = logging.getLogger(__name__)


class SummariesMixin:
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
