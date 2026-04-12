"""
Subscription Service

This module provides the SubscriptionService class for managing user subscriptions,
including batch subscription operations with partial failure handling.

This service follows the repository pattern and depends on repository interfaces
for data access instead of directly accessing the database client.

Requirements: 2.6, 2.7
Validates: Requirements 3.1, 3.2, 3.3
"""

from uuid import UUID

from app.core.logger import get_logger
from app.repositories.feed import FeedRepository
from app.repositories.user_subscription import UserSubscriptionRepository
from app.schemas.feed import BatchSubscribeResponse
from app.services.base import BaseService

logger = get_logger(__name__)


class SubscriptionService(BaseService):
    """
    Service for managing user subscriptions to RSS feeds.

    This service handles:
    - Batch subscription to multiple feeds
    - Partial failure handling
    - Subscription count tracking

    This service uses the repository pattern for data access, depending on
    FeedRepository and UserSubscriptionRepository instead of directly accessing the database.

    Requirements: 2.6, 2.7
    Validates: Requirements 3.1, 3.2, 3.3
    """

    def __init__(
        self, feed_repo: FeedRepository, user_subscription_repo: UserSubscriptionRepository
    ):
        """
        Initialize the SubscriptionService.

        Args:
            feed_repo: Repository for feed data access
            user_subscription_repo: Repository for user subscription data access
        """
        super().__init__()
        self.feed_repo = feed_repo
        self.user_subscription_repo = user_subscription_repo
        self.logger = get_logger(f"{__name__}.SubscriptionService")

    async def batch_subscribe(self, user_id: UUID, feed_ids: list[UUID]) -> BatchSubscribeResponse:
        """
        Subscribe user to multiple feeds at once with partial failure handling.

        This method attempts to subscribe the user to all provided feeds.
        If some subscriptions fail, it continues processing the remaining feeds
        and returns detailed success/failure counts.

        Args:
            user_id: UUID of the user
            feed_ids: List of feed UUIDs to subscribe to

        Returns:
            BatchSubscribeResponse with subscribed_count, failed_count, and errors list

        Raises:
            SupabaseServiceError: If database connection fails completely

        Requirements: 2.6, 2.7
        """
        self.logger.info(
            "Starting batch subscription", user_id=str(user_id), feed_count=len(feed_ids)
        )

        subscribed_count = 0
        failed_count = 0
        errors = []

        # Handle empty feed list
        if not feed_ids:
            self.logger.warning("Empty feed_ids list provided to batch_subscribe")
            return BatchSubscribeResponse(subscribed_count=0, failed_count=0, errors=[])

        # Process each feed individually to handle partial failures
        for feed_id in feed_ids:
            try:
                # Check if feed exists and is active using repository
                feed = await self.feed_repo.get_by_id(feed_id)

                if not feed or not feed.is_active:
                    failed_count += 1
                    error_msg = f"Feed {feed_id} not found or inactive"
                    errors.append(error_msg)
                    self.logger.warning(error_msg, feed_id=str(feed_id))
                    continue

                # Check if already subscribed using repository
                existing_sub = await self.user_subscription_repo.get_by_user_and_feed(
                    user_id, feed_id
                )

                if existing_sub:
                    # Already subscribed - count as success (idempotent)
                    subscribed_count += 1
                    self.logger.debug(
                        "User already subscribed to feed",
                        user_id=str(user_id),
                        feed_id=str(feed_id),
                    )
                    continue

                # Create subscription using repository
                await self.user_subscription_repo.create(
                    {"user_id": str(user_id), "feed_id": str(feed_id)}
                )

                subscribed_count += 1
                self.logger.debug(
                    "Successfully subscribed user to feed",
                    user_id=str(user_id),
                    feed_id=str(feed_id),
                )

            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to subscribe to feed {feed_id}: {e!s}"
                errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True, feed_id=str(feed_id))
                # Continue processing remaining feeds

        self.logger.info(
            "Batch subscription completed",
            subscribed_count=subscribed_count,
            failed_count=failed_count,
            total=len(feed_ids),
        )

        return BatchSubscribeResponse(
            subscribed_count=subscribed_count, failed_count=failed_count, errors=errors
        )
