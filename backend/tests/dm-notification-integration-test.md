# DM Notification Integration Test

## Overview

This document describes the integration tests for the DM notification flow, implemented as part of Task 10 in the bugfix spec for DM and Reading List fixes.

## Test File

`backend/tests/test_dm_notification_integration.py`

## Prerequisites

### Database Migration Required

These integration tests require the `dm_sent_articles` table to exist in the database. This table was created in Task 7.1 of the bugfix implementation.

**Migration File:** `backend/scripts/migrations/003_create_dm_sent_articles_table.sql`

### Applying the Migration

If the tests are skipped with the message:

```
dm_sent_articles table migration not applied
```

Follow these steps:

1. Run the migration helper script:

   ```bash
   cd backend
   python3 tests/apply_dm_sent_articles_migration.py
   ```

2. Copy the SQL output and execute it in your Supabase SQL Editor

3. Verify the table was created:

   ```sql
   SELECT * FROM dm_sent_articles LIMIT 1;
   ```

4. Run the tests again:
   ```bash
   python3 -m pytest tests/test_dm_notification_integration.py -v
   ```

## Test Coverage

The integration tests verify the complete DM notification flow:

### 1. Full DM Notification Flow

- **Test:** `test_full_dm_notification_flow`
- **Coverage:** Query articles → send DM → record sent articles → query again
- **Validates:** Requirements 2.1, 2.2, 3.1, 3.2, 3.3

### 2. Multiple Users Simultaneous Notifications

- **Test:** `test_multiple_users_simultaneous_notifications`
- **Coverage:** Multiple users receiving notifications concurrently
- **Validates:** Requirements 2.1, 2.2

### 3. Weekly Digest Overlapping Time Windows

- **Test:** `test_weekly_digest_overlapping_time_windows`
- **Coverage:** Weekly digest schedule with overlapping 7-day windows
- **Validates:** Requirements 2.1, 2.2, 3.2

### 4. Sent Articles Persist Across Service Restarts

- **Test:** `test_sent_articles_persist_across_service_restarts`
- **Coverage:** Sent articles tracking persists when service restarts
- **Validates:** Requirements 2.1, 2.2

### 5. Edge Case: Empty Sent Articles

- **Test:** `test_edge_case_empty_sent_articles`
- **Coverage:** First-time users with no sent articles history
- **Validates:** Requirements 3.1, 3.2, 3.3

### 6. Edge Case: All Articles Sent

- **Test:** `test_edge_case_all_articles_sent`
- **Coverage:** Users who have received all available articles
- **Validates:** Requirements 2.1, 2.2

### 7. Edge Case: Partial Overlap

- **Test:** `test_edge_case_partial_overlap`
- **Coverage:** Some articles sent, some not sent
- **Validates:** Requirements 2.1, 2.2

### 8. DM Notification Service Integration

- **Test:** `test_dm_notification_service_integration`
- **Coverage:** Full DMNotificationService with mocked Discord bot
- **Validates:** Requirements 2.1, 2.2

## Running the Tests

### Run all integration tests:

```bash
cd backend
python3 -m pytest tests/test_dm_notification_integration.py -v
```

### Run a specific test:

```bash
python3 -m pytest tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_full_dm_notification_flow -v
```

### Run with detailed output:

```bash
python3 -m pytest tests/test_dm_notification_integration.py -vv -s
```

## Expected Results

When the migration is applied and the bugfix is correctly implemented, all 8 tests should pass:

```
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_full_dm_notification_flow PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_multiple_users_simultaneous_notifications PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_weekly_digest_overlapping_time_windows PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_sent_articles_persist_across_service_restarts PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_edge_case_empty_sent_articles PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_edge_case_all_articles_sent PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_edge_case_partial_overlap PASSED
tests/test_dm_notification_integration.py::TestDMNotificationIntegration::test_dm_notification_service_integration PASSED
```

## Troubleshooting

### Tests are skipped

- **Cause:** Migration not applied
- **Solution:** Follow the "Applying the Migration" steps above

### Tests fail with "table not found"

- **Cause:** Migration SQL not executed in Supabase
- **Solution:** Manually run the SQL from `003_create_dm_sent_articles_table.sql` in Supabase SQL Editor

### Tests fail with "invalid literal for int()"

- **Cause:** Discord ID format issue
- **Solution:** This has been fixed in the test code. Ensure you're using the latest version.

## Related Files

- **Bugfix Spec:** `.kiro/specs/dm-and-reading-list-fixes/`
- **Design Document:** `.kiro/specs/dm-and-reading-list-fixes/design.md`
- **Tasks:** `.kiro/specs/dm-and-reading-list-fixes/tasks.md`
- **Migration:** `backend/scripts/migrations/003_create_dm_sent_articles_table.sql`
- **SupabaseService:** `backend/app/services/supabase_service.py`
- **DMNotificationService:** `backend/app/services/dm_notification_service.py`

## Requirements Validated

These integration tests validate the following requirements from the bugfix spec:

- **2.1:** System queries only NEW articles not previously sent
- **2.2:** System tracks and excludes sent articles from future notifications
- **3.1:** Subscription filtering is preserved
- **3.2:** Time window filtering (7 days) is preserved
- **3.3:** Limit (20 articles) and ordering (tinkering_index DESC) are preserved
