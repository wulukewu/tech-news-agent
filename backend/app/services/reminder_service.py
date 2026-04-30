"""
Reminder Service - 基於 embedding 相似度的智能提醒
當用戶加入文章到 reading list 或評高分時，找相似文章透過 Discord DM 通知
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
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
        if settings["reminder_cooldown_hours"] > 0:  # 0 = no cooldown
            if await _check_cooldown(supabase, user_id, settings["reminder_cooldown_hours"]):
                logger.debug(f"User {discord_id} in cooldown, skipping reminder")
                return

        # 2.5. 智能時機檢查（避免在用戶不活躍時發送）
        if not await _check_smart_timing(supabase, user_id):
            logger.debug(f"Not optimal timing for user {discord_id}, skipping reminder")
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

        # 6. 向量相似度搜尋（使用個性化閾值）
        personalized_threshold = await get_personalized_similarity_threshold(
            supabase, user_id, settings["reminder_min_similarity"]
        )

        similar_res = supabase.client.rpc(
            "match_articles",
            {
                "query_embedding": embedding,
                "match_threshold": personalized_threshold,
                "match_count": MAX_SUGGESTIONS + 5,
            },
        ).execute()

        if not similar_res.data:
            return

        suggestions = [
            a
            for a in similar_res.data
            if a["id"] != str(article_id) and a["id"] not in existing_ids
        ][
            : MAX_SUGGESTIONS + 5
        ]  # 多取一些，後面再過濾

        # 6.5. 過濾已經推薦過的文章
        suggestions = await _filter_already_seen(supabase, user_id, suggestions)
        suggestions = suggestions[:MAX_SUGGESTIONS]

        if not suggestions:
            return

        # 7. 組裝訊息並發送
        from app.bot.client import bot

        if not bot or not bot.is_ready():
            logger.warning("Bot not ready, skipping reminder DM")
            return

        trigger_text = "加入閱讀清單" if trigger == "added" else "評為高分"
        title_short = article_title[:60] + ("..." if len(article_title) > 60 else "")
        msg = f"**智能提醒** — 根據你{trigger_text}的文章\n**{title_short}**\n\n"
        msg += "你可能也會喜歡這些相關文章：\n\n"

        for i, a in enumerate(suggestions, 1):
            t = a["title"][:70] + ("..." if len(a["title"]) > 70 else "")
            similarity_pct = int(a["similarity"] * 100)
            msg += f"{i}. **{t}**\n"
            msg += f"   相似度 {similarity_pct}% | 分類 {a.get('category', '未分類')}\n"
            msg += f"   {a['url']}\n\n"

        msg += "**幫助改進推薦**：如果推薦不準確，請在網站設定中提供反饋！"

        user = await bot.fetch_user(int(discord_id))
        await user.send(msg)

        # 8. 更新 last_proactive_dm_at
        await _update_last_dm(supabase, user_id)

        logger.info(
            f"Sent reminder to {discord_id} ({len(suggestions)} articles, trigger={trigger})"
        )

        # 9. 記錄提醒日誌用於追蹤效果
        await _log_reminder_sent(supabase, user_id, article_id, suggestions, trigger)

    except Exception as e:
        logger.warning(f"Failed to send reminder to {discord_id}: {e}")


async def _log_reminder_sent(
    supabase: SupabaseService,
    user_id: str,
    trigger_article_id: UUID,
    suggestions: List[Dict],
    trigger_type: str,
) -> None:
    """記錄發送的提醒，用於效果追蹤"""
    try:
        logs = []
        for suggestion in suggestions:
            logs.append(
                {
                    "user_id": user_id,
                    "trigger_article_id": str(trigger_article_id),
                    "recommended_article_id": suggestion["id"],
                    "trigger_type": trigger_type,
                    "similarity_score": suggestion["similarity"],
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        if logs:
            supabase.client.table("reminder_logs").insert(logs).execute()
    except Exception as e:
        logger.warning(f"Failed to log reminder: {e}")


async def _check_smart_timing(supabase: SupabaseService, user_id: str) -> bool:
    """檢查是否為用戶活躍時間，避免在不活躍時發送"""
    try:
        now = datetime.now(timezone.utc)
        hour = now.hour
        day_of_week = now.weekday()  # 0=Monday, 6=Sunday

        # 查詢用戶在這個時間段的活躍度
        activity_res = (
            supabase.client.table("user_activity_patterns")
            .select("activity_count")
            .eq("user_id", user_id)
            .eq("hour_of_day", hour)
            .eq("day_of_week", day_of_week)
            .maybe_single()
            .execute()
        )

        # 如果沒有活躍記錄，或活躍度很低，延遲發送
        if not activity_res.data or activity_res.data.get("activity_count", 0) < 3:
            return False

        return True
    except Exception:
        return True  # 默認允許發送


async def _filter_already_seen(
    supabase: SupabaseService, user_id: str, suggestions: List[Dict]
) -> List[Dict]:
    """過濾掉用戶已經看過或已推薦過的文章"""
    try:
        # 獲取最近30天已推薦的文章
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        recommended_res = (
            supabase.client.table("reminder_logs")
            .select("recommended_article_id")
            .eq("user_id", user_id)
            .gte("sent_at", thirty_days_ago.isoformat())
            .execute()
        )

        recommended_ids = {row["recommended_article_id"] for row in (recommended_res.data or [])}

        # 過濾掉已推薦的文章
        filtered = [s for s in suggestions if s["id"] not in recommended_ids]
        return filtered

    except Exception:
        return suggestions


async def get_reminder_stats(user_id: str) -> Dict:
    """獲取用戶的提醒統計數據"""
    try:
        supabase = SupabaseService()

        # 本週發送次數
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        week_stats = (
            supabase.client.table("reminder_logs")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("sent_at", week_ago.isoformat())
            .execute()
        )

        # 點擊率統計
        click_stats = (
            supabase.client.table("reminder_logs")
            .select("clicked_at", count="exact")
            .eq("user_id", user_id)
            .gte("sent_at", week_ago.isoformat())
            .is_("clicked_at", "not.null")
            .execute()
        )

        # 最近一次提醒
        last_reminder = (
            supabase.client.table("reminder_logs")
            .select("sent_at, trigger_type")
            .eq("user_id", user_id)
            .order("sent_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )

        total_sent = week_stats.count or 0
        total_clicked = click_stats.count or 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0

        return {
            "week_sent_count": total_sent,
            "week_click_count": total_clicked,
            "click_rate": round(click_rate, 1),
            "last_reminder_at": last_reminder.data.get("sent_at") if last_reminder.data else None,
            "last_reminder_type": last_reminder.data.get("trigger_type")
            if last_reminder.data
            else None,
        }

    except Exception as e:
        logger.warning(f"Failed to get reminder stats: {e}")
        return {
            "week_sent_count": 0,
            "week_click_count": 0,
            "click_rate": 0,
            "last_reminder_at": None,
            "last_reminder_type": None,
        }


async def record_reminder_click(user_id: str, article_id: str) -> None:
    """記錄用戶點擊了推薦文章"""
    try:
        supabase = SupabaseService()

        # 更新最近的提醒記錄
        supabase.client.table("reminder_logs").update(
            {"clicked_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_id", user_id).eq("recommended_article_id", article_id).is_(
            "clicked_at", "null"
        ).execute()

    except Exception as e:
        logger.warning(f"Failed to record reminder click: {e}")


async def get_personalized_similarity_threshold(
    supabase: SupabaseService, user_id: str, base_threshold: float
) -> float:
    """基於用戶反饋動態調整相似度閾值"""
    try:
        # 獲取最近30天的反饋統計
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        feedback_stats = (
            supabase.client.table("reminder_logs")
            .select("user_feedback, similarity_score")
            .eq("user_id", user_id)
            .gte("sent_at", thirty_days_ago.isoformat())
            .is_("user_feedback", "not.null")
            .execute()
        )

        if not feedback_stats.data or len(feedback_stats.data) < 5:
            return base_threshold  # 反饋不足，使用基礎閾值

        accurate_scores = []
        inaccurate_scores = []

        for record in feedback_stats.data:
            score = record["similarity_score"]
            feedback = record["user_feedback"]

            if feedback == "accurate":
                accurate_scores.append(score)
            elif feedback in ["inaccurate", "not_interested"]:
                inaccurate_scores.append(score)

        # 如果準確推薦的平均相似度較低，降低閾值
        # 如果不準確推薦較多，提高閾值
        if accurate_scores and inaccurate_scores:
            avg_accurate = sum(accurate_scores) / len(accurate_scores)
            avg_inaccurate = sum(inaccurate_scores) / len(inaccurate_scores)

            # 動態調整：準確推薦平均分數低 -> 降低閾值；不準確推薦多 -> 提高閾值
            adjustment = (avg_accurate - avg_inaccurate) * 0.1
            adjusted_threshold = max(0.5, min(0.95, base_threshold + adjustment))

            logger.info(
                f"Personalized threshold for user {user_id}: {base_threshold} -> {adjusted_threshold}"
            )
            return adjusted_threshold

        return base_threshold

    except Exception as e:
        logger.warning(f"Failed to get personalized threshold: {e}")
        return base_threshold


async def record_user_feedback(user_id: str, article_id: str, feedback: str) -> None:
    """記錄用戶對推薦的反饋"""
    try:
        supabase = SupabaseService()

        supabase.client.table("reminder_logs").update({"user_feedback": feedback}).eq(
            "user_id", user_id
        ).eq("recommended_article_id", article_id).execute()

    except Exception as e:
        logger.warning(f"Failed to record user feedback: {e}")
