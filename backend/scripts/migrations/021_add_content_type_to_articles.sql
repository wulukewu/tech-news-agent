-- Migration 021: Add content_type to articles table
-- Classifies articles as tutorial/guide/news/reference/project/opinion
-- for learning-path recommendation weighting

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS content_type VARCHAR(20)
        CHECK (content_type IN ('tutorial', 'guide', 'news', 'reference', 'project', 'opinion'));

CREATE INDEX IF NOT EXISTS idx_articles_content_type ON articles(content_type);
