-- Migration: Add deep_summary support to articles table
-- Task: 1.4 擴充 articles 表支援深度摘要
-- Requirements: 4.7, 9.7

-- Add deep_summary column to store AI-generated deep analysis
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS deep_summary TEXT;

-- Add timestamp for when deep_summary was generated
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS deep_summary_generated_at TIMESTAMPTZ;

-- Create partial index for articles with deep summaries
-- This optimizes queries that check for existing summaries
CREATE INDEX IF NOT EXISTS idx_articles_deep_summary
ON articles(id) WHERE deep_summary IS NOT NULL;

-- Add comment to document the purpose
COMMENT ON COLUMN articles.deep_summary IS 'AI-generated deep analysis summary shared across all users';
COMMENT ON COLUMN articles.deep_summary_generated_at IS 'Timestamp when the deep summary was generated';
