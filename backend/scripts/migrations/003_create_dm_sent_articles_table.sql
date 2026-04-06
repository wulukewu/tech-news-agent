-- Migration 003: Create dm_sent_articles table
-- Purpose: Track which articles have been sent to users via DM notifications
-- This prevents duplicate articles from being sent in subsequent weekly digests
-- Related to: Bug Fix - DM Notification Duplicates

-- Create dm_sent_articles table
CREATE TABLE IF NOT EXISTS dm_sent_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, article_id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_user_id ON dm_sent_articles(user_id);
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_article_id ON dm_sent_articles(article_id);
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_sent_at ON dm_sent_articles(sent_at);

-- Add comment to table
COMMENT ON TABLE dm_sent_articles IS 'Tracks articles sent to users via DM notifications to prevent duplicates';
COMMENT ON COLUMN dm_sent_articles.user_id IS 'Reference to the user who received the article';
COMMENT ON COLUMN dm_sent_articles.article_id IS 'Reference to the article that was sent';
COMMENT ON COLUMN dm_sent_articles.sent_at IS 'Timestamp when the article was sent via DM';
