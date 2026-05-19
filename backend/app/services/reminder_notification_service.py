"""
Reminder Notification Service - 發送智能提醒到 Discord DM
"""

import logging
from uuid import UUID

from app.services.notification_service import NotificationService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class ReminderNotificationService:
    """處理提醒通知的發送"""

    def __init__(self):
        from app.bot.client import bot

        self.notification_service = NotificationService(bot=bot)
        self.supabase = SupabaseService()

    async def send_pending_reminders(self, user_id: str) -> int:
        """
        發送用戶的待處理提醒

        Args:
            user_id: 用戶 ID

        Returns:
            成功發送的提醒數量
        """
        try:
            # 獲取待處理的提醒
            result = (
                self.supabase.client.table("reminder_log")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .order("sent_at", desc=True)
                .limit(5)  # 一次最多發送 5 個
                .execute()
            )

            if not result.data:
                logger.debug(f"No pending reminders for user {user_id}")
                return 0

            sent_count = 0
            for reminder in result.data:
                success = await self._send_reminder_dm(user_id, reminder)
                if success:
                    sent_count += 1
                    # 更新狀態為已發送
                    self.supabase.client.table("reminder_log").update({"status": "sent"}).eq(
                        "id", reminder["id"]
                    ).execute()

            logger.info(f"Sent {sent_count}/{len(result.data)} reminders to user {user_id}")
            return sent_count

        except Exception as e:
            logger.error(f"Error sending reminders to user {user_id}: {e}")
            return 0

    async def _send_reminder_dm(self, user_id: str, reminder: dict) -> bool:
        """
        發送單個提醒到 Discord DM

        Args:
            user_id: 用戶 ID
            reminder: 提醒記錄

        Returns:
            是否成功發送
        """
        try:
            context = reminder.get("reminder_context", {})
            title = context.get("title", "New Article")
            description = context.get("description", "")
            priority = context.get("priority_score", 0.5)
            reading_time = context.get("reading_time_estimate", 5)
            action_url = context.get("action_url", "")

            # 構建 Discord 訊息
            message = self._format_reminder_message(
                title, description, priority, reading_time, action_url
            )

            # 發送 DM
            user_uuid = UUID(user_id)
            success = await self.notification_service.send_discord_dm(user_uuid, message)

            return success

        except Exception as e:
            logger.error(f"Error sending reminder DM: {e}")
            return False

    def _format_reminder_message(
        self, title: str, description: str, priority: float, reading_time: int, url: str
    ) -> str:
        """格式化提醒訊息 — 簡潔自然風格"""
        message = f"📌 **{title}**\n"
        message += f"{description}\n"
        message += f"⏱️ 約 {reading_time} 分鐘"
        if url:
            message += f"\n{url}"
        return message


async def send_reminders_for_user(user_id: str) -> int:
    """
    便捷函數：為用戶發送待處理的提醒

    Args:
        user_id: 用戶 ID

    Returns:
        成功發送的提醒數量
    """
    service = ReminderNotificationService()
    return await service.send_pending_reminders(user_id)
