-- Migration 006: Add Business Rule Constraints
-- This migration adds database-level constraints to enforce business rules
-- and ensure data integrity at the database layer.
--
-- Validates: Requirements 14.2, 14.3
--
-- Run this migration with:
-- psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/006_add_business_rule_constraints.sql

-- ============================================================================
-- USERS TABLE CONSTRAINTS
-- ============================================================================

-- Ensure discord_id is not empty
ALTER TABLE users
ADD CONSTRAINT check_users_discord_id_not_empty
CHECK (discord_id IS NOT NULL AND length(trim(discord_id)) > 0);

-- Ensure discord_id is numeric (Discord snowflake IDs are numeric strings)
ALTER TABLE users
ADD CONSTRAINT check_users_discord_id_numeric
CHECK (discord_id ~ '^[0-9]+$');

-- Ensure discord_id length is valid (Discord snowflakes are 17-20 digits)
ALTER TABLE users
ADD CONSTRAINT check_users_discord_id_length
CHECK (length(discord_id) >= 17 AND length(discord_id) <= 20);

-- ============================================================================
-- FEEDS TABLE CONSTRAINTS
-- ============================================================================

-- Ensure feed name is not empty
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_name_not_empty
CHECK (name IS NOT NULL AND length(trim(name)) > 0);

-- Ensure feed name length is reasonable
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_name_length
CHECK (length(name) <= 255);

-- Ensure feed URL is not empty
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_url_not_empty
CHECK (url IS NOT NULL AND length(trim(url)) > 0);

-- Ensure feed URL starts with http:// or https://
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_url_protocol
CHECK (url ~ '^https?://');

-- Ensure feed URL length is reasonable
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_url_length
CHECK (length(url) <= 2048);

-- Ensure category is not empty
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_category_not_empty
CHECK (category IS NOT NULL AND length(trim(category)) > 0);

-- Ensure category length is reasonable
ALTER TABLE feeds
ADD CONSTRAINT check_feeds_category_length
CHECK (length(category) <= 100);

-- ============================================================================
-- ARTICLES TABLE CONSTRAINTS
-- ============================================================================

-- Ensure article title is not empty
ALTER TABLE articles
ADD CONSTRAINT check_articles_title_not_empty
CHECK (title IS NOT NULL AND length(trim(title)) > 0);

-- Ensure article title length is reasonable
ALTER TABLE articles
ADD CONSTRAINT check_articles_title_length
CHECK (length(title) <= 2000);

-- Ensure article URL is not empty
ALTER TABLE articles
ADD CONSTRAINT check_articles_url_not_empty
CHECK (url IS NOT NULL AND length(trim(url)) > 0);

-- Ensure article URL length is reasonable
ALTER TABLE articles
ADD CONSTRAINT check_articles_url_length
CHECK (length(url) <= 2048);

-- Ensure tinkering_index is in valid range (1-5) if not null
-- Note: This constraint already exists in the schema, but we ensure it's present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_articles_tinkering_index_range'
    ) THEN
        ALTER TABLE articles
        ADD CONSTRAINT check_articles_tinkering_index_range
        CHECK (tinkering_index IS NULL OR (tinkering_index >= 1 AND tinkering_index <= 5));
    END IF;
END $$;

-- Ensure ai_summary length is reasonable if not null
ALTER TABLE articles
ADD CONSTRAINT check_articles_ai_summary_length
CHECK (ai_summary IS NULL OR length(ai_summary) <= 5000);

-- Ensure deep_summary length is reasonable if not null
ALTER TABLE articles
ADD CONSTRAINT check_articles_deep_summary_length
CHECK (deep_summary IS NULL OR length(deep_summary) <= 10000);

-- Ensure feed_id is not null (enforce referential integrity)
ALTER TABLE articles
ALTER COLUMN feed_id SET NOT NULL;

-- ============================================================================
-- READING_LIST TABLE CONSTRAINTS
-- ============================================================================

-- Ensure status is not null and has valid value
-- Note: CHECK constraint for status values already exists in schema
ALTER TABLE reading_list
ALTER COLUMN status SET NOT NULL;

-- Ensure status has default value
ALTER TABLE reading_list
ALTER COLUMN status SET DEFAULT 'Unread';

-- Ensure user_id and article_id are not null (enforce referential integrity)
ALTER TABLE reading_list
ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE reading_list
ALTER COLUMN article_id SET NOT NULL;

-- ============================================================================
-- USER_SUBSCRIPTIONS TABLE CONSTRAINTS
-- ============================================================================

-- Ensure user_id and feed_id are not null (enforce referential integrity)
ALTER TABLE user_subscriptions
ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE user_subscriptions
ALTER COLUMN feed_id SET NOT NULL;

-- ============================================================================
-- INDEXES FOR CONSTRAINT VALIDATION PERFORMANCE
-- ============================================================================

-- Create index on deleted_at for soft delete queries (if column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'deleted_at'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'feeds' AND column_name = 'deleted_at'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_feeds_deleted_at ON feeds(deleted_at);
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'articles' AND column_name = 'deleted_at'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_articles_deleted_at ON articles(deleted_at);
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reading_list' AND column_name = 'deleted_at'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_reading_list_deleted_at ON reading_list(deleted_at);
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify constraints were added successfully
DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM pg_constraint
    WHERE conname LIKE 'check_%'
    AND conrelid IN (
        'users'::regclass,
        'feeds'::regclass,
        'articles'::regclass,
        'reading_list'::regclass
    );

    RAISE NOTICE 'Successfully added business rule constraints. Total check constraints: %', constraint_count;
END $$;
