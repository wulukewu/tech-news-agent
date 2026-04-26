-- Migration 017: DM conversation memory & preference summary
-- Requirements: dm-conversation-memory

-- Add preference_summary to preference_model
ALTER TABLE preference_model
  ADD COLUMN IF NOT EXISTS preference_summary TEXT,
  ADD COLUMN IF NOT EXISTS summary_updated_at TIMESTAMPTZ;

-- DM conversations from users (natural language preference signals)
CREATE TABLE IF NOT EXISTS dm_conversations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dm_conversations_user_created
    ON dm_conversations (user_id, created_at DESC);
