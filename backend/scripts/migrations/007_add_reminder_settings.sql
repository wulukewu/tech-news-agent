-- Migration: Add reminder settings columns to user_notification_preferences
-- Run this in Supabase SQL Editor

ALTER TABLE user_notification_preferences
  ADD COLUMN IF NOT EXISTS reminder_enabled BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS reminder_on_add BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS reminder_on_rate BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS reminder_cooldown_hours INTEGER DEFAULT 4,
  ADD COLUMN IF NOT EXISTS reminder_min_similarity FLOAT DEFAULT 0.72;
