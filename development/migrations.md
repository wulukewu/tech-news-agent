# Database Migrations Guide

This document consolidates all database migration documentation for the Tech News Agent project.

## Overview

The project uses SQL migrations to manage database schema changes. All migrations are located in `scripts/migrations/`.

## Migration Files

### 002: User Preferences Table

**File**: `scripts/migrations/002_create_user_preferences_table.sql`

Creates the `user_preferences` table for tracking onboarding progress and user settings.

**Documentation**: See [User Preferences Migration](./USER_PREFERENCES_MIGRATION.md)

**Verification**:

```bash
python3 scripts/migrations/verify_user_preferences.py
```

### 003: Feeds Table Extension

**File**: `scripts/migrations/003_extend_feeds_table_for_recommendations.sql`

Extends the `feeds` table to support the recommendation system.

**Columns Added**:

- `is_recommended` (BOOLEAN)
- `recommendation_priority` (INTEGER)
- `description` (TEXT)
- `updated_at` (TIMESTAMPTZ)

**Documentation**: See migration README in `scripts/migrations/TASK_1.4_README.md`

**Verification**:

```bash
python3 scripts/migrations/verify_feeds_extension.py
```

### 004: Analytics Events Table

**File**: `scripts/migrations/004_create_analytics_events_table.sql`

Creates the `analytics_events` table for tracking user onboarding analytics.

**Verification**:

```bash
python3 scripts/migrations/verify_analytics_events.py
```

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to Supabase Dashboard > SQL Editor
2. Copy the migration SQL file content
3. Paste and execute

### Option 2: Command Line (psql)

```bash
psql $DATABASE_URL -f scripts/migrations/002_create_user_preferences_table.sql
```

### Option 3: Python Scripts

```bash
# Apply specific migration
python3 scripts/migrations/apply_user_preferences_migration.py
```

## Seed Data

### Recommended Feeds

After applying migration 003, seed the recommended feeds:

```bash
python3 scripts/seed_recommended_feeds.py
```

**Verification**:

```bash
python3 scripts/verify_recommended_feeds.py
```

## Migration History

| Migration | Description            | Requirements                 | Status      |
| --------- | ---------------------- | ---------------------------- | ----------- |
| 002       | User Preferences Table | 1.4, 10.1, 10.2, 11.7        | ✅ Complete |
| 003       | Feeds Table Extension  | 2.2, 2.3, 12.5               | ✅ Complete |
| 004       | Analytics Events Table | 14.1, 14.3, 14.4, 14.5, 14.6 | ✅ Complete |

## Related Documentation

- [User Preferences Migration](./USER_PREFERENCES_MIGRATION.md) - Detailed documentation for migration 002
- [Analytics Service](./ANALYTICS_SERVICE.md) - Analytics service implementation
- [Onboarding Service](./ONBOARDING_SERVICE.md) - Onboarding service implementation

## Troubleshooting

### Missing Columns Error

If you get errors about missing columns, ensure all migrations are applied in order:

1. Check current schema: `python3 scripts/check_feeds_schema.py`
2. Apply missing migrations
3. Verify with verification scripts

### Connection Errors

Ensure your `.env` file has correct Supabase credentials:

- `SUPABASE_URL`
- `SUPABASE_KEY`

### Rollback

To rollback migration 003:

```bash
psql $DATABASE_URL -f scripts/migrations/003_rollback_feeds_extension.sql
```

**Warning**: This will remove recommendation-related columns and data.
