-- Add stage_order to learning_progress for efficient per-stage progress calculation
ALTER TABLE learning_progress ADD COLUMN IF NOT EXISTS stage_order INTEGER;

CREATE INDEX IF NOT EXISTS idx_learning_progress_stage_order ON learning_progress(stage_order);
