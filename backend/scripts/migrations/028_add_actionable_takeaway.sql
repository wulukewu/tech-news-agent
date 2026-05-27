-- Migration: Add actionable_takeaway column to articles table
-- Used to store punchy, highly practical "1-second core technical takeaway"

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS actionable_takeaway TEXT;
