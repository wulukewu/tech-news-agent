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
根據「現有摘要」和「新訊息」，合併更新成一段 100 字以內的偏好摘要。
規則：
- 保留現有摘要中的所有偏好，加入新訊息中的新偏好
- 直接描述偏好，不要用「用戶」開頭
- 合併重複的內容，每個偏好只說一次
- 格式：先說喜歡什麼，再說不喜歡什麼
- 只輸出摘要本身，不要加任何前綴或解釋

現有摘要：
{existing_summary}

新訊息：
{messages}"""


async def update_preference_summary(user_id: str, supabase: SupabaseService) -> str | None:
    """
    Fetch recent DM conversations and merge with existing summary.
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

    # Fetch existing summary to merge with
    existing_summary = ""
    try:
        pref_resp = (
            supabase.client.table("preference_model")
            .select("preference_summary")
            .eq("user_id", user_id)
            .execute()
        )
        existing_summary = (pref_resp.data or [{}])[0].get("preference_summary") or ""
    except Exception:
        pass

    messages = "\n".join(f"- {r['content']}" for r in reversed(rows))

    try:
        from groq import AsyncGroq

        from app.core.config import settings

        client = AsyncGroq(api_key=settings.groq_api_key)
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT.format(
                        existing_summary=existing_summary or "（尚無摘要）",
                        messages=messages,
                    ),
                }
            ],
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
            },
            on_conflict="user_id",
        ).execute()
    except Exception as exc:
        logger.error("Failed to save preference summary for %s: %s", user_id, exc)
        return None

    logger.info("Updated preference summary for user %s", user_id)
    return summary
