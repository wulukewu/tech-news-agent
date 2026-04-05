# Database Migrations

This directory contains database migration scripts for the Tech News Agent system.

## Overview

Database migrations are versioned SQL scripts that modify the database schema. Each migration is numbered sequentially and includes verification scripts and documentation.

## Migration Files

### 001_enable_rls_reading_list.sql

This migration implements RLS policies for the `reading_list` table:

- **Enables RLS** on the reading_list table
- **SELECT Policy**: Users can only view their own reading list entries (user_id = auth.uid())
- **INSERT Policy**: Users can only insert entries with their own user_id
- **UPDATE Policy**: Users can only update their own reading list entries
- **DELETE Policy**: Users can only delete their own reading list entries

**Validates**: Requirements 10.8

### 002_create_user_preferences_table.sql

This migration creates the `user_preferences` table for storing user onboarding progress and preferences:

- **Creates user_preferences table** with onboarding tracking fields
- **Creates indexes** for efficient querying by user_id
- **Creates trigger** to auto-update updated_at timestamp
- **Enables RLS** with policies for user data isolation

**Validates**: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 13.4

### 003_extend_feeds_table_for_recommendations.sql

This migration extends the `feeds` table to support the recommendation system:

- **Adds columns**: is_recommended, recommendation_priority, description, updated_at
- **Creates indexes** for efficient recommendation queries
- **Creates trigger** to auto-update updated_at timestamp

**Validates**: Requirements 12.1, 12.2, 12.3, 12.4

### 004_create_analytics_events_table.sql

This migration creates the `analytics_events` table for tracking user onboarding events:

- **Creates analytics_events table** with event tracking fields (user_id, event_type, event_data, created_at)
- **Creates indexes** for efficient analytics queries (user_id, event_type, created_at, event_data GIN)
- **Supports event types**: onboarding_started, step_completed, onboarding_skipped, onboarding_finished, tooltip_shown, tooltip_skipped, feed_subscribed_from_onboarding
- **JSONB event_data** for flexible event metadata storage

**Validates**: Requirements 14.1, 14.2, 14.3

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of the migration file (e.g., `003_extend_feeds_table_for_recommendations.sql`)
4. Paste into the SQL Editor
5. Click **Run** to execute

### Option 2: Using psql (if you have direct database access)

```bash
psql $DATABASE_URL -f scripts/migrations/003_extend_feeds_table_for_recommendations.sql
```

## Verification

After applying each migration, run its verification script:

```bash
# Verify RLS migration
python3 scripts/migrations/verify_rls.py

# Verify user_preferences migration
python3 scripts/migrations/verify_user_preferences.py

# Verify feeds extension migration
python3 scripts/migrations/verify_feeds_extension.py

# Verify analytics_events migration
python3 scripts/migrations/verify_analytics_events.py
```

### Manual Verification in Supabase Dashboard

1. Go to **Authentication > Policies**
2. Select table: `reading_list`
3. Verify that 4 policies are listed:
   - `reading_list_select_policy`
   - `reading_list_insert_policy`
   - `reading_list_update_policy`
   - `reading_list_delete_policy`

## Testing

Run the RLS test suite to validate policy behavior:

```bash
# Run RLS tests
pytest tests/test_rls_policies.py -v
```

The test suite validates:

- RLS is enabled on reading_list table
- Users can insert their own reading list entries
- Users can select their own reading list entries
- Users can update their own reading list entries
- Users can delete their own reading list entries
- User A cannot see User B's reading list entries
- RLS policies enforce user_id = auth.uid() constraint

## RLS Policy Details

### SELECT Policy

```sql
CREATE POLICY reading_list_select_policy ON reading_list
    FOR SELECT
    USING (user_id = auth.uid());
```

**Effect**: Users can only query reading list entries where `user_id` matches their authenticated user ID.

### INSERT Policy

```sql
CREATE POLICY reading_list_insert_policy ON reading_list
    FOR INSERT
    WITH CHECK (user_id = auth.uid());
```

**Effect**: Users can only insert reading list entries with their own `user_id`.

### UPDATE Policy

```sql
CREATE POLICY reading_list_update_policy ON reading_list
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```

**Effect**: Users can only update reading list entries they own, and cannot change the `user_id` to another user.

### DELETE Policy

```sql
CREATE POLICY reading_list_delete_policy ON reading_list
    FOR DELETE
    USING (user_id = auth.uid());
```

**Effect**: Users can only delete their own reading list entries.

## Security Benefits

1. **Automatic Data Isolation**: Database-level enforcement ensures users cannot access other users' data
2. **Defense in Depth**: Even if application-level checks fail, RLS provides a security layer
3. **Simplified Application Code**: No need to manually filter by user_id in every query
4. **Audit Trail**: RLS policies are logged and can be audited

## Important Notes

- RLS policies use `auth.uid()` which requires authenticated requests with valid JWT tokens
- Service role keys bypass RLS (used for admin operations and testing)
- RLS policies are enforced at the database level, providing strong security guarantees
- All queries to reading_list table automatically apply RLS policies

## Troubleshooting

### RLS Not Working

If RLS doesn't seem to be working:

1. Verify RLS is enabled:

   ```sql
   SELECT relname, relrowsecurity
   FROM pg_class
   WHERE relname = 'reading_list';
   ```

   `relrowsecurity` should be `true`

2. Check policies exist:

   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'reading_list';
   ```

   Should return 4 policies

3. Verify JWT token contains correct user_id:
   - Check that `auth.uid()` returns the expected user UUID
   - Ensure JWT token is valid and not expired

### Access Denied Errors

If you get "access denied" errors:

- Ensure you're using a valid JWT token with the correct user_id
- Check that the user_id in your request matches auth.uid()
- Verify the user exists in the users table

## Related Requirements

- **Requirement 10.8**: System SHALL use Row Level Security (RLS) policies to ensure data isolation
- **Requirement 10.1-10.7**: User data isolation requirements
- **Requirement 11**: Data consistency and Single Source of Truth

## Next Steps

After applying RLS:

1. Update API endpoints to use authenticated requests
2. Implement JWT token validation in backend
3. Test cross-platform synchronization with RLS enabled
4. Monitor RLS policy performance in production
