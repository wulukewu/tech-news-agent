"""
Recommendation Reason Service

Generates human-readable reasons for article recommendations.
Uses preference_summary (LLM-generated) when available for personalized reasons;
falls back to rule-based logic.
Requirements: 2.1, 2.2, 2.3
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_reason(
    article: dict[str, Any],
    rating_history: list[dict[str, Any]],
    preference_summary: str | None = None,
) -> str:
    """
    Return a one-sentence recommendation reason.

    Prefers preference_summary-based matching when available.
    Falls back to rating history, then generic message.
    """
    category = (article.get("category") or "").strip()
    title = (article.get("title") or "").strip()

    # If we have a preference summary, try to match keywords from it
    if preference_summary:
        summary_lower = preference_summary.lower()
        # Check if article title or category keywords appear in the summary
        keywords_to_check = [w for w in (category + " " + title).lower().split() if len(w) > 3]
        matched = [kw for kw in keywords_to_check if kw in summary_lower]
        if matched:
            return f"根據你的偏好描述，這篇 {category} 文章符合你的興趣方向"

    if rating_history and category:
        high_rated_in_cat = [
            r
            for r in rating_history
            if r.get("rating")
            and r["rating"] >= 4
            and (r.get("articles") or {}).get("category", "").lower() == category.lower()
        ]
        if high_rated_in_cat:
            return f"你之前給 {category} 相關文章高分，這篇主題相似"

        any_high_rated = [r for r in rating_history if r.get("rating") and r["rating"] >= 4]
        if any_high_rated:
            return f"根據你的閱讀偏好，這篇 {category} 文章可能符合你的興趣"

    return "這篇技術深度較高，符合本平台的精選標準"
