-- Migration: Proactive Learning Agent tables
-- Requirements: 1.1, 12.1

-- User behavior events (reading, rating, click, bookmark)
CREATE TABLE IF NOT EXISTS user_behavior_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL,          -- 'read', 'rate', 'click', 'bookmark', 'skip'
    article_id  UUID REFERENCES articles(id) ON DELETE SET NULL,
    category    TEXT,
    rating      INTEGER,               -- 1-5, nullable
    duration_seconds INTEGER,          -- reading time
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_behavior_events_user_id
    ON user_behavior_events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_events_category
    ON user_behavior_events (user_id, category, created_at DESC);

-- Preference model: per-user category weights + settings
CREATE TABLE IF NOT EXISTS preference_model (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    category_weights JSONB NOT NULL DEFAULT '{}',   -- {category: weight 0-1}
    learning_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_weekly_conversations INTEGER NOT NULL DEFAULT 3,
    conversations_this_week  INTEGER NOT NULL DEFAULT 0,
    week_reset_at   TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Learning conversations (pending questions + responses)
CREATE TABLE IF NOT EXISTS learning_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_type TEXT NOT NULL,   -- 'interest_confirm', 'preference_adjust', 'new_topic', 'feedback'
    question        TEXT NOT NULL,
    options         JSONB,             -- multiple choice options, nullable
    response        TEXT,              -- user's answer, null = pending
    status          TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'answered', 'expired'
    context_data    JSONB,             -- behavior data that triggered this
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_learning_conversations_user_pending
    ON learning_conversations (user_id, status, created_at DESC);
