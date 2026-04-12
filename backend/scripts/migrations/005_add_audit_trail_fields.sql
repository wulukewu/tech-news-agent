-- Migration: Add Audit Trail Fields
-- Description: Adds audit trail fields (created_at, updated_at, modified_by) to critical tables
-- Author: System
-- Date: 2024
-- Validates: Requirements 14.1, 14.4

-- ============================================================================
-- FORWARD MIGRATION: Add audit trail fields
-- ============================================================================

-- Add modified_by field to users table
-- Tracks which user (by discord_id) last modified the record
ALTER TABLE users
ADD COLUMN IF NOT EXISTS modified_by TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- Add modified_by field to feeds table
ALTER TABLE feeds
ADD COLUMN IF NOT EXISTS modified_by TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- Add modified_by field to articles table
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS modified_by TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- Add modified_by field to reading_list table (already has updated_at)
ALTER TABLE reading_list
ADD COLUMN IF NOT EXISTS modified_by TEXT;

-- Add modified_by field to user_subscriptions table
ALTER TABLE user_subscriptions
ADD COLUMN IF NOT EXISTS modified_by TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- ============================================================================
-- Create or replace the update_updated_at_column function
-- This function automatically updates the updated_at timestamp on row updates
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- Create triggers to automatically update updated_at on modifications
-- ============================================================================

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for feeds table
DROP TRIGGER IF EXISTS update_feeds_updated_at ON feeds;
CREATE TRIGGER update_feeds_updated_at
    BEFORE UPDATE ON feeds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for articles table
DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
CREATE TRIGGER update_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for reading_list table (already exists, but recreate for consistency)
DROP TRIGGER IF EXISTS update_reading_list_updated_at ON reading_list;
CREATE TRIGGER update_reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_subscriptions table
DROP TRIGGER IF EXISTS update_user_subscriptions_updated_at ON user_subscriptions;
CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Create indexes for audit trail fields to improve query performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at);
CREATE INDEX IF NOT EXISTS idx_users_modified_by ON users(modified_by);

CREATE INDEX IF NOT EXISTS idx_feeds_updated_at ON feeds(updated_at);
CREATE INDEX IF NOT EXISTS idx_feeds_modified_by ON feeds(modified_by);

CREATE INDEX IF NOT EXISTS idx_articles_updated_at ON articles(updated_at);
CREATE INDEX IF NOT EXISTS idx_articles_modified_by ON articles(modified_by);

CREATE INDEX IF NOT EXISTS idx_reading_list_modified_by ON reading_list(modified_by);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_updated_at ON user_subscriptions(updated_at);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_modified_by ON user_subscriptions(modified_by);

-- ============================================================================
-- Add comments to document the audit trail fields
-- ============================================================================

COMMENT ON COLUMN users.created_at IS 'Timestamp when the user record was created';
COMMENT ON COLUMN users.updated_at IS 'Timestamp when the user record was last updated';
COMMENT ON COLUMN users.modified_by IS 'Discord ID of the user who last modified this record';

COMMENT ON COLUMN feeds.created_at IS 'Timestamp when the feed was created';
COMMENT ON COLUMN feeds.updated_at IS 'Timestamp when the feed was last updated';
COMMENT ON COLUMN feeds.modified_by IS 'Discord ID of the user who last modified this record';

COMMENT ON COLUMN articles.created_at IS 'Timestamp when the article was created';
COMMENT ON COLUMN articles.updated_at IS 'Timestamp when the article was last updated';
COMMENT ON COLUMN articles.modified_by IS 'Discord ID of the user who last modified this record';

COMMENT ON COLUMN reading_list.added_at IS 'Timestamp when the article was added to the reading list';
COMMENT ON COLUMN reading_list.updated_at IS 'Timestamp when the reading list item was last updated';
COMMENT ON COLUMN reading_list.modified_by IS 'Discord ID of the user who last modified this record';

COMMENT ON COLUMN user_subscriptions.subscribed_at IS 'Timestamp when the user subscribed to the feed';
COMMENT ON COLUMN user_subscriptions.updated_at IS 'Timestamp when the subscription was last updated';
COMMENT ON COLUMN user_subscriptions.modified_by IS 'Discord ID of the user who last modified this record';
