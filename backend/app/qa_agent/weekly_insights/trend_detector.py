"""
Trend Detector

Identifies rising/falling technology trends by comparing current week themes
against historical data stored in Supabase.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2
"""

import logging
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class TrendDetector:
    """Detects technology trends from weekly article analysis."""

    def __init__(self, supabase_service: SupabaseService | None = None):
        self.supabase = supabase_service or SupabaseService()

    def detect_trends(
        self,
        current_articles: list[dict[str, Any]],
        historical_counts: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Compare current week's theme frequencies against historical baseline.

        Args:
            current_articles: Analyzed articles for the current week.
            historical_counts: Optional dict of {theme: count} from previous weeks.

        Returns:
            List of trend dicts sorted by momentum (descending):
              - name: theme/technology name
              - domain: technology domain
              - current_count: mentions this week
              - previous_count: mentions in baseline
              - momentum: growth ratio (current / max(previous, 1))
              - direction: "rising" | "stable" | "declining"
        """
        # Count current week themes
        current_counter: Counter = Counter()
        domain_map: dict[str, str] = {}

        for article in current_articles:
            domain = article.get("domain", "other")
            for tag in article.get("themes", []) + article.get("technologies", []):
                tag_lower = tag.lower()
                current_counter[tag_lower] += 1
                domain_map[tag_lower] = domain

        if not current_counter:
            return []

        hist = historical_counts or {}
        trends: list[dict[str, Any]] = []

        for tag, count in current_counter.most_common(30):
            prev = hist.get(tag, 0)
            momentum = round(count / max(prev, 1), 2)

            if prev == 0:
                direction = "rising"
            elif momentum >= 1.5:
                direction = "rising"
            elif momentum <= 0.5:
                direction = "declining"
            else:
                direction = "stable"

            trends.append(
                {
                    "name": tag.title(),
                    "domain": domain_map.get(tag, "other"),
                    "current_count": count,
                    "previous_count": prev,
                    "momentum": momentum,
                    "direction": direction,
                }
            )

        # Sort: rising first, then by count
        trends.sort(key=lambda x: (x["direction"] != "rising", -x["current_count"]))
        return trends

    async def load_historical_counts(self, weeks_back: int = 4) -> dict[str, int]:
        """
        Load aggregated theme counts from the past N weeks of stored insights.

        Returns a dict of {theme_lower: total_count}.
        """
        cutoff = (datetime.now(UTC) - timedelta(weeks=weeks_back)).isoformat()
        try:
            response = (
                self.supabase.client.table("weekly_insights")
                .select("trend_data")
                .gte("created_at", cutoff)
                .execute()
            )
            rows = response.data or []
        except Exception as exc:
            logger.warning("Could not load historical trend data: %s", exc)
            return {}

        counts: Counter = Counter()
        for row in rows:
            trend_data = row.get("trend_data") or []
            for trend in trend_data:
                name = trend.get("name", "").lower()
                counts[name] += trend.get("current_count", 0)

        return dict(counts)
