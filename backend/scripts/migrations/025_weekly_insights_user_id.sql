-- Migration: Add user_id to weekly_insights for per-user personalized reports

ALTER TABLE weekly_insights
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- NULL = global report (legacy), non-NULL = per-user personalized report
CREATE INDEX IF NOT EXISTS idx_weekly_insights_user_id
    ON weekly_insights (user_id, created_at DESC);
