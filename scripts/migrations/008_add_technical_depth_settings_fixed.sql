-- Migration: Add technical depth threshold settings (Fixed)
-- Description: Add technical depth filtering to user notification preferences
-- Author: System
-- Date: 2026-04-20

-- Add technical depth columns to user_notification_preferences table
ALTER TABLE user_notification_preferences
ADD COLUMN IF NOT EXISTS tech_depth_threshold VARCHAR(20) DEFAULT 'basic';

ALTER TABLE user_notification_preferences
ADD COLUMN IF NOT EXISTS tech_depth_enabled BOOLEAN DEFAULT false;

-- Add check constraint for valid depth levels (drop first if exists)
ALTER TABLE user_notification_preferences
DROP CONSTRAINT IF EXISTS chk_tech_depth_threshold;

ALTER TABLE user_notification_preferences
ADD CONSTRAINT chk_tech_depth_threshold
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
