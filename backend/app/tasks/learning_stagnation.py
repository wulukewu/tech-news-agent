"""
Learning Stagnation Check Job

Runs daily to detect users who haven't made learning progress in 3+ days
and sends a Discord DM reminder with their next recommended article.
Requirements: 3.1-3.5
"""

import logging
from datetime import UTC, datetime, timedelta

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

STAGNATION_DAYS = 3
MAX_REMINDERS_PER_WEEK = 2


async def learning_stagnation_check_job() -> None:
    """Check all active learning goals and send reminders for stagnant ones."""
    supabase = SupabaseService()

    try:
        # Get all active learning goals with last progress time
        goals_resp = (
            supabase.client.table("learning_goals")
            .select(
                "id, user_id, title, status, "
                "last_stagnation_reminder_at, stagnation_reminder_count_this_week, "
                "users(discord_id, dm_notifications)"
            )
            .eq("status", "active")
            .execute()
        )
        if not goals_resp.data:
            return

        now = datetime.now(UTC)
        week_start = now - timedelta(days=now.weekday())  # Monday of current week

        for goal in goals_resp.data:
            try:
                await _check_goal(supabase, goal, now, week_start)
            except Exception as exc:
                logger.warning("Failed stagnation check for goal %s: %s", goal["id"], exc)

    except Exception as exc:
        logger.error("learning_stagnation_check_job failed: %s", exc, exc_info=True)


async def _check_goal(
    supabase: SupabaseService,
    goal: dict,
    now: datetime,
    week_start: datetime,
) -> None:
    user = (
        (goal.get("users") or [{}])[0]
        if isinstance(goal.get("users"), list)
        else goal.get("users") or {}
    )
    discord_id = user.get("discord_id")
    dm_enabled = user.get("dm_notifications", False)

    if not discord_id or not dm_enabled:
        return

    # Reset weekly counter if we're in a new week
    last_reminder_at = goal.get("last_stagnation_reminder_at")
    reminder_count = goal.get("stagnation_reminder_count_this_week") or 0

    if last_reminder_at:
        last_dt = datetime.fromisoformat(last_reminder_at.replace("Z", "+00:00"))
        if last_dt < week_start:
            reminder_count = 0  # New week, reset count

    if reminder_count >= MAX_REMINDERS_PER_WEEK:
        return

    # Find last progress update for this goal
    progress_resp = (
        supabase.client.table("learning_progress")
        .select("updated_at")
        .eq("goal_id", goal["id"])
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )

    if progress_resp.data:
        last_progress_str = progress_resp.data[0]["updated_at"]
        last_progress = datetime.fromisoformat(last_progress_str.replace("Z", "+00:00"))
        days_since = (now - last_progress).days
    else:
        # No progress at all — use goal creation time
        created_str = goal.get("created_at", now.isoformat())
        created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        days_since = (now - created_at).days

    if days_since < STAGNATION_DAYS:
        return

    # Get overall completion percentage
    all_progress = (
        supabase.client.table("learning_progress")
        .select("status")
        .eq("goal_id", goal["id"])
        .execute()
    )
    records = all_progress.data or []
    completed = sum(1 for r in records if r["status"] == "completed")
    total = len(records) if records else 1
    completion_pct = round(completed / total * 100)

    # Get next recommended article
    next_article = await _get_next_article(supabase, goal["user_id"], goal["id"])

    # Send DM
    await _send_stagnation_dm(
        discord_id=discord_id,
        goal_title=goal["title"],
        completion_pct=completion_pct,
        days_since=days_since,
        next_article=next_article,
    )

    # Update reminder tracking
    supabase.client.table("learning_goals").update(
        {
            "last_stagnation_reminder_at": now.isoformat(),
            "stagnation_reminder_count_this_week": reminder_count + 1,
        }
    ).eq("id", goal["id"]).execute()

    logger.info(
        "Sent stagnation reminder for goal %s (user %s, %d days idle)",
        goal["id"],
        discord_id,
        days_since,
    )


async def _get_next_article(supabase: SupabaseService, user_id: str, goal_id: str) -> dict | None:
    """Get the next unread article for the current learning stage."""
    try:
        # Get current stage articles via learning_stages → path → goal
        paths_resp = (
            supabase.client.table("learning_paths")
            .select("id, learning_stages(id, stage_order, prerequisites)")
            .eq("goal_id", goal_id)
            .limit(1)
            .execute()
        )
        if not paths_resp.data:
            return None

        stages = sorted(
            paths_resp.data[0].get("learning_stages") or [],
            key=lambda s: s["stage_order"],
        )
        if not stages:
            return None

        # Find first incomplete stage
        completed_resp = (
            supabase.client.table("learning_progress")
            .select("article_id")
            .eq("user_id", user_id)
            .eq("goal_id", goal_id)
            .eq("status", "completed")
            .execute()
        )
        completed_ids = {r["article_id"] for r in (completed_resp.data or [])}

        for stage in stages:
            skills = stage.get("prerequisites") or []
            if not skills:
                continue
            # Find an article matching this stage's skills
            for skill in skills:
                articles_resp = (
                    supabase.client.table("articles")
                    .select("id, title, url")
                    .ilike("category", f"%{skill}%")
                    .not_.in_("id", list(completed_ids) or ["00000000-0000-0000-0000-000000000000"])
                    .order("tinkering_index", desc=True)
                    .limit(1)
                    .execute()
                )
                if articles_resp.data:
                    return articles_resp.data[0]
    except Exception as exc:
        logger.warning("Could not get next article for goal %s: %s", goal_id, exc)
    return None


async def _send_stagnation_dm(
    discord_id: str,
    goal_title: str,
    completion_pct: int,
    days_since: int,
    next_article: dict | None,
) -> None:
    """Send a stagnation reminder DM via the Discord bot."""
    try:
        from app.bot.client import get_bot_client

        bot = get_bot_client()
        if bot is None:
            logger.warning("Bot client not available, skipping stagnation DM")
            return

        user = await bot.fetch_user(int(discord_id))
        if user is None:
            return

        lines = [
            "📚 **學習提醒**",
            "",
            f"你的「**{goal_title}**」學習路徑已經 **{days_since} 天**沒有更新了。",
            f"目前進度：**{completion_pct}%**",
        ]

        if next_article:
            lines += [
                "",
                f"下一篇推薦：[{next_article['title']}]({next_article['url']})",
            ]

        lines += [
            "",
            "繼續學習，保持動力！🚀",
        ]

        await user.send("\n".join(lines))

    except Exception as exc:
        logger.warning("Failed to send stagnation DM to %s: %s", discord_id, exc)
