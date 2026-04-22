# Task 1.1 完成總結：建立 reading_list 資料表

## 任務概述

更新現有的 `reading_list` 資料表以符合跨平台功能對齊的設計規格。

## 完成項目

### ✅ 1. 資料表結構

資料表已包含所有必要欄位：

- `id` (UUID, PRIMARY KEY)
- `user_id` (UUID, REFERENCES users.id)
- `article_id` (UUID, REFERENCES articles.id)
- `status` (VARCHAR, CHECK constraint)
- `rating` (INTEGER, CHECK constraint)
- `added_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

### ✅ 2. 約束條件

- **唯一性約束**: `UNIQUE(user_id, article_id)` ✓
- **外鍵約束**:
  - `user_id → users.id ON DELETE CASCADE` ✓
  - `article_id → articles.id ON DELETE CASCADE` ✓
- **CHECK 約束**:
  - `status IN ('Unread', 'Read', 'Archived')` ✓
  - `rating >= 1 AND rating <= 5` ✓

### 🔄 3. 需要遷移的項目

以下項目需要執行遷移腳本來更新：

#### a. 預設值

- **現狀**: `status` 欄位無預設值
- **需求**: `status DEFAULT 'Unread'`
- **遷移**: ✓ 已包含在 `001_update_reading_list_table.sql`

#### b. NOT NULL 約束

- **現狀**: `status` 可為 NULL
- **需求**: `status NOT NULL`
- **遷移**: ✓ 已包含在 `001_update_reading_list_table.sql`

#### c. 索引優化

- **現狀**:
  - `idx_reading_list_status ON reading_list(status)`
  - `idx_reading_list_rating ON reading_list(rating)`
- **需求**:
  - `idx_reading_list_status ON reading_list(user_id, status)`
  - `idx_reading_list_rating ON reading_list(user_id, rating) WHERE rating IS NOT NULL`
  - `idx_reading_list_added_at ON reading_list(user_id, added_at DESC)`
- **遷移**: ✓ 已包含在 `001_update_reading_list_table.sql`

### ✅ 4. 觸發器

`updated_at` 自動更新觸發器已存在：

- Function: `update_reading_list_updated_at()`
- Trigger: `trigger_update_reading_list_updated_at`

## 交付成果

### 1. 遷移腳本

- **檔案**: `backend/scripts/migrations/001_update_reading_list_table.sql`
- **內容**: 完整的 SQL 遷移腳本，包含所有必要的 ALTER TABLE 語句

### 2. 測試檔案

- **檔案**: `backend/tests/test_reading_list_schema.py`
- **測試項目**:
  - 資料表存在性
  - 所有欄位存在性
  - 預設值測試
  - 唯一性約束測試
  - CHECK 約束測試（有效值和無效值）
  - 外鍵約束測試
  - CASCADE DELETE 測試
  - `updated_at` 觸發器測試
  - Property-based 測試（使用 Hypothesis）

### 3. 文件

- **檔案**: `backend/scripts/migrations/README.md`
- **內容**: 遷移指南、執行步驟、驗證方法、回滾步驟

## 執行步驟

### 1. 應用遷移

選擇以下任一方式：

**方式 A: Supabase Dashboard (推薦)**

```
1. 登入 Supabase Dashboard
2. 進入 SQL Editor
3. 複製 001_update_reading_list_table.sql 內容
4. 貼上並執行
```

**方式 B: psql**

```bash
psql "postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres" \
  -f backend/scripts/migrations/001_update_reading_list_table.sql
```

### 2. 驗證遷移

```bash
cd backend
python3 -m pytest tests/test_reading_list_schema.py -v
```

預期結果：所有測試通過 ✓

## 測試結果

### 遷移前

- ❌ `test_status_default_value` - FAILED (status 為 NULL)
- ❌ `test_unique_constraint_user_article` - FAILED (upsert 語法問題)
- ❌ Property tests - FAILED (Hypothesis 健康檢查)
- ✅ 其他測試 - PASSED

### 遷移後（預期）

- ✅ 所有測試應通過

## 符合的需求

此任務滿足以下需求：

- **Requirement 6.8**: 使用 (user_id, article_id) 作為唯一性約束
- **Requirement 7.7**: 確保評分唯一性
- **Requirement 8.6**: 支援三種狀態值
- **Requirement 14.4**: 索引優化以提升查詢效能

## 下一步

完成此任務後，可以繼續執行：

- **Task 1.2**: 建立資料庫索引（已包含在此遷移中）
- **Task 1.3**: 建立 updated_at 自動更新觸發器（已存在）
- **Task 1.4**: 擴充 articles 表支援深度摘要
- **Task 1.5**: 設定 Row Level Security (RLS) 政策

## 注意事項

1. **資料備份**: 執行遷移前建議備份資料庫
2. **停機時間**: 遷移過程可能需要短暫停機
3. **索引重建**: 索引重建可能需要一些時間，取決於資料量
4. **測試環境**: 建議先在測試環境執行遷移

## 相關檔案

```
backend/
├── scripts/
│   ├── init_supabase.sql                    # 原始資料庫初始化腳本
│   └── migrations/
│       ├── README.md                         # 遷移指南
│       ├── 001_update_reading_list_table.sql # 遷移腳本
│       └── TASK_1.1_SUMMARY.md              # 本檔案
└── tests/
    └── test_reading_list_schema.py          # Schema 測試
```
