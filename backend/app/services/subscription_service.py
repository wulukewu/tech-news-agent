"""
Subscription Service

This module provides the SubscriptionService class for managing user subscriptions,
including batch subscription operations with partial failure handling.

Requirements: 2.6, 2.7
"""

import logging
from uuid import UUID
from typing import List
from supabase import Client

from app.schemas.feed import BatchSubscribeResponse
from app.core.exceptions import SupabaseServiceError


logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing user subscriptions to RSS feeds.
    
    This service handles:
    - Batch subscription to multiple feeds
    - Partial failure handling
    - Subscription count tracking
    
    Requirements: 2.6, 2.7
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the SubscriptionService.
        
        Args:
            supabase_client: Supabase client instance for database operations
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)
    
    async def batch_subscribe(
        self,
        user_id: UUID,
        feed_ids: List[UUID]
    ) -> BatchSubscribeResponse:
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
            f"Starting batch subscription for user {user_id} to {len(feed_ids)} feeds"
        )
        
        subscribed_count = 0
        failed_count = 0
        errors = []
        
        # Handle empty feed list
        if not feed_ids:
            self.logger.warning("Empty feed_ids list provided to batch_subscribe")
            return BatchSubscribeResponse(
                subscribed_count=0,
                failed_count=0,
                errors=[]
            )
        
        # Process each feed individually to handle partial failures
        for feed_id in feed_ids:
            try:
                # Check if feed exists
                feed_response = self.client.table('feeds') \
                    .select('id') \
                    .eq('id', str(feed_id)) \
                    .eq('is_active', True) \
                    .execute()
                
                if not feed_response.data:
                    failed_count += 1
                    error_msg = f"Feed {feed_id} not found or inactive"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
                    continue
                
                # Check if already subscribed
                existing_sub = self.client.table('user_subscriptions') \
                    .select('id') \
                    .eq('user_id', str(user_id)) \
                    .eq('feed_id', str(feed_id)) \
                    .execute()
                
                if existing_sub.data:
                    # Already subscribed - count as success (idempotent)
                    subscribed_count += 1
                    self.logger.debug(
                        f"User {user_id} already subscribed to feed {feed_id}"
                    )
                    continue
                
                # Insert subscription
                self.client.table('user_subscriptions').insert({
                    'user_id': str(user_id),
                    'feed_id': str(feed_id)
                }).execute()
                
                subscribed_count += 1
                self.logger.debug(
                    f"Successfully subscribed user {user_id} to feed {feed_id}"
                )
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to subscribe to feed {feed_id}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)
                # Continue processing remaining feeds
        
        self.logger.info(
            f"Batch subscription completed: {subscribed_count} succeeded, "
            f"{failed_count} failed out of {len(feed_ids)} total"
        )
        
        return BatchSubscribeResponse(
            subscribed_count=subscribed_count,
            failed_count=failed_count,
            errors=errors
        )
