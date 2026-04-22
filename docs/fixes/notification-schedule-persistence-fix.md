# 通知排程持久化修復文檔

## 📋 問題描述

用戶報告：

1. 設定通知頻率後，最上面顯示「已排程」✅
2. 刷新網頁後，狀態仍然顯示「已排程」✅
3. **但過一陣子後再打開，卻顯示「未排程」❌**

## 🔍 根本原因

### 問題分析

APScheduler（用於管理通知排程的調度器）**沒有配置持久化存儲**，導致：

1. **服務重啟時排程丟失**
   - 當後端服務重啟時，所有在記憶體中的 APScheduler jobs 都會消失
   - 沒有機制從資料庫恢復用戶的排程設定

2. **排程狀態查詢邏輯**

   ```python
   # backend/app/services/dynamic_scheduler.py
   async def get_user_job_info(self, user_id: UUID) -> Optional[dict]:
       job_id = f"user_notification_{user_id}"
       job = self.scheduler.get_job(job_id)  # 只檢查記憶體中的 job
       if job:
           return {...}
       return None  # 如果記憶體中沒有，就返回 None
   ```

3. **前端狀態判斷**

   ```typescript
   // frontend/features/notifications/components/PersonalizedNotificationSettings.tsx
   const status = useQuery({
     queryKey: ['notificationStatus'],
     queryFn: getNotificationStatus, // 調用後端 API
     refetchInterval: 30000, // 每 30 秒重新查詢
   });

   // 如果 job_info 為 None，前端就顯示「未排程」
   ```

### 問題流程

```
1. 用戶設定通知頻率 → 創建 APScheduler job → 顯示「已排程」✅
2. 刷新網頁 → job 仍在記憶體中 → 顯示「已排程」✅
3. 後端服務重啟（自動或手動）→ 記憶體清空 → job 丟失
4. 用戶再次打開網頁 → 查詢不到 job → 顯示「未排程」❌
```

## ✅ 實施的修復

### 解決方案：啟動時恢復排程

在應用啟動時，從資料庫讀取所有用戶的通知偏好設定，並重新創建排程。

### 1. 添加恢復排程方法

**文件**: `backend/app/services/dynamic_scheduler.py`

```python
async def restore_all_user_schedules(self) -> dict:
    """
    Restore notification schedules for all users from database.

    This method should be called on application startup to restore
    all user notification schedules that were lost due to service restart.

    Returns:
        dict: Statistics about the restoration process
    """
    try:
        self.logger.info("Starting restoration of all user notification schedules")

        from app.repositories.user_notification_preferences import (
            UserNotificationPreferencesRepository,
        )
        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService()
        prefs_repo = UserNotificationPreferencesRepository(supabase.client)

        # Get all users with active notification preferences
        all_preferences = await prefs_repo.get_all_active_preferences()

        restored_count = 0
        skipped_count = 0
        failed_count = 0

        for preferences in all_preferences:
            try:
                # Skip if notifications are disabled
                if preferences.frequency == "disabled" or not preferences.dm_enabled:
                    skipped_count += 1
                    continue

                # Schedule the user notification
                await self.schedule_user_notification(preferences.user_id, preferences)
                restored_count += 1

                self.logger.debug(
                    "Restored notification schedule",
                    user_id=str(preferences.user_id),
                    frequency=preferences.frequency,
                )

            except Exception as user_error:
                failed_count += 1
                self.logger.warning(
                    "Failed to restore schedule for user",
                    user_id=str(preferences.user_id),
                    error=str(user_error),
                )

        result = {
            "total_users": len(all_preferences),
            "restored": restored_count,
            "skipped": skipped_count,
            "failed": failed_count,
        }

        self.logger.info(
            "Completed restoration of user notification schedules",
            **result,
        )

        return result

    except Exception as e:
        self.logger.error(
            "Failed to restore user schedules",
            error=str(e),
            exc_info=True,
        )
        return {
            "total_users": 0,
            "restored": 0,
            "skipped": 0,
            "failed": 0,
            "error": str(e),
        }
```

### 2. 添加查詢活躍偏好設定的方法

**文件**: `backend/app/repositories/user_notification_preferences.py`

```python
async def get_all_active_preferences(self) -> list[UserNotificationPreferences]:
    """
    Get all active user notification preferences.

    Returns preferences for users who have:
    - frequency != 'disabled'
    - dm_enabled = True

    This is used to restore notification schedules on application startup.

    Returns:
        List of active UserNotificationPreferences entities

    Raises:
        DatabaseError: If database operation fails
    """
    self.logger.info(
        "Getting all active notification preferences",
        operation="get_all_active_preferences",
        table=self.table_name,
    )

    try:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .neq("frequency", "disabled")
            .eq("dm_enabled", True)
            .execute()
        )

        entities = [self._map_to_entity(row) for row in response.data]

        self.logger.info(
            "Successfully retrieved active notification preferences",
            operation="get_all_active_preferences",
            table=self.table_name,
            count=len(entities),
        )

        return entities

    except Exception as e:
        self.logger.error(
            "Failed to get all active preferences",
            exc_info=True,
            operation="get_all_active_preferences",
            table=self.table_name,
            error=str(e),
        )
        self._handle_database_error(
            e, {"operation": "get_all_active_preferences"}
        )
```

### 3. 在啟動時調用恢復方法

**文件**: `backend/app/tasks/scheduler.py`

在 `setup_scheduler()` 函數中添加：

```python
# Restore all user notification schedules from database
# This ensures schedules persist across service restarts
try:
    logger.info("Restoring user notification schedules from database...")
    restore_stats = await _dynamic_scheduler.restore_all_user_schedules()
    logger.info(
        f"User notification schedules restored: "
        f"{restore_stats['restored']} restored, "
        f"{restore_stats['skipped']} skipped, "
        f"{restore_stats['failed']} failed"
    )
except Exception as e:
    logger.error(f"Failed to restore user notification schedules: {e}", exc_info=True)
    # Don't fail the entire setup if restoration fails
    # Individual users can manually reschedule if needed
```

## 🔄 修復流程

### 應用啟動時

```
1. 啟動 FastAPI 應用
   ↓
2. 初始化 APScheduler
   ↓
3. 初始化 DynamicScheduler
   ↓
4. 調用 restore_all_user_schedules()
   ↓
5. 從資料庫查詢所有活躍的用戶偏好設定
   ↓
6. 為每個用戶重新創建 APScheduler job
   ↓
7. 記錄恢復統計信息
```

### 用戶查詢排程狀態時

```
1. 前端調用 /api/notifications/preferences/status
   ↓
2. 後端查詢 APScheduler 中的 job
   ↓
3. 如果 job 存在 → 返回「已排程」
   ↓
4. 如果 job 不存在 → 返回「未排程」

現在：即使服務重啟，job 也會被恢復，所以會返回「已排程」✅
```

## 📊 預期效果

### 修復前

| 時間點 | 服務狀態 | 排程狀態 | 前端顯示  |
| ------ | -------- | -------- | --------- |
| T0     | 運行中   | 已創建   | ✅ 已排程 |
| T1     | 運行中   | 存在     | ✅ 已排程 |
| T2     | **重啟** | **丟失** | ❌ 未排程 |
| T3     | 運行中   | 不存在   | ❌ 未排程 |

### 修復後

| 時間點 | 服務狀態 | 排程狀態     | 前端顯示  |
| ------ | -------- | ------------ | --------- |
| T0     | 運行中   | 已創建       | ✅ 已排程 |
| T1     | 運行中   | 存在         | ✅ 已排程 |
| T2     | **重啟** | **自動恢復** | ✅ 已排程 |
| T3     | 運行中   | 存在         | ✅ 已排程 |

## 🧪 測試步驟

### 1. 驗證恢復功能

```bash
# 1. 啟動後端服務
cd backend
uvicorn app.main:app --reload

# 2. 檢查日誌，應該看到：
# "Restoring user notification schedules from database..."
# "User notification schedules restored: X restored, Y skipped, Z failed"

# 3. 查看恢復統計
# 應該顯示有多少用戶的排程被恢復
```

### 2. 測試排程持久性

```bash
# 1. 在前端設定通知頻率
# 2. 確認顯示「已排程」
# 3. 重啟後端服務
# 4. 刷新前端頁面
# 5. 應該仍然顯示「已排程」✅
```

### 3. 測試不同場景

| 場景             | 預期結果                 |
| ---------------- | ------------------------ |
| 用戶啟用通知     | 排程被創建並恢復         |
| 用戶停用通知     | 排程不被恢復（skipped）  |
| 用戶刪除偏好設定 | 排程不被恢復             |
| 資料庫連接失敗   | 記錄錯誤但不影響應用啟動 |

## 🔧 故障排除

### 問題 1: 恢復失敗

**症狀**: 日誌顯示 "Failed to restore user schedules"

**解決方案**:

1. 檢查資料庫連接
2. 確認 `user_notification_preferences` 表存在
3. 檢查表結構是否正確

### 問題 2: 部分用戶未恢復

**症狀**: `failed` 計數 > 0

**解決方案**:

1. 檢查日誌中的具體錯誤
2. 驗證用戶的偏好設定數據是否有效
3. 確認時區設定是否正確

### 問題 3: 恢復速度慢

**症狀**: 應用啟動時間變長

**解決方案**:

1. 這是正常的，因為需要為所有用戶創建排程
2. 如果用戶數量很大（>1000），考慮：
   - 批次處理
   - 異步恢復（不阻塞啟動）
   - 添加進度指示

## 📈 監控建議

### 關鍵指標

1. **恢復成功率**

   ```
   success_rate = restored / (restored + failed) * 100%
   ```

2. **恢復時間**
   - 記錄 `restore_all_user_schedules()` 的執行時間
   - 如果超過 10 秒，考慮優化

3. **活躍用戶數**
   - 監控 `total_users` 的增長
   - 預估未來的恢復時間

### 日誌監控

在應用啟動日誌中查找：

```
✅ 成功: "User notification schedules restored: X restored, Y skipped, Z failed"
⚠️  警告: "Failed to restore schedule for user"
❌ 錯誤: "Failed to restore user schedules"
```

## 🎯 總結

### 修復內容

- ✅ 添加 `restore_all_user_schedules()` 方法
- ✅ 添加 `get_all_active_preferences()` 查詢方法
- ✅ 在應用啟動時自動恢復所有排程
- ✅ 添加詳細的日誌記錄和錯誤處理

### 影響的文件

1. `backend/app/services/dynamic_scheduler.py` - 添加恢復方法
2. `backend/app/repositories/user_notification_preferences.py` - 添加查詢方法
3. `backend/app/tasks/scheduler.py` - 在啟動時調用恢復

### 優點

1. **自動恢復**: 無需用戶手動操作
2. **可靠性**: 排程狀態與資料庫保持一致
3. **可擴展**: 支持大量用戶
4. **可監控**: 提供詳細的統計信息

### 限制

1. **啟動時間**: 用戶數量多時會增加啟動時間
2. **記憶體使用**: 所有排程都在記憶體中
3. **單點故障**: 如果 APScheduler 崩潰，需要重啟恢復

### 未來改進

1. **持久化 JobStore**: 使用 SQLAlchemyJobStore 直接持久化 jobs
2. **分散式調度**: 使用 Redis 或其他分散式鎖
3. **增量恢復**: 只恢復最近活躍的用戶
4. **健康檢查**: 定期驗證排程狀態

## 📚 相關文檔

- [通知系統修復指南](./notification-system-fixes.md)
- [通知狀態修復指南](../NOTIFICATION_STATUS_FIX_GUIDE.md)
- [測試通知修復文檔](./TEST_NOTIFICATION_FIX.md)
