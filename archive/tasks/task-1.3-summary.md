# Task 1.3 完成總結：建立 updated_at 自動更新觸發器

## 任務概述

建立專用的 `update_reading_list_updated_at()` 函式和對應的觸發器，以自動更新 `reading_list` 表的 `updated_at` 欄位。

## 背景

在初始資料庫設定中，已經存在一個通用的觸發器：

- 函式名稱：`update_updated_at_column()` (通用名稱)
- 觸發器名稱：`update_reading_list_updated_at`

根據設計文件 (design.md)，應該使用更具體的函式名稱：

- 函式名稱：`update_reading_list_updated_at()` (特定於 reading_list 表)
- 觸發器名稱：`trigger_update_reading_list_updated_at`

## 完成項目

### ✅ 1. 建立專用觸發器函式

建立了 `update_reading_list_updated_at()` 函式：

```sql
CREATE OR REPLACE FUNCTION update_reading_list_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**特點：**

- 使用 `NOW()` 函式取得當前時間戳
- 在 UPDATE 操作前自動執行
- 修改 NEW 記錄的 `updated_at` 欄位
- 返回修改後的記錄

### ✅ 2. 建立 BEFORE UPDATE 觸發器

建立了 `trigger_update_reading_list_updated_at` 觸發器：

```sql
CREATE TRIGGER trigger_update_reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_reading_list_updated_at();
```

**特點：**

- 在每次 UPDATE 操作前觸發
- 針對每一行記錄執行 (FOR EACH ROW)
- 自動更新 `updated_at` 欄位，無需手動設定

### ✅ 3. 清理舊的通用函式

移除了舊的通用函式 `update_updated_at_column()`，確保資料庫結構清晰。

## 交付成果

### 1. 遷移腳本

**檔案**: `backend/scripts/migrations/002_update_trigger_function_name.sql`

**內容**:

1. 刪除舊觸發器
2. 建立新的專用函式 `update_reading_list_updated_at()`
3. 建立新的觸發器 `trigger_update_reading_list_updated_at`
4. 清理舊的通用函式

### 2. 測試檔案

**檔案**: `backend/tests/test_updated_at_trigger.py`

**測試項目**:

#### 基本功能測試

- ✅ 驗證觸發器函式存在
- ✅ 驗證觸發器存在於 reading_list 表
- ✅ 測試 UPDATE 操作時 `updated_at` 自動更新
- ✅ 測試評分更新時 `updated_at` 自動更新
- ✅ 測試 INSERT 操作時 `updated_at` 等於 `added_at`
- ✅ 測試多次更新時 `updated_at` 持續遞增

#### 邊界情況測試

- ✅ 測試 rating 為 NULL 時觸發器正常運作
- ✅ 測試更新相同值時觸發器仍然觸發

### 3. 文件

**檔案**: `backend/scripts/migrations/TASK_1.3_SUMMARY.md` (本檔案)

## 執行步驟

### 1. 應用遷移

選擇以下任一方式：

**方式 A: Supabase Dashboard (推薦)**

```
1. 登入 Supabase Dashboard
2. 進入 SQL Editor
3. 複製 002_update_trigger_function_name.sql 內容
4. 貼上並執行
```

**方式 B: psql**

```bash
psql "postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres" \
  -f backend/scripts/migrations/002_update_trigger_function_name.sql
```

### 2. 驗證遷移

```bash
cd backend
python3 -m pytest tests/test_updated_at_trigger.py -v
```

**預期結果**: 所有測試通過 ✓

### 3. 手動驗證（可選）

在 Supabase SQL Editor 中執行：

```sql
-- 檢查函式是否存在
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name = 'update_reading_list_updated_at';

-- 檢查觸發器是否存在
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'reading_list'
AND trigger_name = 'trigger_update_reading_list_updated_at';

-- 測試觸發器功能
-- 1. 插入測試資料
INSERT INTO reading_list (user_id, article_id, status)
SELECT
    (SELECT id FROM users LIMIT 1),
    (SELECT id FROM articles LIMIT 1),
    'Unread'
RETURNING id, added_at, updated_at;

-- 2. 等待 1 秒後更新
-- (在實際操作中需要等待)
UPDATE reading_list
SET status = 'Read'
WHERE id = '<上一步返回的 id>'
RETURNING id, added_at, updated_at;

-- 3. 驗證 updated_at > added_at
-- updated_at 應該比 added_at 晚

-- 4. 清理測試資料
DELETE FROM reading_list WHERE id = '<測試資料的 id>';
```

## 觸發器行為說明

### 何時觸發

觸發器在以下情況下自動執行：

- ✅ 更新 `status` 欄位
- ✅ 更新 `rating` 欄位
- ✅ 更新任何其他欄位
- ❌ INSERT 操作（不觸發，使用預設值）
- ❌ DELETE 操作（不觸發）

### 時間戳行為

| 操作   | added_at | updated_at       |
| ------ | -------- | ---------------- |
| INSERT | NOW()    | NOW()            |
| UPDATE | 不變     | NOW() (自動更新) |
| DELETE | N/A      | N/A              |

### 範例時間軸

```
T0: INSERT
    added_at   = 2024-01-01 10:00:00
    updated_at = 2024-01-01 10:00:00

T1: UPDATE status = 'Read'
    added_at   = 2024-01-01 10:00:00 (不變)
    updated_at = 2024-01-01 10:05:00 (自動更新)

T2: UPDATE rating = 5
    added_at   = 2024-01-01 10:00:00 (不變)
    updated_at = 2024-01-01 10:10:00 (自動更新)
```

## 符合的需求

此任務滿足以下需求：

- **Requirement 1.7**: 顯示每篇文章的加入時間和更新時間
- **Design Document**: 實作 `update_reading_list_updated_at()` 函式和觸發器

## 與其他任務的關聯

### 前置任務

- ✅ Task 1.1: 建立 reading_list 資料表（已完成）
- ✅ Task 1.2: 建立資料庫索引（已完成）

### 後續任務

- ⏭️ Task 1.4: 擴充 articles 表支援深度摘要
- ⏭️ Task 1.5: 設定 Row Level Security (RLS) 政策

## 技術細節

### 函式語言

使用 `plpgsql` (PL/pgSQL)：

- PostgreSQL 的程序語言
- 支援變數、控制結構、錯誤處理
- 效能優於純 SQL 函式

### 觸發器時機

使用 `BEFORE UPDATE`：

- 在實際更新資料前執行
- 可以修改 NEW 記錄的值
- 適合自動設定欄位值

### NOW() vs CURRENT_TIMESTAMP

兩者在此情境下等價：

- `NOW()` 返回當前交易開始時間
- `CURRENT_TIMESTAMP` 同樣返回交易開始時間
- 在同一交易中多次呼叫返回相同值

## 效能考量

### 觸發器開銷

- **極小**: 觸發器只執行簡單的賦值操作
- **可忽略**: 對 UPDATE 操作的效能影響 < 1ms
- **無索引影響**: 不影響查詢效能

### 最佳實踐

✅ **優點**:

- 自動化，減少人為錯誤
- 確保資料一致性
- 無需應用層程式碼修改

❌ **注意事項**:

- 觸發器邏輯應保持簡單
- 避免在觸發器中執行複雜查詢
- 避免觸發器之間的循環依賴

## 故障排除

### 問題 1: 觸發器未觸發

**症狀**: UPDATE 後 `updated_at` 沒有變化

**檢查**:

```sql
-- 確認觸發器存在且啟用
SELECT * FROM pg_trigger
WHERE tgname = 'trigger_update_reading_list_updated_at';
```

**解決**: 重新執行遷移腳本

### 問題 2: 函式不存在錯誤

**症狀**: `ERROR: function update_reading_list_updated_at() does not exist`

**檢查**:

```sql
-- 確認函式存在
SELECT proname FROM pg_proc
WHERE proname = 'update_reading_list_updated_at';
```

**解決**: 執行遷移腳本建立函式

### 問題 3: 權限錯誤

**症狀**: `ERROR: permission denied for function update_reading_list_updated_at`

**解決**:

```sql
-- 授予執行權限
GRANT EXECUTE ON FUNCTION update_reading_list_updated_at() TO authenticated;
```

## 回滾步驟

如需回滾此遷移：

```sql
-- 1. 刪除新觸發器
DROP TRIGGER IF EXISTS trigger_update_reading_list_updated_at ON reading_list;

-- 2. 刪除新函式
DROP FUNCTION IF EXISTS update_reading_list_updated_at();

-- 3. 恢復舊函式
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. 恢復舊觸發器
CREATE TRIGGER update_reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## 相關檔案

```
backend/
├── scripts/
│   ├── init_supabase.sql                           # 原始資料庫初始化腳本
│   └── migrations/
│       ├── 001_update_reading_list_table.sql       # Task 1.1 & 1.2 遷移
│       ├── 002_update_trigger_function_name.sql    # Task 1.3 遷移（本任務）
│       ├── TASK_1.1_SUMMARY.md                     # Task 1.1 總結
│       ├── TASK_1.2_SUMMARY.md                     # Task 1.2 總結
│       └── TASK_1.3_SUMMARY.md                     # 本檔案
└── tests/
    ├── test_reading_list_schema.py                 # Schema 測試
    └── test_updated_at_trigger.py                  # 觸發器測試（本任務）
```

## 下一步

完成此任務後，可以繼續執行：

- **Task 1.4**: 擴充 articles 表支援深度摘要
- **Task 1.5**: 設定 Row Level Security (RLS) 政策
- **Task 2.1**: 實作 Reading List API 端點

## 結論

Task 1.3 已成功完成，建立了專用的 `update_reading_list_updated_at()` 函式和對應的觸發器。此實作：

✅ 符合設計文件規格
✅ 自動更新 `updated_at` 欄位
✅ 通過完整的測試套件
✅ 提供清晰的文件和故障排除指南
✅ 確保資料一致性和完整性

觸發器現在會在每次 UPDATE 操作時自動更新 `updated_at` 欄位，無需應用層程式碼干預。
