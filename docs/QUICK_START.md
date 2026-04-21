# 通知頻率增強功能 - 快速開始

## 🎉 功能概述

使用者現在可以更精確地控制通知時間：

| 頻率 | 之前             | 現在                   |
| ---- | ---------------- | ---------------------- |
| 每日 | ✅ 每天指定時間  | ✅ 每天指定時間        |
| 每週 | ⚠️ 只能星期五    | ✅ 可選任意星期        |
| 每月 | ⚠️ 只能每月 1 號 | ✅ 可選任意日期 (1-31) |

## 🚀 快速測試

### 1. 驗證資料庫遷移

```bash
python3 scripts/verify_migration_009.py
```

預期輸出：

```
✅ Migration verified successfully!
   notification_day_of_week: 5
   notification_day_of_month: 1
```

### 2. 測試排程邏輯

```bash
python3 scripts/test_notification_scheduling.py
```

預期輸出：

```
✅ All tests completed!
```

## 📝 API 使用範例

### 每週一早上 9 點

```bash
curl -X POST http://localhost:8000/api/user/notification-preferences \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "weekly",
    "notificationTime": "09:00",
    "notificationDayOfWeek": 1,
    "timezone": "Asia/Taipei",
    "dmEnabled": true
  }'
```

### 每月 15 號晚上 6 點

```bash
curl -X POST http://localhost:8000/api/user/notification-preferences \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "monthly",
    "notificationTime": "18:00",
    "notificationDayOfMonth": 15,
    "timezone": "Asia/Taipei",
    "dmEnabled": true
  }'
```

### 查詢當前設定

```bash
curl http://localhost:8000/api/user/notification-preferences
```

## 🔢 欄位說明

### notification_day_of_week

每週通知的星期幾：

| 值  | 星期           |
| --- | -------------- |
| 0   | 星期日         |
| 1   | 星期一         |
| 2   | 星期二         |
| 3   | 星期三         |
| 4   | 星期四         |
| 5   | 星期五（預設） |
| 6   | 星期六         |

### notification_day_of_month

每月通知的日期：

- 範圍：1-31
- 預設：1（每月 1 號）
- 特殊處理：如果該月沒有指定日期（如 2 月 31 號），會在該月最後一天發送

## 🐍 Python 程式碼範例

### 建立通知偏好

```python
from backend.app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository
)
from uuid import UUID

repo = UserNotificationPreferencesRepository(supabase_client)

# 每週一早上 9 點
prefs = await repo.create({
    "user_id": str(user_id),
    "frequency": "weekly",
    "notification_time": "09:00",
    "notification_day_of_week": 1,  # Monday
    "timezone": "Asia/Taipei",
    "dm_enabled": True,
})
```

### 更新通知偏好

```python
# 改為每週五
await repo.update_by_user_id(user_id, {
    "notification_day_of_week": 5,  # Friday
})

# 改為每月 15 號
await repo.update_by_user_id(user_id, {
    "frequency": "monthly",
    "notification_day_of_month": 15,
})
```

### 計算下次通知時間

```python
from backend.app.core.timezone_converter import TimezoneConverter

# 每週三晚上 8 點
next_time = TimezoneConverter.get_next_notification_time(
    frequency="weekly",
    notification_time="20:00",
    timezone="Asia/Taipei",
    notification_day_of_week=3,  # Wednesday
)

print(f"Next notification: {next_time}")
# Output: Next notification: 2026-04-22 12:00:00+00:00 (UTC)

# 轉換為本地時間
local_time = TimezoneConverter.convert_to_user_time(next_time, "Asia/Taipei")
print(f"Local time: {local_time}")
# Output: Local time: 2026-04-22 20:00:00+08:00
```

## ✅ 驗證清單

在部署前，請確認：

- [ ] 資料庫遷移已執行
- [ ] 驗證腳本通過
- [ ] 測試腳本通過
- [ ] 現有通知仍正常運作
- [ ] 新欄位有正確的預設值

## 🔍 故障排除

### 問題：欄位不存在

```
column "notification_day_of_week" does not exist
```

**解決方案**：執行資料庫遷移

```bash
# 在 Supabase Dashboard > SQL Editor 執行
# scripts/migrations/009_add_notification_day_fields.sql
```

### 問題：驗證失敗

```
Invalid notification_day_of_week: 7
```

**解決方案**：確保值在有效範圍內

- `notification_day_of_week`: 0-6
- `notification_day_of_month`: 1-31

### 問題：排程時間不正確

**檢查項目**：

1. 時區設定是否正確
2. 星期/日期值是否正確
3. 查看日誌輸出

## 📚 更多資訊

- [完整設計文件](./notification-frequency-enhancement.md)
- [遷移指南](./MIGRATION_009_GUIDE.md)
- [實作總結](./notification-frequency-implementation-summary.md)
- [完成報告](./IMPLEMENTATION_COMPLETE.md)

## 🎯 下一步

### 立即可用

- ✅ API 端點（已支援新欄位）
- ✅ 排程邏輯（已更新）
- ✅ 資料驗證（已實作）

### 待開發

- ⏳ 前端 UI（條件式顯示）
- ⏳ Discord 命令（互動式選擇）
- ⏳ 使用者文件

## 💡 使用建議

### 最佳實踐

1. **每週通知**：選擇工作日（週一到週五）以獲得更好的閱讀率
2. **每月通知**：選擇月初（1-5 號）或月中（15 號）
3. **時間選擇**：避開深夜和清晨，建議 9:00-21:00

### 常見設定

| 使用情境   | 建議設定                |
| ---------- | ----------------------- |
| 工作日早報 | 每週一到五，早上 9:00   |
| 週末摘要   | 每週六，早上 10:00      |
| 月度報告   | 每月 1 號，早上 9:00    |
| 雙週更新   | 每週一和週四，晚上 6:00 |

## 🤝 回饋

如有問題或建議，請：

1. 查看文件
2. 執行測試腳本
3. 檢查日誌
4. 聯絡開發團隊

---

**版本**: 1.0.0
**最後更新**: 2026-04-21
**狀態**: ✅ 可用
