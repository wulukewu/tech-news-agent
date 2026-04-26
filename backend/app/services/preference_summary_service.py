"""
Preference Summary Service

Condenses a user's recent DM conversations into a short preference summary
using Llama 3.1 8B. Stored in preference_model.preference_summary.
Requirements: dm-conversation-memory §2, §3
"""

import logging
from datetime import UTC, datetime

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """你是一個技術內容推薦系統的偏好分析師。
根據以下用戶在 Discord 說的話，用繁體中文寫一段 150 字以內的偏好摘要。
摘要應該描述：用戶喜歡什麼技術主題、偏好什麼深度/風格、不喜歡什麼。
只輸出摘要本身，不要加任何前綴或解釋。

用戶說的話：
{messages}"""


async def update_preference_summary(user_id: str, supabase: SupabaseService) -> str | None:
    """
    Fetch recent DM conversations for a user, condense into a summary, and save.
    Returns the new summary, or None if no conversations found.
    """
    try:
        resp = (
            supabase.client.table("dm_conversations")
            .select("content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        rows = resp.data or []
    except Exception as exc:
        logger.error("Failed to fetch dm_conversations for %s: %s", user_id, exc)
        return None

    if not rows:
        return None

    messages = "\n".join(f"- {r['content']}" for r in reversed(rows))

    try:
        from groq import AsyncGroq

        from app.core.config import settings

        client = AsyncGroq(api_key=settings.groq_api_key)
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(messages=messages)}],
            max_tokens=300,
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM summary generation failed for %s: %s", user_id, exc)
        return None

    try:
        supabase.client.table("preference_model").upsert(
            {
                "user_id": user_id,
                "preference_summary": summary,
                "summary_updated_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to save preference summary for %s: %s", user_id, exc)
        return None

    logger.info("Updated preference summary for user %s", user_id)
    return summary
