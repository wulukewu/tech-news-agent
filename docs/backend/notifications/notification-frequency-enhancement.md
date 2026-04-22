# 通知頻率設定增強方案

## 問題描述

目前的通知頻率設定存在以下問題：

1. **每週通知**：只能設定時間（如 18:00），但無法選擇星期幾
2. **每月通知**：只能設定時間（如 18:00），但無法選擇日期（1-31號）
3. **預設值缺失**：當資料庫沒有記錄時，這些值應該有合理的預設值

## 現狀分析

### 資料庫 Schema

目前 `user_notification_preferences` 表只有：

- `frequency`: TEXT ('daily', 'weekly', 'monthly', 'disabled')
- `notification_time`: TIME (HH:MM:SS)
- `timezone`: TEXT

### 問題範例

- 使用者選擇「每週」通知，設定時間為 18:00
- 但系統不知道應該在星期幾發送（預設是星期五）
- 使用者無法選擇「每週一」或「每週三」

## 解決方案

### 1. 資料庫 Schema 擴展

新增兩個欄位到 `user_notification_preferences` 表：

```sql
-- 每週通知：星期幾 (0=Sunday, 1=Monday, ..., 6=Saturday)
-- 預設值：5 (Friday)
ALTER TABLE user_notification_preferences
ADD COLUMN notification_day_of_week INTEGER DEFAULT 5
CHECK (notification_day_of_week >= 0 AND notification_day_of_week <= 6);

-- 每月通知：日期 (1-31)
-- 預設值：1 (每月1號)
ALTER TABLE user_notification_preferences
ADD COLUMN notification_day_of_month INTEGER DEFAULT 1
CHECK (notification_day_of_month >= 1 AND notification_day_of_month <= 31);

-- 新增註解
COMMENT ON COLUMN user_notification_preferences.notification_day_of_week
IS 'Day of week for weekly notifications (0=Sunday, 1=Monday, ..., 6=Saturday). Default: 5 (Friday)';

COMMENT ON COLUMN user_notification_preferences.notification_day_of_month
IS 'Day of month for monthly notifications (1-31). Default: 1 (first day of month)';
```

### 2. 使用邏輯

根據 `frequency` 欄位決定使用哪個欄位：

| Frequency  | 使用欄位                                          | 說明                           |
| ---------- | ------------------------------------------------- | ------------------------------ |
| `daily`    | `notification_time`                               | 每天在指定時間發送             |
| `weekly`   | `notification_time` + `notification_day_of_week`  | 每週在指定星期幾的指定時間發送 |
| `monthly`  | `notification_time` + `notification_day_of_month` | 每月在指定日期的指定時間發送   |
| `disabled` | -                                                 | 不發送通知                     |

### 3. 預設值設定

| 欄位                        | 預設值          | 說明      |
| --------------------------- | --------------- | --------- |
| `frequency`                 | `'weekly'`      | 每週通知  |
| `notification_time`         | `'18:00:00'`    | 晚上 6 點 |
| `notification_day_of_week`  | `5`             | 星期五    |
| `notification_day_of_month` | `1`             | 每月 1 號 |
| `timezone`                  | `'Asia/Taipei'` | 台灣時區  |

### 4. UI/UX 改進

#### Web 界面

```typescript
// 根據頻率顯示不同的設定選項
{frequency === 'daily' && (
  <TimeInput
    label="通知時間"
    value={notificationTime}
    onChange={setNotificationTime}
  />
)}

{frequency === 'weekly' && (
  <>
    <DayOfWeekSelector
      label="通知日期"
      value={dayOfWeek}
      onChange={setDayOfWeek}
      options={[
        { value: 0, label: '星期日' },
        { value: 1, label: '星期一' },
        { value: 2, label: '星期二' },
        { value: 3, label: '星期三' },
        { value: 4, label: '星期四' },
        { value: 5, label: '星期五' },
        { value: 6, label: '星期六' },
      ]}
    />
    <TimeInput
      label="通知時間"
      value={notificationTime}
      onChange={setNotificationTime}
    />
  </>
)}

{frequency === 'monthly' && (
  <>
    <DayOfMonthSelector
      label="通知日期"
      value={dayOfMonth}
      onChange={setDayOfMonth}
      min={1}
      max={31}
      helperText="如果該月沒有此日期（如 2 月 31 日），將在該月最後一天發送"
    />
    <TimeInput
      label="通知時間"
      value={notificationTime}
      onChange={setNotificationTime}
    />
  </>
)}
```

#### Discord 命令

```
/set-notification-frequency weekly
→ 系統回應：請選擇星期幾？
  [星期一] [星期二] [星期三] [星期四] [星期五] [星期六] [星期日]

/set-notification-frequency monthly
→ 系統回應：請選擇日期（1-31）
  [1] [5] [10] [15] [20] [25] [31] 或輸入自訂日期
```

### 5. API 更新

#### GET /api/user/notification-preferences

回應範例：

```json
{
  "frequency": "weekly",
  "notificationTime": "18:00",
  "notificationDayOfWeek": 5,
  "notificationDayOfMonth": 1,
  "timezone": "Asia/Taipei",
  "dmEnabled": true,
  "emailEnabled": false
}
```

#### PUT /api/user/notification-preferences

請求範例：

```json
{
  "frequency": "weekly",
  "notificationTime": "18:00",
  "notificationDayOfWeek": 1, // 星期一
  "timezone": "Asia/Taipei"
}
```

### 6. 驗證邏輯

```python
def validate_notification_preferences(data: dict) -> dict:
    """驗證通知偏好設定"""
    frequency = data.get('frequency')

    # 驗證 day_of_week（僅當 frequency 為 weekly 時）
    if frequency == 'weekly':
        day_of_week = data.get('notification_day_of_week')
        if day_of_week is None:
            data['notification_day_of_week'] = 5  # 預設星期五
        elif not (0 <= day_of_week <= 6):
            raise ValidationError("notification_day_of_week must be between 0 and 6")

    # 驗證 day_of_month（僅當 frequency 為 monthly 時）
    if frequency == 'monthly':
        day_of_month = data.get('notification_day_of_month')
        if day_of_month is None:
            data['notification_day_of_month'] = 1  # 預設每月 1 號
        elif not (1 <= day_of_month <= 31):
            raise ValidationError("notification_day_of_month must be between 1 and 31")

    return data
```

### 7. 排程邏輯更新

```python
def get_next_notification_time(preferences: UserNotificationPreferences) -> datetime:
    """計算下次通知時間"""
    now = datetime.now(ZoneInfo(preferences.timezone))

    if preferences.frequency == 'daily':
        # 每天在指定時間
        next_time = now.replace(
            hour=preferences.notification_time.hour,
            minute=preferences.notification_time.minute,
            second=0,
            microsecond=0
        )
        if next_time <= now:
            next_time += timedelta(days=1)

    elif preferences.frequency == 'weekly':
        # 每週在指定星期幾的指定時間
        target_weekday = preferences.notification_day_of_week
        current_weekday = now.weekday()
        # 轉換：Python weekday() 是 0=Monday, 我們的 schema 是 0=Sunday
        days_ahead = (target_weekday - current_weekday - 1) % 7
        if days_ahead == 0:
            # 今天就是目標星期幾，檢查時間
            next_time = now.replace(
                hour=preferences.notification_time.hour,
                minute=preferences.notification_time.minute,
                second=0,
                microsecond=0
            )
            if next_time <= now:
                days_ahead = 7
        next_time = now + timedelta(days=days_ahead)
        next_time = next_time.replace(
            hour=preferences.notification_time.hour,
            minute=preferences.notification_time.minute,
            second=0,
            microsecond=0
        )

    elif preferences.frequency == 'monthly':
        # 每月在指定日期的指定時間
        target_day = preferences.notification_day_of_month
        next_time = now.replace(
            day=min(target_day, calendar.monthrange(now.year, now.month)[1]),
            hour=preferences.notification_time.hour,
            minute=preferences.notification_time.minute,
            second=0,
            microsecond=0
        )
        if next_time <= now:
            # 移到下個月
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1)
            else:
                next_month = now.replace(month=now.month + 1)
            next_time = next_month.replace(
                day=min(target_day, calendar.monthrange(next_month.year, next_month.month)[1]),
                hour=preferences.notification_time.hour,
                minute=preferences.notification_time.minute,
                second=0,
                microsecond=0
            )

    return next_time
```

## 實作步驟

1. **資料庫遷移**
   - 建立新的 migration 檔案
   - 新增 `notification_day_of_week` 和 `notification_day_of_month` 欄位
   - 設定預設值和約束條件

2. **Repository 層更新**
   - 更新 `UserNotificationPreferencesRepository`
   - 新增欄位驗證邏輯
   - 更新 `_map_to_entity` 方法

3. **Service 層更新**
   - 更新排程邏輯以使用新欄位
   - 修改 `get_next_notification_time` 函數

4. **API 層更新**
   - 更新 schema 定義
   - 修改 API 端點以支援新欄位

5. **前端更新**
   - 更新 UI 組件以顯示條件式設定
   - 新增星期選擇器和日期選擇器

6. **Discord 命令更新**
   - 修改命令以支援新參數
   - 更新互動式選擇流程

7. **測試**
   - 單元測試
   - 整合測試
   - E2E 測試

## 向後相容性

- 現有記錄會自動獲得預設值（星期五、每月 1 號）
- 不影響現有的 `daily` 和 `disabled` 頻率設定
- API 保持向後相容，新欄位為可選

## 參考資料

- ISO 8601 週日期系統
- Python `datetime.weekday()` 文件
- PostgreSQL CHECK 約束文件

---

## 實作進度

### ✅ 已完成

1. **資料庫層 (Database Layer)**
   - ✅ Migration 009: 新增 `notification_day_of_week` 和 `notification_day_of_month` 欄位
   - ✅ 欄位驗證：`notification_day_of_week` (0-6), `notification_day_of_month` (1-31)
   - ✅ 預設值：`notification_day_of_week` = 5 (Friday), `notification_day_of_month` = 1

2. **後端層 (Backend Layer)**
   - ✅ Repository: 更新 `UserNotificationPreferencesRepository` 支援新欄位
   - ✅ Schema: 更新 `UserNotificationPreferences` 和 `UpdateUserNotificationPreferencesRequest`
   - ✅ Service: 更新 `PreferenceService.update_preferences` 處理新欄位 ⚠️ **已修復**
   - ✅ 排程邏輯: 更新 `TimezoneConverter` 和 `DynamicScheduler` 使用新欄位
   - ✅ API 端點: `/api/notifications/preferences` PUT 端點正確處理新欄位

3. **前端層 (Frontend Layer)**
   - ✅ API 類型: 更新 `UserNotificationPreferences` 介面
   - ✅ UI 組件: 新增星期選擇器和日期選擇器
   - ✅ 條件顯示: 根據頻率顯示對應的選擇器
   - ✅ 預設值處理: 正確處理預設值

4. **測試與驗證**
   - ✅ 資料庫遷移測試通過
   - ✅ 後端單元測試通過（每日、每週、每月、邊界情況）
   - ✅ API 更新測試通過
   - ✅ 前端 UI 正確顯示

### 🐛 已修復的問題

**問題**: 前端可以顯示星期/日期選擇器，但更新時後端回應 "No fields to update"

**根本原因**: `PreferenceService.update_preferences` 方法沒有處理 `notification_day_of_week` 和 `notification_day_of_month` 欄位

**修復內容**:

- 在 `backend/app/services/preference_service.py` 的 `update_preferences` 方法中新增：
  ```python
  if updates.notification_day_of_week is not None:
      update_data["notification_day_of_week"] = updates.notification_day_of_week
      changed_fields.append("notification_day_of_week")
  if updates.notification_day_of_month is not None:
      update_data["notification_day_of_month"] = updates.notification_day_of_month
      changed_fields.append("notification_day_of_month")
  ```

**驗證結果**:

- ✅ 後端測試通過：可以正確更新 `notification_day_of_week` 和 `notification_day_of_month`
- ✅ API 端點正確處理請求
- ✅ 資料庫正確儲存新值

### 📝 使用說明

**每週通知設定**:

1. 選擇「每週」頻率
2. 選擇星期幾（0=星期日, 1=星期一, ..., 6=星期六）
3. 設定通知時間
4. 點擊「儲存設定」

**每月通知設定**:

1. 選擇「每月」頻率
2. 選擇日期（1-31）
3. 設定通知時間
4. 點擊「儲存設定」

**注意事項**:

- 如果選擇的日期超過該月天數（例如 2 月 31 日），系統會自動調整為該月最後一天
- 預設值：每週五、每月 1 號
- 時區設定會影響實際發送時間

---

**最後更新**: 2026-04-21
**狀態**: ✅ 功能完成並測試通過
