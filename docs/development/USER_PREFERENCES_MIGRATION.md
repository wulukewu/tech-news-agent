# Task 1.1: 建立 user_preferences 表格

## Overview

此 migration 建立 `user_preferences` 表格，用於儲存用戶的引導流程進度、Tooltip 教學狀態和語言偏好設定。

## Requirements

- **Requirement 1.4**: 追蹤引導流程進度
- **Requirement 10.1**: 引導進度持久化
- **Requirement 10.2**: 儲存引導步驟狀態
- **Requirement 11.7**: 互動式教學提示狀態追蹤

## Migration File

**File**: `scripts/migrations/002_create_user_preferences_table.sql`

## Table Schema

### user_preferences

| Column                    | Type        | Constraints                                              | Description           |
| ------------------------- | ----------- | -------------------------------------------------------- | --------------------- |
| `id`                      | UUID        | PRIMARY KEY, DEFAULT gen_random_uuid()                   | 唯一識別碼            |
| `user_id`                 | UUID        | REFERENCES users(id) ON DELETE CASCADE, UNIQUE, NOT NULL | 用戶 ID（外鍵）       |
| `onboarding_completed`    | BOOLEAN     | DEFAULT false                                            | 是否完成引導流程      |
| `onboarding_step`         | TEXT        | NULL                                                     | 當前引導步驟          |
| `onboarding_skipped`      | BOOLEAN     | DEFAULT false                                            | 是否跳過引導流程      |
| `onboarding_started_at`   | TIMESTAMPTZ | NULL                                                     | 開始引導的時間戳      |
| `onboarding_completed_at` | TIMESTAMPTZ | NULL                                                     | 完成引導的時間戳      |
| `tooltip_tour_completed`  | BOOLEAN     | DEFAULT false                                            | 是否完成 Tooltip 教學 |
| `tooltip_tour_skipped`    | BOOLEAN     | DEFAULT false                                            | 是否跳過 Tooltip 教學 |
| `preferred_language`      | TEXT        | DEFAULT 'zh-TW'                                          | 偏好語言              |
| `created_at`              | TIMESTAMPTZ | DEFAULT now()                                            | 建立時間              |
| `updated_at`              | TIMESTAMPTZ | DEFAULT now()                                            | 更新時間              |

### Indexes

1. **idx_user_preferences_user_id**: 優化基於 user_id 的查詢
2. **idx_user_preferences_onboarding_completed**: 優化基於 onboarding_completed 的查詢（例如：查詢未完成引導的用戶）

### Triggers

- **update_user_preferences_updated_at**: 自動更新 `updated_at` 欄位

## How to Apply the Migration

### Option 1: Supabase Dashboard (Recommended)

1. 前往 Supabase Dashboard
2. 導航至 **SQL Editor**
3. 複製 `scripts/migrations/002_create_user_preferences_table.sql` 的內容
4. 貼上到 SQL Editor
5. 點擊 **Run** 執行

### Option 2: Using the Apply Script

```bash
# Apply this specific migration
./scripts/migrations/apply_migration.sh scripts/migrations/002_create_user_preferences_table.sql
```

**Prerequisites**:

- `.env` file with `DATABASE_URL` configured
- PostgreSQL client (`psql`) installed

## Verification

### Automated Verification

```bash
# Run the verification script
python3 scripts/migrations/verify_user_preferences.py
```

Expected output:

```
✓ Schema verification successful!
✓ user_preferences table exists
✓ All required columns exist:
  - id, user_id
  - onboarding_completed, onboarding_step, onboarding_skipped
  - onboarding_started_at, onboarding_completed_at
  - tooltip_tour_completed, tooltip_tour_skipped
  - preferred_language
  - created_at, updated_at
✓ Indexes appear to be working
```

### Manual Verification in Supabase Dashboard

1. 前往 **Table Editor**
2. 選擇 `user_preferences` 表格
3. 驗證所有欄位都存在
4. 前往 **Database > Indexes**
5. 驗證以下索引存在：
   - `idx_user_preferences_user_id`
   - `idx_user_preferences_onboarding_completed`

## Usage Examples

### Create User Preferences on First Login

```sql
INSERT INTO user_preferences (user_id, onboarding_started_at)
VALUES ('user-uuid-here', now())
ON CONFLICT (user_id) DO NOTHING;
```

### Update Onboarding Progress

```sql
UPDATE user_preferences
SET
    onboarding_step = 'recommendations',
    updated_at = now()
WHERE user_id = 'user-uuid-here';
```

### Mark Onboarding as Completed

```sql
UPDATE user_preferences
SET
    onboarding_completed = true,
    onboarding_completed_at = now(),
    updated_at = now()
WHERE user_id = 'user-uuid-here';
```

### Skip Onboarding

```sql
UPDATE user_preferences
SET
    onboarding_skipped = true,
    updated_at = now()
WHERE user_id = 'user-uuid-here';
```

### Check if User Has Completed Onboarding

```sql
SELECT onboarding_completed, onboarding_skipped
FROM user_preferences
WHERE user_id = 'user-uuid-here';
```

### Get All Users Who Haven't Completed Onboarding

```sql
SELECT u.id, u.discord_id, up.onboarding_step
FROM users u
LEFT JOIN user_preferences up ON u.id = up.user_id
WHERE up.onboarding_completed = false OR up.onboarding_completed IS NULL;
```

## Data Model Relationships

```
users (1) ----< (1) user_preferences
  id              user_id
```

- **One-to-One**: 每個用戶只有一筆 user_preferences 記錄
- **Cascade Delete**: 當用戶被刪除時，其 preferences 也會被刪除

## Design Decisions

### Why UNIQUE constraint on user_id?

確保每個用戶只有一筆偏好設定記錄，避免資料重複。

### Why separate onboarding_completed and onboarding_skipped?

- `onboarding_completed = true`: 用戶完成了所有引導步驟
- `onboarding_skipped = true`: 用戶選擇跳過引導
- 兩者都是 `false`: 用戶尚未完成或跳過引導

這樣可以區分「完成」和「跳過」兩種不同的狀態。

### Why store onboarding_step as TEXT?

提供彈性以支援未來可能的引導步驟變更，不需要修改資料庫 schema。

可能的值：

- `'welcome'`: 歡迎畫面
- `'recommendations'`: 推薦訂閱來源
- `'complete'`: 完成

### Why index on onboarding_completed?

常見查詢場景：

- 查詢所有未完成引導的用戶（用於分析）
- 檢查用戶是否需要顯示引導流程

索引可以大幅提升這些查詢的效能。

## Testing

### Manual Testing

```sql
-- 1. Create a test user preference
INSERT INTO user_preferences (user_id, onboarding_started_at)
SELECT id, now()
FROM users
LIMIT 1;

-- 2. Update onboarding progress
UPDATE user_preferences
SET onboarding_step = 'recommendations'
WHERE user_id IN (SELECT id FROM users LIMIT 1);

-- 3. Verify updated_at was automatically updated
SELECT user_id, onboarding_step, updated_at
FROM user_preferences
WHERE user_id IN (SELECT id FROM users LIMIT 1);

-- 4. Complete onboarding
UPDATE user_preferences
SET
    onboarding_completed = true,
    onboarding_completed_at = now()
WHERE user_id IN (SELECT id FROM users LIMIT 1);

-- 5. Verify final state
SELECT *
FROM user_preferences
WHERE user_id IN (SELECT id FROM users LIMIT 1);
```

## Rollback

如果需要回滾此 migration：

```sql
-- Drop the table and all related objects
DROP TABLE IF EXISTS user_preferences CASCADE;
```

**Warning**: 這將刪除所有用戶偏好設定資料。

## Related Files

- **Migration**: `scripts/migrations/002_create_user_preferences_table.sql`
- **Verification**: `scripts/migrations/verify_user_preferences.py`
- **Documentation**: `scripts/migrations/TASK_1.1_DOCUMENTATION.md`

## Next Steps

After applying this migration:

1. ✅ Task 1.1: 建立 user_preferences 表格 (COMPLETED)
2. ⏭️ Task 1.2: 擴展 feeds 表格以支援推薦系統
3. ⏭️ Task 1.3: 建立 analytics_events 表格
4. ⏭️ Task 2.x: 實作引導流程 API endpoints

## References

- **Spec Path**: `.kiro/specs/new-user-onboarding-system`
- **Requirements**: `requirements.md` - Requirements 1.4, 10.1, 10.2, 11.7
- **Design**: `design.md` - Database Schema section
