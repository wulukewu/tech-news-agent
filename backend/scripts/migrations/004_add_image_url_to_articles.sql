-- Migration: Add image_url column to articles table
-- Purpose: Store article thumbnail/cover images for better UI display
-- Date: 2026-04-17

-- Add image_url column (nullable, as existing articles won't have images)
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Add comment for documentation
COMMENT ON COLUMN articles.image_url IS 'Article thumbnail or cover image URL (optional)';

-- Create index for faster queries when filtering by image availability
CREATE INDEX IF NOT EXISTS idx_articles_has_image ON articles(id) WHERE image_url IS NOT NULL;
