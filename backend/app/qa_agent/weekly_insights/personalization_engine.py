"""
Personalization Engine

Filters and ranks insights based on a user's reading history and preferences.
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import logging
from collections import Counter
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """Personalizes weekly insights for individual users."""

    def __init__(self, supabase_service: SupabaseService | None = None):
        self.supabase = supabase_service or SupabaseService()

    async def get_user_interests(self, user_id: str) -> dict[str, Any]:
        """
        Derive user interest profile from reading list ratings.

        Returns:
          - top_categories: list of preferred categories
          - top_themes: list of preferred themes/technologies
          - avg_rating: average rating given
        """
        try:
            response = (
                self.supabase.client.table("reading_list")
                .select("rating, articles(ai_summary, feeds(category))")
                .eq("user_id", user_id)
                .not_.is_("rating", "null")
                .gte("rating", 3)
                .execute()
            )
            rows = response.data or []
        except Exception as exc:
            logger.warning("Could not load reading history for user %s: %s", user_id, exc)
            return {"top_categories": [], "top_themes": [], "avg_rating": 0.0}

        category_counter: Counter = Counter()
        theme_counter: Counter = Counter()
        ratings: list[int] = []

        # Common tech keywords for theme extraction
        TECH_KEYWORDS = [
            "react",
            "vue",
            "angular",
            "next.js",
            "typescript",
            "javascript",
            "python",
            "rust",
            "go",
            "java",
            "node",
            "docker",
            "kubernetes",
            "llm",
            "gpt",
            "openai",
            "machine learning",
            "deep learning",
            "ai",
            "aws",
            "azure",
            "gcp",
            "security",
            "postgresql",
            "redis",
            "mongodb",
            "fastapi",
            "django",
            "swift",
            "flutter",
        ]

        for row in rows:
            rating = row.get("rating") or 0
            ratings.append(rating)
            article = row.get("articles") or {}
            feed = article.get("feeds") or {}
            cat = feed.get("category", "")
            if cat:
                category_counter[cat] += rating  # weight by rating
            # Extract themes from ai_summary
            summary = (article.get("ai_summary") or "").lower()
            for kw in TECH_KEYWORDS:
                if kw in summary:
                    theme_counter[kw] += rating

        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        top_categories = [cat for cat, _ in category_counter.most_common(5)]
        top_themes = [kw for kw, _ in theme_counter.most_common(5)]

        return {
            "top_categories": top_categories,
            "top_themes": top_themes,
            "avg_rating": round(avg_rating, 2),
        }

    def personalize_clusters(
        self,
        clusters: list[dict[str, Any]],
        user_interests: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Re-rank clusters based on user interests.

        Clusters matching user's preferred categories are boosted.
        """
        top_cats = {c.lower() for c in user_interests.get("top_categories", [])}
        top_themes = {t.lower() for t in user_interests.get("top_themes", [])}
        if not top_cats and not top_themes:
            return clusters

        def score(cluster: dict[str, Any]) -> float:
            base = cluster.get("strength", 0.0)
            name = cluster.get("name", "").lower()
            keywords = [k.lower() for k in cluster.get("top_keywords", [])]
            # Boost if cluster name or keywords match user's preferred categories or themes
            if any(c in name or any(c in k for k in keywords) for c in top_cats):
                base += 1.0
            if any(t in name or any(t in k for k in keywords) for t in top_themes):
                base += 0.5
            return base

        return sorted(clusters, key=score, reverse=True)

    def get_missed_articles(
        self,
        articles: list[dict[str, Any]],
        user_interests: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Suggest high-quality articles the user might have missed,
        filtered by their preferred categories.
        """
        top_cats = {c.lower() for c in user_interests.get("top_categories", [])}

        candidates = [
            a
            for a in articles
            if (not top_cats or a.get("category", "").lower() in top_cats)
            and a.get("tinkering_index", 0) >= 6
        ]

        # Sort by tinkering_index descending
        candidates.sort(key=lambda a: a.get("tinkering_index", 0), reverse=True)
        return candidates[:limit]
