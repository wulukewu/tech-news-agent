"""
Proactive Recommendation Job

After each RSS fetch, scores new articles per user's preference model and
sends a personalized Discord DM with inline feedback buttons.
Requirements: 1.1-1.5, 4.1-4.3
"""

import logging
from datetime import UTC, datetime, timedelta

from app.qa_agent.proactive_learning.weight_adjuster import WeightAdjuster
from app.services.recommendation_reason import generate_reason
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

TOP_N = 5
MIN_RATINGS_FOR_PERSONALIZATION = 5


async def proactive_recommendation_job(new_article_ids: list[str]) -> None:
    """
    Triggered after background_fetch_job completes.

    Args:
        new_article_ids: IDs of articles inserted in this fetch cycle.
                         If empty, job exits immediately (Requirement 1.5).
    """
    if not new_article_ids:
        logger.info("Proactive recommendation: no new articles, skipping.")
        return

    logger.info("Starting proactive recommendation job for %d new articles", len(new_article_ids))

    supabase = SupabaseService()

    # Fetch full article data for the new articles
    try:
        resp = (
            supabase.client.table("articles")
            .select("id, title, url, category, tinkering_index, ai_summary")
            .in_("id", new_article_ids)
            .execute()
        )
        new_articles = resp.data or []
    except Exception as exc:
        logger.error("Failed to fetch new articles for proactive recommendation: %s", exc)
        return

    if not new_articles:
        return

    # Fetch users with DM enabled (returns discord_ids)
    try:
        resp = (
            supabase.client.table("users")
            .select("id, discord_id, last_proactive_dm_at, proactive_dm_frequency_hours")
            .eq("dm_notifications_enabled", True)
            .execute()
        )
        users = resp.data or []
    except Exception as exc:
        logger.error("Failed to fetch DM-enabled users: %s", exc)
        return

    if not users:
        logger.info("No users with DM enabled, skipping proactive recommendation.")
        return

    from app.bot.client import bot

    if not bot.is_ready():
        logger.warning("Bot not ready, skipping proactive recommendation DMs.")
        return

    from app.bot.cogs.proactive_dm import send_proactive_dm

    adjuster = WeightAdjuster()
    sent_count = 0

    for user in users:
        user_id = user["id"]
        discord_id = user["discord_id"]

        # Cooldown check (Requirement 4.3)
        frequency_hours = user.get("proactive_dm_frequency_hours") or 20
        last_dm = user.get("last_proactive_dm_at")
        if last_dm:
            last_dm_dt = datetime.fromisoformat(last_dm.replace("Z", "+00:00"))
            if datetime.now(UTC) - last_dm_dt < timedelta(hours=frequency_hours):
                logger.debug("User %s within cooldown, skipping.", discord_id)
                continue

        try:
            articles_with_reasons = await _build_recommendations(
                supabase, adjuster, user_id, discord_id, new_articles
            )
        except Exception as exc:
            logger.error("Failed to build recommendations for user %s: %s", discord_id, exc)
            continue

        if not articles_with_reasons:
            continue

        success = await send_proactive_dm(bot, discord_id, articles_with_reasons)
        if success:
            # Update last_proactive_dm_at (Requirement 4.2)
            try:
                supabase.client.table("users").update(
                    {"last_proactive_dm_at": datetime.now(UTC).isoformat()}
                ).eq("id", user_id).execute()
            except Exception as exc:
                logger.error("Failed to update last_proactive_dm_at for %s: %s", discord_id, exc)
            sent_count += 1

    logger.info("Proactive recommendation job complete: %d DMs sent.", sent_count)


async def _build_recommendations(
    supabase: SupabaseService,
    adjuster: WeightAdjuster | None,
    user_id: str,
    discord_id: str,
    new_articles: list[dict],
) -> list[dict]:
    """Score articles and build recommendation payload for one user."""
    if adjuster is None:
        adjuster = WeightAdjuster()

    # Fetch user's rating history and preference summary in parallel
    rating_history = []
    preference_summary = None

    try:
        resp = (
            supabase.client.table("reading_list")
            .select("rating, articles(category)")
            .eq("user_id", user_id)
            .not_.is_("rating", "null")
            .order("updated_at", desc=True)
            .limit(50)
            .execute()
        )
        rating_history = resp.data or []
    except Exception as exc:
        logger.warning("Could not fetch rating history for %s: %s", discord_id, exc)

    try:
        resp = (
            supabase.client.table("preference_model")
            .select("preference_summary, category_weights")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if resp.data:
            preference_summary = resp.data.get("preference_summary")
    except Exception as exc:
        logger.warning("Could not fetch preference summary for %s: %s", discord_id, exc)

    has_enough_history = len(rating_history) >= MIN_RATINGS_FOR_PERSONALIZATION
    has_summary = bool(preference_summary)

    if has_enough_history:
        scored = await adjuster.score_articles(user_id, new_articles)
    elif has_summary:
        # Use preference_summary to boost articles matching keywords
        scored = _score_by_summary(new_articles, preference_summary)
    else:
        # Fall back to tinkering_index
        scored = sorted(
            new_articles,
            key=lambda a: a.get("tinkering_index") or 0,
            reverse=True,
        )

    top_articles = scored[:TOP_N]
    if not top_articles:
        return []

    result = []
    for article in top_articles:
        if has_enough_history or has_summary:
            reason = generate_reason(article, rating_history, preference_summary)
        else:
            reason = "這篇技術深度較高，符合本平台的精選標準（還在學習你的偏好）"
        result.append({"article": article, "reason": reason, "user_id": user_id})

    return result


def _score_by_summary(articles: list[dict], summary: str) -> list[dict]:
    """Boost articles whose category/title keywords appear in the preference summary."""
    summary_lower = summary.lower()
    scored = []
    for article in articles:
        base = (article.get("tinkering_index") or 5) / 10.0
        text = ((article.get("category") or "") + " " + (article.get("title") or "")).lower()
        keywords = [w for w in text.split() if len(w) > 3]
        boost = sum(0.1 for kw in keywords if kw in summary_lower)
        scored.append({**article, "preference_score": round(min(1.0, base + boost), 3)})
    scored.sort(key=lambda a: a["preference_score"], reverse=True)
    return scored
