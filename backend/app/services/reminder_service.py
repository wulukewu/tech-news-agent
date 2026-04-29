"""
Reminder Service - 基於 embedding 相似度的智能提醒
當用戶加入文章到 reading list 或評高分時，找相似文章透過 Discord DM 通知
"""
import json
import logging
from uuid import UUID

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.72
MAX_SUGGESTIONS = 3


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

        # 1. 取得觸發文章的 embedding 和標題
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

        # 2. 取得用戶已在 reading list 的文章 ID（避免重複推薦）
        user_uuid = await supabase.get_or_create_user(discord_id)
        existing_res = (
            supabase.client.table("reading_list")
            .select("article_id")
            .eq("user_id", str(user_uuid))
            .execute()
        )
        existing_ids = {row["article_id"] for row in (existing_res.data or [])}

        # 3. 向量相似度搜尋
        similar_res = supabase.client.rpc(
            "match_articles",
            {
                "query_embedding": embedding,
                "match_threshold": SIMILARITY_THRESHOLD,
                "match_count": MAX_SUGGESTIONS + 5,  # 多取幾個以便過濾
            },
        ).execute()

        if not similar_res.data:
            return

        # 4. 過濾掉自身和已在 reading list 的文章
        suggestions = [
            a
            for a in similar_res.data
            if a["id"] != str(article_id) and a["id"] not in existing_ids
        ][:MAX_SUGGESTIONS]

        if not suggestions:
            return

        # 5. 確認用戶有開啟 DM 通知
        dm_enabled = await supabase.get_notification_settings(discord_id)
        if not dm_enabled:
            return

        # 6. 組裝訊息並發送
        trigger_text = "加入閱讀清單" if trigger == "added" else "評為高分"
        msg = f"📚 **智能提醒** — 根據你{trigger_text}的文章\n"
        msg += f"**{article_title[:60]}{'...' if len(article_title) > 60 else ''}**\n\n"
        msg += "你可能也會喜歡這些相關文章：\n\n"

        for i, a in enumerate(suggestions, 1):
            similarity_pct = int(a["similarity"] * 100)
            msg += f"{i}. **{a['title'][:70]}{'...' if len(a['title']) > 70 else ''}**\n"
            msg += f"   相似度 {similarity_pct}% | {a.get('category', '未分類')}\n"
            msg += f"   {a['url']}\n\n"

        # 透過 bot 發送 DM
        from app.bot.client import bot

        if not bot or not bot.is_ready():
            logger.warning("Bot not ready, skipping reminder DM")
            return

        user = await bot.fetch_user(int(discord_id))
        await user.send(msg)
        logger.info(f"Sent similar articles reminder to {discord_id} ({len(suggestions)} articles)")

    except Exception as e:
        # 提醒是非關鍵功能，失敗不影響主流程
        logger.warning(f"Failed to send reminder to {discord_id}: {e}")
