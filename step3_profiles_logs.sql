-- 步驟 6: 建立 user_profiles 資料表
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reading_history JSONB DEFAULT '[]',
    preferred_topics JSONB DEFAULT '[]',
    language_preference VARCHAR(10) DEFAULT 'zh',
    interaction_patterns JSONB DEFAULT '{}',
    query_count INTEGER DEFAULT 0,
    satisfaction_scores JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NULL
);

-- 步驟 7: 建立 query_logs 資料表
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_vector vector(1536),
    response_data JSONB,
    response_time_ms INTEGER,
    articles_found INTEGER DEFAULT 0,
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NULL
);

-- 步驟 8: 建立剩餘索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_language_preference ON user_profiles(language_preference);
CREATE INDEX IF NOT EXISTS idx_user_profiles_query_count ON user_profiles(query_count);
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON user_profiles(updated_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_deleted_at ON user_profiles(deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_conversation_id ON query_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_response_time ON query_logs(response_time_ms);
CREATE INDEX IF NOT EXISTS idx_query_logs_satisfaction ON query_logs(satisfaction_rating);
CREATE INDEX IF NOT EXISTS idx_query_logs_deleted_at ON query_logs(deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_query_logs_vector_cosine
ON query_logs USING ivfflat (query_vector vector_cosine_ops)
WITH (lists = 100);
