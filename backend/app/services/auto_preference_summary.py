"""
Auto Preference Summary

Triggers preference_summary update automatically after preference statements,
without requiring the user to manually run /update_profile.

Trigger condition: >= 3 new DM messages since last summary update, OR >= 24h since last update.
This avoids calling the LLM on every single message.
"""

import asyncio
import logging
from datetime import UTC, datetime

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

_MIN_NEW_MESSAGES = 3
_MIN_HOURS = 24


async def maybe_update_preference_summary(user_id: str) -> None:
    """
    Check trigger condition and update preference_summary in the background if met.
    Safe to call after every preference statement — will no-op if condition not met.
    """
    supabase = SupabaseService()

    try:
        resp = (
            supabase.client.table("preference_model")
            .select("summary_updated_at")
            .eq("user_id", user_id)
            .execute()
        )
        last_update_str = (resp.data or [{}])[0].get("summary_updated_at")
    except Exception:
        last_update_str = None

    last_update = None
    if last_update_str:
        try:
            last_update = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
        except Exception:
            pass

    # Count new messages since last update
    try:
        query = (
            supabase.client.table("dm_conversations")
            .select("id", count="exact")
            .eq("user_id", user_id)
        )
        if last_update:
            query = query.gte("created_at", last_update.isoformat())
        count_resp = query.execute()
        new_count = count_resp.count or 0
    except Exception:
        new_count = 0

    hours_since = (datetime.now(UTC) - last_update).total_seconds() / 3600 if last_update else 999

    if new_count < _MIN_NEW_MESSAGES and hours_since < _MIN_HOURS:
        return  # Condition not met, skip

    logger.info(
        "Auto-triggering preference summary update for user %s "
        "(new_messages=%d, hours_since=%.1f)",
        user_id,
        new_count,
        hours_since,
    )

    try:
        from app.services.preference_summary_service import update_preference_summary

        await update_preference_summary(user_id, supabase)
    except Exception as exc:
        logger.warning("Auto preference summary update failed for %s: %s", user_id, exc)


def schedule_preference_summary_update(user_id: str) -> None:
    """Fire-and-forget: schedule the update as a background task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(maybe_update_preference_summary(user_id))
    except Exception as exc:
        logger.warning("Could not schedule preference summary update: %s", exc)
