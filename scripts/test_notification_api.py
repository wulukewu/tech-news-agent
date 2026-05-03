#!/usr/bin/env python3
"""
簡單的通知API測試腳本
測試新的個人化通知設定功能是否正常工作
"""

import asyncio
import json
import sys
from uuid import uuid4

# 添加後端路徑到 Python path
sys.path.append('backend')

from app.services.supabase_service import SupabaseService
from app.services.preference_service import PreferenceService
from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.schemas.user_notification_preferences import UpdateUserNotificationPreferencesRequest


async def test_notification_preferences():
    """測試通知偏好設定的基本功能"""
    print("🧪 開始測試通知偏好設定功能...")

    try:
        # 初始化服務
        supabase = SupabaseService()
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)

        # 創建測試用戶ID
        test_user_id = uuid4()
        print(f"📝 使用測試用戶ID: {test_user_id}")

        # 測試1: 獲取默認偏好設定
        print("\n1️⃣ 測試獲取默認偏好設定...")
        preferences = await preference_service.get_user_preferences(test_user_id)
        print(f"✅ 默認偏好設定: {preferences}")

        # 測試2: 更新偏好設定
        print("\n2️⃣ 測試更新偏好設定...")
        update_request = UpdateUserNotificationPreferencesRequest(
            frequency='daily',
            notification_time='09:00',
            timezone='Asia/Tokyo',
            dm_enabled=True,
            email_enabled=False
        )

        updated_preferences = await preference_service.update_preferences(
            test_user_id,
            update_request
        )
        print(f"✅ 更新後的偏好設定: {updated_preferences}")

        # 測試3: 驗證更新是否成功
        print("\n3️⃣ 驗證更新是否成功...")
        retrieved_preferences = await preference_service.get_user_preferences(test_user_id)

        assert retrieved_preferences.frequency == 'daily'
        assert retrieved_preferences.notification_time == '09:00:00'
        assert retrieved_preferences.timezone == 'Asia/Tokyo'
        assert retrieved_preferences.dm_enabled == True
        assert retrieved_preferences.email_enabled == False

        print("✅ 所有驗證通過！")

        # 測試4: 測試驗證功能
        print("\n4️⃣ 測試驗證功能...")
        try:
            invalid_request = UpdateUserNotificationPreferencesRequest(
                frequency='invalid_frequency',  # 無效的頻率
                notification_time='25:00',      # 無效的時間
                timezone='Invalid/Timezone'    # 無效的時區
            )
            await preference_service.update_preferences(test_user_id, invalid_request)
            print("❌ 驗證功能失敗 - 應該拒絕無效數據")
        except Exception as e:
            print(f"✅ 驗證功能正常 - 正確拒絕無效數據: {e}")

        print("\n🎉 所有測試通過！通知偏好設定功能正常工作。")
        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """測試API端點是否正常響應"""
    print("\n🌐 測試API端點...")

    try:
        import aiohttp

        # 測試健康檢查端點
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/api/health') as response:
                if response.status == 200:
                    print("✅ 後端API服務正常運行")
                    return True
                else:
                    print(f"❌ 後端API服務異常: {response.status}")
                    return False

    except Exception as e:
        print(f"⚠️  無法連接到後端API服務: {e}")
        print("請確保後端服務正在運行 (python -m uvicorn app.main:app --reload)")
        return False


if __name__ == "__main__":
    print("🚀 Tech News Agent - 通知系統測試")
    print("=" * 50)

    # 運行測試
    loop = asyncio.get_event_loop()

    # 測試API連接
    api_ok = loop.run_until_complete(test_api_endpoints())

    if api_ok:
        # 測試通知偏好設定功能
        prefs_ok = loop.run_until_complete(test_notification_preferences())

        if prefs_ok:
            print("\n🎊 所有測試完成！系統運行正常。")
            sys.exit(0)
        else:
            print("\n💥 偏好設定測試失敗")
            sys.exit(1)
    else:
        print("\n💥 API連接測試失敗")
        sys.exit(1)
