"""Mixin extracted from app/qa_agent/response_generator.py."""
import logging
from typing import List, Optional
from uuid import UUID

from app.qa_agent.models import (
    ArticleMatch,
    UserProfile,
)

logger = logging.getLogger(__name__)


class ReadingHistoryMixin:
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
