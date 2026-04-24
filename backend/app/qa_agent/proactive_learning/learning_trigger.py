"""
Learning Trigger

Decides when to initiate a proactive learning conversation based on
behavior anomalies and interest changes.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

from .behavior_analyzer import BehaviorAnalyzer
from .interest_tracker import InterestTracker

logger = logging.getLogger(__name__)

MAX_WEEKLY_CONVERSATIONS = 3


class LearningTrigger:
    """Evaluates whether a proactive learning conversation should be triggered."""

    def __init__(self, supabase: SupabaseService | None = None):
        self.supabase = supabase or SupabaseService()
        self.analyzer = BehaviorAnalyzer(self.supabase)
        self.tracker = InterestTracker(self.supabase)

    async def should_trigger(self, user_id: str) -> tuple[bool, dict[str, Any]]:
        """
        Evaluate whether a learning conversation should be triggered for this user.

        Returns:
            (should_trigger: bool, context: dict with trigger reason and data)
        """
        # Check weekly conversation limit
        pref = await self._get_preference(user_id)
        if not pref.get("learning_enabled", True):
            return False, {}

        conversations_this_week = pref.get("conversations_this_week", 0)
        max_weekly = pref.get("max_weekly_conversations", MAX_WEEKLY_CONVERSATIONS)
        if conversations_this_week >= max_weekly:
            logger.debug("User %s hit weekly conversation limit", user_id)
            return False, {}

        # Check for engagement anomalies
        anomalies = await self.analyzer.detect_anomalies(user_id)
        if anomalies:
            return True, {"reason": "engagement_drop", "anomalies": anomalies}

        # Check for new interests
        interests = await self.tracker.get_interest_summary(user_id)
        if interests["new_interests"]:
            return True, {"reason": "new_interest", **interests}

        if interests["decaying_interests"]:
            return True, {"reason": "interest_decay", **interests}

        return False, {}

    async def _get_preference(self, user_id: str) -> dict[str, Any]:
        """Load or create preference model row for user."""
        try:
            resp = (
                self.supabase.client.table("preference_model")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if resp.data:
                # Reset weekly counter if needed
                row = resp.data
                week_reset = row.get("week_reset_at")
                if week_reset:
                    reset_dt = datetime.fromisoformat(week_reset)
                    if datetime.now(UTC) > reset_dt + timedelta(weeks=1):
                        self.supabase.client.table("preference_model").update(
                            {
                                "conversations_this_week": 0,
                                "week_reset_at": datetime.now(UTC).isoformat(),
                            }
                        ).eq("user_id", user_id).execute()
                        row["conversations_this_week"] = 0
                return row
        except Exception:
            pass
        # Create default row
        try:
            self.supabase.client.table("preference_model").upsert(
                {"user_id": user_id, "week_reset_at": datetime.now(UTC).isoformat()}
            ).execute()
        except Exception as exc:
            logger.warning("Could not upsert preference_model: %s", exc)
        return {
            "learning_enabled": True,
            "conversations_this_week": 0,
            "max_weekly_conversations": MAX_WEEKLY_CONVERSATIONS,
        }

    async def increment_conversation_count(self, user_id: str) -> None:
        """Increment the weekly conversation counter after triggering."""
        try:
            self.supabase.client.rpc(
                "increment_conversations_this_week", {"uid": user_id}
            ).execute()
        except Exception:
            # Fallback: manual increment
            try:
                pref = await self._get_preference(user_id)
                new_count = pref.get("conversations_this_week", 0) + 1
                self.supabase.client.table("preference_model").update(
                    {"conversations_this_week": new_count}
                ).eq("user_id", user_id).execute()
            except Exception as exc:
                logger.warning("Failed to increment conversation count: %s", exc)
