"""
Recommendation Service

This module provides the RecommendationService class for managing recommended feeds,
including querying recommended feeds, grouping by category, and updating recommendation status.

Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
"""

import logging
from uuid import UUID
from typing import List, Dict, Optional
from datetime import datetime, timezone

from supabase import Client

from app.schemas.recommendation import RecommendedFeed, RecommendedFeedsResponse, FeedsByCategoryResponse


logger = logging.getLogger(__name__)


class RecommendationServiceError(Exception):
    """Base exception for RecommendationService errors"""
    pass


class RecommendationService:
    """
    Service for managing recommended feeds and recommendations.
    
    This service handles:
    - Retrieving recommended feeds sorted by priority
    - Grouping feeds by category
    - Updating recommendation status for feeds
    
    Requirements: 2.1, 2.2, 4.1, 12.1, 12.4
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the RecommendationService.
        
        Args:
            supabase_client: Supabase client instance for database operations
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)
    
    async def get_recommended_feeds(self, user_id: Optional[UUID] = None) -> List[RecommendedFeed]:
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
            
            # Query feeds table for recommended feeds
            response = self.client.table('feeds') \
                .select('*') \
                .eq('is_recommended', True) \
                .order('recommendation_priority', desc=True) \
                .execute()
            
            if not response.data:
                self.logger.info("No recommended feeds found")
                return []
            
            # Get user subscriptions if user_id provided
            subscribed_feed_ids = set()
            if user_id:
                subscribed_feed_ids = await self._get_user_subscribed_feed_ids(user_id)
            
            # Convert to RecommendedFeed objects
            recommended_feeds = []
            for feed_data in response.data:
                feed = RecommendedFeed(
                    id=UUID(feed_data['id']),
                    name=feed_data['name'],
                    url=feed_data['url'],
                    category=feed_data.get('category', 'Uncategorized'),
                    description=feed_data.get('description'),
                    is_recommended=feed_data.get('is_recommended', False),
                    recommendation_priority=feed_data.get('recommendation_priority', 0),
                    is_subscribed=UUID(feed_data['id']) in subscribed_feed_ids
                )
                recommended_feeds.append(feed)
            
            self.logger.info(f"Retrieved {len(recommended_feeds)} recommended feeds")
            return recommended_feeds
            
        except Exception as e:
            self.logger.error(f"Failed to get recommended feeds: {e}")
            raise RecommendationServiceError(f"Failed to get recommended feeds: {str(e)}")
    
    async def get_feeds_by_category(
        self,
        category: str,
        user_id: Optional[UUID] = None
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
            
            # Query feeds table for this category
            response = self.client.table('feeds') \
                .select('*') \
                .eq('category', category) \
                .order('is_recommended', desc=True) \
                .order('recommendation_priority', desc=True) \
                .execute()
            
            if not response.data:
                self.logger.info(f"No feeds found for category: {category}")
                return FeedsByCategoryResponse(
                    category=category,
                    feeds=[],
                    feed_count=0
                )
            
            # Get user subscriptions if user_id provided
            subscribed_feed_ids = set()
            if user_id:
                subscribed_feed_ids = await self._get_user_subscribed_feed_ids(user_id)
            
            # Convert to RecommendedFeed objects
            feeds = []
            for feed_data in response.data:
                feed = RecommendedFeed(
                    id=UUID(feed_data['id']),
                    name=feed_data['name'],
                    url=feed_data['url'],
                    category=feed_data.get('category', 'Uncategorized'),
                    description=feed_data.get('description'),
                    is_recommended=feed_data.get('is_recommended', False),
                    recommendation_priority=feed_data.get('recommendation_priority', 0),
                    is_subscribed=UUID(feed_data['id']) in subscribed_feed_ids
                )
                feeds.append(feed)
            
            self.logger.info(f"Retrieved {len(feeds)} feeds for category: {category}")
            
            return FeedsByCategoryResponse(
                category=category,
                feeds=feeds,
                feed_count=len(feeds)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get feeds for category {category}: {e}")
            raise RecommendationServiceError(f"Failed to get feeds by category: {str(e)}")
    
    async def update_recommendation_status(
        self,
        feed_id: UUID,
        is_recommended: bool,
        priority: int
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
                f"Updating recommendation status for feed {feed_id}: "
                f"is_recommended={is_recommended}, priority={priority}"
            )
            
            # Validate priority range
            if priority < 0:
                raise RecommendationServiceError("Priority must be non-negative")
            
            # Update the feed record
            update_data = {
                'is_recommended': is_recommended,
                'recommendation_priority': priority,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('feeds') \
                .update(update_data) \
                .eq('id', str(feed_id)) \
                .execute()
            
            if not response.data:
                raise RecommendationServiceError(f"Feed not found: {feed_id}")
            
            self.logger.info(f"Successfully updated recommendation status for feed {feed_id}")
            
        except RecommendationServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update recommendation status for feed {feed_id}: {e}")
            raise RecommendationServiceError(f"Failed to update recommendation status: {str(e)}")
    
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
            response = self.client.table('user_subscriptions') \
                .select('feed_id') \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not response.data:
                return set()
            
            return {UUID(sub['feed_id']) for sub in response.data}
            
        except Exception as e:
            self.logger.warning(f"Failed to get user subscriptions for {user_id}: {e}")
            return set()
