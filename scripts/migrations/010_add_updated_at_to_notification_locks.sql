-- Migration 010: Add updated_at column to notification_locks table
-- This column is needed for tracking when locks are updated/released

-- Add updated_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'notification_locks'
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE notification_locks
        ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

        -- Add comment
        COMMENT ON COLUMN notification_locks.updated_at IS 'When this lock was last updated';

        RAISE NOTICE 'Added updated_at column to notification_locks table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in notification_locks table';
    END IF;
END $$;
