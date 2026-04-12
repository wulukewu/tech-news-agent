-- Migration: Add Soft Delete Support
-- This migration adds deleted_at field to critical entities for audit trail preservation
-- Validates: Requirements 14.5

-- Add deleted_at column to users table
ALTER TABLE users
ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Add deleted_at column to feeds table
ALTER TABLE feeds
ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Add deleted_at column to articles table
ALTER TABLE articles
ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Add deleted_at column to reading_list table
ALTER TABLE reading_list
ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Create indexes for soft delete queries (to efficiently filter out deleted records)
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_feeds_deleted_at ON feeds(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_deleted_at ON articles(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_reading_list_deleted_at ON reading_list(deleted_at) WHERE deleted_at IS NULL;

-- Add comments to document the soft delete pattern
COMMENT ON COLUMN users.deleted_at IS 'Timestamp when the user was soft-deleted. NULL means not deleted.';
COMMENT ON COLUMN feeds.deleted_at IS 'Timestamp when the feed was soft-deleted. NULL means not deleted.';
COMMENT ON COLUMN articles.deleted_at IS 'Timestamp when the article was soft-deleted. NULL means not deleted.';
COMMENT ON COLUMN reading_list.deleted_at IS 'Timestamp when the reading list item was soft-deleted. NULL means not deleted.';
