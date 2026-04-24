"""
Weight Adjuster

Applies preference model weights to article scoring for recommendations.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import logging
from typing import Any

from .preference_model import PreferenceModel

logger = logging.getLogger(__name__)

EXPLORATION_RATIO = 0.15  # 15% of recommendations kept as exploration (anti-filter-bubble)


class WeightAdjuster:
    """Adjusts article recommendation scores using learned preference weights."""

    def __init__(self):
        self.pref_model = PreferenceModel()

    async def score_articles(
        self,
        user_id: str,
        articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Re-score articles using preference weights.

        Each article gets a `preference_score` field (0-1).
        Preserves EXPLORATION_RATIO of articles at neutral score to avoid filter bubble.

        Args:
            user_id: The user to personalize for.
            articles: List of article dicts with at least 'category' and 'tinkering_index'.

        Returns:
            Articles sorted by adjusted score (descending).
        """
        model = await self.pref_model.get(user_id)
        weights: dict[str, float] = model.get("category_weights") or {}

        if not weights:
            return articles  # No preferences yet, return as-is

        scored: list[dict[str, Any]] = []
        for article in articles:
            cat = (article.get("category") or "").lower()
            base_score = (article.get("tinkering_index") or 5) / 10.0
            pref_weight = weights.get(cat, 0.5)
            adjusted = round(base_score * 0.6 + pref_weight * 0.4, 3)
            scored.append({**article, "preference_score": adjusted})

        # Sort by adjusted score
        scored.sort(key=lambda a: a["preference_score"], reverse=True)

        # Inject exploration articles (low-weight categories) to avoid filter bubble
        n_explore = max(1, int(len(scored) * EXPLORATION_RATIO))
        low_weight = [
            a for a in scored if weights.get((a.get("category") or "").lower(), 0.5) < 0.3
        ]
        if low_weight:
            explore_picks = low_weight[:n_explore]
            # Move them to random positions in the top half
            main = [a for a in scored if a not in explore_picks]
            insert_at = max(1, len(main) // 3)
            result = main[:insert_at] + explore_picks + main[insert_at:]
            return result

        return scored

    async def apply_feedback(
        self,
        user_id: str,
        adjustments: dict[str, float],
    ) -> dict[str, float]:
        """
        Apply feedback-derived weight adjustments to the preference model.

        Returns updated weights.
        """
        return await self.pref_model.apply_adjustments(user_id, adjustments)
