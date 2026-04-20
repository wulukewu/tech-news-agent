-- Migration 005: Create user_notification_preferences table
-- Task 1.1: Create database migration for user_notification_preferences table
-- Requirements: 4.1, 4.2, 4.3, 4.6, 4.7
--
-- This migration creates the user_notification_preferences table to store individual
-- user notification settings for the personalized notification frequency feature.
-- This replaces the system-wide DM_NOTIFICATION_CRON with per-user preferences.
--
-- Default values:
-- - frequency: weekly (every Friday)
-- - notification_time: 18:00 (6 PM)
-- - timezone: Asia/Taipei
-- - dm_enabled: true
-- - email_enabled: false

-- Create user_notification_preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification frequency: daily, weekly, monthly, disabled
    frequency TEXT NOT NULL DEFAULT 'weekly'
        CHECK (frequency IN ('daily', 'weekly', 'monthly', 'disabled')),

    -- Notification time in HH:MM format (24-hour)
    notification_time TIME NOT NULL DEFAULT '18:00:00',

    -- IANA timezone identifier
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',

    -- Channel preferences
    dm_enabled BOOLEAN NOT NULL DEFAULT true,
    email_enabled BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Ensure one preference record per user
    UNIQUE(user_id)
);

-- Create indexes for optimized query performance
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_user_id
    ON user_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_frequency
    ON user_notification_preferences(frequency);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to document the table and columns
COMMENT ON TABLE user_notification_preferences IS 'Stores individual user notification preferences for personalized notification scheduling';
COMMENT ON COLUMN user_notification_preferences.user_id IS 'Foreign key to users table, one preference record per user';
COMMENT ON COLUMN user_notification_preferences.frequency IS 'Notification frequency: daily, weekly, monthly, or disabled';
COMMENT ON COLUMN user_notification_preferences.notification_time IS 'Time of day to send notifications in user timezone (HH:MM format)';
COMMENT ON COLUMN user_notification_preferences.timezone IS 'IANA timezone identifier for user location';
COMMENT ON COLUMN user_notification_preferences.dm_enabled IS 'Whether Discord DM notifications are enabled';
COMMENT ON COLUMN user_notification_preferences.email_enabled IS 'Whether email notifications are enabled';
