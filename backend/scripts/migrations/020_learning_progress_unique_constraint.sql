-- Remove duplicate learning_progress records, keeping only the latest per (user, goal, article)
DELETE FROM learning_progress
WHERE id NOT IN (
  SELECT DISTINCT ON (user_id, goal_id, article_id) id
  FROM learning_progress
  ORDER BY user_id, goal_id, article_id, updated_at DESC
);

-- Add unique constraint to prevent future duplicates
ALTER TABLE learning_progress
  ADD CONSTRAINT learning_progress_user_goal_article_unique
  UNIQUE (user_id, goal_id, article_id);
