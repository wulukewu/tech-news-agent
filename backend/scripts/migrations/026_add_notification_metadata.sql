-- Migration: Add metadata JSONB column to user_notification_preferences
-- Used to store engagement tracking data (e.g., no_engagement_streak)

ALTER TABLE user_notification_preferences
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
