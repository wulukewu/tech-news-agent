-- Migration 009: Add notification day fields for weekly and monthly notifications
-- Date: 2026-04-21
-- Purpose: Add notification_day_of_week and notification_day_of_month fields to support
--          more granular control over weekly and monthly notification scheduling

-- Add notification_day_of_week column for weekly notifications
-- 0 = Sunday, 1 = Monday, ..., 6 = Saturday
-- Default: 5 (Friday) to match existing behavior
ALTER TABLE user_notification_preferences
ADD COLUMN IF NOT EXISTS notification_day_of_week INTEGER DEFAULT 5
CHECK (notification_day_of_week >= 0 AND notification_day_of_week <= 6);

-- Add notification_day_of_month column for monthly notifications
-- 1-31 representing the day of the month
-- Default: 1 (first day of month)
ALTER TABLE user_notification_preferences
ADD COLUMN IF NOT EXISTS notification_day_of_month INTEGER DEFAULT 1
CHECK (notification_day_of_month >= 1 AND notification_day_of_month <= 31);

-- Add comments for documentation
COMMENT ON COLUMN user_notification_preferences.notification_day_of_week IS
'Day of week for weekly notifications (0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday). Default: 5 (Friday)';

COMMENT ON COLUMN user_notification_preferences.notification_day_of_month IS
'Day of month for monthly notifications (1-31). If the specified day does not exist in a month (e.g., Feb 31), the notification will be sent on the last day of that month. Default: 1 (first day of month)';

-- Update existing records to have default values
UPDATE user_notification_preferences
SET
    notification_day_of_week = 5,  -- Friday
    notification_day_of_month = 1   -- First day of month
WHERE
    notification_day_of_week IS NULL
    OR notification_day_of_month IS NULL;

-- Create index for efficient querying by frequency and day
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_frequency_day
ON user_notification_preferences(frequency, notification_day_of_week, notification_day_of_month);
