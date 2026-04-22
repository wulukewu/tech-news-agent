# Migration 009: 通知日期欄位增強

## 概述

此遷移為 `user_notification_preferences` 表新增兩個欄位，以支援更精確的每週和每月通知排程：

- `notification_day_of_week`: 每週通知的星期幾（0=星期日, 6=星期六）
- `notification_day_of_month`: 每月通知的日期（1-31）

## 問題背景

在此遷移之前，系統存在以下限制：

1. **每週通知**：只能設定時間（如 18:00），但無法選擇星期幾（預設為星期五）
2. **每月通知**：只能設定時間（如 18:00），但無法選擇日期（預設為每月 1 號）
3. 使用者無法自訂每週或每月的具體日期

## 解決方案

### 新增欄位

| 欄位名稱                    | 類型    | 預設值 | 約束 | 說明                                             |
| --------------------------- | ------- | ------ | ---- | ------------------------------------------------ |
| `notification_day_of_week`  | INTEGER | 5      | 0-6  | 每週通知的星期幾（0=星期日, 5=星期五, 6=星期六） |
| `notification_day_of_month` | INTEGER | 1      | 1-31 | 每月通知的日期（1-31）                           |

### 使用邏輯

根據 `frequency` 欄位決定使用哪些欄位：

| Frequency  | 使用欄位                                          | 範例            |
| ---------- | ------------------------------------------------- | --------------- |
| `daily`    | `notification_time`                               | 每天 18:00      |
| `weekly`   | `notification_time` + `notification_day_of_week`  | 每週五 18:00    |
| `monthly`  | `notification_time` + `notification_day_of_month` | 每月 1 號 18:00 |
| `disabled` | -                                                 | 不發送通知      |

## 執行遷移

### 方法 1: Supabase Dashboard（推薦）

1. 前往 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的專案
3. 點擊左側選單的 **SQL Editor**
4. 點擊 **New query**
5. 複製 `scripts/migrations/009_add_notification_day_fields.sql` 的內容
6. 貼上到編輯器
7. 點擊 **Run** 或按 `Cmd/Ctrl + Enter`

### 方法 2: psql 命令列

如果你有安裝 `psql`：

```bash
psql "$DATABASE_URL" -f scripts/migrations/009_add_notification_day_fields.sql
```

### 方法 3: 使用輔助腳本

```bash
# 顯示遷移指引
./scripts/apply_migration_009.sh

# 顯示完整 SQL（需要手動執行）
python3 scripts/execute_migration_009.py
```

## 驗證遷移

執行遷移後，使用以下命令驗證：

```bash
# 設定環境變數（如果尚未設定）
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"

# 執行驗證
python3 scripts/verify_migration_009.py
```

預期輸出：

```
🔍 Verifying migration 009...
✅ Migration verified successfully!
   Found 1 record(s)

📊 Sample data:
   notification_day_of_week: 5
   notification_day_of_month: 1
```

## 影響範圍

### 資料庫層

- ✅ 新增兩個欄位到 `user_notification_preferences` 表
- ✅ 設定預設值（星期五、每月 1 號）
- ✅ 新增檢查約束確保值的有效性
- ✅ 更新現有記錄以包含預設值
- ✅ 新增索引以優化查詢效能

### 後端層

- ✅ 更新 `UserNotificationPreferences` entity model
- ✅ 更新 `UserNotificationPreferencesRepository`
- ✅ 新增欄位驗證邏輯
- ✅ 更新 Pydantic schemas
- ⏳ 更新排程邏輯（待實作）
- ⏳ 更新 API 端點（待實作）

### 前端層

- ⏳ 更新 UI 組件以顯示條件式設定（待實作）
- ⏳ 新增星期選擇器（待實作）
- ⏳ 新增日期選擇器（待實作）

### Discord 命令

- ⏳ 更新命令以支援新參數（待實作）
- ⏳ 新增互動式選擇流程（待實作）

## 向後相容性

✅ **完全向後相容**

- 現有記錄會自動獲得預設值（星期五、每月 1 號）
- 不影響現有的 `daily` 和 `disabled` 頻率設定
- API 保持向後相容，新欄位為可選
- 現有的通知排程不會中斷

## 預設值說明

### 為什麼選擇星期五？

根據現有系統的預設行為，每週通知預設在星期五發送，這與大多數使用者的工作週期相符（週末前查看一週的技術新聞）。

### 為什麼選擇每月 1 號？

每月 1 號是最直觀的預設值，代表每月開始時查看上個月的技術新聞摘要。

## 特殊情況處理

### 每月日期不存在的情況

如果指定的日期在某個月份不存在（例如 2 月 31 日），系統會在該月的最後一天發送通知。

範例：

- 設定：每月 31 號 18:00
- 2 月：在 2 月 28 日（或 29 日）18:00 發送
- 4 月：在 4 月 30 日 18:00 發送
- 5 月：在 5 月 31 日 18:00 發送

## 測試建議

### 單元測試

```python
def test_notification_day_of_week_validation():
    """測試星期幾的驗證"""
    # Valid values: 0-6
    assert validate_day_of_week(0) == True  # Sunday
    assert validate_day_of_week(5) == True  # Friday
    assert validate_day_of_week(6) == True  # Saturday

    # Invalid values
    with pytest.raises(ValidationError):
        validate_day_of_week(-1)
    with pytest.raises(ValidationError):
        validate_day_of_week(7)

def test_notification_day_of_month_validation():
    """測試日期的驗證"""
    # Valid values: 1-31
    assert validate_day_of_month(1) == True
    assert validate_day_of_month(15) == True
    assert validate_day_of_month(31) == True

    # Invalid values
    with pytest.raises(ValidationError):
        validate_day_of_month(0)
    with pytest.raises(ValidationError):
        validate_day_of_month(32)
```

### 整合測試

```python
async def test_weekly_notification_with_custom_day():
    """測試自訂星期幾的每週通知"""
    # 設定每週一 09:00 通知
    prefs = await create_preferences(
        frequency="weekly",
        notification_time="09:00",
        notification_day_of_week=1  # Monday
    )

    # 驗證下次通知時間是星期一
    next_time = get_next_notification_time(prefs)
    assert next_time.weekday() == 0  # Python's Monday = 0
```

## 後續步驟

1. ✅ 執行資料庫遷移
2. ✅ 驗證遷移成功
3. ⏳ 更新排程邏輯以使用新欄位
4. ⏳ 更新 API 端點
5. ⏳ 更新前端 UI
6. ⏳ 更新 Discord 命令
7. ⏳ 撰寫測試
8. ⏳ 更新使用者文件

## 參考資料

- [設計文件](./notification-frequency-enhancement.md)
- [Migration SQL](../scripts/migrations/009_add_notification_day_fields.sql)
- [Repository 更新](../backend/app/repositories/user_notification_preferences.py)
- [Schema 更新](../backend/app/schemas/user_notification_preferences.py)

## 問題排查

### 遷移失敗

如果遷移失敗，檢查：

1. 是否有足夠的資料庫權限
2. 表是否存在
3. 是否有衝突的約束名稱

### 驗證失敗

如果驗證失敗，檢查：

1. 環境變數是否正確設定
2. 網路連線是否正常
3. Supabase 專案是否啟用

### 欄位不存在

如果查詢時提示欄位不存在：

1. 確認遷移已成功執行
2. 檢查資料庫連線是否指向正確的專案
3. 嘗試重新執行遷移

## 聯絡支援

如有問題，請：

1. 檢查 [GitHub Issues](https://github.com/your-repo/issues)
2. 查看 [Supabase 狀態頁面](https://status.supabase.com)
3. 聯絡開發團隊
