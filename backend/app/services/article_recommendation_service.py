"""
Article Recommendation Service

This module provides the ArticleRecommendationService class for generating
personalized article recommendations based on user ratings and preferences.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
"""

import hashlib
import random
from datetime import datetime, timedelta
from uuid import UUID

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.repositories.article import ArticleRepository
from app.repositories.reading_list import ReadingListRepository
from app.schemas.recommendation import (
    ArticleRecommendation,
    ArticleRecommendationsResponse,
    DismissRecommendationRequest,
    RecommendationInteraction,
    RefreshRecommendationsRequest,
)
from app.services.base import BaseService

logger = get_logger(__name__)


class ArticleRecommendationService(BaseService):
    """
    Service for generating personalized article recommendations.

    This service analyzes user rating patterns to recommend articles
    that match their preferences and interests.

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
    """

    MIN_RATINGS_REQUIRED = 3  # Minimum ratings needed for recommendations
    MAX_RECOMMENDATIONS = 50  # Maximum recommendations to generate
    CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence score for recommendations

    def __init__(
        self,
        article_repo: ArticleRepository,
        reading_list_repo: ReadingListRepository,
    ):
        """
        Initialize the ArticleRecommendationService.

        Args:
            article_repo: Repository for article data access
            reading_list_repo: Repository for reading list data access
        """
        super().__init__()
        self.article_repo = article_repo
        self.reading_list_repo = reading_list_repo
        self.logger = get_logger(f"{__name__}.ArticleRecommendationService")
        self._dismissed_recommendations = set()  # In-memory store for dismissed recommendations

    async def get_recommendations(
        self, user_id: UUID, limit: int = 10
    ) -> ArticleRecommendationsResponse:
        """
        Get personalized article recommendations for a user.

        Validates: Requirements 3.1, 3.2, 3.6
        """
        try:
            self.logger.info("Getting recommendations for user", user_id=str(user_id))

            # Get user's rating count
            user_rating_count = await self._get_user_rating_count(user_id)

            # Check if user has sufficient data
            if user_rating_count < self.MIN_RATINGS_REQUIRED:
                self.logger.info(
                    "Insufficient rating data for recommendations",
                    user_id=str(user_id),
                    rating_count=user_rating_count,
                    min_required=self.MIN_RATINGS_REQUIRED,
                )
                return ArticleRecommendationsResponse(
                    recommendations=[],
                    total_count=0,
                    has_sufficient_data=False,
                    min_ratings_required=self.MIN_RATINGS_REQUIRED,
                    user_rating_count=user_rating_count,
                )

            # Generate recommendations
            recommendations = await self._generate_recommendations(user_id, limit)

            self.logger.info(
                "Generated recommendations",
                user_id=str(user_id),
                count=len(recommendations),
            )

            return ArticleRecommendationsResponse(
                recommendations=recommendations,
                total_count=len(recommendations),
                has_sufficient_data=True,
                min_ratings_required=self.MIN_RATINGS_REQUIRED,
                user_rating_count=user_rating_count,
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get recommendations",
                error_code=ErrorCode.SERVICE_ERROR,
                context={"user_id": str(user_id), "limit": limit},
            )

    async def refresh_recommendations(
        self, user_id: UUID, request: RefreshRecommendationsRequest
    ) -> ArticleRecommendationsResponse:
        """
        Refresh recommendations to generate new suggestions.

        Validates: Requirement 3.5
        """
        try:
            self.logger.info("Refreshing recommendations", user_id=str(user_id))

            # Clear dismissed recommendations for this user
            self._dismissed_recommendations.clear()

            # Generate new recommendations
            return await self.get_recommendations(user_id, request.limit or 10)

        except Exception as e:
            self._handle_error(
                e,
                "Failed to refresh recommendations",
                error_code=ErrorCode.SERVICE_ERROR,
                context={"user_id": str(user_id)},
            )

    async def dismiss_recommendation(
        self, user_id: UUID, request: DismissRecommendationRequest
    ) -> None:
        """
        Dismiss a recommendation.

        Validates: Requirement 3.7
        """
        try:
            self.logger.info(
                "Dismissing recommendation",
                user_id=str(user_id),
                recommendation_id=request.recommendation_id,
            )

            # Add to dismissed set (in production, this would be stored in database)
            self._dismissed_recommendations.add(request.recommendation_id)

        except Exception as e:
            self._handle_error(
                e,
                "Failed to dismiss recommendation",
                error_code=ErrorCode.SERVICE_ERROR,
                context={"user_id": str(user_id), "recommendation_id": request.recommendation_id},
            )

    async def track_interaction(
        self, user_id: UUID, interaction: RecommendationInteraction
    ) -> None:
        """
        Track recommendation interaction for analytics.

        Validates: Requirement 3.8
        """
        try:
            self.logger.info(
                "Tracking recommendation interaction",
                user_id=str(user_id),
                recommendation_id=interaction.recommendation_id,
                interaction_type=interaction.interaction_type,
            )

            # In production, this would store interaction data in analytics database
            # For now, just log the interaction

        except Exception as e:
            self.logger.warning(
                "Failed to track recommendation interaction",
                user_id=str(user_id),
                recommendation_id=interaction.recommendation_id,
                error=str(e),
            )
            # Don't raise error for analytics tracking failures

    # Private helper methods

    async def _get_user_rating_count(self, user_id: UUID) -> int:
        """Get the number of articles the user has rated."""
        try:
            # Count reading list items with ratings
            items, _ = await self.reading_list_repo.list_by_user_with_pagination(
                user_id=user_id,
                page=1,
                page_size=1000,  # Get all items to count ratings
            )

            rating_count = sum(1 for item in items if item.rating is not None and item.rating >= 4)
            return rating_count

        except Exception as e:
            self.logger.warning(
                "Failed to get user rating count",
                user_id=str(user_id),
                error=str(e),
            )
            return 0

    async def _generate_recommendations(
        self, user_id: UUID, limit: int
    ) -> list[ArticleRecommendation]:
        """Generate personalized recommendations based on user preferences."""
        try:
            # Get user's highly rated articles (4+ stars)
            rated_items, _ = await self.reading_list_repo.list_by_user_with_pagination(
                user_id=user_id,
                page=1,
                page_size=1000,
            )

            # Filter for highly rated articles
            highly_rated_items = [
                item for item in rated_items if item.rating is not None and item.rating >= 4
            ]

            if not highly_rated_items:
                return []

            # Get user's preferred categories and tinkering levels
            user_preferences = await self._analyze_user_preferences(highly_rated_items)

            # Get candidate articles (not in reading list)
            candidate_articles = await self._get_candidate_articles(user_id, limit * 3)

            # Score and rank articles
            recommendations = []
            for article in candidate_articles:
                score = self._calculate_recommendation_score(article, user_preferences)

                if score >= self.CONFIDENCE_THRESHOLD:
                    recommendation_id = self._generate_recommendation_id(user_id, article.id)

                    # Skip if dismissed
                    if recommendation_id in self._dismissed_recommendations:
                        continue

                    reason = self._generate_recommendation_reason(article, user_preferences)

                    recommendation = ArticleRecommendation(
                        id=recommendation_id,
                        article_id=article.id,
                        title=article.title,
                        url=article.url,
                        feed_name=article.feed_name,
                        category=article.category,
                        published_at=article.published_at,
                        tinkering_index=article.tinkering_index or 3,
                        ai_summary=article.ai_summary,
                        reason=reason,
                        confidence=score,
                        generated_at=datetime.utcnow(),
                        dismissed=False,
                    )

                    recommendations.append(recommendation)

            # Sort by confidence score (descending) and limit results
            recommendations.sort(key=lambda x: x.confidence, reverse=True)
            return recommendations[:limit]

        except Exception as e:
            self.logger.error(
                "Failed to generate recommendations",
                user_id=str(user_id),
                error=str(e),
            )
            return []

    async def _analyze_user_preferences(self, rated_items) -> dict:
        """Analyze user preferences from their highly rated articles."""
        categories = {}
        tinkering_levels = []

        for item in rated_items:
            # Get article details (in production, this would be a join query)
            try:
                article = await self.article_repo.get_by_id(item.article_id)
                if article:
                    # Count category preferences
                    categories[article.category] = categories.get(article.category, 0) + 1

                    # Track tinkering level preferences
                    if article.tinkering_index:
                        tinkering_levels.append(article.tinkering_index)
            except Exception:
                continue

        # Calculate preferred categories (top 3)
        preferred_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]

        # Calculate average preferred tinkering level
        avg_tinkering = sum(tinkering_levels) / len(tinkering_levels) if tinkering_levels else 3

        return {
            "preferred_categories": [cat for cat, _ in preferred_categories],
            "avg_tinkering_level": avg_tinkering,
            "category_weights": dict(preferred_categories),
        }

    async def _get_candidate_articles(self, user_id: UUID, limit: int):
        """Get articles that are candidates for recommendation."""
        try:
            # Get user's reading list article IDs to exclude
            user_items, _ = await self.reading_list_repo.list_by_user_with_pagination(
                user_id=user_id,
                page=1,
                page_size=1000,
            )

            excluded_article_ids = {item.article_id for item in user_items}

            # Get recent articles (last 30 days) that user hasn't read
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            # In production, this would be a more sophisticated query
            # For now, get recent articles and filter out user's articles
            articles, _ = await self.article_repo.list_with_pagination(
                page=1,
                page_size=limit,
                order_by="published_at",
                ascending=False,
            )

            # Filter out articles in user's reading list
            candidate_articles = [
                article
                for article in articles
                if article.id not in excluded_article_ids
                and article.published_at
                and article.published_at >= cutoff_date
                and article.tinkering_index is not None
            ]

            return candidate_articles

        except Exception as e:
            self.logger.error(
                "Failed to get candidate articles",
                user_id=str(user_id),
                error=str(e),
            )
            return []

    def _calculate_recommendation_score(self, article, user_preferences) -> float:
        """Calculate recommendation score for an article."""
        score = 0.0

        # Category match bonus
        if article.category in user_preferences["preferred_categories"]:
            category_weight = user_preferences["category_weights"].get(article.category, 0)
            score += 0.4 * min(category_weight / 5.0, 1.0)  # Max 0.4 for category match

        # Tinkering level similarity
        if article.tinkering_index:
            tinkering_diff = abs(article.tinkering_index - user_preferences["avg_tinkering_level"])
            tinkering_score = max(0, 1.0 - (tinkering_diff / 4.0))  # Normalize to 0-1
            score += 0.3 * tinkering_score  # Max 0.3 for tinkering match

        # Recency bonus (newer articles get higher scores)
        if article.published_at:
            days_old = (datetime.utcnow() - article.published_at).days
            recency_score = max(0, 1.0 - (days_old / 30.0))  # Decay over 30 days
            score += 0.2 * recency_score  # Max 0.2 for recency

        # Quality bonus (articles with AI summaries are preferred)
        if article.ai_summary:
            score += 0.1

        # Add some randomness to avoid always showing the same articles
        score += random.uniform(0, 0.1)

        return min(score, 1.0)  # Cap at 1.0

    def _generate_recommendation_reason(self, article, user_preferences) -> str:
        """Generate a human-readable reason for the recommendation."""
        reasons = []

        # Category-based reason
        if article.category in user_preferences["preferred_categories"]:
            reasons.append(f"您經常閱讀 {article.category} 類別的文章")

        # Tinkering level reason
        if article.tinkering_index:
            if abs(article.tinkering_index - user_preferences["avg_tinkering_level"]) <= 1:
                reasons.append(f"技術深度 ({article.tinkering_index}/5) 符合您的偏好")

        # Quality reason
        if article.ai_summary:
            reasons.append("這篇文章有詳細的 AI 摘要")

        # Default reason
        if not reasons:
            reasons.append("根據您的閱讀偏好推薦")

        return "，".join(reasons[:2])  # Limit to 2 reasons

    def _generate_recommendation_id(self, user_id: UUID, article_id: UUID) -> str:
        """Generate a unique recommendation ID."""
        # Create a deterministic ID based on user and article
        content = f"{user_id}:{article_id}:{datetime.utcnow().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
