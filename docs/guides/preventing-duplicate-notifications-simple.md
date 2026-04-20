# 防止重複通知 - 零配置指南

## 🎯 好消息：無需任何配置！

你的系統已經自動具備防重複通知功能，**不需要設定任何參數**。

## 🔧 自動工作原理

當本地開發和 Render 同時運行時：

```
本地實例啟動 → 自動生成 ID: instance_12345_1713600000
Render 實例啟動 → 自動生成 ID: instance_67890_1713600001
                              ↓
                    兩個 ID 不同，鎖機制自動生效
                              ↓
                    只有一個實例能成功發送通知
```

## ✅ 驗證是否正常工作

啟動應用後，檢查日誌：

```bash
# 應該看到類似的日誌
INFO - LockManager initialized with instance_id: instance_12345_1713600000
INFO - Successfully acquired notification lock, lock_id=xxx, instance_id=instance_12345_1713600000
```

如果另一個實例嘗試發送相同通知：

```bash
INFO - Notification already being processed by another instance, skipping
```

## 🚀 部署步驟

### 1. 本地開發

```bash
# 正常啟動，無需額外配置
python -m uvicorn app.main:app --reload
```

### 2. Render 部署

```bash
# 正常部署，無需額外環境變數
# 系統會自動處理重複防護
```

## 🔍 可選：自訂實例名稱

如果你想要更清楚的實例識別（非必需）：

**本地 `.env`**:

```bash
INSTANCE_ID=my_local_dev
```

**Render 環境變數**:

```
INSTANCE_ID=my_render_prod
```

## 🧪 測試重複防護

想要測試鎖機制是否正常工作？使用這個簡單腳本：

```python
# test_lock.py
import asyncio
from uuid import uuid4
from datetime import datetime
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def test_duplicate_prevention():
    """測試重複防護"""
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)

    user_id = uuid4()
    notification_type = "test_notification"
    scheduled_time = datetime.utcnow()

    print(f"實例 ID: {lock_manager.instance_id}")

    # 第一次嘗試
    lock1 = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time
    )

    # 第二次嘗試（模擬另一個實例）
    lock2 = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time
    )

    print(f"第一次獲取鎖: {'成功' if lock1 else '失敗'}")
    print(f"第二次獲取鎖: {'成功' if lock2 else '失敗'}")
    print(f"重複防護: {'✅ 正常' if (lock1 and not lock2) else '❌ 異常'}")

    # 清理
    if lock1:
        await lock_manager.release_lock(lock1.id, "completed")

if __name__ == "__main__":
    asyncio.run(test_duplicate_prevention())
```

執行測試：

```bash
cd backend && python test_lock.py
```

預期輸出：

```
實例 ID: instance_12345_1713600000
第一次獲取鎖: 成功
第二次獲取鎖: 失敗
重複防護: ✅ 正常
```

## 🔧 故障排除

### 如果仍然收到重複通知

1. **檢查日誌**：

```bash
grep "Successfully acquired notification lock" logs/app.log
grep "Notification already being processed" logs/app.log
```

2. **檢查資料庫**：

```sql
SELECT * FROM notification_locks ORDER BY created_at DESC LIMIT 10;
```

3. **手動清理鎖**：

```python
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def cleanup():
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)
    cleaned = await lock_manager.cleanup_expired_locks()
    print(f"清理了 {cleaned} 個過期鎖")
```

## 📊 監控建議

定期檢查鎖統計（可選）：

```python
# monitor.py
import asyncio
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def check_stats():
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)
    stats = await lock_manager.get_lock_statistics()

    print(f"總鎖數: {stats['total_locks']}")
    print(f"活躍鎖: {stats['active_locks']}")
    print(f"過期鎖: {stats['expired_locks']}")

asyncio.run(check_stats())
```

## 🎉 總結

- ✅ **零配置**：不需要設定任何環境變數
- ✅ **自動防護**：系統自動防止重複通知
- ✅ **多實例安全**：本地 + Render 同時運行沒問題
- ✅ **自動清理**：過期鎖會自動清理
- ✅ **完整測試**：包含測試覆蓋

現在你可以安心地同時運行本地開發和 Render 部署，不會再有重複通知的困擾！
