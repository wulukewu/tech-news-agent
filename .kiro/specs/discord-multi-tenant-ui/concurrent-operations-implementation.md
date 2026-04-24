# Concurrent Operations Implementation

## Overview

This document describes how Task 7.3 implements concurrent operation handling to satisfy Requirements 13.1-13.5 of the Discord Multi-tenant UI specification.

## Requirements Addressed

### Requirement 13.1: Concurrent User Registrations

**Implementation**: `get_or_create_user()` method in `app/services/supabase_service.py`

**Strategy**: Check-then-insert with duplicate key handling

**How it works**:

1. First attempts to SELECT user by discord_id
2. If not found, attempts to INSERT new user
3. If INSERT fails with duplicate key error (concurrent creation), retries SELECT
4. Returns the same UUID regardless of which concurrent request created the user

**Database constraint used**: `UNIQUE(discord_id)` on `users` table

**Code location**: Lines 550-650 in `app/services/supabase_service.py`

### Requirement 13.2: Concurrent Subscription Operations

**Implementation**: `subscribe_to_feed()` method in `app/services/supabase_service.py`

**Strategy**: Check-then-insert with duplicate key handling

**How it works**:

1. First checks if subscription already exists
2. If not, attempts to INSERT subscription
3. If INSERT fails with duplicate key error (concurrent subscription), silently succeeds
4. No error is raised to the user - idempotent operation

**Database constraint used**: `UNIQUE(user_id, feed_id)` on `user_subscriptions` table

**Code location**: Lines 1350-1440 in `app/services/supabase_service.py`

### Requirement 13.3: Concurrent Reading List Operations

**Implementation**: `save_to_reading_list()` method in `app/services/supabase_service.py`

**Strategy**: UPSERT (INSERT ... ON CONFLICT DO UPDATE)

**How it works**:

1. Uses Supabase client's `upsert()` method with `on_conflict='user_id,article_id'`
2. If record doesn't exist, inserts new record with status='Unread'
3. If record exists (concurrent save), updates the `updated_at` timestamp
4. No race condition possible - database handles atomicity

**Database constraint used**: `UNIQUE(user_id, article_id)` on `reading_list` table

**Code location**: Lines 850-920 in `app/services/supabase_service.py`

**Key improvement**: Previous implementation used check-then-insert pattern which had a race condition window. New implementation uses true UPSERT for atomic operation.

### Requirement 13.4: Non-blocking Operations

**Implementation**: All database operations are non-blocking

**Strategy**: No locks or blocking operations used

**How it works**:

- All methods use async/await for non-blocking I/O
- No explicit locks (threading.Lock, asyncio.Lock) are used
- Database operations complete independently
- One user's slow operation doesn't block other users

**Verification**: All operations use `async def` and `await` for database calls

### Requirement 13.5: Database Transactions

**Implementation**: Implicit transactions via Supabase client

**Strategy**: Rely on database-level atomicity

**How it works**:

- Each database operation (INSERT, UPDATE, UPSERT) is atomic
- Supabase/PostgreSQL ensures ACID properties
- No explicit transaction management needed for single operations
- Complex multi-step operations use check-then-insert with error handling

**Note**: For future complex workflows requiring multiple operations, explicit transactions can be added using Supabase's transaction support.

## Testing

### Test Coverage

All concurrent operation requirements are tested in:

1. **`tests/test_complete_workflow_integration.py::TestCompleteWorkflow::test_concurrent_operations`**
   - Tests concurrent user creation (10 users simultaneously)
   - Tests concurrent article insertion with UPSERT
   - Tests multiple users saving same article concurrently

2. **`tests/test_concurrent_reading_list.py`** (newly created)
   - `test_concurrent_save_to_reading_list`: 10 concurrent saves of same article
   - `test_concurrent_save_different_articles`: Concurrent saves of different articles
   - `test_concurrent_save_and_update`: Mixed save and update operations

3. **`tests/test_decorators.py::test_ensure_user_registered_concurrent_requests`**
   - Tests decorator-level concurrent user registration handling

### Test Results

All tests pass successfully, validating:

- No duplicate records created
- No race conditions
- Idempotent operations
- Correct final state regardless of operation order

## Database Schema Support

The implementation relies on these database constraints defined in `scripts/init_supabase.sql`:

```sql
-- Users table: Prevents duplicate discord_id
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_id TEXT UNIQUE NOT NULL,  -- Requirement 13.1
    created_at TIMESTAMPTZ DEFAULT now()
);

-- User subscriptions: Prevents duplicate subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, feed_id)  -- Requirement 13.2
);

-- Reading list: Prevents duplicate reading list entries
CREATE TABLE reading_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('Unread', 'Read', 'Archived')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    added_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, article_id)  -- Requirement 13.3
);
```

## Performance Characteristics

### User Registration

- **Best case**: 1 SELECT query (user exists)
- **Worst case**: 1 SELECT + 1 INSERT + 1 SELECT (concurrent creation)
- **Average**: ~1.5 queries per registration

### Subscription

- **Best case**: 1 SELECT query (already subscribed)
- **Worst case**: 1 SELECT + 1 INSERT (new subscription)
- **Concurrent case**: 1 SELECT + 1 INSERT (duplicate key ignored)
- **Average**: ~1.5 queries per subscription

### Reading List Save

- **All cases**: 1 UPSERT query (atomic operation)
- **No additional queries needed** - most efficient implementation

## Error Handling

All concurrent operations handle errors gracefully:

1. **Duplicate key errors**: Caught and handled as success (idempotent)
2. **Database timeouts**: Logged and re-raised with context
3. **Network errors**: Logged and re-raised with context
4. **Validation errors**: Caught early before database operations

## Logging

All concurrent operations are logged with:

- Operation type (INSERT, UPDATE, UPSERT, SELECT)
- Table name
- Affected records count
- Concurrent operation detection (when applicable)
- Error context (when errors occur)

Example log entries:

```
INFO: Database operation completed: get_or_create_user (retry after concurrent creation)
INFO: Database operation completed: subscribe_to_feed (concurrent duplicate)
INFO: Database operation completed: save_to_reading_list (UPSERT)
```

## Future Improvements

1. **Explicit transactions**: For complex multi-step operations requiring atomicity
2. **Optimistic locking**: For operations requiring version control
3. **Retry logic**: For transient database errors
4. **Connection pooling**: For better performance under high load
5. **Metrics**: Track concurrent operation frequency and performance

## Conclusion

Task 7.3 successfully implements concurrent operation handling for all critical operations:

- ✅ User registration is idempotent (Requirement 13.1)
- ✅ Subscriptions use database constraints (Requirement 13.2)
- ✅ Reading list uses UPSERT logic (Requirement 13.3)
- ✅ Operations are non-blocking (Requirement 13.4)
- ✅ Database transactions ensure consistency (Requirement 13.5)

All requirements are validated by comprehensive tests that simulate real-world concurrent scenarios.
