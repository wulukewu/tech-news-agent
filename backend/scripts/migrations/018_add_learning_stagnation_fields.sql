-- Migration 018: Add stagnation tracking fields to learning_goals
ALTER TABLE learning_goals
  ADD COLUMN IF NOT EXISTS last_stagnation_reminder_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS stagnation_reminder_count_this_week INTEGER DEFAULT 0;
