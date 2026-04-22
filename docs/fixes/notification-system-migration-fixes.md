# 通知系統遷移修復文檔

## 📋 問題總結

在將通知系統從舊的 `users` 表遷移到新的 `user_notification_preferences` 表後，出現了多個問題：

1. **排程持久性問題**: 服務重啟後排程丟失，顯示「未排程」
2. **資料庫欄位錯誤**: 查詢不存在的欄位導致錯誤
3. **用戶偏好設定不存在**: 更新時找不到記錄
4. **測試通知失敗**: 無法發送測試通知

## 🔍 根本原因

### 1. 排程持久性問題

**原因**: APScheduler 沒有持久化存儲，服務重啟時所有排程丟失

**影響**: 用戶設定通知後，服務重啟會導致排程消失

### 2. 資料庫欄位錯誤

**原因**: `NotificationSettingsService` 仍在查詢舊的欄位：

- `notification_frequency`
- `min_tinkering_index`
- `quiet_hours_enabled`
- `quiet_hours_start`
- `quiet_hours_end`

這些欄位已經不在 `users` 表中了。

**錯誤訊息**:

```
column users.notification_frequency does not exist
```

### 3. 用戶偏好設定不存在

**原因**: 當用戶第一次更新偏好設定時，`user_notification_preferences` 表中還沒有記錄

**錯誤訊息**:

```
User notification preferences not found for user bc627dfa-7101-4e98-8e92-bbc02f97e7cd
```

## ✅ 實施的修復

### 修復 1: 排程持久化

**文件**:

- `backend/app/services/dynamic_scheduler.py`
- `backend/app/repositories/user_notification_preferences.py`
- `backend/app/main.py`

**修改內容**:

1. **添加恢復排程方法** (`dynamic_scheduler.py`):

```python
async def restore_all_user_schedules(self) -> dict:
    """
    Restore notification schedules for all users from database.
    """
    # Get all active preferences from database
    all_preferences = await prefs_repo.get_all_active_preferences()

    # Restore each user's schedule
    for preferences in all_preferences:
        if preferences.frequency != "disabled" and preferences.dm_enabled:
            await self.schedule_user_notification(preferences.user_id, preferences)
```

2. **添加查詢活躍偏好設定** (`user_notification_preferences.py`):

```python
async def get_all_active_preferences(self) -> list[UserNotificationPreferences]:
    """
    Get all active user notification preferences.
    """
    response = (
        self.client.table(self.table_name)
        .select("*")
        .neq("frequency", "disabled")
        .eq("dm_enabled", True)
        .execute()
    )
    return [self._map_to_entity(row) for row in response.data]
```

3. **在啟動時調用恢復** (`main.py`):

```python
# Restore all user notification schedules from database
try:
    logger.info("Restoring user notification schedules from database...")
    restore_stats = await dynamic_scheduler.restore_all_user_schedules()
    logger.info(
        f"User notification schedules restored: "
        f"{restore_stats['restored']} restored, "
        f"{restore_stats['skipped']} skipped, "
        f"{restore_stats['failed']} failed"
    )
except Exception as e:
    logger.error(f"Failed to restore user notification schedules: {e}", exc_info=True)
```

### 修復 2: 資料庫欄位錯誤

**文件**: `backend/app/services/notification_settings_service.py`

**修改內容**:

1. **簡化 `_get_user_data` 方法**:

```python
async def _get_user_data(self, user_id: UUID) -> dict:
    """Get user data from database."""
    # Only query fields that actually exist in users table
    response = (
        self.supabase_service.client.table("users")
        .select("id, discord_id")  # 只查詢存在的欄位
        .eq("id", str(user_id))
        .execute()
    )

    if not response.data:
        return {}

    user_data = response.data[0]
    return {
        "id": user_data["id"],
        "discord_id": user_data["discord_id"],
    }
```

2. **修改 `get_notification_settings` 從新表獲取數據**:

```python
# Get all settings from the new personalized preferences table
prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
preferences = await prefs_repo.get_by_user_id(user_id)

if preferences:
    dm_enabled = preferences.dm_enabled
    frequency = preferences.frequency
else:
    # Use defaults if no preferences exist
    dm_enabled = True
    frequency = "weekly"
```

3. **修改 `update_notification_settings` 更新新表**:

```python
# Update frequency in preferences table if provided
if updates.frequency is not None:
    prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)

    # Get or create preferences
    preferences = await prefs_repo.get_by_user_id(user_id)
    if not preferences:
        preferences = await prefs_repo.create_default_for_user(user_id)

    # Update frequency
    await prefs_repo.update_by_user_id(user_id, {"frequency": updates.frequency})
```

### 修復 3: 用戶偏好設定不存在

**文件**: `backend/app/services/preference_service.py`

**修改內容**:

1. **在更新前確保記錄存在**:

```python
async def update_preferences(self, user_id: UUID, updates: ...) -> ...:
    # Ensure user has preferences (create if not exists)
    old_preferences = await self.preferences_repo.get_by_user_id(user_id)
    if not old_preferences:
        self.logger.info("Creating default preferences before update", user_id=str(user_id))
        old_preferences = await self.create_default_preferences(user_id)

    # Convert request to update data
    update_data = {}
    # ... build update_data ...

    # If no fields to update, return existing preferences
    if not update_data:
        self.logger.info("No fields to update, returning existing preferences")
        return old_preferences

    # Update preferences
    updated_preferences = await self.preferences_repo.update_by_user_id(user_id, update_data)
```

2. **處理空更新**:

- 如果 `update_data` 為空（所有字段都是 None），直接返回現有偏好設定
- 避免調用 `update_by_user_id` 導致錯誤

## 📊 修復效果

### 修復前

| 問題         | 症狀                         | 影響              |
| ------------ | ---------------------------- | ----------------- |
| 排程丟失     | 服務重啟後顯示「未排程」     | 用戶需要重新設定  |
| 欄位錯誤     | `column does not exist` 錯誤 | 無法獲取/更新設定 |
| 記錄不存在   | `User not found` 錯誤        | 無法更新偏好設定  |
| 測試通知失敗 | 無法發送測試消息             | 用戶無法驗證設定  |

### 修復後

| 功能       | 狀態    | 說明               |
| ---------- | ------- | ------------------ |
| 排程持久化 | ✅ 正常 | 服務重啟後自動恢復 |
| 獲取設定   | ✅ 正常 | 從新表正確讀取     |
| 更新設定   | ✅ 正常 | 自動創建記錄       |
| 測試通知   | ✅ 正常 | 可以發送測試消息   |

## 🧪 測試步驟

### 1. 測試排程持久化

```bash
# 1. 設定通知頻率
# 2. 確認顯示「已排程」
# 3. 重啟後端服務
docker-compose restart backend
# 4. 刷新前端頁面
# 5. 應該仍然顯示「已排程」✅
```

### 2. 測試新用戶設定

```bash
# 1. 使用新用戶登入（沒有偏好設定記錄）
# 2. 嘗試更新通知頻率
# 3. 應該自動創建記錄並更新成功✅
```

### 3. 測試通知發送

```bash
# 1. 點擊「發送測試通知」按鈕
# 2. 應該收到 Discord 測試消息✅
```

### 4. 檢查日誌

```bash
# 啟動時應該看到：
# "Restoring user notification schedules from database..."
# "User notification schedules restored: X restored, Y skipped, Z failed"
```

## 🔧 故障排除

### 問題 1: 排程未恢復

**症狀**: 啟動日誌顯示 `restored: 0`

**檢查**:

```sql
-- 檢查是否有活躍的偏好設定
SELECT * FROM user_notification_preferences
WHERE frequency != 'disabled' AND dm_enabled = true;
```

**解決方案**:

- 確保用戶已設定通知頻率
- 確保 `dm_enabled` 為 `true`

### 問題 2: 欄位錯誤仍然出現

**症狀**: 仍然看到 `column does not exist` 錯誤

**檢查**:

- 確認是否還有其他服務在查詢舊欄位
- 搜索代碼中的 `notification_frequency`、`min_tinkering_index` 等

**解決方案**:

```bash
# 搜索所有使用舊欄位的地方
grep -r "notification_frequency" backend/app/
grep -r "min_tinkering_index" backend/app/
```

### 問題 3: 測試通知失敗

**症狀**: 點擊測試通知按鈕後出錯

**檢查**:

1. Discord bot 是否運行
2. 用戶是否啟用 DM
3. 用戶是否有 `discord_id`

**解決方案**:

```bash
# 檢查 bot 狀態
docker-compose logs bot

# 檢查用戶數據
SELECT id, discord_id FROM users WHERE id = 'user_uuid';

# 檢查偏好設定
SELECT * FROM user_notification_preferences WHERE user_id = 'user_uuid';
```

## 📚 相關文檔

- [通知排程持久化修復](./NOTIFICATION_SCHEDULE_PERSISTENCE_FIX.md)
- [測試通知修復](./TEST_NOTIFICATION_FIX.md)
- [通知系統修復指南](./notification-system-fixes.md)

## 🎯 總結

### 修復的文件

1. `backend/app/services/dynamic_scheduler.py` - 添加恢復排程方法
2. `backend/app/repositories/user_notification_preferences.py` - 添加查詢活躍偏好設定
3. `backend/app/main.py` - 在啟動時調用恢復
4. `backend/app/services/notification_settings_service.py` - 修復資料庫查詢
5. `backend/app/services/preference_service.py` - 修復更新邏輯

### 關鍵改進

- ✅ 排程在服務重啟後自動恢復
- ✅ 不再查詢不存在的資料庫欄位
- ✅ 自動創建缺失的偏好設定記錄
- ✅ 測試通知功能正常工作
- ✅ 完整的錯誤處理和日誌記錄

### 未來改進

1. **持久化 JobStore**: 使用 SQLAlchemyJobStore 直接持久化 APScheduler jobs
2. **分散式調度**: 使用 Redis 支持多實例部署
3. **增量恢復**: 只恢復最近活躍的用戶
4. **健康檢查**: 定期驗證排程狀態
