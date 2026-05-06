"""測試智能提醒生成器"""
import asyncio
import sys

sys.path.insert(0, "/app")

import pytest

from app.services.intelligent_reminder_generator import IntelligentReminderGenerator
from app.services.supabase_service import SupabaseService

pytestmark = pytest.mark.skip(reason="requires real Supabase/network connection")


async def test_reminder_generation():
    print("🧪 測試智能提醒生成器\n")

    # 1. 獲取一個測試用戶
    supabase = SupabaseService()
    users = supabase.client.table("users").select("id, discord_id").limit(1).execute()

    if not users.data:
        print("❌ 沒有找到用戶")
        return

    user = users.data[0]
    user_id = str(user["id"])
    print(f"✅ 測試用戶: {user['discord_id']}")
    print(f"   User ID: {user_id}\n")

    # 2. 檢查用戶的閱讀數據
    reading_list = (
        supabase.client.table("reading_list")
        .select("*, articles(title, category)")
        .eq("user_id", user_id)
        .execute()
    )
    print(f"📚 用戶閱讀列表: {len(reading_list.data)} 篇文章")

    if reading_list.data:
        for item in reading_list.data[:3]:
            article = item.get("articles", {})
            rating = item.get("rating", "未評分")
            print(f"   - {article.get('title', 'N/A')[:50]}... (評分: {rating})")
    print()

    # 3. 生成提醒
    print("🤖 開始生成智能提醒...\n")
    generator = IntelligentReminderGenerator()
    reminders = await generator.generate_reminders_for_user(user_id)

    if reminders:
        print(f"✅ 成功生成 {len(reminders)} 個提醒:\n")
        for i, reminder in enumerate(reminders, 1):
            context = reminder.get("reminder_context", {})
            print(f"{i}. {context.get('title', 'N/A')[:60]}")
            print(f"   描述: {context.get('description', 'N/A')[:80]}...")
            print(f"   優先級: {context.get('priority_score', 0):.2f}")
            print(f"   閱讀時間: {context.get('reading_time_estimate', 0)} 分鐘")
            print(f"   狀態: {reminder.get('status', 'N/A')}\n")
    else:
        print("⚠️  沒有生成任何提醒")
        print("   可能原因:")
        print("   - 用戶沒有閱讀歷史")
        print("   - 沒有合適的候選文章")
        print("   - 提醒功能被停用")

    # 4. 檢查資料庫中的提醒
    print("\n📊 檢查資料庫中的提醒記錄:")
    all_reminders = (
        supabase.client.table("reminder_log")
        .select("*")
        .eq("user_id", user_id)
        .order("sent_at", desc=True)
        .limit(5)
        .execute()
    )
    print(f"   總共 {len(all_reminders.data)} 條提醒記錄")


if __name__ == "__main__":
    asyncio.run(test_reminder_generation())
