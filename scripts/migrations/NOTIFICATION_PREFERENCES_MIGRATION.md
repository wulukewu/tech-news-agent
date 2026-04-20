# User Notification Preferences Migration

This migration implements the database schema for the **Personalized Notification Frequency** feature, which replaces the system-wide `DM_NOTIFICATION_CRON` with individual user notification preferences.

## Overview

The migration creates two new tables:

1. **`user_notification_preferences`** - Stores individual user notification settings
2. **`notification_locks`** - Prevents duplicate notifications in multi-instance deployments

## Migration Files

- `005_create_user_notification_preferences_table.sql` - Main preferences table
- `006_create_notification_locks_table.sql` - Notification locking mechanism
- `apply_notification_preferences_migration.py` - Python script to apply migrations
- `verify_notification_preferences.py` - Verification script

## Schema Details

### user_notification_preferences Table

| Column              | Type        | Default           | Description                                              |
| ------------------- | ----------- | ----------------- | -------------------------------------------------------- |
| `id`                | UUID        | gen_random_uuid() | Primary key                                              |
| `user_id`           | UUID        | -                 | Foreign key to users table (CASCADE DELETE)              |
| `frequency`         | TEXT        | 'weekly'          | Notification frequency: daily, weekly, monthly, disabled |
| `notification_time` | TIME        | '18:00:00'        | Time of day to send notifications (24-hour format)       |
| `timezone`          | TEXT        | 'Asia/Taipei'     | IANA timezone identifier                                 |
| `dm_enabled`        | BOOLEAN     | true              | Whether Discord DM notifications are enabled             |
| `email_enabled`     | BOOLEAN     | false             | Whether email notifications are enabled                  |
| `created_at`        | TIMESTAMPTZ | now()             | Record creation timestamp                                |
| `updated_at`        | TIMESTAMPTZ | now()             | Last update timestamp                                    |

**Constraints:**

- `UNIQUE(user_id)` - One preference record per user
- `CHECK (frequency IN ('daily', 'weekly', 'monthly', 'disabled'))` - Valid frequency values

**Indexes:**

- `idx_user_notification_preferences_user_id` - Optimizes user lookups
- `idx_user_notification_preferences_frequency` - Optimizes frequency-based queries

### notification_locks Table

| Column              | Type        | Default           | Description                                         |
| ------------------- | ----------- | ----------------- | --------------------------------------------------- |
| `id`                | UUID        | gen_random_uuid() | Primary key                                         |
| `user_id`           | UUID        | -                 | Foreign key to users table (CASCADE DELETE)         |
| `notification_type` | TEXT        | -                 | Type of notification (e.g., 'weekly_digest')        |
| `scheduled_time`    | TIMESTAMPTZ | -                 | When notification was scheduled                     |
| `status`            | TEXT        | 'pending'         | Lock status: pending, processing, completed, failed |
| `instance_id`       | TEXT        | -                 | Backend instance that acquired the lock             |
| `created_at`        | TIMESTAMPTZ | now()             | Lock creation timestamp                             |
| `expires_at`        | TIMESTAMPTZ | -                 | Lock expiration time (prevents deadlocks)           |

**Constraints:**

- `UNIQUE(user_id, notification_type, scheduled_time)` - One lock per user/type/time
- `CHECK (status IN ('pending', 'processing', 'completed', 'failed'))` - Valid status values

**Indexes:**

- `idx_notification_locks_user_scheduled` - Optimizes user/time queries
- `idx_notification_locks_status_expires` - Optimizes cleanup operations
- `idx_notification_locks_instance_status` - Optimizes instance-based queries

## Default Values

New users will receive these default notification preferences:

- **Frequency**: Weekly (every Friday)
- **Time**: 18:00 (6 PM)
- **Timezone**: Asia/Taipei
- **DM Enabled**: true
- **Email Enabled**: false

## How to Apply

### Method 1: Using psql (Recommended)

```bash
# Apply both migrations
psql $DATABASE_URL -f scripts/migrations/005_create_user_notification_preferences_table.sql
psql $DATABASE_URL -f scripts/migrations/006_create_notification_locks_table.sql
```

### Method 2: Using Supabase Dashboard

1. Open your Supabase project dashboard
2. Go to SQL Editor
3. Copy and paste the contents of each migration file
4. Execute the SQL

### Method 3: Using the Python script

```bash
cd scripts/migrations
python apply_notification_preferences_migration.py
```

Note: The Python script only checks if tables exist. You'll still need to apply the SQL manually.

## Verification

After applying the migrations, verify they worked correctly:

```bash
cd scripts/migrations
python verify_notification_preferences.py
```

This will:

- Check that both tables exist and are accessible
- Validate the schema by inserting and removing a test record
- Confirm all constraints and indexes are in place

## Requirements Satisfied

This migration satisfies the following requirements from the spec:

- **4.1**: Create user_notification_preferences table with required fields
- **4.2**: Add foreign key constraint to users table with CASCADE delete
- **4.3**: Add check constraints for frequency enum values
- **4.6**: Add indexes for user_id and frequency columns
- **4.7**: Support database relationships and performance optimization
- **10.1-10.5**: Implement notification locking mechanism for multi-instance coordination

## Integration Notes

After applying these migrations:

1. **Backend Services**: Update notification services to use the new preference system
2. **Default Creation**: Implement logic to create default preferences for new users
3. **Migration Path**: Existing users will need default preferences created
4. **Cleanup**: Remove the old `DM_NOTIFICATION_CRON` environment variable dependency

## Rollback

If you need to rollback these migrations:

```sql
-- Remove the tables (this will cascade delete all data)
DROP TABLE IF EXISTS notification_locks;
DROP TABLE IF EXISTS user_notification_preferences;

-- Remove the trigger function if no other tables use it
DROP FUNCTION IF EXISTS update_updated_at_column();
```

⚠️ **Warning**: Rollback will permanently delete all user notification preferences!
