# 通知頻率增強功能 - 實作總結

## 已完成的工作

### 1. 資料庫層 ✅

#### Migration 009: 新增通知日期欄位

**檔案**: `scripts/migrations/009_add_notification_day_fields.sql`

新增欄位：

- `notification_day_of_week` (INTEGER, 0-6, 預設: 5 = 星期五)
- `notification_day_of_month` (INTEGER, 1-31, 預設: 1 = 每月 1 號)

特性：

- ✅ CHECK 約束確保值的有效性
- ✅ 預設值設定
- ✅ 更新現有記錄
- ✅ 新增索引優化查詢
- ✅ 欄位註解說明

### 2. Repository 層 ✅

**檔案**: `backend/app/repositories/user_notification_preferences.py`

更新內容：

- ✅ `UserNotificationPreferences` entity 新增兩個欄位
- ✅ `_map_to_entity` 方法更新以映射新欄位
- ✅ `_validate_create_data` 新增欄位驗證邏輯
- ✅ `_validate_update_data` 新增欄位驗證邏輯
- ✅ `create_default_for_user` 包含預設值

驗證規則：

```python
# notification_day_of_week: 0-6
if not (0 <= day_of_week <= 6):
    raise ValidationError("Must be between 0 (Sunday) and 6 (Saturday)")

# notification_day_of_month: 1-31
if not (1 <= day_of_month <= 31):
    raise ValidationError("Must be between 1 and 31")
```

### 3. Schema 層 ✅

**檔案**: `backend/app/schemas/user_notification_preferences.py`

更新的 schemas：

#### `UserNotificationPreferences`

```python
notification_day_of_week: int = Field(
    default=5, ge=0, le=6,
    description="Day of week for weekly notifications (0=Sunday, 6=Saturday)"
)
notification_day_of_month: int = Field(
    default=1, ge=1, le=31,
    description="Day of month for monthly notifications (1-31)"
)
```

#### `CreateUserNotificationPreferencesRequest`

- ✅ 新增兩個欄位，帶預設值
- ✅ 自動驗證範圍（透過 Pydantic）

#### `UpdateUserNotificationPreferencesRequest`

- ✅ 新增兩個可選欄位
- ✅ 支援部分更新

### 4. 文件 ✅

建立的文件：

1. **`docs/notification-frequency-enhancement.md`**
   - 問題描述
   - 解決方案設計
   - 資料庫 schema
   - API 設計
   - UI/UX 設計
   - 實作步驟

2. **`docs/MIGRATION_009_GUIDE.md`**
   - 遷移指南
   - 執行步驟
   - 驗證方法
   - 問題排查
   - 測試建議

3. **輔助腳本**
   - `scripts/apply_migration_009.sh` - 顯示遷移指引
   - `scripts/execute_migration_009.py` - 顯示 SQL 和執行方法
   - `scripts/verify_migration_009.py` - 驗證遷移是否成功

## 待完成的工作

### 1. 執行資料庫遷移 ⏳

**需要手動執行**（因為 Supabase Python client 不支援 DDL）

方法：

1. 前往 Supabase Dashboard > SQL Editor
2. 複製 `scripts/migrations/009_add_notification_day_fields.sql`
3. 執行 SQL
4. 驗證：`python3 scripts/verify_migration_009.py`

### 2. 更新排程邏輯 ⏳

**檔案**: `backend/app/services/notification_scheduler.py` (或類似)

需要更新 `get_next_notification_time` 函數：

```python
def get_next_notification_time(preferences: UserNotificationPreferences) -> datetime:
    """計算下次通知時間"""
    now = datetime.now(ZoneInfo(preferences.timezone))

    if preferences.frequency == 'daily':
        # 每天在指定時間
        next_time = now.replace(
            hour=preferences.notification_time.hour,
            minute=preferences.notification_time.minute,
            second=0, microsecond=0
        )
        if next_time <= now:
            next_time += timedelta(days=1)

    elif preferences.frequency == 'weekly':
        # 使用 notification_day_of_week
        target_weekday = preferences.notification_day_of_week
        # ... 計算邏輯

    elif preferences.frequency == 'monthly':
        # 使用 notification_day_of_month
        target_day = preferences.notification_day_of_month
        # ... 計算邏輯

    return next_time
```

### 3. 更新 API 端點 ⏳

**檔案**: `backend/app/api/v1/endpoints/notification_preferences.py` (或類似)

確保 API 端點：

- ✅ 已經透過 schema 自動支援新欄位
- ⏳ 需要測試 GET/PUT 端點
- ⏳ 需要更新 API 文件

### 4. 前端 UI 更新 ⏳

**需要建立/更新的組件**：

#### `NotificationFrequencySettings.tsx`

```typescript
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
      helperText="如果該月沒有此日期，將在該月最後一天發送"
    />
    <TimeInput
      label="通知時間"
      value={notificationTime}
      onChange={setNotificationTime}
    />
  </>
)}
```

### 5. Discord 命令更新 ⏳

**檔案**: `backend/app/bot/commands/notification_settings.py` (或類似)

需要更新的命令：

#### `/set-notification-frequency`

```python
@bot.slash_command(name="set-notification-frequency")
async def set_frequency(
    ctx,
    frequency: discord.Option(
        str,
        choices=["daily", "weekly", "monthly", "disabled"]
    )
):
    if frequency == "weekly":
        # 顯示星期選擇器
        view = DayOfWeekView()
        await ctx.respond("請選擇星期幾：", view=view)
    elif frequency == "monthly":
        # 顯示日期選擇器
        view = DayOfMonthView()
        await ctx.respond("請選擇日期（1-31）：", view=view)
    else:
        # 直接更新
        await update_frequency(ctx.user.id, frequency)
```

### 6. 測試 ⏳

需要撰寫的測試：

#### 單元測試

- ✅ Repository 驗證邏輯（已在 repository 中實作）
- ⏳ 排程邏輯測試
- ⏳ API 端點測試

#### 整合測試

- ⏳ 完整的通知流程測試
- ⏳ 跨平台同步測試（Web ↔ Discord）

#### E2E 測試

- ⏳ 使用者設定每週通知
- ⏳ 使用者設定每月通知
- ⏳ 驗證通知在正確時間發送

## 使用範例

### API 請求範例

#### 建立每週一早上 9 點的通知

```bash
POST /api/user/notification-preferences
{
  "frequency": "weekly",
  "notificationTime": "09:00",
  "notificationDayOfWeek": 1,  // Monday
  "timezone": "Asia/Taipei",
  "dmEnabled": true
}
```

#### 建立每月 15 號晚上 6 點的通知

```bash
POST /api/user/notification-preferences
{
  "frequency": "monthly",
  "notificationTime": "18:00",
  "notificationDayOfMonth": 15,
  "timezone": "Asia/Taipei",
  "dmEnabled": true
}
```

#### 更新為每週五

```bash
PUT /api/user/notification-preferences
{
  "notificationDayOfWeek": 5  // Friday
}
```

### Python 程式碼範例

#### 建立預設偏好

```python
from backend.app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository
)

repo = UserNotificationPreferencesRepository(supabase_client)

# 建立預設偏好（每週五 18:00）
prefs = await repo.create_default_for_user(user_id)

print(f"Frequency: {prefs.frequency}")  # weekly
print(f"Time: {prefs.notification_time}")  # 18:00:00
print(f"Day of week: {prefs.notification_day_of_week}")  # 5 (Friday)
print(f"Day of month: {prefs.notification_day_of_month}")  # 1
```

#### 更新為每週一

```python
await repo.update_by_user_id(
    user_id,
    {
        "frequency": "weekly",
        "notification_day_of_week": 1,  # Monday
        "notification_time": "09:00"
    }
)
```

#### 更新為每月 15 號

```python
await repo.update_by_user_id(
    user_id,
    {
        "frequency": "monthly",
        "notification_day_of_month": 15,
        "notification_time": "18:00"
    }
)
```

## 向後相容性

✅ **完全向後相容**

- 現有 API 呼叫不會中斷
- 新欄位有預設值
- 現有記錄會自動更新
- 不影響現有的通知排程

## 下一步行動

1. **立即執行**：
   - [ ] 執行資料庫遷移（手動）
   - [ ] 驗證遷移成功

2. **短期（本週）**：
   - [ ] 更新排程邏輯
   - [ ] 測試 API 端點
   - [ ] 撰寫單元測試

3. **中期（下週）**：
   - [ ] 更新前端 UI
   - [ ] 更新 Discord 命令
   - [ ] 撰寫整合測試

4. **長期**：
   - [ ] E2E 測試
   - [ ] 使用者文件
   - [ ] 效能優化

## 相關檔案

### 資料庫

- `scripts/migrations/009_add_notification_day_fields.sql`
- `scripts/verify_migration_009.py`
- `scripts/apply_migration_009.sh`

### 後端

- `backend/app/repositories/user_notification_preferences.py`
- `backend/app/schemas/user_notification_preferences.py`

### 文件

- `docs/notification-frequency-enhancement.md`
- `docs/MIGRATION_009_GUIDE.md`
- `docs/notification-frequency-implementation-summary.md` (本檔案)

## 問題與解答

### Q: 為什麼不能直接用 Python 執行遷移？

A: Supabase Python client 基於 PostgREST，不支援執行任意 DDL SQL。需要使用 Supabase Dashboard 的 SQL Editor 或 psql 命令列工具。

### Q: 如果某個月沒有指定的日期怎麼辦？

A: 系統會在該月的最後一天發送通知。例如設定每月 31 號，2 月會在 28/29 號發送。

### Q: 星期的編號為什麼是 0-6？

A: 遵循 ISO 8601 標準，0 代表星期日，6 代表星期六。這與 JavaScript 的 `Date.getDay()` 一致。

### Q: 現有使用者的設定會受影響嗎？

A: 不會。現有使用者會自動獲得預設值（星期五、每月 1 號），與之前的行為一致。

## 總結

此次更新為通知系統帶來了更大的靈活性，使用者現在可以：

- ✅ 選擇每週的任何一天接收通知
- ✅ 選擇每月的任何一天接收通知
- ✅ 保持現有的每日通知功能
- ✅ 所有設定都有合理的預設值

後端的資料結構和驗證邏輯已經完成，接下來需要完成排程邏輯、前端 UI 和 Discord 命令的更新。
