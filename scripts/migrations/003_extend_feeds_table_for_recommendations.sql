-- Migration 003: Extend feeds table for recommendation system
-- Task 1.2: 擴展 feeds 表格
-- Requirements: 12.1, 12.2, 12.3, 12.4
--
-- This migration adds columns to support the new user onboarding recommendation system:
-- - is_recommended: Flag to mark feeds as recommended for new users
-- - recommendation_priority: Integer to control display order (higher = more important)
-- - description: Text description to help users understand the feed content
-- - updated_at: Timestamp to track when feed metadata was last modified

-- Add new columns to feeds table
ALTER TABLE feeds
ADD COLUMN is_recommended BOOLEAN DEFAULT false,
ADD COLUMN recommendation_priority INTEGER DEFAULT 0,
ADD COLUMN description TEXT,
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();

-- Create indexes to support recommendation queries
CREATE INDEX idx_feeds_is_recommended ON feeds(is_recommended);
CREATE INDEX idx_feeds_recommendation_priority ON feeds(recommendation_priority DESC);

-- Create trigger to automatically update updated_at timestamp
CREATE TRIGGER update_feeds_updated_at
    BEFORE UPDATE ON feeds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to document the migration
COMMENT ON COLUMN feeds.is_recommended IS 'Flag indicating if this feed should be recommended to new users during onboarding';
COMMENT ON COLUMN feeds.recommendation_priority IS 'Priority for ordering recommended feeds (higher values appear first)';
COMMENT ON COLUMN feeds.description IS 'User-facing description of the feed content and purpose';
COMMENT ON COLUMN feeds.updated_at IS 'Timestamp of last update to feed metadata';
