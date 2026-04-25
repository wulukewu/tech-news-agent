-- Migration: add created_by to feeds table
-- Run this in Supabase SQL Editor

ALTER TABLE feeds ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE CASCADE;

-- Index for fast per-user custom feed lookup
CREATE INDEX IF NOT EXISTS idx_feeds_created_by ON feeds(created_by);
