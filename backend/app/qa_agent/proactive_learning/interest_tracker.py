"""
Interest Tracker

Detects new topic exploration, interest growth, and interest decay.
Requirements: 1.5, 6.1, 6.2, 6.3
"""

import logging
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

NEW_TOPIC_THRESHOLD = 3  # articles in a new category to flag as new interest
DECAY_DAYS = 21  # no activity for this many days = interest decay


class InterestTracker:
    """Tracks user interest changes over time."""

    def __init__(self, supabase: SupabaseService | None = None):
        self.supabase = supabase or SupabaseService()

    async def get_new_interests(self, user_id: str, days: int = 14) -> list[str]:
        """
        Return categories the user started exploring recently (≥ NEW_TOPIC_THRESHOLD reads)
        but had no activity in the prior period.
        """
        cutoff_recent = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        cutoff_prior = (datetime.now(UTC) - timedelta(days=days * 2)).isoformat()

        try:
            recent_resp = (
                self.supabase.client.table("user_behavior_events")
                .select("category")
                .eq("user_id", user_id)
                .eq("event_type", "read")
                .gte("created_at", cutoff_recent)
                .execute()
            )
            prior_resp = (
                self.supabase.client.table("user_behavior_events")
                .select("category")
                .eq("user_id", user_id)
                .eq("event_type", "read")
                .gte("created_at", cutoff_prior)
                .lt("created_at", cutoff_recent)
                .execute()
            )
        except Exception as exc:
            logger.warning("Failed to fetch interest data: %s", exc)
            return []

        recent_cats = Counter(e["category"] for e in (recent_resp.data or []) if e.get("category"))
        prior_cats = {e["category"] for e in (prior_resp.data or []) if e.get("category")}

        return [
            cat
            for cat, count in recent_cats.items()
            if count >= NEW_TOPIC_THRESHOLD and cat not in prior_cats
        ]

    async def get_decaying_interests(self, user_id: str) -> list[str]:
        """
        Return categories with no activity in the past DECAY_DAYS but active before.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=DECAY_DAYS)).isoformat()
        try:
            recent_resp = (
                self.supabase.client.table("user_behavior_events")
                .select("category")
                .eq("user_id", user_id)
                .gte("created_at", cutoff)
                .execute()
            )
            all_resp = (
                self.supabase.client.table("user_behavior_events")
                .select("category")
                .eq("user_id", user_id)
                .lt("created_at", cutoff)
                .execute()
            )
        except Exception as exc:
            logger.warning("Failed to fetch decay data: %s", exc)
            return []

        recent_cats = {e["category"] for e in (recent_resp.data or []) if e.get("category")}
        old_cats = {e["category"] for e in (all_resp.data or []) if e.get("category")}
        return list(old_cats - recent_cats)

    async def get_interest_summary(self, user_id: str) -> dict[str, Any]:
        """Return a combined summary of new and decaying interests."""
        new = await self.get_new_interests(user_id)
        decaying = await self.get_decaying_interests(user_id)
        return {"new_interests": new, "decaying_interests": decaying}
