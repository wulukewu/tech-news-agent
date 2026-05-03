# 🚨 IMMEDIATE FIX: Apply Database Migration

## The Problem

Your QA chat is failing because the `conversations` table doesn't exist.

## Quick Fix (2 minutes)

### Step 1: Open Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. Find your project: `ieqskggdhlvepuslouxy`
3. Click on it

### Step 2: Open SQL Editor

1. Click "SQL Editor" in the left sidebar
2. Click "New query"

### Step 3: Copy the Migration SQL

The migration file is at: `backend/scripts/migrations/007_create_intelligent_qa_schema.sql`

**I'll show you the key parts you need to copy:**

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create conversations table (THIS IS WHAT'S MISSING)
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations(last_updated);
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;

-- Create other required tables for full QA functionality
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

-- Create vector indexes
CREATE INDEX IF NOT EXISTS idx_article_embeddings_cosine
ON article_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_query_logs_vector_cosine
ON query_logs USING ivfflat (query_vector vector_cosine_ops)
WITH (lists = 100);
```

### Step 4: Run the SQL

1. Paste the SQL above into the SQL Editor
2. Click "Run"
3. Wait for "Success" message

### Step 5: Restart Backend

```bash
docker-compose restart tech-news-agent-backend-dev
```

## Test It

1. Go to http://localhost:3000/chat
2. Try asking a question
3. Should work now! 🎉

---

**This will fix the error immediately and unlock your QA agent!**
