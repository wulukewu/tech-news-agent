"""
Recommendation Service

This module provides the RecommendationService class for managing recommended feeds,
including querying recommended feeds, grouping by category, and updating recommendation status.

This service follows the repository pattern and depends on repository interfaces
for data access instead of directly accessing the database client.

Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
Validates: Requirements 3.1, 3.2, 3.3
"""

from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger
from app.repositories.feed import FeedRepository
from app.repositories.user_subscription import UserSubscriptionRepository
from app.schemas.recommendation import (
    FeedsByCategoryResponse,
    RecommendedFeed,
)
from app.services.base import BaseService

logger = get_logger(__name__)


class RecommendationService(BaseService):
    """
    Service for managing recommended feeds and recommendations.

    This service handles:
    - Retrieving recommended feeds sorted by priority
    - Grouping feeds by category
    - Updating recommendation status for feeds

    This service uses the repository pattern for data access, depending on
    FeedRepository and UserSubscriptionRepository instead of directly accessing the database.

    Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
    Validates: Requirements 3.1, 3.2, 3.3
    """

    def __init__(
        self, feed_repo: FeedRepository, user_subscription_repo: UserSubscriptionRepository
    ):
        """
        Initialize the RecommendationService.

        Args:
            feed_repo: Repository for feed data access
            user_subscription_repo: Repository for user subscription data access
        """
        super().__init__()
        self.feed_repo = feed_repo
        self.user_subscription_repo = user_subscription_repo
        self.logger = get_logger(f"{__name__}.RecommendationService")

    async def get_recommended_feeds(self, user_id: UUID | None = None) -> list[RecommendedFeed]:
        """
        Get all recommended feeds sorted by recommendation_priority.

        Queries feeds table WHERE is_recommended = true and orders by
        recommendation_priority DESC (higher priority first).

        If user_id is provided, includes subscription status for that user.

        Args:
            user_id: Optional UUID of the user to check subscription status

        Returns:
            List of RecommendedFeed objects sorted by priority (highest first)

        Raises:
            RecommendationServiceError: If database operation fails

        Requirements: 2.1, 12.1, 12.4
        """
        try:
            self.logger.info("Getting recommended feeds")

            # Query feeds using repository
            feeds = await self.feed_repo.list_recommended_feeds()

            if not feeds:
                self.logger.info("No recommended feeds found")
                return []

            # Get user subscriptions if user_id provided
            subscribed_feed_ids = set()
            if user_id:
                subscribed_feed_ids = await self._get_user_subscribed_feed_ids(user_id)

            # Convert to RecommendedFeed objects
            recommended_feeds = []
            for feed in feeds:
                recommended_feed = RecommendedFeed(
                    id=feed.id,
                    name=feed.name,
                    url=feed.url,
                    category=feed.category,
                    description=feed.description,
                    is_recommended=feed.is_recommended,
                    recommendation_priority=feed.recommendation_priority,
                    is_subscribed=feed.id in subscribed_feed_ids,
                )
                recommended_feeds.append(recommended_feed)

            self.logger.info("Retrieved recommended feeds", feed_count=len(recommended_feeds))
            return recommended_feeds

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get recommended feeds",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id) if user_id else None},
            )

    async def get_feeds_by_category(
        self, category: str, user_id: UUID | None = None
    ) -> FeedsByCategoryResponse:
        """
        Get all feeds in a specific category, sorted by recommendation_priority.

        Returns both recommended and non-recommended feeds in the category,
        with recommended feeds appearing first (sorted by priority).

        Args:
            category: Category name to filter by
            user_id: Optional UUID of the user to check subscription status

        Returns:
            FeedsByCategoryResponse with feeds sorted by priority

        Raises:
            RecommendationServiceError: If database operation fails

        Requirements: 2.1, 4.1, 12.4
        """
        try:
            self.logger.info(f"Getting feeds for category: {category}")

            # Query feeds by category using repository
            feeds = await self.feed_repo.list_by_category(category, include_inactive=False)

            if not feeds:
                self.logger.info(f"No feeds found for category: {category}")
                return FeedsByCategoryResponse(category=category, feeds=[], feed_count=0)

            # Sort feeds: recommended first (by priority), then non-recommended
            feeds.sort(key=lambda f: (not f.is_recommended, -f.recommendation_priority))

            # Get user subscriptions if user_id provided
            subscribed_feed_ids = set()
            if user_id:
                subscribed_feed_ids = await self._get_user_subscribed_feed_ids(user_id)

            # Convert to RecommendedFeed objects
            recommended_feeds = []
            for feed in feeds:
                recommended_feed = RecommendedFeed(
                    id=feed.id,
                    name=feed.name,
                    url=feed.url,
                    category=feed.category,
                    description=feed.description,
                    is_recommended=feed.is_recommended,
                    recommendation_priority=feed.recommendation_priority,
                    is_subscribed=feed.id in subscribed_feed_ids,
                )
                recommended_feeds.append(recommended_feed)

            self.logger.info(
                "Retrieved feeds for category", category=category, feed_count=len(recommended_feeds)
            )

            return FeedsByCategoryResponse(
                category=category, feeds=recommended_feeds, feed_count=len(recommended_feeds)
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get feeds by category",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"category": category, "user_id": str(user_id) if user_id else None},
            )

    async def update_recommendation_status(
        self, feed_id: UUID, is_recommended: bool, priority: int
    ) -> None:
        """
        Update the recommendation status and priority for a feed.

        Sets is_recommended flag and recommendation_priority for the specified feed.
        Also updates the updated_at timestamp.

        Args:
            feed_id: UUID of the feed to update
            is_recommended: Whether the feed should be recommended
            priority: Recommendation priority (0-1000, higher = more important)

        Raises:
            RecommendationServiceError: If database operation fails or feed not found

        Requirements: 12.1, 12.4
        """
        try:
            self.logger.info(
                "Updating recommendation status",
                feed_id=str(feed_id),
                is_recommended=is_recommended,
                priority=priority,
            )

            # Validate priority range
            if priority < 0:
                raise ValidationError(
                    "Priority must be non-negative",
                    error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                    details={"priority": priority},
                )

            # Update using repository
            await self.feed_repo.update_recommendation_status(feed_id, is_recommended, priority)

            self.logger.info("Successfully updated recommendation status", feed_id=str(feed_id))

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to update recommendation status",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={
                    "feed_id": str(feed_id),
                    "is_recommended": is_recommended,
                    "priority": priority,
                },
            )

    # Private helper methods

    async def _get_user_subscribed_feed_ids(self, user_id: UUID) -> set:
        """
        Get set of feed IDs that the user is subscribed to.

        Args:
            user_id: UUID of the user

        Returns:
            Set of feed UUIDs
        """
        try:
            feed_ids = await self.user_subscription_repo.list_feed_ids_by_user(user_id)
            return set(feed_ids)

        except Exception as e:
            self.logger.warning(
                "Failed to get user subscriptions", user_id=str(user_id), error=str(e)
            )
            return set()
