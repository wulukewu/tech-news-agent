"""Mixin extracted from retrieval_engine.py."""
import logging
from typing import List, Optional
from uuid import UUID

from app.qa_agent.models import ArticleMatch, UserProfile

logger = logging.getLogger(__name__)


class ReExpandMixin:
    async def _expand_by_related_topics(
        self, original_results: List[ArticleMatch], user_uuid: UUID, existing_ids: set, limit: int
    ) -> List[ArticleMatch]:
        """Expand search by finding articles in related topics/categories."""
        if not original_results or limit <= 0:
            return []

        # Extract categories from original results
        categories = {match.category for match in original_results if match.category}
        if not categories:
            return []

        try:
            # This would ideally use a more sophisticated topic similarity search
            # For now, we'll use a simple category-based expansion
            related_matches = []

            # Search for articles in the same categories with lower threshold
            for category in categories:
                if len(related_matches) >= limit:
                    break

                # This is a simplified implementation - in a real system,
                # you'd want to search by category metadata or use topic modeling
                category_results = await self._vector_store.search_similar(
                    query_vector=[0.0] * 1536,  # Placeholder - would use category embeddings
                    user_id=user_uuid,
                    limit=limit - len(related_matches),
                    threshold=0.1,  # Very low threshold for category expansion
                )

                for vm in category_results:
                    if (
                        vm.article_id not in existing_ids
                        and vm.metadata
                        and vm.metadata.get("category") == category
                    ):
                        match = self._vector_match_to_article_match(vm)
                        if match is not None:
                            related_matches.append(match)
                            if len(related_matches) >= limit:
                                break

            logger.debug(f"Found {len(related_matches)} related topic results")
            return related_matches

        except Exception as exc:
            logger.error(f"Error in related topic expansion: {exc}")
            return []

    async def _expand_by_keywords(
        self, query_text: str, user_uuid: UUID, existing_ids: set, limit: int
    ) -> List[ArticleMatch]:
        """Expand search using keyword-based fallback when semantic search fails."""
        if not query_text or limit <= 0:
            return []

        try:
            keywords = self._extract_keywords(query_text)
            if not keywords:
                return []

            # This is a simplified keyword search - in a real system,
            # you'd want to implement full-text search in the database
            keyword_results = []

            # Search with very low threshold to get more results for keyword filtering
            broad_results = await self._vector_store.search_similar(
                query_vector=[0.0] * 1536,  # Placeholder vector
                user_id=user_uuid,
                limit=limit * 3,  # Get more to filter by keywords
                threshold=0.05,  # Very low threshold
            )

            for vm in broad_results:
                if vm.article_id in existing_ids:
                    continue

                # Check if any keywords match in title or content
                searchable_text = (
                    vm.metadata.get("title", "") + " " + (vm.chunk_text or "")
                ).lower()

                keyword_matches = sum(1 for kw in keywords if kw in searchable_text)
                if keyword_matches > 0:
                    match = self._vector_match_to_article_match(vm)
                    if match is not None:
                        # Adjust score based on keyword matches
                        keyword_score = keyword_matches / len(keywords)
                        object.__setattr__(
                            match, "combined_score", keyword_score * 0.5
                        )  # Lower score for fallback
                        keyword_results.append(match)

                        if len(keyword_results) >= limit:
                            break

            # Sort by keyword relevance
            keyword_results.sort(key=lambda m: m.combined_score, reverse=True)
            logger.debug(f"Found {len(keyword_results)} keyword-based results")
            return keyword_results[:limit]

        except Exception as exc:
            logger.error(f"Error in keyword expansion: {exc}")
            return []

    async def suggest_related_topics(
        self, original_results: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """
        Suggest related topics when search expansion cannot find enough results.

        Args:
            original_results: Original search results to analyze
            user_profile: Optional user profile for personalized suggestions

        Returns:
            List of suggested topic strings

        Validates: Requirements 2.5
        """
        if not original_results:
            # Default suggestions based on user profile or general topics
            if user_profile and user_profile.preferred_topics:
                return user_profile.preferred_topics[:5]
            return ["programming", "ai", "web-development", "data-science", "technology"]

        # Extract topics from original results
        categories = [match.category for match in original_results if match.category]

        # Simple topic suggestion based on categories
        # In a real system, this would use topic modeling or knowledge graphs
        topic_suggestions = []

        for category in set(categories):
            # Add related topics based on category
            if "programming" in category.lower():
                topic_suggestions.extend(["algorithms", "software-engineering", "code-review"])
            elif "ai" in category.lower():
                topic_suggestions.extend(["machine-learning", "deep-learning", "neural-networks"])
            elif "web" in category.lower():
                topic_suggestions.extend(["frontend", "backend", "full-stack"])
            elif "data" in category.lower():
                topic_suggestions.extend(["analytics", "visualization", "statistics"])

        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(topic_suggestions))[:10]

        logger.debug(f"Generated {len(unique_suggestions)} topic suggestions")
        return unique_suggestions
