-- Migration 018: Add source tracking to reading_list
-- Tracks whether articles were added from Discord or Web interface

-- Add source column to reading_list
ALTER TABLE reading_list
ADD COLUMN source TEXT CHECK (source IN ('discord', 'web')) DEFAULT 'web';

-- Create index for source filtering
CREATE INDEX idx_reading_list_source ON reading_list(source);

-- Update existing records to 'web' (already set by DEFAULT)
-- No action needed as DEFAULT handles it

COMMENT ON COLUMN reading_list.source IS 'Source platform: discord or web';
