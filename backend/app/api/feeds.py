"""
Feed and Subscription Management API Endpoints

This module provides API endpoints for managing RSS feed subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from uuid import UUID
import logging

from app.api.auth import get_current_user
from app.services.supabase_service import SupabaseService
from app.services.subscription_service import SubscriptionService
from app.schemas.feed import (
    FeedResponse,
    SubscriptionToggleRequest,
    SubscriptionToggleResponse,
    BatchSubscribeRequest,
    BatchSubscribeResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/feeds", response_model=List[FeedResponse])
async def list_feeds(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Query all available RSS feeds with user subscription status
    
    Returns a list of all active feeds, with each feed marked as subscribed
    or not subscribed based on the current user's subscriptions.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        List[FeedResponse]: List of feeds with subscription status
        
    Raises:
        HTTPException: 500 when database query fails
        
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
    """
    try:
        supabase = SupabaseService()
        
        # Query all active feeds
        feeds = await supabase.get_active_feeds()
        
        # Query user subscriptions
        discord_id = current_user["discord_id"]
        subscriptions = await supabase.get_user_subscriptions(discord_id)
        
        # Create a set of subscribed feed IDs for fast lookup
        subscribed_feed_ids = {sub.feed_id for sub in subscriptions}
        
        # Build response with subscription status
        feed_responses = []
        for feed in feeds:
            feed_response = FeedResponse(
                id=feed.id,
                name=feed.name,
                url=feed.url,
                category=feed.category,
                is_subscribed=feed.id in subscribed_feed_ids
            )
            feed_responses.append(feed_response)
        
        # Sort by category and name
        feed_responses.sort(key=lambda f: (f.category, f.name))
        
        logger.info(
            f"Listed {len(feed_responses)} feeds for user {current_user['user_id']}"
        )
        
        return feed_responses
        
    except Exception as e:
        logger.error(
            f"Failed to list feeds for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )


@router.post("/subscriptions/toggle", response_model=SubscriptionToggleResponse)
async def toggle_subscription(
    request: SubscriptionToggleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Toggle subscription status for a feed
    
    If the user is subscribed to the feed, unsubscribe them.
    If the user is not subscribed, subscribe them.
    
    Args:
        request: Request containing feed_id to toggle
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        SubscriptionToggleResponse: New subscription status
        
    Raises:
        HTTPException: 404 when feed_id does not exist
        HTTPException: 422 when request body is invalid (handled by Pydantic)
        HTTPException: 500 when database operation fails
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10
    """
    try:
        supabase = SupabaseService()
        discord_id = current_user["discord_id"]
        feed_id = request.feed_id
        
        # Verify feed exists
        feeds = await supabase.get_active_feeds()
        feed_exists = any(feed.id == feed_id for feed in feeds)
        
        if not feed_exists:
            logger.warning(
                f"User {current_user['user_id']} attempted to toggle non-existent feed {feed_id}"
            )
            raise HTTPException(
                status_code=404,
                detail="Feed not found"
            )
        
        # Check current subscription status
        subscriptions = await supabase.get_user_subscriptions(discord_id)
        is_currently_subscribed = any(sub.feed_id == feed_id for sub in subscriptions)
        
        # Toggle subscription
        if is_currently_subscribed:
            await supabase.unsubscribe_from_feed(discord_id, feed_id)
            new_status = False
            logger.info(
                f"User {current_user['user_id']} unsubscribed from feed {feed_id}"
            )
        else:
            await supabase.subscribe_to_feed(discord_id, feed_id)
            new_status = True
            logger.info(
                f"User {current_user['user_id']} subscribed to feed {feed_id}"
            )
        
        return SubscriptionToggleResponse(
            feed_id=feed_id,
            is_subscribed=new_status
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to toggle subscription for user {current_user['user_id']}, feed {request.feed_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )


@router.post("/subscriptions/batch", response_model=BatchSubscribeResponse)
async def batch_subscribe(
    request: BatchSubscribeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Subscribe to multiple feeds at once
    
    Subscribes the user to all provided feeds. Handles partial failures gracefully,
    continuing to process remaining feeds even if some fail. Returns detailed
    success and failure counts.
    
    Args:
        request: Request containing list of feed_ids to subscribe to
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        BatchSubscribeResponse: Counts of successful and failed subscriptions with error details
        
    Raises:
        HTTPException: 422 when request body is invalid (handled by Pydantic)
        HTTPException: 500 when database connection fails completely
        
    Requirements: 2.6, 2.7
    """
    try:
        supabase = SupabaseService()
        subscription_service = SubscriptionService(supabase.client)
        
        # Get user UUID
        user_uuid = await supabase.get_or_create_user(current_user["discord_id"])
        
        # Perform batch subscription
        result = await subscription_service.batch_subscribe(user_uuid, request.feed_ids)
        
        logger.info(
            f"Batch subscription for user {current_user['user_id']}: "
            f"{result.subscribed_count} succeeded, {result.failed_count} failed"
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed batch subscription for user {current_user['user_id']}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )
