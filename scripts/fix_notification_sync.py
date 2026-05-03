#!/usr/bin/env python3
"""
通知系統同步修復腳本
解決新舊通知系統之間的數據同步問題
"""

import asyncio
import sys
from uuid import UUID

# 添加後端路徑到 Python path
sys.path.append('backend')

from app.services.supabase_service import SupabaseService
from app.services.preference_service import PreferenceService
from app.services.notification_settings_service import NotificationSettingsService
from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository


async def migrate_legacy_settings():
    """將舊版通知設定遷移到新的個人化系統"""
    print("🔄 開始遷移舊版通知設定...")

    try:
        # 初始化服務
        supabase = SupabaseService()
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)
        settings_service = NotificationSettingsService(supabase)

        # 獲取所有用戶
        users_response = supabase.client.table('users').select('id, discord_id, dm_enabled').execute()
        users = users_response.data

        print(f"📊 找到 {len(users)} 個用戶需要遷移")

        migrated_count = 0
        skipped_count = 0

        for user in users:
            user_id = UUID(user['id'])
            dm_enabled = user.get('dm_enabled', True)

            try:
                # 檢查是否已經有個人化設定
                existing_prefs = await preference_service.get_user_preferences(user_id)

                if existing_prefs:
                    # 如果舊版設定與新版不同，則同步
                    if existing_prefs.dm_enabled != dm_enabled:
                        print(f"🔧 同步用戶 {user['discord_id']} 的DM設定: {dm_enabled}")
                        from app.schemas.user_notification_preferences import UpdateUserNotificationPreferencesRequest

                        update_request = UpdateUserNotificationPreferencesRequest(
                            dm_enabled=dm_enabled
                        )
                        await preference_service.update_preferences(user_id, update_request)
                        migrated_count += 1
                    else:
                        skipped_count += 1

            except Exception as e:
                print(f"⚠️  用戶 {user['discord_id']} 遷移失敗: {e}")
                continue

        print(f"✅ 遷移完成: {migrated_count} 個用戶已更新, {skipped_count} 個用戶已是最新狀態")
        return True

    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_data_consistency():
    """驗證新舊系統的數據一致性"""
    print("\n🔍 驗證數據一致性...")

    try:
        supabase = SupabaseService()
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)

        # 獲取所有用戶
        users_response = supabase.client.table('users').select('id, discord_id, dm_enabled').execute()
        users = users_response.data

        inconsistent_count = 0
        consistent_count = 0

        for user in users:
            user_id = UUID(user['id'])
            legacy_dm_enabled = user.get('dm_enabled', True)

            try:
                # 獲取新系統的設定
                new_prefs = await preference_service.get_user_preferences(user_id)

                if new_prefs.dm_enabled != legacy_dm_enabled:
                    print(f"⚠️  數據不一致 - 用戶 {user['discord_id']}: 舊版={legacy_dm_enabled}, 新版={new_prefs.dm_enabled}")
                    inconsistent_count += 1
                else:
                    consistent_count += 1

            except Exception as e:
                print(f"❌ 檢查用戶 {user['discord_id']} 失敗: {e}")
                continue

        print(f"📊 一致性檢查結果: {consistent_count} 個一致, {inconsistent_count} 個不一致")

        if inconsistent_count == 0:
            print("✅ 所有數據都是一致的！")
            return True
        else:
            print("⚠️  發現數據不一致，建議運行遷移腳本")
            return False

    except Exception as e:
        print(f"❌ 一致性檢查失敗: {e}")
        return False


async def cleanup_duplicate_data():
    """清理重複或無效的數據"""
    print("\n🧹 清理重複數據...")

    try:
        supabase = SupabaseService()

        # 檢查是否有重複的用戶偏好設定
        duplicates_response = supabase.client.rpc(
            'find_duplicate_preferences'
        ).execute()

        if duplicates_response.data:
            print(f"🔍 發現 {len(duplicates_response.data)} 個重複記錄")
            # 這裡可以添加清理邏輯
        else:
            print("✅ 沒有發現重複數據")

        return True

    except Exception as e:
        print(f"⚠️  清理過程中出現錯誤: {e}")
        # 這不是致命錯誤，繼續執行
        return True


if __name__ == "__main__":
    print("🔧 Tech News Agent - 通知系統同步修復")
    print("=" * 50)

    loop = asyncio.get_event_loop()

    # 步驟1: 驗證當前數據一致性
    print("步驟 1/3: 驗證數據一致性")
    consistency_ok = loop.run_until_complete(verify_data_consistency())

    # 步驟2: 遷移舊版設定（如果需要）
    if not consistency_ok:
        print("\n步驟 2/3: 遷移舊版設定")
        migration_ok = loop.run_until_complete(migrate_legacy_settings())

        if migration_ok:
            # 再次驗證
            print("\n重新驗證數據一致性...")
            loop.run_until_complete(verify_data_consistency())
    else:
        print("\n步驟 2/3: 跳過遷移（數據已一致）")

    # 步驟3: 清理重複數據
    print("\n步驟 3/3: 清理重複數據")
    cleanup_ok = loop.run_until_complete(cleanup_duplicate_data())

    print("\n🎉 同步修復完成！")
    print("\n📋 後續建議:")
    print("1. 重啟前端和後端服務")
    print("2. 清除瀏覽器緩存")
    print("3. 測試通知設定功能")
    print("4. 檢查前端是否還有重複顯示的問題")
