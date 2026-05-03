# SQL Initialization Integration Tests

## Overview

The integration tests in `test_sql_init_integration.py` verify that the SQL initialization script (`scripts/init_supabase.sql`) has been executed correctly in your Supabase database.

## Prerequisites

Before running these tests, you must:

1. **Create a Supabase project** (or use an existing one)
2. **Execute the SQL script** in Supabase Dashboard:
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Copy and paste the contents of `scripts/init_supabase.sql`
   - Execute the script
3. **Configure environment variables** in your `.env` file:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-or-service-role-key
   ```

## Running the Tests

Once the prerequisites are met, run the integration tests:

```bash
# Run all SQL integration tests
pytest tests/test_sql_init_integration.py -v

# Run a specific test class
pytest tests/test_sql_init_integration.py::TestSQLInitialization -v

# Run a specific test
pytest tests/test_sql_init_integration.py::TestSQLInitialization::test_users_table_exists -v
```

## What the Tests Verify

### TestSQLInitialization

- SQL script can be executed successfully
- All 5 tables are created (users, feeds, user_subscriptions, articles, reading_list)
- pgvector extension is enabled
- All required indexes are created

### TestTableStructure

- Each table has the correct columns
- Default values are set correctly (e.g., `is_active` defaults to `true`)
- Embedding column exists and allows NULL values

### TestConstraints

- UNIQUE constraints work (discord_id, feed URL, article URL)
- CHECK constraints work (reading_list status, rating range)
- CASCADE DELETE works correctly for foreign keys

## Expected Behavior

- **If the SQL script has been executed**: All tests should pass ✅
- **If the SQL script has NOT been executed**: All tests will fail with "Could not find the table" errors ❌

## Test Data Cleanup

The tests automatically clean up any test data they create, so you don't need to worry about polluting your database.

## Troubleshooting

### Error: "Could not find the table 'public.users' in the schema cache"

This means the SQL script hasn't been executed yet. Follow the prerequisites above.

### Error: "SUPABASE_URL and SUPABASE_KEY must be set"

Make sure your `.env` file contains the required environment variables.

### Error: Connection timeout or network errors

Check that:

- Your Supabase project is running
- Your API key is valid
- Your network connection is stable
- Supabase service is not experiencing downtime (check status.supabase.com)

## Notes

- These are **integration tests** that require a real Supabase database
- They are not mocked - they test against actual database operations
- Run these tests in a development/test environment, not production
- The tests use random IDs to avoid conflicts with existing data
