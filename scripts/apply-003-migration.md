# Apply Migration 003: Extend Feeds Table for Recommendations

## Prerequisites

Task 1.2 must be completed before Task 1.4. This migration adds the necessary columns to support the recommendation system.

## Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Navigate to **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy and paste the entire contents of `scripts/migrations/003_extend_feeds_table_for_recommendations.sql`
6. Click **Run** or press `Ctrl+Enter`
7. Verify success message appears

## Option 2: Using psql Command Line

If you have `DATABASE_URL` set in your `.env` file:

```bash
psql $DATABASE_URL -f scripts/migrations/003_extend_feeds_table_for_recommendations.sql
```

## Option 3: Using the Migration Script

```bash
cd scripts/migrations
./apply_migration.sh 003_extend_feeds_table_for_recommendations.sql
```

## Verification

After applying the migration, verify it worked:

```bash
python3 scripts/migrations/verify_feeds_extension.py
```

Or check manually:

```bash
python3 scripts/check_feeds_schema.py
```

You should see these new columns:

- `is_recommended` (BOOLEAN)
- `recommendation_priority` (INTEGER)
- `description` (TEXT)
- `updated_at` (TIMESTAMPTZ)

## Next Step

Once the migration is applied, you can run the seed script:

```bash
python3 scripts/seed_recommended_feeds.py
```

## Troubleshooting

### Error: "relation 'feeds' does not exist"

The feeds table hasn't been created yet. Run the init script first:

```bash
psql $DATABASE_URL -f scripts/init_supabase.sql
```

### Error: "column already exists"

The migration has already been applied. You can safely proceed to the seed script.

### Error: "permission denied"

Make sure you're using the service role key (not the anon key) in your `SUPABASE_KEY` environment variable.
