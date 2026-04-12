-- Rollback Migration 003: Extend feeds table for recommendation system
-- Task 1.2: 擴展 feeds 表格
--
-- This script rolls back the changes made by 003_extend_feeds_table_for_recommendations.sql
-- Use this only if you need to undo the migration

-- Remove trigger
DROP TRIGGER IF EXISTS update_feeds_updated_at ON feeds;

-- Remove indexes
DROP INDEX IF EXISTS idx_feeds_recommendation_priority;
DROP INDEX IF EXISTS idx_feeds_is_recommended;

-- Remove columns (in reverse order of addition)
ALTER TABLE feeds
DROP COLUMN IF EXISTS updated_at,
DROP COLUMN IF EXISTS description,
DROP COLUMN IF EXISTS recommendation_priority,
DROP COLUMN IF EXISTS is_recommended;

-- Note: This rollback is safe to run multiple times (idempotent)
-- It uses IF EXISTS clauses to prevent errors if objects don't exist
