#!/usr/bin/env python3
"""
通知狀態診斷腳本
檢查為什麼通知顯示為「未排程」
"""

import asyncio
import sys
from uuid import UUID

# 添加後端路徑到 Python path
sys.path.append('backend')

from app.services.supabase_service import SupabaseService
from app.services.preference_service import PreferenceService
from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.tasks.scheduler import get_dynamic_scheduler
from app.services.notification_system_integration import get_notification_system_integration


async def diagnose_notification_status():
    """診斷通知狀態問題"""
    print("🔍 開始診斷通知狀態問題...")

    try:
        # 初始化服務
        supabase = SupabaseService()
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)
        preference_service = PreferenceService(prefs_repo)

        print("\n1️⃣ 檢查動態排程器狀態...")
        dynamic_scheduler = get_dynamic_scheduler()
        if dynamic_scheduler:
            print("✅ 動態排程器已初始化")
        else:
            print("❌ 動態排程器未初始化")
            return False

        print("\n2️⃣ 檢查通知系統集成...")
        integration_service = get_notification_system_integration()
        if integration_service:
            print("✅ 通知系統集成已初始化")
        else:
            print("❌ 通知系統集成未初始化")

        print("\n3️⃣ 檢查用戶偏好設定...")
        # 獲取所有用戶偏好設定
        all_preferences = await prefs_repo.list_all()
        print(f"📊 找到 {len(all_preferences)} 個用戶偏好設定")

        if not all_preferences:
            print("⚠️  沒有找到任何用戶偏好設定")
            return False

        print("\n4️⃣ 檢查個別用戶的排程狀態...")
        for i, prefs in enumerate(all_preferences[:3]):  # 只檢查前3個用戶
            print(f"\n用戶 {i+1}: {prefs.user_id}")
            print(f"  - 頻率: {prefs.frequency}")
            print(f"  - 時間: {prefs.notification_time}")
            print(f"  - 時區: {prefs.timezone}")
            print(f"  - DM啟用: {prefs.dm_enabled}")

            if prefs.frequency == 'disabled' or not prefs.dm_enabled:
                print("  ⚠️  通知已停用，跳過排程檢查")
                continue

            # 檢查排程狀態
            try:
                job_info = await dynamic_scheduler.get_user_job_info(prefs.user_id)
                if job_info:
                    print(f"  ✅ 已排程: {job_info}")
                else:
                    print("  ❌ 未排程")

                    # 嘗試創建排程
                    print("  🔧 嘗試創建排程...")
                    if integration_service:
                        await integration_service.schedule_user_notification(
                            prefs.user_id,
                            prefs.frequency,
                            prefs.notification_time,
                            prefs.timezone
                        )
                        print("  ✅ 排程創建成功")

                        # 再次檢查
                        job_info = await dynamic_scheduler.get_user_job_info(prefs.user_id)
                        if job_info:
                            print(f"  ✅ 確認排程已創建: {job_info}")
                        else:
                            print("  ❌ 排程創建失敗")
                    else:
                        print("  ❌ 無法創建排程：集成服務未初始化")

            except Exception as e:
                print(f"  ❌ 檢查排程時出錯: {e}")

        print("\n5️⃣ 檢查排程器整體狀態...")
        try:
            # 獲取所有排程任務
            jobs = dynamic_scheduler.scheduler.get_jobs()
            print(f"📊 當前排程任務數量: {len(jobs)}")

            for job in jobs[:5]:  # 只顯示前5個任務
                print(f"  - 任務ID: {job.id}")
                print(f"    下次執行: {job.next_run_time}")
                print(f"    觸發器: {job.trigger}")

        except Exception as e:
            print(f"❌ 獲取排程任務時出錯: {e}")

        print("\n🎉 診斷完成！")
        return True

    except Exception as e:
        print(f"❌ 診斷過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


async def fix_notification_scheduling():
    """嘗試修復通知排程問題"""
    print("\n🔧 開始修復通知排程...")

    try:
        # 重新初始化系統
        from app.services.system_initialization import initialize_personalized_notification_system

        supabase = SupabaseService()
        print("🔄 重新初始化個人化通知系統...")

        init_results = await initialize_personalized_notification_system(supabase)

        if init_results.get("success", False):
            print("✅ 系統重新初始化成功")
            print(f"  - 遷移用戶: {init_results.get('migration', {}).get('migrated_count', 0)}")
            print(f"  - 排程用戶: {init_results.get('scheduling', {}).get('scheduled_count', 0)}")
            return True
        else:
            print("❌ 系統重新初始化失敗")
            print(f"結果: {init_results}")
            return False

    except Exception as e:
        print(f"❌ 修復過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Tech News Agent - 通知狀態診斷工具")
    print("=" * 50)

    loop = asyncio.get_event_loop()

    # 步驟1: 診斷問題
    diagnosis_ok = loop.run_until_complete(diagnose_notification_status())

    if not diagnosis_ok:
        print("\n💥 診斷發現問題，嘗試修復...")
        # 步驟2: 嘗試修復
        fix_ok = loop.run_until_complete(fix_notification_scheduling())

        if fix_ok:
            print("\n🎊 修復完成！請重新檢查前端狀態。")
        else:
            print("\n💥 自動修復失敗，需要手動檢查。")
    else:
        print("\n🎊 診斷完成，系統狀態正常！")

    print("\n📋 建議的後續步驟:")
    print("1. 重啟後端服務")
    print("2. 重新載入前端頁面")
    print("3. 檢查通知設定頁面的狀態顯示")
