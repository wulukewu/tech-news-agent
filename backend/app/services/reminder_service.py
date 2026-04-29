"""
Reminder Service - 基於 embedding 相似度的智能提醒
當用戶加入文章到 reading list 或評高分時，找相似文章透過 Discord DM 通知
"""
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

# Defaults (used when DB columns don't exist yet)
_DEFAULTS = {
    "reminder_enabled": True,
    "reminder_on_add": True,
    "reminder_on_rate": True,
    "reminder_cooldown_hours": 4,
    "reminder_min_similarity": 0.72,
}
MAX_SUGGESTIONS = 3


async def _get_reminder_settings(supabase: SupabaseService, user_id: str) -> dict:
    """讀取用戶提醒設定，欄位不存在時回傳預設值"""
    try:
        cols = ",".join(_DEFAULTS.keys())
        r = (
            supabase.client.table("user_notification_preferences")
            .select(cols)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if r.data:
            return {k: r.data.get(k, v) for k, v in _DEFAULTS.items()}
    except Exception:
        pass
    return dict(_DEFAULTS)


async def _check_cooldown(supabase: SupabaseService, user_id: str, cooldown_hours: int) -> bool:
    """回傳 True 表示還在 cooldown 期間（不應發送）"""
    try:
        r = (
            supabase.client.table("users")
            .select("last_proactive_dm_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        last_dm = r.data.get("last_proactive_dm_at") if r.data else None
        if not last_dm:
            return False
        last_dt = datetime.fromisoformat(last_dm.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
        return elapsed < cooldown_hours
    except Exception:
        return False


async def _update_last_dm(supabase: SupabaseService, user_id: str) -> None:
    try:
        supabase.client.table("users").update(
            {"last_proactive_dm_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user_id).execute()
    except Exception:
        pass


async def send_similar_articles_reminder(
    discord_id: str,
    article_id: UUID,
    trigger: str = "added",  # "added" | "rated"
) -> None:
    """
    找出與 article_id 相似的文章，透過 Discord DM 通知用戶。
    在背景執行，不阻塞 API 回應。
    """
    try:
        supabase = SupabaseService()
        user_uuid = await supabase.get_or_create_user(discord_id)
        user_id = str(user_uuid)

        # 1. 讀取用戶設定
        settings = await _get_reminder_settings(supabase, user_id)

        if not settings["reminder_enabled"]:
            return
        if trigger == "added" and not settings["reminder_on_add"]:
            return
        if trigger == "rated" and not settings["reminder_on_rate"]:
            return

        # 2. Cooldown 檢查
        if await _check_cooldown(supabase, user_id, settings["reminder_cooldown_hours"]):
            logger.debug(f"User {discord_id} in cooldown, skipping reminder")
            return

        # 3. 確認用戶有開啟 DM 通知
        if not await supabase.get_notification_settings(discord_id):
            return

        # 4. 取得觸發文章的 embedding 和標題
        article_res = (
            supabase.client.table("articles")
            .select("title, embedding")
            .eq("id", str(article_id))
            .single()
            .execute()
        )
        if not article_res.data or not article_res.data.get("embedding"):
            return

        article_title = article_res.data["title"]
        embedding = article_res.data["embedding"]
        if isinstance(embedding, str):
            embedding = json.loads(embedding)

        # 5. 取得用戶已在 reading list 的文章 ID（避免重複推薦）
        existing_res = (
            supabase.client.table("reading_list")
            .select("article_id")
            .eq("user_id", user_id)
            .execute()
        )
        existing_ids = {row["article_id"] for row in (existing_res.data or [])}

        # 6. 向量相似度搜尋
        similar_res = supabase.client.rpc(
            "match_articles",
            {
                "query_embedding": embedding,
                "match_threshold": settings["reminder_min_similarity"],
                "match_count": MAX_SUGGESTIONS + 5,
            },
        ).execute()

        if not similar_res.data:
            return

        suggestions = [
            a
            for a in similar_res.data
            if a["id"] != str(article_id) and a["id"] not in existing_ids
        ][:MAX_SUGGESTIONS]

        if not suggestions:
            return

        # 7. 組裝訊息並發送
        from app.bot.client import bot

        if not bot or not bot.is_ready():
            logger.warning("Bot not ready, skipping reminder DM")
            return

        trigger_text = "加入閱讀清單" if trigger == "added" else "評為高分"
        title_short = article_title[:60] + ("..." if len(article_title) > 60 else "")
        msg = f"📚 **智能提醒** — 根據你{trigger_text}的文章\n**{title_short}**\n\n"
        msg += "你可能也會喜歡這些相關文章：\n\n"

        for i, a in enumerate(suggestions, 1):
            t = a["title"][:70] + ("..." if len(a["title"]) > 70 else "")
            msg += f"{i}. **{t}**\n"
            msg += f"   相似度 {int(a['similarity'] * 100)}% | {a.get('category', '未分類')}\n"
            msg += f"   {a['url']}\n\n"

        user = await bot.fetch_user(int(discord_id))
        await user.send(msg)

        # 8. 更新 last_proactive_dm_at
        await _update_last_dm(supabase, user_id)

        logger.info(
            f"Sent reminder to {discord_id} ({len(suggestions)} articles, trigger={trigger})"
        )

    except Exception as e:
        logger.warning(f"Failed to send reminder to {discord_id}: {e}")
