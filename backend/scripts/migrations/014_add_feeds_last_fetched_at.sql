-- Migration 014: Add last_fetched_at to feeds table
-- Tracks when each feed was last successfully fetched

ALTER TABLE feeds ADD COLUMN IF NOT EXISTS last_fetched_at TIMESTAMPTZ;

COMMENT ON COLUMN feeds.last_fetched_at IS 'Timestamp of the last successful RSS fetch for this feed';
