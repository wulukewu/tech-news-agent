# Task 1.3 驗證指南

## 驗證觸發器功能

本文件提供手動驗證步驟，確認 `update_reading_list_updated_at()` 函式和觸發器正確運作。

## 前置條件

- 已執行 `002_update_trigger_function_name.sql` 遷移腳本
- 有 Supabase Dashboard 存取權限
- 資料庫中已有測試用的 users 和 articles 資料

## 驗證步驟

### 步驟 1: 檢查函式是否存在

在 Supabase SQL Editor 中執行：

```sql
SELECT
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name = 'update_reading_list_updated_at';
```

**預期結果**:

```
routine_name                    | routine_type | data_type
--------------------------------|--------------|----------
update_reading_list_updated_at  | FUNCTION     | trigger
```

✅ 如果返回一行記錄，表示函式存在  
❌ 如果返回空結果，需要執行遷移腳本

---

### 步驟 2: 檢查觸發器是否存在

```sql
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'reading_list'
AND trigger_name = 'trigger_update_reading_list_updated_at';
```

**預期結果**:

```
trigger_name                          | event_manipulation | event_object_table | action_timing | action_statement
--------------------------------------|--------------------|--------------------|---------------|------------------
trigger_update_reading_list_updated_at| UPDATE             | reading_list       | BEFORE        | EXECUTE FUNCTION update_reading_list_updated_at()
```

✅ 如果返回一行記錄，表示觸發器存在且配置正確  
❌ 如果返回空結果，需要執行遷移腳本

---

### 步驟 3: 測試觸發器功能

#### 3.1 準備測試資料

首先，取得一個測試用的 user_id 和 article_id：

```sql
-- 取得第一個用戶的 ID
SELECT id, discord_id FROM users LIMIT 1;

-- 取得第一篇文章的 ID
SELECT id, title FROM articles LIMIT 1;
```

記下這兩個 UUID，在後續步驟中使用。

#### 3.2 插入測試記錄

```sql
-- 替換 <user_id> 和 <article_id> 為實際的 UUID
INSERT INTO reading_list (user_id, article_id, status)
VALUES (
    '<user_id>',
    '<article_id>',
    'Unread'
)
RETURNING id, added_at, updated_at;
```

**預期結果**:

```
id                                   | added_at                    | updated_at
-------------------------------------|-----------------------------|--------------------------
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | 2024-01-15 10:00:00.123456 | 2024-01-15 10:00:00.123456
```

✅ `added_at` 和 `updated_at` 應該幾乎相同（差異 < 1 秒）  
記下返回的 `id`，在後續步驟中使用

#### 3.3 等待並更新記錄

**重要**: 等待至少 2 秒，以確保時間戳有明顯差異

```sql
-- 替換 <reading_list_id> 為上一步返回的 id
UPDATE reading_list
SET status = 'Read'
WHERE id = '<reading_list_id>'
RETURNING id, added_at, updated_at;
```

**預期結果**:

```
id                                   | added_at                    | updated_at
-------------------------------------|-----------------------------|--------------------------
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | 2024-01-15 10:00:00.123456 | 2024-01-15 10:00:02.789012
```

✅ **驗證點**:

- `added_at` 應該與插入時相同（未改變）
- `updated_at` 應該比 `added_at` 晚（自動更新）
- 時間差應該 >= 2 秒

❌ 如果 `updated_at` 沒有變化，表示觸發器未正常運作

#### 3.4 測試評分更新

再次等待 2 秒，然後更新評分：

```sql
-- 替換 <reading_list_id> 為測試記錄的 id
UPDATE reading_list
SET rating = 5
WHERE id = '<reading_list_id>'
RETURNING id, status, rating, added_at, updated_at;
```

**預期結果**:

```
id       | status | rating | added_at                    | updated_at
---------|--------|--------|-----------------------------|--------------------------
xxxxxxxx | Read   | 5      | 2024-01-15 10:00:00.123456 | 2024-01-15 10:00:04.567890
```

✅ **驗證點**:

- `updated_at` 應該比上一次更新的時間更晚
- `added_at` 仍然保持不變

#### 3.5 清理測試資料

```sql
-- 替換 <reading_list_id> 為測試記錄的 id
DELETE FROM reading_list WHERE id = '<reading_list_id>';
```

---

### 步驟 4: 測試邊界情況

#### 4.1 測試 NULL rating

```sql
-- 插入沒有評分的記錄
INSERT INTO reading_list (user_id, article_id, status, rating)
VALUES (
    '<user_id>',
    '<article_id>',
    'Unread',
    NULL
)
RETURNING id, rating, added_at, updated_at;

-- 記下 id，等待 2 秒

-- 更新狀態
UPDATE reading_list
SET status = 'Read'
WHERE id = '<reading_list_id>'
RETURNING id, rating, added_at, updated_at;

-- 驗證 updated_at 已更新

-- 清理
DELETE FROM reading_list WHERE id = '<reading_list_id>';
```

✅ 觸發器應該正常運作，即使 rating 為 NULL

#### 4.2 測試更新相同值

```sql
-- 插入記錄
INSERT INTO reading_list (user_id, article_id, status)
VALUES (
    '<user_id>',
    '<article_id>',
    'Read'
)
RETURNING id, status, added_at, updated_at;

-- 記下 id，等待 2 秒

-- 更新為相同的狀態值
UPDATE reading_list
SET status = 'Read'  -- 相同的值
WHERE id = '<reading_list_id>'
RETURNING id, status, added_at, updated_at;

-- 驗證 updated_at 仍然更新了

-- 清理
DELETE FROM reading_list WHERE id = '<reading_list_id>';
```

✅ 即使值沒有改變，觸發器也應該更新 `updated_at`

---

### 步驟 5: 測試多次更新

```sql
-- 插入記錄
INSERT INTO reading_list (user_id, article_id, status)
VALUES (
    '<user_id>',
    '<article_id>',
    'Unread'
)
RETURNING id, added_at, updated_at;

-- 記下 id 和 updated_at (T0)

-- 等待 2 秒，第一次更新
UPDATE reading_list SET status = 'Read' WHERE id = '<reading_list_id>'
RETURNING updated_at;  -- T1

-- 等待 2 秒，第二次更新
UPDATE reading_list SET rating = 3 WHERE id = '<reading_list_id>'
RETURNING updated_at;  -- T2

-- 等待 2 秒，第三次更新
UPDATE reading_list SET rating = 5 WHERE id = '<reading_list_id>'
RETURNING updated_at;  -- T3

-- 等待 2 秒，第四次更新
UPDATE reading_list SET status = 'Archived' WHERE id = '<reading_list_id>'
RETURNING updated_at;  -- T4

-- 清理
DELETE FROM reading_list WHERE id = '<reading_list_id>';
```

✅ **驗證點**: T0 < T1 < T2 < T3 < T4 (時間戳嚴格遞增)

---

## 驗證檢查清單

完成所有驗證步驟後，確認以下項目：

- [ ] ✅ 函式 `update_reading_list_updated_at()` 存在
- [ ] ✅ 觸發器 `trigger_update_reading_list_updated_at` 存在
- [ ] ✅ 觸發器配置為 BEFORE UPDATE
- [ ] ✅ INSERT 時 `updated_at` 等於 `added_at`
- [ ] ✅ UPDATE 時 `updated_at` 自動更新
- [ ] ✅ UPDATE 時 `added_at` 保持不變
- [ ] ✅ 更新 status 時觸發器運作
- [ ] ✅ 更新 rating 時觸發器運作
- [ ] ✅ rating 為 NULL 時觸發器運作
- [ ] ✅ 更新相同值時觸發器仍然運作
- [ ] ✅ 多次更新時 `updated_at` 持續遞增

## 常見問題

### Q1: 觸發器沒有觸發

**症狀**: UPDATE 後 `updated_at` 沒有變化

**可能原因**:

1. 觸發器不存在或被禁用
2. 函式不存在
3. 權限問題

**解決方法**:

```sql
-- 檢查觸發器狀態
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgname = 'trigger_update_reading_list_updated_at';

-- tgenabled 應該是 'O' (enabled)
-- 如果是 'D' (disabled)，啟用它：
ALTER TABLE reading_list ENABLE TRIGGER trigger_update_reading_list_updated_at;
```

### Q2: 函式不存在錯誤

**症狀**: `ERROR: function update_reading_list_updated_at() does not exist`

**解決方法**: 重新執行遷移腳本 `002_update_trigger_function_name.sql`

### Q3: 時間戳沒有差異

**症狀**: `updated_at` 和 `added_at` 完全相同

**可能原因**: 更新操作執行太快，在同一毫秒內完成

**解決方法**: 在 INSERT 和 UPDATE 之間等待至少 1-2 秒

### Q4: 舊函式仍然存在

**症狀**: 同時存在 `update_updated_at_column()` 和 `update_reading_list_updated_at()`

**檢查**:

```sql
SELECT proname FROM pg_proc
WHERE proname LIKE 'update_%updated_at%';
```

**解決方法**: 手動刪除舊函式

```sql
DROP FUNCTION IF EXISTS update_updated_at_column();
```

## 自動化驗證腳本

如果有 Python 環境和 Supabase 憑證，可以執行自動化測試：

```bash
cd backend
python3 -m pytest tests/test_updated_at_trigger.py -v
```

**注意**: 需要設定環境變數：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## 驗證完成

如果所有檢查項目都通過 ✅，表示 Task 1.3 已成功完成！

觸發器現在會在每次 UPDATE 操作時自動更新 `updated_at` 欄位。

---

## 相關文件

- [Task 1.3 總結](TASK_1.3_SUMMARY.md)
- [遷移腳本](002_update_trigger_function_name.sql)
- [測試檔案](../../tests/test_updated_at_trigger.py)
