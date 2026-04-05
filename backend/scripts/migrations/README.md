# Database Migrations

This directory contains SQL migration scripts for the Tech News Agent database.

## Migration Files

### 001_update_reading_list_table.sql

**Purpose:** Update the `reading_list` table to match design specifications for cross-platform feature parity.

**Changes:**

- Add `DEFAULT 'Unread'` to `status` column
- Add `NOT NULL` constraint to `status` column
- Replace simple indexes with optimized composite indexes:
  - `idx_reading_list_status` → `(user_id, status)`
  - `idx_reading_list_rating` → `(user_id, rating) WHERE rating IS NOT NULL`
  - Add `idx_reading_list_added_at` → `(user_id, added_at DESC)`

**Requirements:** Task 1.1 - 建立 reading_list 資料表

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Log in to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of the migration file
4. Paste into the SQL Editor
5. Click **Run** to execute

### Option 2: Supabase CLI

```bash
# If you have Supabase CLI installed
supabase db push
```

### Option 3: psql Command Line

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Run the migration
\i backend/scripts/migrations/001_update_reading_list_table.sql
```

## Verification

After applying the migration, run the schema tests to verify:

```bash
cd backend
python3 -m pytest tests/test_reading_list_schema.py -v
```

All tests should pass after the migration is applied.

## Rollback

If you need to rollback this migration:

```sql
-- Rollback: Revert to original indexes
DROP INDEX IF EXISTS idx_reading_list_status;
DROP INDEX IF EXISTS idx_reading_list_rating;
DROP INDEX IF EXISTS idx_reading_list_added_at;

-- Recreate original indexes
CREATE INDEX idx_reading_list_status ON reading_list(status);
CREATE INDEX idx_reading_list_rating ON reading_list(rating);

-- Remove NOT NULL constraint from status
ALTER TABLE reading_list ALTER COLUMN status DROP NOT NULL;

-- Remove default value from status
ALTER TABLE reading_list ALTER COLUMN status DROP DEFAULT;
```

## Migration History

| Migration | Date       | Description                      | Status  |
| --------- | ---------- | -------------------------------- | ------- |
| 001       | 2024-01-XX | Update reading_list table schema | Pending |
