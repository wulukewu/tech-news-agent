-- 分步驟執行的遷移 SQL
-- 如果上面的版本還有問題，請一段一段執行

-- 步驟 1: 啟用 pgvector 擴充功能
CREATE EXTENSION IF NOT EXISTS vector;

-- 步驟 2: 建立 conversations 資料表（修復當前錯誤）
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

-- 步驟 3: 建立 conversations 索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations(last_updated);
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;
