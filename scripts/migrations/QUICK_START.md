# Quick Start: Task 1.4 Migration

## For Existing Databases

### Step 1: Ensure Prerequisites

Make sure you have:

- PostgreSQL client (`psql`) installed
- `DATABASE_URL` set in your `.env` file
- Python 3 with `supabase` and `python-dotenv` packages

### Step 2: Apply Migration

```bash
# Option A: Using the shell script (recommended)
./scripts/migrations/apply_migration.sh scripts/migrations/001_add_deep_summary_to_articles.sql

# Option B: Using psql directly
psql $DATABASE_URL -f scripts/migrations/001_add_deep_summary_to_articles.sql
```

### Step 3: Verify Changes

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

## For New Installations

No action needed! The changes are already included in:

- `scripts/init_supabase.sql`
- `backend/scripts/init_supabase.sql`

## What This Migration Does

Adds two columns to the `articles` table:

1. `deep_summary` (TEXT) - Stores AI-generated deep analysis
2. `deep_summary_generated_at` (TIMESTAMPTZ) - Timestamp of generation

Plus a partial index for performance:

- `idx_articles_deep_summary` - Optimizes summary existence checks

## Troubleshooting

### Error: "DATABASE_URL not set"

Add to your `.env` file:

```bash
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

Get it from: Supabase Dashboard > Settings > Database > Connection string

### Error: "relation 'articles' does not exist"

Run the full init script first:

```bash
psql $DATABASE_URL -f scripts/init_supabase.sql
```

### Error: "column already exists"

This is safe to ignore - the migration is idempotent and uses `IF NOT EXISTS`.

## Need Help?

See detailed documentation:

- `scripts/migrations/TASK_1.4_DOCUMENTATION.md` - Full documentation
- `scripts/migrations/README.md` - Migration guide
- `scripts/migrations/TASK_1.4_SUMMARY.md` - What was done
