-- Migration: Create user_preferences table for onboarding system
-- Task: 1.1 建立 user_preferences 表格
-- Requirements: 1.4, 10.1, 10.2, 11.7

-- Create user_preferences table
-- Stores user onboarding progress, tooltip tour status, and language preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,

    -- Onboarding progress
    onboarding_completed BOOLEAN DEFAULT false,
    onboarding_step TEXT,
    onboarding_skipped BOOLEAN DEFAULT false,
    onboarding_started_at TIMESTAMPTZ,
    onboarding_completed_at TIMESTAMPTZ,

    -- Tooltip tour
    tooltip_tour_completed BOOLEAN DEFAULT false,
    tooltip_tour_skipped BOOLEAN DEFAULT false,

    -- Language preference
    preferred_language TEXT DEFAULT 'zh-TW',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for optimized query performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_onboarding_completed ON user_preferences(onboarding_completed);

-- Create trigger to automatically update updated_at timestamp
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to document the table and columns
COMMENT ON TABLE user_preferences IS 'Stores user onboarding progress, tooltip tour status, and personalization preferences';
COMMENT ON COLUMN user_preferences.user_id IS 'Foreign key to users table, one preference record per user';
COMMENT ON COLUMN user_preferences.onboarding_completed IS 'Whether user has completed the onboarding flow';
COMMENT ON COLUMN user_preferences.onboarding_step IS 'Current step in onboarding flow (welcome, recommendations, complete)';
COMMENT ON COLUMN user_preferences.onboarding_skipped IS 'Whether user skipped the onboarding flow';
COMMENT ON COLUMN user_preferences.onboarding_started_at IS 'Timestamp when user started onboarding';
COMMENT ON COLUMN user_preferences.onboarding_completed_at IS 'Timestamp when user completed onboarding';
COMMENT ON COLUMN user_preferences.tooltip_tour_completed IS 'Whether user has completed the tooltip tour';
COMMENT ON COLUMN user_preferences.tooltip_tour_skipped IS 'Whether user skipped the tooltip tour';
COMMENT ON COLUMN user_preferences.preferred_language IS 'User preferred language code (default: zh-TW)';
