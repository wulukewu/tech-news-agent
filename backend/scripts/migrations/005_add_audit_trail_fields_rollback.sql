-- Rollback Migration: Remove Audit Trail Fields
-- Description: Removes audit trail fields added by 005_add_audit_trail_fields.sql
-- Author: System
-- Date: 2024
-- Validates: Requirements 14.4

-- ============================================================================
-- ROLLBACK: Remove audit trail fields and triggers
-- ============================================================================

-- Drop triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_feeds_updated_at ON feeds;
DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
DROP TRIGGER IF EXISTS update_user_subscriptions_updated_at ON user_subscriptions;
-- Note: Keep reading_list trigger as it existed before this migration

-- Drop indexes
DROP INDEX IF EXISTS idx_users_updated_at;
DROP INDEX IF EXISTS idx_users_modified_by;
DROP INDEX IF EXISTS idx_feeds_updated_at;
DROP INDEX IF EXISTS idx_feeds_modified_by;
DROP INDEX IF EXISTS idx_articles_updated_at;
DROP INDEX IF EXISTS idx_articles_modified_by;
DROP INDEX IF EXISTS idx_reading_list_modified_by;
DROP INDEX IF EXISTS idx_user_subscriptions_updated_at;
DROP INDEX IF EXISTS idx_user_subscriptions_modified_by;

-- Remove modified_by columns
ALTER TABLE users DROP COLUMN IF EXISTS modified_by;
ALTER TABLE feeds DROP COLUMN IF EXISTS modified_by;
ALTER TABLE articles DROP COLUMN IF EXISTS modified_by;
ALTER TABLE reading_list DROP COLUMN IF EXISTS modified_by;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS modified_by;

-- Remove updated_at columns (except reading_list which had it originally)
ALTER TABLE users DROP COLUMN IF EXISTS updated_at;
ALTER TABLE feeds DROP COLUMN IF EXISTS updated_at;
ALTER TABLE articles DROP COLUMN IF EXISTS updated_at;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS updated_at;

-- Note: reading_list.updated_at is preserved as it existed in the original schema
-- Note: The update_updated_at_column() function is preserved as it's used by reading_list

-- Remove comments
COMMENT ON COLUMN users.created_at IS NULL;
COMMENT ON COLUMN feeds.created_at IS NULL;
COMMENT ON COLUMN articles.created_at IS NULL;
COMMENT ON COLUMN reading_list.added_at IS NULL;
COMMENT ON COLUMN reading_list.updated_at IS NULL;
COMMENT ON COLUMN user_subscriptions.subscribed_at IS NULL;
