"""測試提醒觸發機制"""
import asyncio
import sys

sys.path.insert(0, "/app")

from uuid import UUID

from app.api.reading_list import _fire_reminder
from app.services.supabase_service import SupabaseService


async def test_trigger():
    print("🧪 測試提醒觸發機制\n")

    # 獲取測試數據
    supabase = SupabaseService()

    # 獲取一個用戶
    users = supabase.client.table("users").select("discord_id").limit(1).execute()
    if not users.data:
        print("❌ 沒有用戶")
        return

    discord_id = users.data[0]["discord_id"]
    print(f"✅ 測試用戶: {discord_id}")

    # 獲取一篇文章
    articles = supabase.client.table("articles").select("id, title").limit(1).execute()
    if not articles.data:
        print("❌ 沒有文章")
        return

    article_id = UUID(articles.data[0]["id"])
    article_title = articles.data[0]["title"]
    print(f"✅ 測試文章: {article_title[:50]}...")

    # 檢查提醒記錄數量（觸發前）
    user_uuid = await supabase.get_or_create_user(discord_id)
    before_count = (
        supabase.client.table("reminder_log")
        .select("id", count="exact")
        .eq("user_id", str(user_uuid))
        .execute()
    )
    print(f"\n📊 觸發前提醒數量: {before_count.count}")

    # 觸發提醒
    print("\n🔥 觸發提醒機制...")
    await _fire_reminder(discord_id, article_id, "added")

    # 等待一下讓背景任務完成
    await asyncio.sleep(2)

    # 檢查提醒記錄數量（觸發後）
    after_count = (
        supabase.client.table("reminder_log")
        .select("id", count="exact")
        .eq("user_id", str(user_uuid))
        .execute()
    )
    print(f"📊 觸發後提醒數量: {after_count.count}")

    new_reminders = after_count.count - before_count.count
    if new_reminders > 0:
        print(f"\n✅ 成功生成 {new_reminders} 個新提醒！")

        # 顯示最新的提醒
        latest = (
            supabase.client.table("reminder_log")
            .select("*")
            .eq("user_id", str(user_uuid))
            .order("sent_at", desc=True)
            .limit(3)
            .execute()
        )

        print("\n最新提醒:")
        for r in latest.data[:3]:
            ctx = r.get("reminder_context", {})
            print(f"  - {ctx.get('title', 'N/A')[:50]}")
            print(f"    優先級: {ctx.get('priority_score', 0):.2f}")
    else:
        print("\n⚠️  沒有生成新提醒")
        print("   可能原因:")
        print("   - 提醒功能被停用")
        print("   - 沒有合適的候選文章")
        print("   - 已經有足夠的提醒")


if __name__ == "__main__":
    asyncio.run(test_trigger())
