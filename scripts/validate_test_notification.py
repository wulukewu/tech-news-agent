#!/usr/bin/env python3
"""
快速驗證測試通知功能
檢查所有必要的組件是否正確配置
"""

import sys
import os

# 添加後端路徑
sys.path.append('backend')

def check_imports():
    """檢查所有必要的導入是否可用"""
    print("🔍 檢查導入...")

    try:
        from app.services.notification_settings_service import NotificationSettingsService
        print("  ✅ NotificationSettingsService")
    except ImportError as e:
        print(f"  ❌ NotificationSettingsService: {e}")
        return False

    try:
        from app.services.notification_service import NotificationService
        print("  ✅ NotificationService")
    except ImportError as e:
        print(f"  ❌ NotificationService: {e}")
        return False

    try:
        from app.bot.client import bot
        print("  ✅ Discord bot client")
    except ImportError as e:
        print(f"  ❌ Discord bot client: {e}")
        return False

    try:
        from app.core.errors import ServiceError, ErrorCode
        print("  ✅ Error classes")
    except ImportError as e:
        print(f"  ❌ Error classes: {e}")
        return False

    return True


def check_method_signature():
    """檢查 send_test_notification 方法簽名"""
    print("\n🔍 檢查方法簽名...")

    try:
        from app.services.notification_settings_service import NotificationSettingsService
        import inspect

        method = getattr(NotificationSettingsService, 'send_test_notification', None)
        if method is None:
            print("  ❌ send_test_notification 方法不存在")
            return False

        sig = inspect.signature(method)
        print(f"  ✅ 方法簽名: {sig}")

        # 檢查方法是否為 async
        if inspect.iscoroutinefunction(method):
            print("  ✅ 方法是異步的")
        else:
            print("  ❌ 方法不是異步的")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 檢查失敗: {e}")
        return False


def check_api_endpoint():
    """檢查 API 端點是否存在"""
    print("\n🔍 檢查 API 端點...")

    api_file = 'backend/app/api/notifications.py'
    if not os.path.exists(api_file):
        print(f"  ❌ API 文件不存在: {api_file}")
        return False

    with open(api_file, 'r') as f:
        content = f.read()

        if '@router.post("/test")' in content:
            print("  ✅ /api/notifications/test 端點存在")
        else:
            print("  ❌ /api/notifications/test 端點不存在")
            return False

        if 'send_test_notification' in content:
            print("  ✅ send_test_notification 函數存在")
        else:
            print("  ❌ send_test_notification 函數不存在")
            return False

    return True


def check_frontend_integration():
    """檢查前端集成"""
    print("\n🔍 檢查前端集成...")

    # 檢查 API 客戶端
    api_file = 'frontend/lib/api/notifications.ts'
    if not os.path.exists(api_file):
        print(f"  ❌ API 客戶端文件不存在: {api_file}")
        return False

    with open(api_file, 'r') as f:
        content = f.read()

        if 'sendTestNotification' in content:
            print("  ✅ sendTestNotification 函數存在")
        else:
            print("  ❌ sendTestNotification 函數不存在")
            return False

        if '/api/notifications/test' in content:
            print("  ✅ API 端點路徑正確")
        else:
            print("  ❌ API 端點路徑不正確")
            return False

    # 檢查組件
    component_file = 'frontend/features/notifications/components/PersonalizedNotificationSettings.tsx'
    if not os.path.exists(component_file):
        print(f"  ❌ 組件文件不存在: {component_file}")
        return False

    with open(component_file, 'r') as f:
        content = f.read()

        if 'sendTestNotification' in content:
            print("  ✅ 組件調用 sendTestNotification")
        else:
            print("  ❌ 組件未調用 sendTestNotification")
            return False

    return True


def main():
    """主函數"""
    print("🚀 Tech News Agent - 測試通知功能驗證")
    print("=" * 60)

    checks = [
        ("導入檢查", check_imports),
        ("方法簽名檢查", check_method_signature),
        ("API 端點檢查", check_api_endpoint),
        ("前端集成檢查", check_frontend_integration),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 執行失敗: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 驗證結果:")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有檢查通過！測試通知功能已正確配置。")
        print("\n📝 下一步:")
        print("  1. 啟動後端服務器: cd backend && uvicorn app.main:app --reload")
        print("  2. 啟動 Discord bot: python3 backend/run_bot.py")
        print("  3. 啟動前端: cd frontend && npm run dev")
        print("  4. 在前端點擊「發送測試通知」按鈕")
        print("  5. 檢查 Discord 私訊是否收到測試消息")
        return 0
    else:
        print("\n💥 部分檢查失敗，請修復上述問題。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
