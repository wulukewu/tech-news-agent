-- Migration: Create weekly_insights table
-- Requirements: 9.1, 9.2 (historical trend storage)

CREATE TABLE IF NOT EXISTS weekly_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start TIMESTAMPTZ NOT NULL,
    period_end   TIMESTAMPTZ NOT NULL,
    article_count INTEGER NOT NULL DEFAULT 0,
    executive_summary TEXT,
    clusters      JSONB,
    trends        JSONB,
    missed_articles JSONB,
    trend_data    JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast "latest report" queries
CREATE INDEX IF NOT EXISTS idx_weekly_insights_created_at
    ON weekly_insights (created_at DESC);

-- Index for historical trend queries
CREATE INDEX IF NOT EXISTS idx_weekly_insights_period_start
    ON weekly_insights (period_start DESC);
