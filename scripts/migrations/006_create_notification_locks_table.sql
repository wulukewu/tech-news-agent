-- Migration 006: Create notification_locks table
-- Task 1.1: Create database migration for notification_locks table (part of user_notification_preferences feature)
-- Requirements: 4.4, 4.5, 4.7, 10.1, 10.2, 10.3, 10.4, 10.5
--
-- This migration creates the notification_locks table to prevent duplicate notifications
-- when multiple backend instances are running simultaneously. Uses atomic database
-- operations to coordinate notification delivery across instances.
--
-- Lock statuses:
-- - pending: Lock created, ready for processing
-- - processing: Lock acquired by an instance, notification in progress
-- - completed: Notification successfully sent
-- - failed: Notification failed to send

-- Create notification_locks table
CREATE TABLE IF NOT EXISTS notification_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Type of notification (e.g., 'weekly_digest', 'daily_summary')
    notification_type TEXT NOT NULL,

    -- When this notification was scheduled to be sent
    scheduled_time TIMESTAMPTZ NOT NULL,

    -- Lock status for coordination between instances
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Instance ID that acquired the lock
    instance_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Ensure unique lock per user/type/time combination
    UNIQUE(user_id, notification_type, scheduled_time)
);

-- Create indexes for efficient lock queries and cleanup
CREATE INDEX IF NOT EXISTS idx_notification_locks_user_scheduled
    ON notification_locks(user_id, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_notification_locks_status_expires
    ON notification_locks(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_notification_locks_instance_status
    ON notification_locks(instance_id, status);

-- Add comments to document the table and columns
COMMENT ON TABLE notification_locks IS 'Prevents duplicate notifications across multiple backend instances using atomic locking';
COMMENT ON COLUMN notification_locks.user_id IS 'Foreign key to users table, identifies user for this notification lock';
COMMENT ON COLUMN notification_locks.notification_type IS 'Type of notification being locked (weekly_digest, daily_summary, etc.)';
COMMENT ON COLUMN notification_locks.scheduled_time IS 'When this notification was scheduled to be sent';
COMMENT ON COLUMN notification_locks.status IS 'Lock status: pending, processing, completed, or failed';
COMMENT ON COLUMN notification_locks.instance_id IS 'Identifier of the backend instance that acquired this lock';
COMMENT ON COLUMN notification_locks.expires_at IS 'When this lock expires to prevent deadlocks';
