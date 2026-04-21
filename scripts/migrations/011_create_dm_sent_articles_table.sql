-- Migration 011: Create dm_sent_articles table
-- This table tracks which articles have been sent to users to avoid duplicates

-- Create dm_sent_articles table
CREATE TABLE IF NOT EXISTS dm_sent_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notification_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'

    -- Prevent duplicate records
    UNIQUE(user_id, article_id),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_user_sent
    ON dm_sent_articles(user_id, sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_article
    ON dm_sent_articles(article_id);

-- Index for cleanup queries (articles older than 90 days)
-- Note: We use a simple index on sent_at instead of a partial index with now()
-- because now() is not IMMUTABLE and cannot be used in index predicates
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_cleanup
    ON dm_sent_articles(sent_at);

-- Add comments
COMMENT ON TABLE dm_sent_articles IS 'Tracks which articles have been sent to users via DM to avoid duplicates';
COMMENT ON COLUMN dm_sent_articles.user_id IS 'User who received the article';
COMMENT ON COLUMN dm_sent_articles.article_id IS 'Article that was sent';
COMMENT ON COLUMN dm_sent_articles.sent_at IS 'When the article was sent';
COMMENT ON COLUMN dm_sent_articles.notification_type IS 'Type of notification: daily, weekly, or monthly';
