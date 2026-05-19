"""測試 Discord 提醒通知"""

import asyncio
import sys

sys.path.insert(0, "/app")

import pytest

from app.services.reminder_notification_service import ReminderNotificationService
from app.services.supabase_service import SupabaseService

pytestmark = pytest.mark.skip(reason="requires real Supabase/network connection")


async def test_notification():
    print("🧪 測試 Discord 提醒通知\n")

    supabase = SupabaseService()
    service = ReminderNotificationService()

    # 獲取有待處理提醒的用戶
    pending = (
        supabase.client.table("reminder_log")
        .select("user_id")
        .eq("status", "pending")
        .limit(1)
        .execute()
    )

    if not pending.data:
        print("❌ 沒有待處理的提醒")
        return

    user_id = pending.data[0]["user_id"]
    print(f"✅ 測試用戶: {user_id}")

    # 檢查待處理提醒數量
    count_result = (
        supabase.client.table("reminder_log")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("status", "pending")
        .execute()
    )
    print(f"📊 待處理提醒數量: {count_result.count}")

    # 發送提醒
    print("\n📤 發送提醒到 Discord DM...")
    sent_count = await service.send_pending_reminders(user_id)

    if sent_count > 0:
        print(f"\n✅ 成功發送 {sent_count} 個提醒！")

        # 檢查狀態更新
        after_count = (
            supabase.client.table("reminder_log")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "sent")
            .execute()
        )
        print(f"📊 已發送提醒數量: {after_count.count}")
    else:
        print("\n⚠️  沒有發送任何提醒")
        print("   可能原因:")
        print("   - Discord bot 未啟動")
        print("   - 用戶 Discord ID 無效")
        print("   - 發送失敗")


if __name__ == "__main__":
    asyncio.run(test_notification())
