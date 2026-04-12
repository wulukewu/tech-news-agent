-- Rollback Migration: Remove Soft Delete Support
-- This rollback removes the deleted_at field from all tables

-- Drop indexes
DROP INDEX IF EXISTS idx_users_deleted_at;
DROP INDEX IF EXISTS idx_feeds_deleted_at;
DROP INDEX IF EXISTS idx_articles_deleted_at;
DROP INDEX IF EXISTS idx_reading_list_deleted_at;

-- Remove deleted_at columns
ALTER TABLE users DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE feeds DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE articles DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE reading_list DROP COLUMN IF EXISTS deleted_at;
