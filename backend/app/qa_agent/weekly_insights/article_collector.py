"""
Article Collector

Collects articles from the past week (or custom date range) for weekly insights analysis.
Requirements: 1.1, 1.5
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class ArticleCollector:
    """Collects articles from the database for a given time window."""

    def __init__(self, supabase_service: SupabaseService | None = None):
        self.supabase = supabase_service or SupabaseService()

    async def collect_weekly_articles(
        self,
        days: int = 7,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Collect all articles published within the past `days` days.

        Args:
            days: Number of days to look back (default 7).
            end_date: End of the window (default: now UTC).

        Returns:
            List of article dicts with id, title, url, ai_summary, tinkering_index,
            published_at, feed_name, category.
        """
        if end_date is None:
            end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        logger.info(
            "Collecting articles from %s to %s",
            start_date.isoformat(),
            end_date.isoformat(),
        )

        try:
            response = (
                self.supabase.client.table("articles")
                .select(
                    "id, title, url, ai_summary, tinkering_index, published_at, "
                    "feeds(name, category)"
                )
                .gte("published_at", start_date.isoformat())
                .lte("published_at", end_date.isoformat())
                .not_.is_("published_at", "null")
                .order("published_at", desc=True)
                .execute()
            )
            articles = response.data or []
        except Exception as exc:
            logger.error("Failed to fetch articles: %s", exc)
            return []

        # Flatten feed info
        result: list[dict[str, Any]] = []
        for a in articles:
            feed = a.pop("feeds", None) or {}
            result.append(
                {
                    "id": a.get("id"),
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "ai_summary": a.get("ai_summary") or "",
                    "tinkering_index": a.get("tinkering_index") or 0,
                    "published_at": a.get("published_at"),
                    "feed_name": feed.get("name", ""),
                    "category": feed.get("category", ""),
                }
            )

        logger.info("Collected %d articles", len(result))
        return result
