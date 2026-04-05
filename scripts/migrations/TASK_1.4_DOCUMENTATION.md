# Task 1.4: 擴充 articles 表支援深度摘要

## Overview

This task extends the `articles` table to support deep summary functionality, which stores AI-generated deep analysis summaries that are shared across all users.

## Requirements

- **Requirement 4.7**: THE Web_Frontend SHALL 將生成的 Deep_Summary 儲存到 Supabase 供重複查看
- **Requirement 9.7**: THE 系統 SHALL 將 Deep_Summary 儲存在 articles 表的 ai_summary 欄位

## Changes Made

### 1. Database Schema Changes

Added two new columns to the `articles` table:

- `deep_summary` (TEXT): Stores the AI-generated deep analysis summary
- `deep_summary_generated_at` (TIMESTAMPTZ): Timestamp when the summary was generated

### 2. Index Creation

Created a partial index for performance optimization:

```sql
CREATE INDEX idx_articles_deep_summary
ON articles(id) WHERE deep_summary IS NOT NULL;
```

This index optimizes queries that check for existing summaries, supporting the caching requirement.

### 3. Files Modified/Created

#### Created:

- `scripts/migrations/001_add_deep_summary_to_articles.sql` - Migration script for existing databases
- `scripts/migrations/README.md` - Migration documentation
- `scripts/migrations/apply_migration.sh` - Shell script to apply migrations
- `scripts/migrations/verify_schema.py` - Python script to verify schema changes
- `scripts/migrations/TASK_1.4_DOCUMENTATION.md` - This documentation

#### Modified:

- `scripts/init_supabase.sql` - Updated for new installations
- `backend/scripts/init_supabase.sql` - Updated for new installations

## Design Rationale

### Why separate `ai_summary` and `deep_summary`?

The existing `ai_summary` column is kept for quick, lightweight summaries, while `deep_summary` is used for comprehensive AI-generated analysis. This separation allows:

1. **Different use cases**: Quick summaries vs. detailed analysis
2. **Performance**: Can load articles with quick summaries without fetching large deep summaries
3. **Flexibility**: Different LLM prompts and models for different summary types

### Why a partial index?

The partial index `WHERE deep_summary IS NOT NULL` provides:

1. **Smaller index size**: Only indexes articles with summaries
2. **Faster queries**: Optimizes the common pattern of checking if a summary exists
3. **Cache efficiency**: Supports the requirement to check for existing summaries before generating new ones

## Usage

### For Existing Databases

Apply the migration:

```bash
# Using the shell script
./scripts/migrations/apply_migration.sh scripts/migrations/001_add_deep_summary_to_articles.sql

# Or directly with psql
psql $DATABASE_URL -f scripts/migrations/001_add_deep_summary_to_articles.sql
```

Verify the changes:

```bash
python3 scripts/migrations/verify_schema.py
```

### For New Installations

The changes are already included in `scripts/init_supabase.sql`, so no additional steps are needed.

## Testing

### Manual Testing

1. **Verify columns exist**:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'articles'
AND column_name IN ('deep_summary', 'deep_summary_generated_at');
```

2. **Verify index exists**:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'articles'
AND indexname = 'idx_articles_deep_summary';
```

3. **Test insert/update**:

```sql
-- Insert test data
INSERT INTO articles (title, url, deep_summary, deep_summary_generated_at)
VALUES ('Test Article', 'https://example.com/test', 'Test summary', NOW())
RETURNING id, deep_summary, deep_summary_generated_at;

-- Update existing article
UPDATE articles
SET deep_summary = 'Updated summary',
    deep_summary_generated_at = NOW()
WHERE id = 'your-article-id';
```

### Automated Testing

Run the verification script:

```bash
python3 scripts/migrations/verify_schema.py
```

Expected output:

```
✓ Schema verification successful!
✓ articles.deep_summary column exists
✓ articles.deep_summary_generated_at column exists
✓ Index idx_articles_deep_summary appears to be working
```

## Integration Points

### Backend API

The deep summary columns will be used by:

1. **POST /api/articles/{article_id}/deep-summary** - Generate and store deep summary
2. **GET /api/articles/{article_id}/deep-summary** - Retrieve cached deep summary

### Caching Logic

```python
# Check if summary exists
existing = supabase.table('articles')\
    .select('deep_summary, deep_summary_generated_at')\
    .eq('id', article_id)\
    .single()\
    .execute()

if existing.data and existing.data.get('deep_summary'):
    # Return cached summary
    return existing.data['deep_summary']

# Generate new summary
summary = await llm_service.generate_deep_summary(article_url)

# Store in database
supabase.table('articles')\
    .update({
        'deep_summary': summary,
        'deep_summary_generated_at': datetime.utcnow()
    })\
    .eq('id', article_id)\
    .execute()
```

## Performance Considerations

1. **Index Usage**: The partial index ensures fast lookups when checking for existing summaries
2. **Column Size**: TEXT columns can store large summaries without size limits
3. **Null Values**: Articles without summaries have NULL values, which don't consume significant space

## Security Considerations

1. **Shared Data**: Deep summaries are shared across all users (not user-specific)
2. **No RLS Needed**: Since summaries are public, no Row Level Security policies are required
3. **Input Validation**: Backend should validate summary content before storing

## Rollback

If needed, rollback the migration:

```sql
-- Remove index
DROP INDEX IF EXISTS idx_articles_deep_summary;

-- Remove columns
ALTER TABLE articles DROP COLUMN IF EXISTS deep_summary;
ALTER TABLE articles DROP COLUMN IF EXISTS deep_summary_generated_at;
```

## Next Steps

After completing this task:

1. ✓ Task 1.4 completed - Schema extended
2. → Task 1.5 - Set up Row Level Security (RLS) policies
3. → Task 2.7 - Implement Deep Summary API endpoints
4. → Task 2.8 - Write property-based tests for deep summary

## References

- Design Document: `.kiro/specs/cross-platform-feature-parity/design.md`
- Requirements: `.kiro/specs/cross-platform-feature-parity/requirements.md`
- Tasks: `.kiro/specs/cross-platform-feature-parity/tasks.md`
