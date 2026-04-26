import logging
from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user

from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning-content-simple", tags=["Learning Content Simple"])


def get_supabase_service() -> SupabaseService:
    return SupabaseService()


@router.get("/articles")
async def get_learning_articles(
    content_types: List[str] = Query(default=["tutorial", "guide", "project"]),
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get articles with basic educational filtering."""
    try:
        # Get articles from educational feeds
        educational_feeds_result = (
            supabase.client.table("feed_categories")
            .select("feed_id")
            .in_("feed_type", ["educational", "official"])
            .execute()
        )

        if not educational_feeds_result.data:
            # Fallback: get all articles
            articles_result = (
                supabase.client.table("articles")
                .select("id, title, url, published_at, ai_summary, tinkering_index, feed_id")
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )
        else:
            feed_ids = [item["feed_id"] for item in educational_feeds_result.data]
            articles_result = (
                supabase.client.table("articles")
                .select("id, title, url, published_at, ai_summary, tinkering_index, feed_id")
                .in_("feed_id", feed_ids)
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )

        articles = articles_result.data or []

        # Add mock classification for now
        recommendations = []
        for article in articles:
            # Simple heuristic classification
            title_lower = article["title"].lower()

            if any(word in title_lower for word in ["tutorial", "how to", "guide"]):
                content_type = "tutorial"
                learning_value = 0.8
                difficulty = 2
            elif any(word in title_lower for word in ["build", "create", "project"]):
                content_type = "project"
                learning_value = 0.9
                difficulty = 3
            elif any(word in title_lower for word in ["introduction", "getting started", "basics"]):
                content_type = "guide"
                learning_value = 0.7
                difficulty = 1
            else:
                content_type = "reference"
                learning_value = 0.6
                difficulty = 2

            recommendations.append(
                {
                    "article": article,
                    "classification": {
                        "content_type": content_type,
                        "difficulty_level": difficulty,
                        "learning_value_score": learning_value,
                        "educational_features": {
                            "has_code_examples": "code" in title_lower
                            or "programming" in title_lower,
                            "has_step_by_step": "step" in title_lower or "tutorial" in title_lower,
                            "estimated_reading_time": max(
                                5, len(article.get("ai_summary", "")) // 50
                            ),
                        },
                    },
                    "score": learning_value,
                }
            )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Using simplified classification - full LLM classification coming soon!",
        }

    except Exception as e:
        logger.error(f"Failed to get learning articles: {e}")
        return {"recommendations": [], "count": 0, "error": str(e)}
