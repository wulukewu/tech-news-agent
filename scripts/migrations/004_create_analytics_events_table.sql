-- Migration 004: Create analytics_events table
-- Task 1.3: 建立 analytics_events 表格
-- Requirements: 14.1, 14.2, 14.3
-- 
-- This migration creates the analytics_events table to track user onboarding events
-- and behavior for analysis and optimization of the onboarding flow.
-- 
-- Event types include:
-- - onboarding_started: User begins onboarding flow
-- - step_completed: User completes an onboarding step
-- - onboarding_skipped: User skips onboarding
-- - onboarding_finished: User completes entire onboarding
-- - tooltip_shown: Tooltip displayed to user
-- - tooltip_skipped: User skips tooltip tour
-- - feed_subscribed_from_onboarding: User subscribes to feed during onboarding

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes to support analytics queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_data ON analytics_events USING GIN(event_data);

-- Add comments to document the table and columns
COMMENT ON TABLE analytics_events IS 'Tracks user onboarding events and behavior for analysis and optimization';
COMMENT ON COLUMN analytics_events.user_id IS 'Foreign key to users table, identifies which user triggered the event';
COMMENT ON COLUMN analytics_events.event_type IS 'Type of event (onboarding_started, step_completed, onboarding_skipped, etc.)';
COMMENT ON COLUMN analytics_events.event_data IS 'JSONB field containing event-specific data (step name, duration, etc.)';
COMMENT ON COLUMN analytics_events.created_at IS 'Timestamp when the event occurred';
