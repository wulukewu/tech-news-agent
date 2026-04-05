# Task 1.3: 建立 updated_at 自動更新觸發器 - 快速指南

## 概述

本遷移將通用的觸發器函式重命名為專用的 `update_reading_list_updated_at()` 函式，以符合設計文件規格。

## 快速執行

### 選項 1: Supabase Dashboard (推薦)

1. 登入 [Supabase Dashboard](https://app.supabase.com)
2. 選擇你的專案
3. 點擊左側選單的 **SQL Editor**
4. 點擊 **New Query**
5. 複製 `002_update_trigger_function_name.sql` 的內容
6. 貼上到編輯器
7. 點擊 **Run** 執行

### 選項 2: psql 命令列

```bash
# 設定連線字串
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres"

# 執行遷移
psql $DATABASE_URL -f backend/scripts/migrations/002_update_trigger_function_name.sql
```

### 選項 3: Python 腳本

```python
import os
from supabase import create_client

# 讀取 SQL 檔案
with open('backend/scripts/migrations/002_update_trigger_function_name.sql', 'r') as f:
    sql = f.read()

# 執行遷移
supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

# 注意: Supabase Python SDK 不直接支援執行任意 SQL
# 建議使用 Supabase Dashboard 或 psql
```

## 驗證

### 快速驗證

在 SQL Editor 中執行：

```sql
-- 檢查函式
SELECT routine_name FROM information_schema.routines
WHERE routine_name = 'update_reading_list_updated_at';

-- 檢查觸發器
SELECT trigger_name FROM information_schema.triggers
WHERE trigger_name = 'trigger_update_reading_list_updated_at';
```

兩個查詢都應該返回一行記錄。

### 完整驗證

參考 [TASK_1.3_VERIFICATION.md](TASK_1.3_VERIFICATION.md) 進行完整的功能測試。

## 遷移內容

此遷移執行以下操作：

1. ✅ 刪除舊觸發器 `update_reading_list_updated_at`
2. ✅ 建立新函式 `update_reading_list_updated_at()`
3. ✅ 建立新觸發器 `trigger_update_reading_list_updated_at`
4. ✅ 清理舊函式 `update_updated_at_column()`

## 影響範圍

- **資料表**: `reading_list`
- **停機時間**: 無（遷移瞬間完成）
- **資料變更**: 無（只修改觸發器定義）
- **向後相容**: 是（功能完全相同）

## 回滾

如需回滾，參考 [TASK_1.3_SUMMARY.md](TASK_1.3_SUMMARY.md) 的回滾步驟。

## 相關文件

- [完整總結](TASK_1.3_SUMMARY.md) - 詳細的任務說明和技術細節
- [驗證指南](TASK_1.3_VERIFICATION.md) - 手動驗證步驟
- [測試檔案](../../tests/test_updated_at_trigger.py) - 自動化測試

## 問題排查

如遇到問題，請參考：

- [TASK_1.3_SUMMARY.md](TASK_1.3_SUMMARY.md) 的「故障排除」章節
- [TASK_1.3_VERIFICATION.md](TASK_1.3_VERIFICATION.md) 的「常見問題」章節

## 下一步

完成此遷移後，繼續執行：

- Task 1.4: 擴充 articles 表支援深度摘要
- Task 1.5: 設定 Row Level Security (RLS) 政策
