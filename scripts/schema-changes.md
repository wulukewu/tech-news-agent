# Schema Changes: Task 1.4

## Visual Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      articles TABLE                          │
├─────────────────────────────────────────────────────────────┤
│ EXISTING COLUMNS:                                            │
│  • id                    UUID PRIMARY KEY                    │
│  • feed_id               UUID                                │
│  • title                 TEXT NOT NULL                       │
│  • url                   TEXT UNIQUE NOT NULL                │
│  • published_at          TIMESTAMPTZ                         │
│  • tinkering_index       INTEGER                             │
│  • ai_summary            TEXT                                │
│  • embedding             VECTOR(1536)                        │
│  • created_at            TIMESTAMPTZ                         │
├─────────────────────────────────────────────────────────────┤
│ NEW COLUMNS (Task 1.4):                                      │
│  ✨ deep_summary          TEXT                               │
│  ✨ deep_summary_generated_at  TIMESTAMPTZ                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         INDEXES                              │
├─────────────────────────────────────────────────────────────┤
│ EXISTING:                                                    │
│  • idx_articles_feed_id                                      │
│  • idx_articles_published_at                                 │
│  • idx_articles_embedding (HNSW)                             │
├─────────────────────────────────────────────────────────────┤
│ NEW (Task 1.4):                                              │
│  ✨ idx_articles_deep_summary (PARTIAL)                      │
│     WHERE deep_summary IS NOT NULL                           │
└─────────────────────────────────────────────────────────────┘
```

## Column Details

### deep_summary

- **Type**: TEXT
- **Nullable**: YES
- **Purpose**: Store AI-generated deep analysis summaries
- **Shared**: Yes (not user-specific, shared across all users)
- **Size**: Unlimited (TEXT type)

**Example Value**:

```
This article discusses the implementation of vector databases...
Key points:
1. Performance considerations for HNSW indexes
2. Trade-offs between accuracy and speed
3. Best practices for embedding generation
...
```

### deep_summary_generated_at

- **Type**: TIMESTAMPTZ (Timestamp with timezone)
- **Nullable**: YES
- **Purpose**: Track when the summary was generated
- **Use Case**: Cache invalidation, analytics, debugging

**Example Value**:

```
2024-01-15 14:30:22.123456+00
```

## Index Details

### idx_articles_deep_summary

- **Type**: Partial B-tree index
- **Columns**: id
- **Condition**: WHERE deep_summary IS NOT NULL
- **Purpose**: Optimize queries checking for existing summaries

**Optimized Queries**:

```sql
-- Fast: Uses the partial index
SELECT id, deep_summary
FROM articles
WHERE id = 'some-uuid'
AND deep_summary IS NOT NULL;

-- Fast: Index scan
SELECT COUNT(*)
FROM articles
WHERE deep_summary IS NOT NULL;
```

## Data Flow

```
┌─────────────┐
│   User      │
│  Request    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Check if deep_summary exists       │
│  SELECT deep_summary                │
│  WHERE id = ? AND                   │
│  deep_summary IS NOT NULL           │
│  ← Uses idx_articles_deep_summary   │
└──────┬──────────────────────────────┘
       │
       ├─── EXISTS ──→ Return cached summary
       │
       └─── NULL ────→ Generate new summary
                       │
                       ▼
                ┌──────────────────┐
                │  Call LLM API    │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────────────┐
                │  UPDATE articles         │
                │  SET deep_summary = ?,   │
                │      deep_summary_       │
                │      generated_at = NOW()│
                └──────────────────────────┘
```

## Storage Considerations

### Size Estimates

Assuming:

- Average deep summary: 2,000 characters
- 10,000 articles with summaries

**Storage**:

- Column data: ~20 MB (2KB × 10,000)
- Index overhead: ~1-2 MB
- Total: ~22 MB

### Performance Impact

- **Minimal**: Partial index only indexes articles with summaries
- **Read Performance**: Significantly improved for cache checks
- **Write Performance**: Negligible impact (index only updated when summary exists)

## Comparison: ai_summary vs deep_summary

| Feature        | ai_summary           | deep_summary          |
| -------------- | -------------------- | --------------------- |
| **Purpose**    | Quick summary        | Detailed analysis     |
| **Length**     | Short (~200 chars)   | Long (~2000 chars)    |
| **Generation** | Fast                 | Slower (more tokens)  |
| **Use Case**   | Article list preview | Full article analysis |
| **Indexed**    | No                   | Yes (partial)         |
| **Timestamp**  | No                   | Yes                   |

## Migration Safety

✅ **Safe to run on production**:

- Uses `IF NOT EXISTS` - idempotent
- Non-blocking - doesn't lock table
- Nullable columns - no data required
- Partial index - minimal overhead

⚠️ **Considerations**:

- Large tables: Index creation may take time
- Concurrent writes: Safe, but may be slightly slower during index creation

## Rollback Plan

If needed, rollback with:

```sql
-- Remove index
DROP INDEX IF EXISTS idx_articles_deep_summary;

-- Remove columns
ALTER TABLE articles
DROP COLUMN IF EXISTS deep_summary,
DROP COLUMN IF EXISTS deep_summary_generated_at;
```

**Impact**: No data loss (only removes new columns)

## Testing Queries

### Verify Schema

```sql
-- Check columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'articles'
AND column_name IN ('deep_summary', 'deep_summary_generated_at');

-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'articles'
AND indexname = 'idx_articles_deep_summary';
```

### Test Functionality

```sql
-- Insert test article with summary
INSERT INTO articles (title, url, deep_summary, deep_summary_generated_at)
VALUES (
    'Test Article',
    'https://example.com/test-' || gen_random_uuid(),
    'This is a test deep summary',
    NOW()
)
RETURNING id, deep_summary, deep_summary_generated_at;

-- Query with index
EXPLAIN ANALYZE
SELECT id, deep_summary
FROM articles
WHERE deep_summary IS NOT NULL
LIMIT 10;
```

## References

- Task: `.kiro/specs/cross-platform-feature-parity/tasks.md` (Task 1.4)
- Requirements: 4.7, 9.7
- Design: `.kiro/specs/cross-platform-feature-parity/design.md`
