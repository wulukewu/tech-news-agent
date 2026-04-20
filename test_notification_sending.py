#!/usr/bin/env python3
"""
測試通知發送功能
驗證測試通知是否能正確發送到Discord
"""

import asyncio
import sys
from uuid import uuid4

# 添加後端路徑到 Python path
sys.path.append('backend')

from app.services.supabase_service import SupabaseService
from app.services.notification_settings_service import NotificationSettingsService


async def test_notification_sending():
    """測試通知發送功能"""
    print("🧪 開始測試通知發送功能...")

    try:
        # 初始化服務
        supabase = SupabaseService()
        notification_service = NotificationSettingsService(supabase)

        # 獲取一個真實用戶來測試
        users_response = supabase.client.table('users').select('id, discord_id, dm_enabled').limit(1).execute()

        if not users_response.data:
            print("❌ 沒有找到用戶進行測試")
            return False

        user = users_response.data[0]
        user_id = user['id']
        discord_id = user['discord_id']

        print(f"📝 使用測試用戶: {discord_id}")

        # 檢查用戶是否啟用了DM通知
        if not user.get('dm_enabled', True):
            print("⚠️  用戶的DM通知已停用，跳過測試")
            return True

        print("📤 發送測試通知...")

        # 發送測試通知
        await notification_service.send_test_notification(user_id)

        print("✅ 測試通知發送成功！")
        print(f"請檢查Discord用戶 {discord_id} 是否收到測試消息")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_discord_bot_connection():
    """測試Discord bot連接"""
    print("\n🤖 測試Discord bot連接...")

    try:
        from app.bot.client import bot

        if bot.is_ready():
            print("✅ Discord bot已連接並準備就緒")
            print(f"Bot用戶: {bot.user}")
            return True
        else:
            print("⚠️  Discord bot未準備就緒")
            print("請確保Discord bot正在運行")
            return False

    except Exception as e:
        print(f"❌ Discord bot連接測試失敗: {e}")
        return False


async def test_notification_service_integration():
    """測試通知服務集成"""
    print("\n🔗 測試通知服務集成...")

    try:
        from app.services.notification_service import NotificationService
        from app.bot.client import bot

        supabase = SupabaseService()
        notification_service = NotificationService(supabase, bot_client=bot)

        print("✅ NotificationService 初始化成功")

        # 測試一個簡單的Discord DM發送（使用測試用戶ID）
        users_response = supabase.client.table('users').select('id, discord_id').limit(1).execute()

        if users_response.data:
            user = users_response.data[0]
            user_id = user['id']

            print(f"📤 測試發送Discord DM到用戶 {user['discord_id']}...")

            test_message = "🔧 **系統測試**\n\n這是一個系統測試消息，用來驗證Discord通知功能。"

            success = await notification_service.send_discord_dm(user_id, test_message)

            if success:
                print("✅ Discord DM發送成功")
                return True
            else:
                print("❌ Discord DM發送失敗")
                return False
        else:
            print("⚠️  沒有找到測試用戶")
            return False

    except Exception as e:
        print(f"❌ 通知服務集成測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Tech News Agent - 通知發送測試")
    print("=" * 50)

    loop = asyncio.get_event_loop()

    # 測試1: Discord bot連接
    bot_ok = loop.run_until_complete(test_discord_bot_connection())

    # 測試2: 通知服務集成
    if bot_ok:
        service_ok = loop.run_until_complete(test_notification_service_integration())

        # 測試3: 完整的測試通知功能
        if service_ok:
            notification_ok = loop.run_until_complete(test_notification_sending())

            if notification_ok:
                print("\n🎉 所有測試通過！測試通知功能正常工作。")
                sys.exit(0)
            else:
                print("\n💥 測試通知功能失敗")
                sys.exit(1)
        else:
            print("\n💥 通知服務集成測試失敗")
            sys.exit(1)
    else:
        print("\n💥 Discord bot連接測試失敗")
        print("請確保Discord bot正在運行並已連接")
        sys.exit(1)
