# 通知鎖機制 (Notification Lock Mechanism)

## 概述

為了防止在多實例環境（例如本地開發 + Render 部署）中重複發送 DM 通知，我們實作了基於資料庫的分散式鎖機制。

## 問題背景

當系統同時在多個環境運行時（例如：本地開發環境 + Render 生產環境），會出現以下問題：

- 兩個實例的排程器會在相同時間觸發通知任務
- 導致使用者收到重複的 DM 通知
- 影響使用者體驗，造成困擾

## 解決方案

### 架構設計

使用 `LockManager` 服務實作原子性的通知鎖機制：

```
┌─────────────────┐         ┌─────────────────┐
│  本地開發實例    │         │  Render 實例     │
│  (Instance 1)   │         │  (Instance 2)   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │  嘗試獲取鎖                │  嘗試獲取鎖
         ├──────────┐       ┌────────┤
         │          ▼       ▼        │
         │    ┌──────────────────┐   │
         │    │  notification_   │   │
         │    │  locks 資料表    │   │
         │    └──────────────────┘   │
         │          │       │        │
         │  ✅ 獲取成功  ❌ 已存在   │
         │          │                │
         ▼          ▼                ▼
    發送通知    跳過發送        跳過發送
```

### 核心元件

#### 1. LockManager Service

位置：`backend/app/services/lock_manager.py`

主要功能：

- `acquire_notification_lock()`: 原子性獲取鎖
- `release_lock()`: 釋放鎖並更新狀態
- `cleanup_expired_locks()`: 清理過期鎖

#### 2. DynamicScheduler Integration

位置：`backend/app/services/dynamic_scheduler.py`

在 `_send_user_notification()` 方法中整合鎖機制：

```python
async def _send_user_notification(
    self, user_id: UUID, preferences: UserNotificationPreferences
) -> None:
    # 1. 初始化 LockManager
    lock_manager = LockManager(supabase.client)

    # 2. 嘗試獲取鎖
    lock = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=f"{preferences.frequency}_digest",
        scheduled_time=datetime.utcnow(),
        ttl_minutes=30
    )

    # 3. 如果鎖已存在，跳過發送
    if not lock:
        logger.info("Notification already being processed by another instance")
        return

    try:
        # 4. 發送通知
        success = await dm_service.send_personalized_digest(str(user_id))

        # 5. 釋放鎖
        await lock_manager.release_lock(
            lock.id,
            "completed" if success else "failed"
        )
    except Exception as e:
        # 6. 發生錯誤時也要釋放鎖
        await lock_manager.release_lock(lock.id, "failed")
        raise e
```

### 資料庫結構

`notification_locks` 資料表：

| 欄位              | 類型      | 說明                             |
| ----------------- | --------- | -------------------------------- |
| id                | UUID      | 鎖的唯一識別碼                   |
| user_id           | UUID      | 使用者 ID                        |
| notification_type | TEXT      | 通知類型（例如：weekly_digest）  |
| scheduled_time    | TIMESTAMP | 排程時間                         |
| status            | TEXT      | 狀態（pending/completed/failed） |
| instance_id       | TEXT      | 獲取鎖的實例 ID                  |
| created_at        | TIMESTAMP | 建立時間                         |
| expires_at        | TIMESTAMP | 過期時間                         |

唯一約束：`(user_id, notification_type, scheduled_time)`

## 工作流程

### 正常流程

1. **排程觸發**：兩個實例同時觸發通知任務
2. **競爭鎖**：兩個實例同時嘗試在資料庫中插入鎖記錄
3. **獲勝者**：第一個成功插入的實例獲得鎖
4. **失敗者**：第二個實例因唯一約束衝突而無法獲取鎖
5. **發送通知**：獲勝實例發送通知
6. **釋放鎖**：發送完成後更新鎖狀態為 `completed`

### 錯誤處理

1. **發送失敗**：鎖狀態更新為 `failed`，允許後續重試
2. **實例崩潰**：鎖會在 TTL（預設 30 分鐘）後自動過期
3. **清理機制**：定期清理過期的鎖記錄

## 實例識別

每個實例使用唯一的 `instance_id` 識別：

```python
def _get_instance_id(self) -> str:
    # 優先使用環境變數
    instance_id = os.environ.get("INSTANCE_ID")
    if not instance_id:
        # 否則使用 PID + 時間戳生成
        instance_id = f"instance_{os.getpid()}_{int(time.time())}"
    return instance_id
```

### 設定實例 ID

**本地開發**：

```bash
export INSTANCE_ID="local_dev"
```

**Render 部署**：
在 Render 環境變數中設定：

```
INSTANCE_ID=render_production
```

## 測試

### 單元測試

位置：`backend/tests/services/test_dynamic_scheduler.py`

測試案例：

1. `test_send_user_notification_success`: 成功獲取鎖並發送
2. `test_send_user_notification_lock_already_exists`: 鎖已存在時跳過
3. `test_send_user_notification_failure_releases_lock`: 失敗時釋放鎖
4. `test_send_user_notification_bot_not_ready`: Bot 未就緒時釋放鎖

### 整合測試

位置：`backend/tests/integration/test_lock_manager_integration.py`

測試多實例並發場景。

## 監控與維護

### 日誌記錄

鎖機制會記錄以下關鍵事件：

```python
# 獲取鎖成功
logger.info("Successfully acquired notification lock",
    lock_id=str(lock.id),
    instance_id=lock_manager.instance_id
)

# 鎖已存在（重複防護）
logger.info("Notification already being processed by another instance",
    user_id=str(user_id),
    notification_type=notification_type
)

# 釋放鎖
logger.info("Successfully released notification lock",
    lock_id=str(lock.id),
    status=status
)
```

### 清理機制

定期清理過期鎖：

```python
# 在 scheduler.py 中註冊清理任務
scheduler.add_job(
    lock_manager.cleanup_expired_locks,
    trigger=CronTrigger(hour="*/6"),  # 每 6 小時執行一次
    id="lock_cleanup",
    name="Notification Lock Cleanup"
)
```

### 監控指標

可以透過 `LockManager.get_lock_statistics()` 獲取統計資訊：

```python
stats = await lock_manager.get_lock_statistics()
# {
#     "total_locks": 150,
#     "active_locks": 10,
#     "expired_locks": 5,
#     "by_status": {
#         "pending": 10,
#         "completed": 130,
#         "failed": 10
#     }
# }
```

## 效能考量

### 資料庫負載

- 每次通知發送需要 2 次資料庫操作（獲取鎖 + 釋放鎖）
- 使用索引優化查詢效能
- 定期清理過期記錄避免資料表膨脹

### TTL 設定

預設 TTL 為 30 分鐘，可根據實際情況調整：

```python
lock = await lock_manager.acquire_notification_lock(
    user_id=user_id,
    notification_type=notification_type,
    scheduled_time=scheduled_time,
    ttl_minutes=30  # 可調整
)
```

## 最佳實踐

1. **設定唯一的實例 ID**：確保每個環境有不同的 `INSTANCE_ID`
2. **監控鎖狀態**：定期檢查 `failed` 狀態的鎖，排查問題
3. **適當的 TTL**：根據通知發送時間設定合理的 TTL
4. **定期清理**：確保清理任務正常運行
5. **日誌分析**：透過日誌追蹤重複發送的情況

## 相關文件

- [Lock Manager Service](../api/lock-manager.md)
- [Dynamic Scheduler](../api/dynamic-scheduler.md)
- [Notification System](../api/notification-system.md)

## 變更歷史

| 日期       | 版本 | 說明                     |
| ---------- | ---- | ------------------------ |
| 2024-04-20 | 1.0  | 初始版本，實作基本鎖機制 |
