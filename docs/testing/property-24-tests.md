# Property 24 Tests - Setup Instructions

## Overview

The Property 24 tests verify the **Onboarding UI Conditional Display** logic, which determines when the onboarding modal should be shown to users based on their completion and skip states.

## Prerequisites

Before running the Property 24 tests, you **MUST** ensure the `user_preferences` table exists in your test database.

### Step 1: Apply the Migration

Run the migration script to create the `user_preferences` table:

```bash
python3 scripts/migrations/apply_user_preferences_migration.py
```

If the script indicates the table doesn't exist, you have two options:

#### Option A: Using psql (Recommended)

```bash
psql $DATABASE_URL -f scripts/migrations/002_create_user_preferences_table.sql
```

#### Option B: Using Supabase Dashboard

1. Open your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy the contents of `scripts/migrations/002_create_user_preferences_table.sql`
4. Paste and execute the SQL

### Step 2: Verify the Migration

Verify the table was created successfully:

```bash
python3 scripts/migrations/verify_user_preferences.py
```

You should see:

```
✓ user_preferences table exists
✓ All required columns exist
✓ All indexes exist
```

## Running the Tests

Once the migration is applied, run the Property 24 tests:

```bash
# Run all Property 24 tests
python3 -m pytest backend/tests/test_onboarding_property_24.py -v

# Run a specific test
python3 -m pytest backend/tests/test_onboarding_property_24.py::test_property_24_new_user_should_show_onboarding -v

# Run with Hypothesis verbosity
HYPOTHESIS_PROFILE=debug python3 -m pytest backend/tests/test_onboarding_property_24.py -v
```

## Test Coverage

The Property 24 test suite includes:

1. **Core Logic Tests**
   - Truth table verification (all 4 combinations of completed/skipped)
   - New user default state
   - Completed user state
   - Skipped user state
   - In-progress user state

2. **State Transition Tests**
   - Transition from in-progress to completed
   - Transition from in-progress to skipped
   - Reset after completion

3. **Property-Based Tests** (using Hypothesis)
   - Random state combinations
   - Progress update sequences
   - Multiple query consistency
   - Action sequence verification

## Troubleshooting

### Error: "Could not find the table 'public.user_preferences'"

This means the migration hasn't been applied. Follow Step 1 above.

### Hypothesis HealthCheck Warnings

The tests use `@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])` to allow property-based testing with function-scoped fixtures. This is intentional and safe for these tests.

### Test Database Cleanup

The tests use the `test_user` fixture which automatically cleans up test data after each test. If you encounter orphaned data, you can manually clean up:

```sql
DELETE FROM user_preferences WHERE user_id IN (
  SELECT id FROM users WHERE discord_id LIKE 'test_user_%'
);
```

## Requirements Validated

These tests validate:

- **Requirement 10.4**: 首次登入的用戶應自動看到引導 Modal
- **Requirement 10.5**: 已完成或跳過引導的用戶不應再看到 Modal

## Related Files

- **Service**: `backend/app/services/onboarding_service.py`
- **Schema**: `backend/app/schemas/onboarding.py`
- **Migration**: `scripts/migrations/002_create_user_preferences_table.sql`
- **Design**: `.kiro/specs/new-user-onboarding-system/design.md` (Property 24)
