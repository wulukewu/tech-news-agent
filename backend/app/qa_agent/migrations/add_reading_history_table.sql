-- Migration: Add reading_history table for detailed tracking
-- Requirements: 8.1, 8.3, 8.5

-- Create reading_history table
CREATE TABLE IF NOT EXISTS reading_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    article_id UUID NOT NULL,
    read_at TIMESTAMP NOT NULL DEFAULT NOW(),
    read_duration_seconds INTEGER,
    completion_rate FLOAT CHECK (completion_rate >= 0 AND completion_rate <= 1),
    satisfaction_score FLOAT CHECK (satisfaction_score >= 0 AND satisfaction_score <= 1),
    feedback_type VARCHAR(20) DEFAULT 'implicit',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, article_id, read_at)
);

-- Create indexes for efficient queries
CREATE INDEX idx_reading_history_user_id ON reading_history(user_id);
CREATE INDEX idx_reading_history_article_id ON reading_history(article_id);
CREATE INDEX idx_reading_history_read_at ON reading_history(read_at DESC);
CREATE INDEX idx_reading_history_user_read_at ON reading_history(user_id, read_at DESC);

-- Add comment
COMMENT ON TABLE reading_history IS 'Detailed reading history tracking with engagement metrics';
COMMENT ON COLUMN reading_history.read_duration_seconds IS 'Time spent reading the article in seconds';
COMMENT ON COLUMN reading_history.completion_rate IS 'Percentage of article read (0.0-1.0)';
COMMENT ON COLUMN reading_history.satisfaction_score IS 'User satisfaction score (0.0-1.0)';
COMMENT ON COLUMN reading_history.feedback_type IS 'Type of feedback: explicit or implicit';
