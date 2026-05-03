# 測試通知功能修復文檔

## 📋 問題描述

用戶報告「發送測試通知」按鈕點擊後沒有實際發送 Discord 消息，只是記錄日誌。

## 🔍 根本原因

`NotificationSettingsService.send_test_notification()` 方法原本只記錄日誌消息，並沒有實際調用 Discord bot 發送 DM。

## ✅ 實施的修復

### 1. 後端修復

**文件**: `backend/app/services/notification_settings_service.py`

**修改內容**:

- 導入 `NotificationService` 和 Discord `bot` 客戶端
- 導入 `ServiceError` 用於錯誤處理
- 實際調用 `NotificationService.send_discord_dm()` 發送測試消息
- 添加成功/失敗的錯誤處理

**修改後的代碼**:

```python
async def send_test_notification(self, user_id: UUID) -> None:
    """
    Send a test notification to the user.

    Args:
        user_id: UUID of the user

    Raises:
        ServiceError: If operation fails
    """
    try:
        self.logger.info("Sending test notification", user_id=str(user_id))

        # Get user's Discord ID
        user_data = await self._get_user_data(user_id)
        discord_id = user_data.get("discord_id")

        if not discord_id:
            raise ValidationError(
                "User not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details={"user_id": str(user_id)},
            )

        # Check if DM notifications are enabled
        dm_enabled = await self._get_dm_enabled_from_preferences(user_id)

        if not dm_enabled:
            raise ValidationError(
                "DM notifications are disabled",
                error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                details={"user_id": str(user_id)},
            )

        # Actually send the test notification via Discord
        from app.services.notification_service import NotificationService
        from app.bot.client import bot
        from app.core.errors import ServiceError

        notification_service = NotificationService(self.supabase_service, bot_client=bot)

        test_message = "🧪 **測試通知**\n\n這是一個測試通知，用來確認您的通知設定正常運作。\n\n如果您收到這條消息，表示通知功能已正確配置！✅"

        success = await notification_service.send_discord_dm(user_id, test_message)

        if success:
            self.logger.info(
                "Test notification sent successfully",
                user_id=str(user_id),
                discord_id=discord_id
            )
        else:
            raise ServiceError(
                "Failed to send test notification via Discord",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                details={"user_id": str(user_id), "discord_id": discord_id},
            )

    except ValidationError:
        raise
    except Exception as e:
        self._handle_error(
            e,
            "Failed to send test notification",
            error_code=ErrorCode.INTERNAL_ERROR,
            context={"user_id": str(user_id)},
        )
```

### 2. 前端改進

**文件**: `frontend/features/notifications/components/PersonalizedNotificationSettings.tsx`

**已有的錯誤處理**:

- 400 錯誤: 通知設定有誤
- 500 錯誤: 服務器錯誤
- 網絡錯誤: 網絡連接問題
- 通用錯誤: 其他失敗情況

### 3. API 端點

**文件**: `backend/app/api/notifications.py`

**端點**: `POST /api/notifications/test`

**功能**:

- 獲取當前用戶
- 調用 `NotificationSettingsService.send_test_notification()`
- 處理各種錯誤情況（ValidationError, ServiceError, 通用錯誤）

## 🧪 驗證工具

### 1. 快速驗證腳本

**文件**: `validate_test_notification.py`

**功能**:

- 檢查所有必要的導入
- 驗證方法簽名
- 確認 API 端點存在
- 檢查前端集成

**運行**:

```bash
python3 validate_test_notification.py
```

### 2. 完整測試腳本

**文件**: `test_notification_sending.py`

**功能**:

- 測試 Discord bot 連接
- 測試通知服務集成
- 測試完整的測試通知功能

**運行**:

```bash
python3 test_notification_sending.py
```

## 📝 測試步驟

### 前置條件

1. **Discord bot 必須運行**:

   ```bash
   python3 backend/run_bot.py
   ```

2. **後端服務器必須運行**:

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **前端必須運行**:
   ```bash
   cd frontend
   npm run dev
   ```

### 測試流程

1. 登入前端應用
2. 導航到「設定」→「通知」
3. 確保「Discord 私訊」已啟用
4. 點擊「發送測試通知」按鈕
5. 檢查 Discord 私訊是否收到測試消息

### 預期結果

**成功情況**:

- 前端顯示: "✅ 測試通知已發送！請檢查您的Discord私訊。"
- Discord 收到消息:

  ```
  🧪 **測試通知**

  這是一個測試通知，用來確認您的通知設定正常運作。

  如果您收到這條消息，表示通知功能已正確配置！✅
  ```

**失敗情況**:

- DM 未啟用: "❌ 通知設定有誤，請檢查您的設定"
- 服務器錯誤: "❌ 服務器錯誤，請稍後再試"
- 網絡錯誤: "❌ 網絡連接錯誤，請檢查網絡"

## 🔧 故障排除

### 問題 1: Discord bot 未連接

**症狀**: 測試通知失敗，錯誤提示 "Bot not available"

**解決方案**:

```bash
# 檢查 bot 是否運行
ps aux | grep run_bot.py

# 如果沒有運行，啟動 bot
python3 backend/run_bot.py
```

### 問題 2: 用戶 DM 已關閉

**症狀**: Discord 返回 "User has DMs disabled or bot is blocked"

**解決方案**:

1. 在 Discord 中啟用私訊
2. 確保沒有封鎖 bot
3. 在伺服器設定中允許來自伺服器成員的私訊

### 問題 3: 用戶未找到

**症狀**: 錯誤提示 "User not found"

**解決方案**:

1. 確保用戶已在資料庫中註冊
2. 檢查用戶的 `discord_id` 是否正確
3. 嘗試重新登入

### 問題 4: DM 通知已停用

**症狀**: 錯誤提示 "DM notifications are disabled"

**解決方案**:

1. 在通知設定頁面啟用「Discord 私訊」
2. 確保 `user_notification_preferences` 表中 `dm_enabled` 為 `true`

## 📊 驗證結果

運行 `validate_test_notification.py` 的輸出:

```
🚀 Tech News Agent - 測試通知功能驗證
============================================================
🔍 檢查導入...
  ✅ NotificationSettingsService
  ✅ NotificationService
  ✅ Discord bot client
  ✅ Error classes

🔍 檢查方法簽名...
  ✅ 方法簽名: (self, user_id: uuid.UUID) -> None
  ✅ 方法是異步的

🔍 檢查 API 端點...
  ✅ /api/notifications/test 端點存在
  ✅ send_test_notification 函數存在

🔍 檢查前端集成...
  ✅ sendTestNotification 函數存在
  ✅ API 端點路徑正確
  ✅ 組件調用 sendTestNotification

============================================================
📊 驗證結果:
============================================================
✅ 通過 - 導入檢查
✅ 通過 - 方法簽名檢查
✅ 通過 - API 端點檢查
✅ 通過 - 前端集成檢查
============================================================

🎉 所有檢查通過！測試通知功能已正確配置。
```

## 🎯 總結

### 修復內容

- ✅ 修改 `send_test_notification()` 實際發送 Discord DM
- ✅ 添加適當的錯誤處理和日誌記錄
- ✅ 前端已有完善的錯誤提示
- ✅ 創建驗證和測試工具

### 影響的文件

1. `backend/app/services/notification_settings_service.py` - 主要修復
2. `validate_test_notification.py` - 新增驗證工具
3. `docs/TEST_NOTIFICATION_FIX.md` - 本文檔

### 下一步

1. 提交更改到版本控制
2. 在開發環境測試功能
3. 部署到生產環境
4. 監控測試通知的成功率

## 📚 相關文檔

- [通知系統修復指南](./notification-system-fixes.md)
- [通知狀態修復指南](../NOTIFICATION_STATUS_FIX_GUIDE.md)
- [通知修復用戶指南](../NOTIFICATION_FIXES_GUIDE.md)
