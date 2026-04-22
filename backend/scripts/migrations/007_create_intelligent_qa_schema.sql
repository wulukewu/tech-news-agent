-- Migration 007: Create Intelligent Q&A Agent Schema
-- Description: Creates database schema for intelligent Q&A agent with pgvector extension
-- Author: System
-- Date: 2024
-- Validates: Requirements 5.1, 7.1, 10.1
-- Task: 1.1 Create PostgreSQL database schema with pgvector extension

-- ============================================================================
-- ENABLE PGVECTOR EXTENSION
-- ============================================================================

-- Enable pgvector extension for vector similarity search (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- ARTICLE EMBEDDINGS TABLE
-- ============================================================================

-- Create article_embeddings table for storing vector embeddings
-- This table stores vector embeddings for articles to enable semantic search
CREATE TABLE IF NOT EXISTS article_embeddings (
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,  -- OpenAI embedding dimension
    chunk_index INTEGER NOT NULL DEFAULT 0,  -- For chunked articles
    chunk_text TEXT,  -- The text chunk that was embedded
    metadata JSONB DEFAULT '{}',  -- Additional metadata for the embedding
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,  -- Discord ID of user who last modified
    deleted_at TIMESTAMPTZ DEFAULT NULL,  -- Soft delete support
    PRIMARY KEY (article_id, chunk_index)
);

-- Create vector similarity indexes for efficient cosine similarity search
CREATE INDEX IF NOT EXISTS idx_article_embeddings_cosine
ON article_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_created_at ON article_embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_deleted_at ON article_embeddings(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- CONVERSATIONS TABLE
-- ============================================================================

-- Create conversations table for storing multi-turn conversation context
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context JSONB NOT NULL DEFAULT '{}',  -- Conversation context and history
    current_topic TEXT,  -- Current conversation topic
    turn_count INTEGER DEFAULT 0,  -- Number of turns in conversation
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + INTERVAL '7 days'),  -- Auto-expire conversations
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,  -- Discord ID of user who last modified
    deleted_at TIMESTAMPTZ DEFAULT NULL  -- Soft delete support
);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations(last_updated);
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- USER PROFILES TABLE
-- ============================================================================

-- Create user_profiles table for storing user preferences and reading history
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reading_history JSONB DEFAULT '[]',  -- Array of article IDs user has read
    preferred_topics JSONB DEFAULT '[]',  -- Array of preferred topic strings
    language_preference VARCHAR(10) DEFAULT 'zh',  -- User's preferred language
    interaction_patterns JSONB DEFAULT '{}',  -- User interaction patterns and preferences
    query_count INTEGER DEFAULT 0,  -- Total number of queries made
    satisfaction_scores JSONB DEFAULT '[]',  -- Array of satisfaction ratings
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,  -- Discord ID of user who last modified
    deleted_at TIMESTAMPTZ DEFAULT NULL  -- Soft delete support
);

-- Create indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_language_preference ON user_profiles(language_preference);
CREATE INDEX IF NOT EXISTS idx_user_profiles_query_count ON user_profiles(query_count);
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON user_profiles(updated_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_deleted_at ON user_profiles(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- QUERY LOGS TABLE
-- ============================================================================

-- Create query_logs table for storing encrypted query logs
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,  -- The user's query (will be encrypted at application level)
    query_vector vector(1536),  -- Vector representation of the query
    response_data JSONB,  -- Structured response data
    response_time_ms INTEGER,  -- Response time in milliseconds
    articles_found INTEGER DEFAULT 0,  -- Number of articles found
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,  -- Discord ID of user who last modified
    deleted_at TIMESTAMPTZ DEFAULT NULL  -- Soft delete support
);

-- Create indexes for query_logs
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_conversation_id ON query_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_response_time ON query_logs(response_time_ms);
CREATE INDEX IF NOT EXISTS idx_query_logs_satisfaction ON query_logs(satisfaction_rating);
CREATE INDEX IF NOT EXISTS idx_query_logs_deleted_at ON query_logs(deleted_at) WHERE deleted_at IS NULL;

-- Create vector similarity index for query vectors
CREATE INDEX IF NOT EXISTS idx_query_logs_vector_cosine
ON query_logs USING ivfflat (query_vector vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- UPDATE TRIGGERS FOR AUDIT TRAIL
-- ============================================================================

-- Create triggers to automatically update updated_at timestamps
CREATE TRIGGER update_article_embeddings_updated_at
    BEFORE UPDATE ON article_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_query_logs_updated_at
    BEFORE UPDATE ON query_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- BUSINESS RULE CONSTRAINTS
-- ============================================================================

-- Article embeddings constraints
ALTER TABLE article_embeddings
ADD CONSTRAINT check_article_embeddings_chunk_index_non_negative
CHECK (chunk_index >= 0);

-- Conversations constraints
ALTER TABLE conversations
ADD CONSTRAINT check_conversations_turn_count_non_negative
CHECK (turn_count >= 0);

ALTER TABLE conversations
ADD CONSTRAINT check_conversations_expires_after_creation
CHECK (expires_at > created_at);

-- User profiles constraints
ALTER TABLE user_profiles
ADD CONSTRAINT check_user_profiles_language_valid
CHECK (language_preference IN ('zh', 'en', 'zh-TW', 'zh-CN', 'en-US', 'en-GB'));

ALTER TABLE user_profiles
ADD CONSTRAINT check_user_profiles_query_count_non_negative
CHECK (query_count >= 0);

-- Query logs constraints
ALTER TABLE query_logs
ADD CONSTRAINT check_query_logs_query_text_not_empty
CHECK (query_text IS NOT NULL AND length(trim(query_text)) > 0);

ALTER TABLE query_logs
ADD CONSTRAINT check_query_logs_response_time_non_negative
CHECK (response_time_ms IS NULL OR response_time_ms >= 0);

ALTER TABLE query_logs
ADD CONSTRAINT check_query_logs_articles_found_non_negative
CHECK (articles_found >= 0);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

-- Table comments
COMMENT ON TABLE article_embeddings IS 'Stores vector embeddings for articles to enable semantic search';
COMMENT ON TABLE conversations IS 'Stores multi-turn conversation context and history';
COMMENT ON TABLE user_profiles IS 'Stores user preferences, reading history, and interaction patterns';
COMMENT ON TABLE query_logs IS 'Stores encrypted query logs for analytics and improvement';

-- Column comments for article_embeddings
COMMENT ON COLUMN article_embeddings.article_id IS 'Reference to the article this embedding represents';
COMMENT ON COLUMN article_embeddings.embedding IS 'Vector embedding (1536 dimensions for OpenAI embeddings)';
COMMENT ON COLUMN article_embeddings.chunk_index IS 'Index for chunked articles (0 for single chunk)';
COMMENT ON COLUMN article_embeddings.chunk_text IS 'The text chunk that was embedded';
COMMENT ON COLUMN article_embeddings.metadata IS 'Additional metadata for the embedding (JSON)';

-- Column comments for conversations
COMMENT ON COLUMN conversations.context IS 'Conversation context and history (JSON)';
COMMENT ON COLUMN conversations.current_topic IS 'Current conversation topic for context';
COMMENT ON COLUMN conversations.turn_count IS 'Number of turns in this conversation';
COMMENT ON COLUMN conversations.expires_at IS 'When this conversation expires and can be cleaned up';

-- Column comments for user_profiles
COMMENT ON COLUMN user_profiles.reading_history IS 'Array of article IDs the user has read (JSON)';
COMMENT ON COLUMN user_profiles.preferred_topics IS 'Array of preferred topic strings (JSON)';
COMMENT ON COLUMN user_profiles.language_preference IS 'User preferred language (zh, en, etc.)';
COMMENT ON COLUMN user_profiles.interaction_patterns IS 'User interaction patterns and preferences (JSON)';
COMMENT ON COLUMN user_profiles.query_count IS 'Total number of queries made by this user';
COMMENT ON COLUMN user_profiles.satisfaction_scores IS 'Array of satisfaction ratings (JSON)';

-- Column comments for query_logs
COMMENT ON COLUMN query_logs.query_text IS 'The user query text (encrypted at application level)';
COMMENT ON COLUMN query_logs.query_vector IS 'Vector representation of the query for similarity search';
COMMENT ON COLUMN query_logs.response_data IS 'Structured response data (JSON)';
COMMENT ON COLUMN query_logs.response_time_ms IS 'Response time in milliseconds';
COMMENT ON COLUMN query_logs.articles_found IS 'Number of articles found for this query';
COMMENT ON COLUMN query_logs.satisfaction_rating IS 'User satisfaction rating (1-5)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables were created successfully
DO $
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('article_embeddings', 'conversations', 'user_profiles', 'query_logs')
    AND table_schema = 'public';

    RAISE NOTICE 'Successfully created intelligent Q&A schema. Tables created: %', table_count;

    -- Verify pgvector extension is enabled
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'pgvector extension is enabled and ready for use';
    ELSE
        RAISE WARNING 'pgvector extension is not enabled - vector operations will not work';
    END IF;
END $;

-- ============================================================================
-- PERFORMANCE OPTIMIZATION NOTES
-- ============================================================================

-- The ivfflat indexes are created with lists=100 which is suitable for up to 100,000 vectors
-- For larger datasets, consider increasing the lists parameter:
-- - 100,000 vectors: lists = 100
-- - 1,000,000 vectors: lists = 1000
-- - 10,000,000 vectors: lists = 10000

-- Vector similarity search performance tips:
-- 1. Use LIMIT in queries to avoid scanning all vectors
-- 2. Consider using probes parameter for ivfflat index tuning
-- 3. Monitor query performance and adjust index parameters as needed
-- 4. Use partial indexes on deleted_at for better performance on active records
