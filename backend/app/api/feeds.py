"""
Feed and Subscription Management API Endpoints

This module provides API endpoints for managing RSS feed subscriptions.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

import feedparser
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.schemas.feed import (
    BatchSubscribeRequest,
    BatchSubscribeResponse,
    FeedResponse,
    SubscriptionToggleRequest,
    SubscriptionToggleResponse,
)
from app.schemas.responses import SuccessResponse, success_response
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _check_feed_health(client: httpx.AsyncClient, url: str) -> str:
    """Return 'healthy' or 'error' for a feed URL."""
    try:
        r = await client.head(url, timeout=5, follow_redirects=True)
        return "healthy" if r.status_code < 400 else "error"
    except Exception:
        return "error"


class AddCustomFeedRequest(BaseModel):
    url: str
    name: str | None = None
    category: str | None = None


@router.get("/feeds", response_model=SuccessResponse[list[FeedResponse]])
async def list_feeds(current_user: dict[str, Any] = Depends(get_current_user)):
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

        # Query all active feeds (system + this user's custom feeds)
        user_uuid = current_user["user_id"]
        from uuid import UUID as _UUID

        if not isinstance(user_uuid, _UUID):
            user_uuid = _UUID(str(user_uuid))
        feeds = await supabase.get_active_feeds(user_id=user_uuid)

        # Query user subscriptions
        discord_id = current_user["discord_id"]
        subscriptions = await supabase.get_user_subscriptions(discord_id)

        # Create a map of feed_id -> subscription info for fast lookup
        subscription_map = {sub.feed_id: sub for sub in subscriptions}
        subscribed_feed_ids = set(subscription_map.keys())

        # Batch query article stats per feed (one query, not N queries)
        from datetime import datetime, timedelta, timezone

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        stats_resp = (
            supabase.client.table("articles")
            .select("feed_id, tinkering_index, published_at")
            .execute()
        )
        feed_stats: dict = {}
        for row in stats_resp.data or []:
            fid = row.get("feed_id")
            if not fid:
                continue
            s = feed_stats.setdefault(fid, {"total": 0, "this_week": 0, "ti_sum": 0.0})
            s["total"] += 1
            if row.get("published_at") and row["published_at"] >= week_ago:
                s["this_week"] += 1
            s["ti_sum"] += row.get("tinkering_index") or 0

        # Build response with subscription status
        feed_responses = []
        for feed in feeds:
            sub = subscription_map.get(feed.id)
            s = feed_stats.get(str(feed.id), {"total": 0, "this_week": 0, "ti_sum": 0.0})
            avg_ti = round(s["ti_sum"] / s["total"], 1) if s["total"] > 0 else 0.0
            feed_response = FeedResponse(
                id=feed.id,
                name=feed.name,
                url=feed.url,
                category=feed.category,
                is_subscribed=feed.id in subscribed_feed_ids,
                is_custom=feed.created_by is not None,
                last_updated=feed.last_fetched_at.isoformat() if feed.last_fetched_at else None,
                notification_enabled=sub.notification_enabled if sub else True,
                total_articles=s["total"],
                articles_this_week=s["this_week"],
                average_tinkering_index=avg_ti,
            )
            feed_responses.append(feed_response)

        # Run health checks in parallel
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, verify=False) as client:
            health_results = await asyncio.gather(
                *[_check_feed_health(client, str(f.url)) for f in feed_responses]
            )
        for feed_response, status in zip(feed_responses, health_results):
            feed_response.health_status = status

        # Sort by category and name
        feed_responses.sort(key=lambda f: (f.category, f.name))

        logger.info(f"Listed {len(feed_responses)} feeds for user {current_user['user_id']}")

        return success_response(feed_responses)

    except Exception as e:
        logger.error(
            f"Failed to list feeds for user {current_user['user_id']}: {e!s}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.post("/subscriptions/toggle", response_model=SuccessResponse[SubscriptionToggleResponse])
async def toggle_subscription(
    request: SubscriptionToggleRequest, current_user: dict[str, Any] = Depends(get_current_user)
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
            raise HTTPException(status_code=404, detail="Feed not found")

        # Check current subscription status
        subscriptions = await supabase.get_user_subscriptions(discord_id)
        is_currently_subscribed = any(sub.feed_id == feed_id for sub in subscriptions)

        # Toggle subscription
        if is_currently_subscribed:
            await supabase.unsubscribe_from_feed(discord_id, feed_id)
            new_status = False
            logger.info(f"User {current_user['user_id']} unsubscribed from feed {feed_id}")
        else:
            await supabase.subscribe_to_feed(discord_id, feed_id)
            new_status = True
            logger.info(f"User {current_user['user_id']} subscribed to feed {feed_id}")

        return success_response(
            SubscriptionToggleResponse(feed_id=feed_id, is_subscribed=new_status)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to toggle subscription for user {current_user['user_id']}, feed {request.feed_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.post("/subscriptions/batch", response_model=SuccessResponse[BatchSubscribeResponse])
async def batch_subscribe(
    request: BatchSubscribeRequest, current_user: dict[str, Any] = Depends(get_current_user)
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
        user_uuid = current_user["user_id"]

        # Direct upsert — bypass SubscriptionService which requires deleted_at column
        subscribed_count = 0
        failed_count = 0
        errors: list[str] = []

        for feed_id in request.feed_ids:
            try:
                supabase.client.table("user_subscriptions").upsert(
                    {"user_id": str(user_uuid), "feed_id": str(feed_id)},
                    on_conflict="user_id,feed_id",
                ).execute()
                subscribed_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(str(e))

        from app.schemas.feed import BatchSubscribeResponse

        result = BatchSubscribeResponse(
            subscribed_count=subscribed_count,
            failed_count=failed_count,
            errors=errors,
        )

        logger.info(
            f"Batch subscription for user {current_user['user_id']}: "
            f"{result.subscribed_count} succeeded, {result.failed_count} failed"
        )

        return success_response(result)

    except Exception as e:
        logger.error(
            f"Failed batch subscription for user {current_user['user_id']}: {e!s}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.post(
    "/subscriptions/batch-unsubscribe", response_model=SuccessResponse[BatchSubscribeResponse]
)
async def batch_unsubscribe(
    request: BatchSubscribeRequest, current_user: dict[str, Any] = Depends(get_current_user)
):
    """Unsubscribe from multiple feeds at once"""
    try:
        supabase = SupabaseService()
        user_uuid = current_user["user_id"]

        unsubscribed_count = 0
        failed_count = 0
        errors: list[str] = []

        for feed_id in request.feed_ids:
            try:
                supabase.client.table("user_subscriptions").delete().eq(
                    "user_id", str(user_uuid)
                ).eq("feed_id", str(feed_id)).execute()
                unsubscribed_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(str(e))

        from app.schemas.feed import BatchSubscribeResponse

        result = BatchSubscribeResponse(
            subscribed_count=unsubscribed_count,
            failed_count=failed_count,
            errors=errors,
        )
        return success_response(result)

    except Exception as e:
        logger.error(f"Failed batch unsubscription: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.post("/feeds/preview")
async def preview_feed(
    request: AddCustomFeedRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Preview an RSS feed before adding it."""
    try:
        parsed = feedparser.parse(request.url)
        if parsed.bozo and not parsed.entries:
            raise HTTPException(status_code=400, detail="Invalid or unreachable RSS feed URL")

        feed_info = parsed.feed
        return success_response(
            {
                "title": feed_info.get("title", request.url),
                "description": feed_info.get("subtitle") or feed_info.get("description"),
                "url": request.url,
                "articleCount": len(parsed.entries),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview feed {request.url}: {e!s}")
        raise HTTPException(status_code=400, detail="Failed to fetch feed")


@router.post("/feeds/custom", response_model=SuccessResponse[FeedResponse])
async def add_custom_feed(
    request: AddCustomFeedRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Add a custom RSS feed and auto-subscribe the user."""
    try:
        supabase = SupabaseService()
        discord_id = current_user["discord_id"]
        from uuid import UUID as _UUID

        user_uuid = current_user["user_id"]
        if not isinstance(user_uuid, _UUID):
            user_uuid = _UUID(str(user_uuid))

        # Parse feed to get title if name not provided
        name = request.name
        if not name:
            parsed = feedparser.parse(request.url)
            name = parsed.feed.get("title") or request.url

        category = request.category or "自訂"

        # Find or create the feed — custom feeds are per-user, so always create new
        existing_id = await supabase.find_feed_by_url(request.url)
        if existing_id:
            feed_id = existing_id
        else:
            feed_id = await supabase.create_feed(name, request.url, category, created_by=user_uuid)

        # Auto-subscribe
        await supabase.subscribe_to_feed(discord_id, feed_id)

        return success_response(
            FeedResponse(
                id=feed_id,
                name=name,
                url=request.url,  # type: ignore[arg-type]
                category=category,
                is_subscribed=True,
                is_custom=True,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add custom feed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add feed")


@router.patch("/subscriptions/{feed_id}/notification")
async def update_subscription_notification(
    feed_id: UUID,
    enabled: bool,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Toggle per-feed DM notification setting."""
    try:
        supabase = SupabaseService()
        user_uuid = current_user["user_id"]
        from uuid import UUID as _UUID

        if not isinstance(user_uuid, _UUID):
            user_uuid = _UUID(str(user_uuid))

        result = (
            supabase.client.table("user_subscriptions")
            .update({"notification_enabled": enabled})
            .eq("user_id", str(user_uuid))
            .eq("feed_id", str(feed_id))
            .execute()
        )

        # Supabase update doesn't always return data; treat as success if no exception
        return success_response({"feed_id": str(feed_id), "notification_enabled": enabled})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification setting: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")


async def delete_feed(
    feed_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Delete a custom feed (only the creator can delete their own custom feeds)."""
    try:
        supabase = SupabaseService()
        from uuid import UUID as _UUID

        user_uuid = current_user["user_id"]
        if not isinstance(user_uuid, _UUID):
            user_uuid = _UUID(str(user_uuid))

        feeds = await supabase.get_active_feeds(user_id=user_uuid)
        target = next((f for f in feeds if str(f.id) == str(feed_id)), None)

        if not target:
            raise HTTPException(status_code=404, detail="Feed not found")

        if target.created_by is None:
            raise HTTPException(status_code=403, detail="Cannot delete system feeds")

        if str(target.created_by) != str(user_uuid):
            raise HTTPException(status_code=403, detail="You can only delete your own feeds")

        await supabase.delete_feed(feed_id)
        logger.info(f"User {current_user['user_id']} deleted custom feed {feed_id}")
        return success_response({"message": "Feed deleted"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete feed {feed_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
