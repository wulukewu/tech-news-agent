-- Migration 016: Add proactive DM fields to users table
-- Requirements: 4.2, 4.3, 4.4

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS last_proactive_dm_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS proactive_dm_frequency_hours INTEGER DEFAULT 20;
