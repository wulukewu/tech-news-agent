-- 最小化遷移：只建立 QA Agent 必需的資料表
-- 複製這段 SQL 到 Supabase Dashboard > SQL Editor 執行

-- 啟用 pgvector 擴充功能
CREATE EXTENSION IF NOT EXISTS vector;

-- 建立 conversations 資料表（修復當前錯誤）
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context JSONB NOT NULL DEFAULT '{}',
    current_topic TEXT,
    turn_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + INTERVAL '7 days'),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NULL
);

-- 建立索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations(last_updated);
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;

-- 建立 article_embeddings 資料表（語義搜尋用）
CREATE TABLE IF NOT EXISTS article_embeddings (
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    PRIMARY KEY (article_id, chunk_index)
);

-- 建立向量索引
CREATE INDEX IF NOT EXISTS idx_article_embeddings_cosine
ON article_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_created_at ON article_embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_deleted_at ON article_embeddings(deleted_at) WHERE deleted_at IS NULL;

-- 建立 user_profiles 資料表（個人化用）
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

-- 建立 query_logs 資料表（分析用）
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

-- 建立索引
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

-- 驗證建立成功（簡化版本）
SELECT 'QA Agent 資料表建立完成！' as status;
