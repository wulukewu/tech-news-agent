-- Migration: Add technical depth threshold settings
-- Description: Add technical depth filtering to user notification preferences
-- Author: System
-- Date: 2026-04-20

-- Add technical depth columns to user_notification_preferences table
ALTER TABLE user_notification_preferences
ADD COLUMN IF NOT EXISTS tech_depth_threshold VARCHAR(20) DEFAULT 'basic',
ADD COLUMN IF NOT EXISTS tech_depth_enabled BOOLEAN DEFAULT false;

-- Add check constraint for valid depth levels
ALTER TABLE user_notification_preferences
ADD CONSTRAINT IF NOT EXISTS chk_tech_depth_threshold
CHECK (tech_depth_threshold IN ('basic', 'intermediate', 'advanced', 'expert'));

-- Create index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_tech_depth
ON user_notification_preferences(user_id, tech_depth_enabled, tech_depth_threshold);

-- Add comments for documentation
COMMENT ON COLUMN user_notification_preferences.tech_depth_threshold IS 'Minimum technical depth level for notifications (basic, intermediate, advanced, expert)';
COMMENT ON COLUMN user_notification_preferences.tech_depth_enabled IS 'Whether technical depth filtering is enabled';

-- Update existing users with default values (disabled by default for backward compatibility)
UPDATE user_notification_preferences
SET
    tech_depth_threshold = 'basic',
    tech_depth_enabled = false
WHERE
    tech_depth_threshold IS NULL
    OR tech_depth_enabled IS NULL;

-- Verify the migration
DO $$
DECLARE
    column_exists_threshold BOOLEAN;
    column_exists_enabled BOOLEAN;
    constraint_exists BOOLEAN;
    index_exists BOOLEAN;
    updated_count INTEGER;
BEGIN
    -- Check if columns exist
    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'user_notification_preferences'
        AND column_name = 'tech_depth_threshold'
    ) INTO column_exists_threshold;

    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'user_notification_preferences'
        AND column_name = 'tech_depth_enabled'
    ) INTO column_exists_enabled;

    IF NOT column_exists_threshold OR NOT column_exists_enabled THEN
        RAISE EXCEPTION 'Migration failed: Technical depth columns were not created';
    END IF;

    -- Check if constraint exists
    SELECT EXISTS (
        SELECT FROM information_schema.table_constraints
        WHERE table_name = 'user_notification_preferences'
        AND constraint_name = 'chk_tech_depth_threshold'
    ) INTO constraint_exists;

    IF NOT constraint_exists THEN
        RAISE EXCEPTION 'Migration failed: Technical depth constraint was not created';
    END IF;

    -- Check if index exists
    SELECT EXISTS (
        SELECT FROM pg_indexes
        WHERE tablename = 'user_notification_preferences'
        AND indexname = 'idx_user_notification_preferences_tech_depth'
    ) INTO index_exists;

    IF NOT index_exists THEN
        RAISE EXCEPTION 'Migration failed: Technical depth index was not created';
    END IF;

    -- Check if existing records were updated
    SELECT COUNT(*) INTO updated_count
    FROM user_notification_preferences
    WHERE tech_depth_threshold IS NOT NULL AND tech_depth_enabled IS NOT NULL;

    RAISE NOTICE 'Migration completed successfully: Technical depth settings added to % user records', updated_count;
END $$;
