-- Migration 006 Rollback: Remove Business Rule Constraints
-- This script removes the database-level constraints added in migration 006
--
-- Run this rollback with:
-- psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/006_add_business_rule_constraints_rollback.sql

-- ============================================================================
-- REMOVE USERS TABLE CONSTRAINTS
-- ============================================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS check_users_discord_id_not_empty;
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_users_discord_id_numeric;
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_users_discord_id_length;

-- ============================================================================
-- REMOVE FEEDS TABLE CONSTRAINTS
-- ============================================================================

ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_name_not_empty;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_name_length;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_url_not_empty;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_url_protocol;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_url_length;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_category_not_empty;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS check_feeds_category_length;

-- ============================================================================
-- REMOVE ARTICLES TABLE CONSTRAINTS
-- ============================================================================

ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_title_not_empty;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_title_length;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_url_not_empty;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_url_length;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_tinkering_index_range;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_ai_summary_length;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_articles_deep_summary_length;

-- Note: We don't remove NOT NULL constraints on foreign keys as they should remain
-- for referential integrity. If you need to remove them, uncomment:
-- ALTER TABLE articles ALTER COLUMN feed_id DROP NOT NULL;

-- ============================================================================
-- REMOVE READING_LIST TABLE CONSTRAINTS
-- ============================================================================

-- Note: We don't remove NOT NULL constraints on status, user_id, article_id
-- as they are essential for data integrity. If you need to remove them, uncomment:
-- ALTER TABLE reading_list ALTER COLUMN status DROP NOT NULL;
-- ALTER TABLE reading_list ALTER COLUMN status DROP DEFAULT;
-- ALTER TABLE reading_list ALTER COLUMN user_id DROP NOT NULL;
-- ALTER TABLE reading_list ALTER COLUMN article_id DROP NOT NULL;

-- ============================================================================
-- REMOVE USER_SUBSCRIPTIONS TABLE CONSTRAINTS
-- ============================================================================

-- Note: We don't remove NOT NULL constraints on foreign keys as they should remain
-- for referential integrity. If you need to remove them, uncomment:
-- ALTER TABLE user_subscriptions ALTER COLUMN user_id DROP NOT NULL;
-- ALTER TABLE user_subscriptions ALTER COLUMN feed_id DROP NOT NULL;

-- ============================================================================
-- REMOVE INDEXES
-- ============================================================================

DROP INDEX IF EXISTS idx_users_deleted_at;
DROP INDEX IF EXISTS idx_feeds_deleted_at;
DROP INDEX IF EXISTS idx_articles_deleted_at;
DROP INDEX IF EXISTS idx_reading_list_deleted_at;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Successfully rolled back business rule constraints migration.';
END $$;
