-- Migration script to add DM notifications support to existing database
-- Run this in Supabase SQL Editor if you already have the database set up

-- Add dm_notifications_enabled column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;

-- Add comment for documentation
COMMENT ON COLUMN users.dm_notifications_enabled IS 'Whether user wants to receive DM notifications for new articles (default: true)';

