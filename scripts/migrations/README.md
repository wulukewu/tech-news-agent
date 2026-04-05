# Database Migrations - Row Level Security (RLS)

This directory contains database migration scripts for implementing Row Level Security on the reading_list table.

## Overview

Row Level Security (RLS) ensures that users can only access their own reading list data, providing automatic data isolation at the database level. This is a critical security feature that prevents users from viewing or modifying other users' personal data.

## Migration Files

### 001_enable_rls_reading_list.sql

This migration implements RLS policies for the `reading_list` table:

- **Enables RLS** on the reading_list table
- **SELECT Policy**: Users can only view their own reading list entries (user_id = auth.uid())
- **INSERT Policy**: Users can only insert entries with their own user_id
- **UPDATE Policy**: Users can only update their own reading list entries
- **DELETE Policy**: Users can only delete their own reading list entries

**Validates**: Requirements 10.8

## How to Apply the Migration

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `001_enable_rls_reading_list.sql`
4. Paste into the SQL Editor
5. Click **Run** to execute

### Option 2: Using the Apply Script

```bash
# Run the apply script (displays instructions)
python3 scripts/migrations/apply_rls_migration.py
```

This script will:

- Connect to Supabase
- Display the migration SQL
- Provide instructions for manual execution

## Verification

After applying the migration, verify that RLS is working correctly:

```bash
# Run the verification script
python3 scripts/migrations/verify_rls.py
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
