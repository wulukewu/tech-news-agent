"""
Behavior Analyzer

Collects and analyzes user reading behavior to compute per-category engagement metrics
and detect anomalous changes.
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """Analyzes user behavior events to derive engagement metrics."""

    def __init__(self, supabase: SupabaseService | None = None):
        self.supabase = supabase or SupabaseService()

    async def record_event(
        self,
        user_id: str,
        event_type: str,
        article_id: str | None = None,
        category: str | None = None,
        rating: int | None = None,
        duration_seconds: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Persist a single behavior event."""
        try:
            self.supabase.client.table("user_behavior_events").insert(
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    "article_id": article_id,
                    "category": category,
                    "rating": rating,
                    "duration_seconds": duration_seconds,
                    "metadata": metadata or {},
                }
            ).execute()
        except Exception as exc:
            logger.warning("Failed to record behavior event: %s", exc)

    async def get_engagement_metrics(
        self, user_id: str, days: int = 30
    ) -> dict[str, dict[str, float]]:
        """
        Compute per-category engagement metrics for the past N days.

        Returns:
            {category: {avg_rating, read_count, avg_duration, engagement_score}}
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        try:
            resp = (
                self.supabase.client.table("user_behavior_events")
                .select("event_type, category, rating, duration_seconds")
                .eq("user_id", user_id)
                .gte("created_at", cutoff)
                .execute()
            )
            events = resp.data or []
        except Exception as exc:
            logger.warning("Failed to fetch behavior events: %s", exc)
            return {}

        # Aggregate by category
        cat_data: dict[str, dict[str, list]] = defaultdict(
            lambda: {"ratings": [], "durations": [], "reads": 0}
        )
        for e in events:
            cat = e.get("category") or "unknown"
            if e.get("rating"):
                cat_data[cat]["ratings"].append(e["rating"])
            if e.get("duration_seconds"):
                cat_data[cat]["durations"].append(e["duration_seconds"])
            if e.get("event_type") == "read":
                cat_data[cat]["reads"] += 1

        metrics: dict[str, dict[str, float]] = {}
        for cat, data in cat_data.items():
            avg_rating = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 0.0
            avg_duration = (
                sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0.0
            )
            # Simple engagement score: weighted combination
            score = round(
                avg_rating * 0.5
                + min(avg_duration / 300, 1.0) * 0.3
                + min(data["reads"] / 10, 1.0) * 0.2,
                3,
            )
            metrics[cat] = {
                "avg_rating": round(avg_rating, 2),
                "read_count": data["reads"],
                "avg_duration": round(avg_duration, 1),
                "engagement_score": score,
            }
        return metrics

    async def detect_anomalies(self, user_id: str) -> list[dict[str, Any]]:
        """
        Compare last 7 days vs previous 7 days to detect engagement drops.

        Returns list of anomaly dicts: {category, change_pct, type}
        """
        recent = await self.get_engagement_metrics(user_id, days=7)
        previous = await self.get_engagement_metrics(user_id, days=14)

        anomalies: list[dict[str, Any]] = []
        for cat, curr in recent.items():
            prev = previous.get(cat, {})
            prev_score = prev.get("engagement_score", 0)
            curr_score = curr.get("engagement_score", 0)
            if prev_score > 0:
                change_pct = (curr_score - prev_score) / prev_score * 100
                if change_pct <= -40:
                    anomalies.append(
                        {
                            "category": cat,
                            "change_pct": round(change_pct, 1),
                            "type": "engagement_drop",
                        }
                    )
        return anomalies
