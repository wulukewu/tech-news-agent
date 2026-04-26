"""
Recommendation Reason Service

Generates human-readable reasons for article recommendations.
Rule-based first (fast, no token cost); falls back to a generic message.
Requirements: 2.1, 2.2, 2.3
"""

from typing import Any


def generate_reason(article: dict[str, Any], rating_history: list[dict[str, Any]]) -> str:
    """
    Return a one-sentence recommendation reason.

    Args:
        article: Article dict with at least 'category'.
        rating_history: List of reading_list rows with 'rating' and article join data
                        (each row should have article.category accessible).

    Returns:
        A short reason string.
    """
    category = (article.get("category") or "").strip()

    if rating_history and category:
        # Find highly-rated articles in the same category
        high_rated_in_cat = [
            r
            for r in rating_history
            if r.get("rating")
            and r["rating"] >= 4
            and (r.get("articles") or {}).get("category", "").lower() == category.lower()
        ]
        if high_rated_in_cat:
            return f"你之前給 {category} 相關文章高分，這篇主題相似"

        # Any high-rated articles at all → mention the category difference
        any_high_rated = [r for r in rating_history if r.get("rating") and r["rating"] >= 4]
        if any_high_rated:
            return f"根據你的閱讀偏好，這篇 {category} 文章可能符合你的興趣"

    return "這篇技術深度較高，符合本平台的精選標準"
