# 防止重複通知部署指南

## 快速設定

### 1. 環境變數設定

**本地開發環境** (`.env`):

```bash
# 設定唯一的實例 ID
INSTANCE_ID=local_dev_$(whoami)

# 其他必要設定
DATABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

**Render 生產環境**:
在 Render Dashboard 的環境變數中添加：

```
INSTANCE_ID=render_production
```

### 2. 驗證設定

啟動應用後，檢查日誌中的實例 ID：

```bash
# 本地開發
python -m uvicorn app.main:app --reload

# 查看日誌，應該看到類似：
# INFO - LockManager initialized with instance_id: local_dev_yourname
```

### 3. 測試重複防護

可以使用以下腳本測試鎖機制：

```python
# test_duplicate_prevention.py
import asyncio
from uuid import uuid4
from datetime import datetime
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def test_concurrent_notifications():
    """測試並發通知的重複防護"""

    # 模擬兩個實例
    supabase1 = SupabaseService()
    supabase2 = SupabaseService()

    lock_manager1 = LockManager(supabase1.client)
    lock_manager2 = LockManager(supabase2.client)

    # 覆寫實例 ID 模擬不同實例
    lock_manager1.instance_id = "instance_1"
    lock_manager2.instance_id = "instance_2"

    # 相同的通知參數
    user_id = uuid4()
    notification_type = "weekly_digest"
    scheduled_time = datetime.utcnow()

    async def try_send_notification(instance_name, lock_manager):
        print(f"[{instance_name}] 嘗試獲取鎖...")

        lock = await lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time
        )

        if lock:
            print(f"[{instance_name}] ✅ 成功獲取鎖，發送通知")
            await asyncio.sleep(0.5)  # 模擬發送時間
            await lock_manager.release_lock(lock.id, "completed")
            print(f"[{instance_name}] 🔓 釋放鎖")
            return True
        else:
            print(f"[{instance_name}] ❌ 鎖已存在，跳過發送")
            return False

    # 並發執行
    results = await asyncio.gather(
        try_send_notification("Instance 1", lock_manager1),
        try_send_notification("Instance 2", lock_manager2)
    )

    successful_sends = sum(results)
    print(f"\n📊 結果：{successful_sends}/2 個實例成功發送")
    print("✅ 重複防護正常工作！" if successful_sends == 1 else "❌ 出現問題")

if __name__ == "__main__":
    asyncio.run(test_concurrent_notifications())
```

## 常見問題排除

### 問題 1：仍然收到重複通知

**可能原因**：

- 兩個實例使用相同的 `INSTANCE_ID`
- 資料庫連線問題導致鎖機制失效

**解決方法**：

```bash
# 檢查實例 ID 是否不同
grep "instance_id" logs/app.log

# 確保環境變數正確設定
echo $INSTANCE_ID
```

### 問題 2：通知完全停止發送

**可能原因**：

- 鎖沒有正確釋放
- 過期鎖沒有清理

**解決方法**：

```python
# 手動清理過期鎖
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def cleanup_locks():
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)
    cleaned = await lock_manager.cleanup_expired_locks()
    print(f"清理了 {cleaned} 個過期鎖")

# 或者強制釋放特定使用者的鎖
async def force_release_user_lock(user_id, notification_type):
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)

    released = await lock_manager.force_release_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=datetime.utcnow()
    )
    print(f"強制釋放鎖：{'成功' if released else '未找到'}")
```

### 問題 3：效能影響

**監控鎖統計**：

```python
# 檢查鎖統計資訊
async def check_lock_stats():
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)
    stats = await lock_manager.get_lock_statistics()

    print(f"總鎖數：{stats['total_locks']}")
    print(f"活躍鎖：{stats['active_locks']}")
    print(f"過期鎖：{stats['expired_locks']}")

    if stats['expired_locks'] > 100:
        print("⚠️  建議執行清理任務")
```

## 部署檢查清單

### 部署前

- [ ] 設定唯一的 `INSTANCE_ID` 環境變數
- [ ] 確認資料庫遷移已執行（`notification_locks` 表存在）
- [ ] 測試鎖機制功能

### 部署後

- [ ] 檢查應用日誌中的實例 ID
- [ ] 驗證通知發送正常
- [ ] 監控是否有重複通知
- [ ] 確認清理任務正常運行

### 定期維護

- [ ] 每週檢查鎖統計資訊
- [ ] 監控 `failed` 狀態的鎖數量
- [ ] 清理過期鎖記錄

## 監控腳本

建立監控腳本 `scripts/monitor_locks.py`：

```python
#!/usr/bin/env python3
"""
通知鎖監控腳本
"""
import asyncio
from datetime import datetime, timedelta
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

async def monitor_locks():
    """監控鎖狀態並生成報告"""
    supabase = SupabaseService()
    lock_manager = LockManager(supabase.client)

    print("🔒 通知鎖監控報告")
    print("=" * 50)
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"實例 ID：{lock_manager.instance_id}")
    print()

    # 獲取統計資訊
    stats = await lock_manager.get_lock_statistics()

    print("📊 統計資訊：")
    print(f"  總鎖數：{stats['total_locks']}")
    print(f"  活躍鎖：{stats['active_locks']}")
    print(f"  過期鎖：{stats['expired_locks']}")
    print()

    print("📈 按狀態分布：")
    for status, count in stats.get('by_status', {}).items():
        print(f"  {status}: {count}")
    print()

    # 檢查異常情況
    warnings = []

    if stats['expired_locks'] > 50:
        warnings.append(f"過期鎖過多：{stats['expired_locks']} 個")

    failed_count = stats.get('by_status', {}).get('failed', 0)
    if failed_count > 10:
        warnings.append(f"失敗鎖過多：{failed_count} 個")

    if warnings:
        print("⚠️  警告：")
        for warning in warnings:
            print(f"  - {warning}")
        print()

        # 自動清理
        print("🧹 執行自動清理...")
        cleaned = await lock_manager.cleanup_expired_locks()
        print(f"  清理了 {cleaned} 個過期鎖")
    else:
        print("✅ 狀態正常")

    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(monitor_locks())
```

使用方法：

```bash
# 手動執行監控
python scripts/monitor_locks.py

# 設定 cron 定期執行（每小時）
0 * * * * cd /path/to/project && python scripts/monitor_locks.py >> logs/lock_monitor.log 2>&1
```

## 效能優化建議

### 1. 資料庫索引

確保 `notification_locks` 表有適當的索引：

```sql
-- 主要查詢索引
CREATE INDEX IF NOT EXISTS idx_notification_locks_user_type_time
ON notification_locks(user_id, notification_type, scheduled_time);

-- 清理任務索引
CREATE INDEX IF NOT EXISTS idx_notification_locks_expires_at
ON notification_locks(expires_at);

-- 狀態查詢索引
CREATE INDEX IF NOT EXISTS idx_notification_locks_status
ON notification_locks(status);
```

### 2. TTL 調整

根據通知發送時間調整 TTL：

```python
# 快速通知：較短 TTL
lock = await lock_manager.acquire_notification_lock(
    user_id=user_id,
    notification_type="instant_alert",
    scheduled_time=scheduled_time,
    ttl_minutes=5  # 5 分鐘
)

# 批量處理：較長 TTL
lock = await lock_manager.acquire_notification_lock(
    user_id=user_id,
    notification_type="weekly_digest",
    scheduled_time=scheduled_time,
    ttl_minutes=60  # 1 小時
)
```

### 3. 批量清理

定期批量清理過期鎖：

```python
# 在 scheduler.py 中設定更頻繁的清理
scheduler.add_job(
    lock_manager.cleanup_expired_locks,
    trigger=CronTrigger(minute="*/30"),  # 每 30 分鐘
    id="lock_cleanup_frequent",
    name="Frequent Lock Cleanup"
)
```

這樣就完成了完整的重複通知防護機制！現在你的系統可以安全地在多個環境同時運行，不會出現重複推播的問題。
