-- Migration: Add status tracking to weekly_insights table
-- Enables resume-on-restart for interrupted generation jobs

ALTER TABLE weekly_insights
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed',
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;

-- Backfill existing rows
UPDATE weekly_insights SET status = 'completed' WHERE status IS NULL;

CREATE INDEX IF NOT EXISTS idx_weekly_insights_status
    ON weekly_insights (status, started_at);
