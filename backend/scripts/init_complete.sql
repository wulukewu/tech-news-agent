-- =============================================================================
-- Tech News Agent — Complete Database Initialization Script
-- =============================================================================
-- Run this single script in Supabase SQL Editor to set up the entire database
-- from scratch. It is fully idempotent (safe to re-run).
-- Schema verified against production on 2026-05-07.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- EXTENSIONS
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- PRE-PATCH: Add columns to any pre-existing tables before CREATE TABLE runs
-- (CREATE TABLE IF NOT EXISTS skips entirely if the table already exists)
-- ---------------------------------------------------------------------------

ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS last_proactive_dm_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS proactive_dm_frequency_hours INTEGER DEFAULT 20;

ALTER TABLE IF EXISTS feeds ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE IF EXISTS feeds ADD COLUMN IF NOT EXISTS last_fetched_at TIMESTAMPTZ;

ALTER TABLE IF EXISTS user_subscriptions ADD COLUMN IF NOT EXISTS notification_enabled BOOLEAN NOT NULL DEFAULT true;

ALTER TABLE IF EXISTS articles ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE IF EXISTS articles ADD COLUMN IF NOT EXISTS content_type VARCHAR(20);

ALTER TABLE IF EXISTS reading_list ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'web';

-- ---------------------------------------------------------------------------
-- SHARED TRIGGER FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- CORE TABLES
-- ---------------------------------------------------------------------------

-- users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    dm_notifications_enabled BOOLEAN DEFAULT true,
    last_proactive_dm_at TIMESTAMPTZ,
    proactive_dm_frequency_hours INTEGER DEFAULT 20
);

-- Patch pre-existing tables BEFORE CREATE TABLE IF NOT EXISTS (which skips if table exists)
ALTER TABLE users ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_proactive_dm_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS proactive_dm_frequency_hours INTEGER DEFAULT 20;

-- feeds
CREATE TABLE IF NOT EXISTS feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    last_fetched_at TIMESTAMPTZ
);

ALTER TABLE feeds ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE feeds ADD COLUMN IF NOT EXISTS last_fetched_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_feeds_is_active ON feeds(is_active);
CREATE INDEX IF NOT EXISTS idx_feeds_category ON feeds(category);
CREATE INDEX IF NOT EXISTS idx_feeds_created_by ON feeds(created_by);

-- user_subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMPTZ DEFAULT now(),
    notification_enabled BOOLEAN NOT NULL DEFAULT true,
    UNIQUE(user_id, feed_id)
);

-- Ensure columns added by migrations exist (safe for pre-existing tables)
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS notification_enabled BOOLEAN NOT NULL DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_feed_id ON user_subscriptions(feed_id);

-- articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMPTZ,
    tinkering_index INTEGER,
    ai_summary TEXT,
    embedding VECTOR(1024),
    fts_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(ai_summary, '')), 'B')
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT now(),
    category TEXT,
    content_type VARCHAR(20) CHECK (content_type IN ('tutorial', 'guide', 'news', 'reference', 'project', 'opinion'))
);

-- Ensure columns added by migrations exist (safe for pre-existing tables)
ALTER TABLE articles ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS content_type VARCHAR(20) CHECK (content_type IN ('tutorial', 'guide', 'news', 'reference', 'project', 'opinion'));
-- fts_vector: add only if missing (generated columns require DO block)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'articles' AND column_name = 'fts_vector'
    ) THEN
        ALTER TABLE articles
            ADD COLUMN fts_vector tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(ai_summary, '')), 'B')
            ) STORED;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_articles_feed_id ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_articles_content_type ON articles(content_type);
CREATE INDEX IF NOT EXISTS idx_articles_fts ON articles USING gin(fts_vector);

-- Backfill category from feeds for existing articles
UPDATE articles a SET category = f.category FROM feeds f WHERE a.feed_id = f.id AND a.category IS NULL;

-- reading_list
CREATE TABLE IF NOT EXISTS reading_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('Unread', 'Read', 'Archived')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    added_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    source TEXT CHECK (source IN ('discord', 'web')) DEFAULT 'web',
    UNIQUE(user_id, article_id)
);

-- Ensure columns added by migrations exist (safe for pre-existing tables)
ALTER TABLE reading_list ADD COLUMN IF NOT EXISTS source TEXT CHECK (source IN ('discord', 'web')) DEFAULT 'web';

CREATE INDEX IF NOT EXISTS idx_reading_list_user_id ON reading_list(user_id);
CREATE INDEX IF NOT EXISTS idx_reading_list_status ON reading_list(user_id, status);
CREATE INDEX IF NOT EXISTS idx_reading_list_rating ON reading_list(user_id, rating) WHERE rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reading_list_added_at ON reading_list(user_id, added_at DESC);
CREATE INDEX IF NOT EXISTS idx_reading_list_source ON reading_list(source);

DROP TRIGGER IF EXISTS update_reading_list_updated_at ON reading_list;
CREATE TRIGGER update_reading_list_updated_at
    BEFORE UPDATE ON reading_list FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- dm_sent_articles
CREATE TABLE IF NOT EXISTS dm_sent_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notification_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_user_id ON dm_sent_articles(user_id);
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_article_id ON dm_sent_articles(article_id);
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_sent_at ON dm_sent_articles(sent_at);

-- ---------------------------------------------------------------------------
-- NOTIFICATION TABLES
-- ---------------------------------------------------------------------------

-- user_notification_preferences
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    frequency TEXT NOT NULL DEFAULT 'weekly'
        CHECK (frequency IN ('daily', 'weekly', 'monthly', 'disabled')),
    notification_time TIME NOT NULL DEFAULT '18:00:00',
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',
    dm_enabled BOOLEAN NOT NULL DEFAULT true,
    email_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    tech_depth_threshold VARCHAR(20) DEFAULT 'basic'
        CONSTRAINT chk_tech_depth_threshold CHECK (tech_depth_threshold IN ('basic', 'intermediate', 'advanced', 'expert')),
    tech_depth_enabled BOOLEAN DEFAULT false,
    notification_day_of_week INTEGER DEFAULT 5
        CHECK (notification_day_of_week >= 0 AND notification_day_of_week <= 6),
    notification_day_of_month INTEGER DEFAULT 1
        CHECK (notification_day_of_month >= 1 AND notification_day_of_month <= 31),
    reminder_enabled BOOLEAN DEFAULT true,
    reminder_on_add BOOLEAN DEFAULT true,
    reminder_on_rate BOOLEAN DEFAULT true,
    reminder_cooldown_hours INTEGER DEFAULT 4,
    reminder_min_similarity FLOAT DEFAULT 0.72,
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_user_id ON user_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_frequency ON user_notification_preferences(frequency);

DROP TRIGGER IF EXISTS update_user_notification_preferences_updated_at ON user_notification_preferences;
CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- user_quiet_hours
CREATE TABLE IF NOT EXISTS user_quiet_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    weekdays INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7],
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_quiet_hours_user_id ON user_quiet_hours(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_quiet_hours_unique_user ON user_quiet_hours(user_id);

CREATE OR REPLACE FUNCTION update_user_quiet_hours_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_user_quiet_hours_updated_at ON user_quiet_hours;
CREATE TRIGGER trigger_update_user_quiet_hours_updated_at
    BEFORE UPDATE ON user_quiet_hours FOR EACH ROW EXECUTE FUNCTION update_user_quiet_hours_updated_at();

-- notification_locks
CREATE TABLE IF NOT EXISTS notification_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    instance_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, notification_type, scheduled_time)
);

CREATE INDEX IF NOT EXISTS idx_notification_locks_user_scheduled ON notification_locks(user_id, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_notification_locks_status_expires ON notification_locks(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_notification_locks_instance_status ON notification_locks(instance_id, status);

-- notification_history
CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('discord', 'email')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('sent', 'failed', 'queued', 'cancelled')),
    content TEXT,
    feed_source VARCHAR(255),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_user_sent_at ON notification_history(user_id, sent_at DESC);

CREATE OR REPLACE FUNCTION update_notification_history_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_notification_history_updated_at ON notification_history;
CREATE TRIGGER trigger_update_notification_history_updated_at
    BEFORE UPDATE ON notification_history FOR EACH ROW EXECUTE FUNCTION update_notification_history_updated_at();

-- ---------------------------------------------------------------------------
-- QA AGENT / CONVERSATIONS
-- ---------------------------------------------------------------------------

-- article_embeddings
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

CREATE INDEX IF NOT EXISTS idx_article_embeddings_cosine ON article_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_deleted_at ON article_embeddings(deleted_at) WHERE deleted_at IS NULL;

DROP TRIGGER IF EXISTS update_article_embeddings_updated_at ON article_embeddings;
CREATE TRIGGER update_article_embeddings_updated_at
    BEFORE UPDATE ON article_embeddings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- conversations
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
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    title VARCHAR(200),
    platform VARCHAR(20) NOT NULL DEFAULT 'web'
        CONSTRAINT conversations_valid_platform CHECK (platform IN ('web', 'discord')),
    tags JSONB DEFAULT '[]',
    summary TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    -- Discord Thread + Summary Buffer Memory (migration 027)
    thread_id TEXT,
    summary_buffer TEXT,
    summary_updated_at TIMESTAMPTZ,
    summarized_until_message_at TIMESTAMPTZ,
    approx_token_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_tags ON conversations USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(user_id, is_archived);
CREATE INDEX IF NOT EXISTS idx_conversations_user_active_recent ON conversations(user_id, is_archived, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_user_platform_archived ON conversations(user_id, platform, is_archived);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_id ON conversations(thread_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_conversations_discord_thread_unique
    ON conversations(thread_id)
    WHERE platform = 'discord' AND thread_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_fulltext ON conversations USING gin(
    (setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
     setweight(to_tsvector('english', coalesce(summary, '')), 'B'))
);

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- conversation_messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('web', 'discord')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    -- Discord Thread + Summary Buffer Memory (migration 027)
    thread_id TEXT,
    approx_tokens INTEGER NOT NULL DEFAULT 0,
    is_summarized BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON conversation_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_content_search ON conversation_messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_desc ON conversation_messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread_created
    ON conversation_messages(thread_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread_unsummarized
    ON conversation_messages(thread_id, is_summarized, created_at);

CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations SET message_count = message_count + 1, last_message_at = NEW.created_at WHERE id = NEW.conversation_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations SET message_count = GREATEST(message_count - 1, 0) WHERE id = OLD.conversation_id;
    END IF;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_conversation_stats_insert ON conversation_messages;
CREATE TRIGGER trg_conversation_stats_insert AFTER INSERT ON conversation_messages FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();
DROP TRIGGER IF EXISTS trg_conversation_stats_delete ON conversation_messages;
CREATE TRIGGER trg_conversation_stats_delete AFTER DELETE ON conversation_messages FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();

-- user_platform_links
CREATE TABLE IF NOT EXISTS user_platform_links (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('web', 'discord')),
    platform_user_id VARCHAR(100) NOT NULL,
    platform_username VARCHAR(100),
    linked_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE,
    verification_data JSONB DEFAULT '{}',
    PRIMARY KEY (user_id, platform),
    UNIQUE (platform, platform_user_id)
);

CREATE INDEX IF NOT EXISTS idx_platform_links_platform_user ON user_platform_links(platform, platform_user_id);

-- conversation_tags
CREATE TABLE IF NOT EXISTS conversation_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag_name VARCHAR(50) NOT NULL,
    color VARCHAR(7),
    created_at TIMESTAMPTZ DEFAULT now(),
    usage_count INTEGER DEFAULT 0,
    UNIQUE (user_id, tag_name)
);

CREATE INDEX IF NOT EXISTS idx_conversation_tags_user_id ON conversation_tags(user_id);

-- user_profiles
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

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- query_logs
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

CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_conversation_id ON query_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_deleted_at ON query_logs(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_query_logs_vector_cosine ON query_logs USING ivfflat (query_vector vector_cosine_ops) WITH (lists = 100);

DROP TRIGGER IF EXISTS update_query_logs_updated_at ON query_logs;
CREATE TRIGGER update_query_logs_updated_at
    BEFORE UPDATE ON query_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ---------------------------------------------------------------------------
-- REMINDER SYSTEM
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS article_graph (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    target_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('prerequisite', 'follow_up', 'related', 'update')),
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    analysis_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_article_id, target_article_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_article_graph_source ON article_graph(source_article_id);
CREATE INDEX IF NOT EXISTS idx_article_graph_target ON article_graph(target_article_id);

DROP TRIGGER IF EXISTS update_article_graph_updated_at ON article_graph;
CREATE TRIGGER update_article_graph_updated_at
    BEFORE UPDATE ON article_graph FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS technology_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technology_name VARCHAR(255) NOT NULL,
    current_version VARCHAR(100) NOT NULL,
    previous_version VARCHAR(100),
    version_type VARCHAR(20) NOT NULL CHECK (version_type IN ('major', 'minor', 'patch')),
    release_date TIMESTAMPTZ,
    release_notes TEXT,
    importance_level INTEGER NOT NULL CHECK (importance_level >= 1 AND importance_level <= 5),
    source_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(technology_name, current_version)
);

DROP TRIGGER IF EXISTS update_technology_registry_updated_at ON technology_registry;
CREATE TRIGGER update_technology_registry_updated_at
    BEFORE UPDATE ON technology_registry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS reminder_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    max_daily_reminders INTEGER DEFAULT 5 CHECK (max_daily_reminders >= 0 AND max_daily_reminders <= 20),
    preferred_channels JSONB DEFAULT '["discord"]',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    reminder_frequency VARCHAR(20) DEFAULT 'smart' CHECK (reminder_frequency IN ('smart', 'daily', 'weekly', 'disabled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

DROP TRIGGER IF EXISTS update_reminder_settings_updated_at ON reminder_settings;
CREATE TRIGGER update_reminder_settings_updated_at
    BEFORE UPDATE ON reminder_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS reminder_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL CHECK (reminder_type IN ('article_relation', 'version_update', 'learning_path')),
    content_id UUID,
    reminder_context JSONB NOT NULL DEFAULT '{}',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('discord', 'web', 'email')),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'read', 'clicked', 'dismissed', 'failed')),
    response_time INTERVAL,
    effectiveness_score FLOAT CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminder_log_user_sent ON reminder_log(user_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_reminder_log_status ON reminder_log(status);

DROP TRIGGER IF EXISTS update_reminder_log_updated_at ON reminder_log;
CREATE TRIGGER update_reminder_log_updated_at
    BEFORE UPDATE ON reminder_log FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('reading_time', 'active_hours', 'response_rate')),
    pattern_data JSONB NOT NULL DEFAULT '{}',
    confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, pattern_type)
);

-- ---------------------------------------------------------------------------
-- PROACTIVE LEARNING AGENT
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_behavior_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    category TEXT,
    rating INTEGER,
    duration_seconds INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_behavior_events_user_id ON user_behavior_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_events_category ON user_behavior_events(user_id, category, created_at DESC);

CREATE TABLE IF NOT EXISTS preference_model (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    category_weights JSONB NOT NULL DEFAULT '{}',
    learning_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_weekly_conversations INTEGER NOT NULL DEFAULT 3,
    conversations_this_week INTEGER NOT NULL DEFAULT 0,
    week_reset_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    preference_summary TEXT,
    summary_updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS learning_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_type TEXT NOT NULL,
    question TEXT NOT NULL,
    options JSONB,
    response TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    context_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_learning_conversations_user_pending ON learning_conversations(user_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS dm_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dm_conversations_user_created ON dm_conversations(user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- WEEKLY INSIGHTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS weekly_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    article_count INTEGER NOT NULL DEFAULT 0,
    executive_summary TEXT,
    clusters JSONB,
    trends JSONB,
    missed_articles JSONB,
    trend_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'completed',
    started_at TIMESTAMPTZ,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_weekly_insights_created_at ON weekly_insights(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_period_start ON weekly_insights(period_start DESC);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_status ON weekly_insights(status, started_at);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_user_id ON weekly_insights(user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- LEARNING PATH PLANNING
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS learning_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_skill VARCHAR(100) NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5) DEFAULT 1,
    estimated_hours INTEGER DEFAULT 0,
    status VARCHAR(20) CHECK (status IN ('active', 'completed', 'paused', 'cancelled')) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_stagnation_reminder_at TIMESTAMPTZ,
    stagnation_reminder_count_this_week INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_learning_goals_user_id ON learning_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_goals_status ON learning_goals(status);

DROP TRIGGER IF EXISTS update_learning_goals_updated_at ON learning_goals;
CREATE TRIGGER update_learning_goals_updated_at
    BEFORE UPDATE ON learning_goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    path_data JSONB NOT NULL,
    total_stages INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_paths_goal_id ON learning_paths(goal_id);

DROP TRIGGER IF EXISTS update_learning_paths_updated_at ON learning_paths;
CREATE TRIGGER update_learning_paths_updated_at
    BEFORE UPDATE ON learning_paths FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS learning_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    stage_order INTEGER NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    stage_description TEXT,
    estimated_hours INTEGER DEFAULT 0,
    prerequisites TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_stages_path_id ON learning_stages(path_id);

CREATE TABLE IF NOT EXISTS learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES learning_stages(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('not_started', 'in_progress', 'completed', 'skipped')) DEFAULT 'not_started',
    completion_percentage INTEGER CHECK (completion_percentage BETWEEN 0 AND 100) DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    stage_order INTEGER,
    CONSTRAINT learning_progress_user_goal_article_unique UNIQUE (user_id, goal_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_goal_id ON learning_progress(goal_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_status ON learning_progress(status);
CREATE INDEX IF NOT EXISTS idx_learning_progress_stage_order ON learning_progress(stage_order);

DROP TRIGGER IF EXISTS update_learning_progress_updated_at ON learning_progress;
CREATE TRIGGER update_learning_progress_updated_at
    BEFORE UPDATE ON learning_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS skill_tree (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5) DEFAULT 1,
    estimated_hours INTEGER DEFAULT 0,
    prerequisites VARCHAR(100)[],
    tags VARCHAR(50)[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS update_skill_tree_updated_at ON skill_tree;
CREATE TRIGGER update_skill_tree_updated_at
    BEFORE UPDATE ON skill_tree FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ---------------------------------------------------------------------------
-- KNOWLEDGE GRAPH
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS technical_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_builtin BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_builtin_domain_name ON technical_domains(name) WHERE created_by IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_custom_domain_name_per_user ON technical_domains(name, created_by) WHERE created_by IS NOT NULL;

DROP TRIGGER IF EXISTS update_technical_domains_updated_at ON technical_domains;
CREATE TRIGGER update_technical_domains_updated_at
    BEFORE UPDATE ON technical_domains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES technical_domains(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(300) NOT NULL,
    description TEXT,
    difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    estimated_hours FLOAT DEFAULT 1.0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_domain ON knowledge_nodes(domain_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_embedding ON knowledge_nodes USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;

CREATE TABLE IF NOT EXISTS node_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'prerequisite'
        CHECK (dependency_type IN ('prerequisite', 'related', 'extends')),
    confidence_score FLOAT NOT NULL DEFAULT 1.0 CHECK (confidence_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, dependency_type)
);

CREATE INDEX IF NOT EXISTS idx_node_dependencies_source ON node_dependencies(source_node_id);
CREATE INDEX IF NOT EXISTS idx_node_dependencies_target ON node_dependencies(target_node_id);

CREATE TABLE IF NOT EXISTS user_node_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'completed')),
    completed_at TIMESTAMPTZ,
    time_spent_minutes INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, node_id)
);

CREATE INDEX IF NOT EXISTS idx_user_node_progress_user ON user_node_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_node_progress_node ON user_node_progress(node_id);

CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES technical_domains(id) ON DELETE CASCADE,
    badge_type VARCHAR(50) NOT NULL,
    badge_name VARCHAR(200) NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, domain_id, badge_type)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);

-- ---------------------------------------------------------------------------
-- CONTENT ENHANCEMENT
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS feed_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    feed_type VARCHAR(20) NOT NULL CHECK (feed_type IN ('educational', 'news', 'official', 'community')),
    content_focus VARCHAR(20) NOT NULL CHECK (content_focus IN ('tutorial', 'guide', 'reference', 'news', 'project')),
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    update_frequency_hours INTEGER DEFAULT 24,
    target_audience VARCHAR(50),
    primary_topics TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_feed_category UNIQUE (feed_id)
);

CREATE TABLE IF NOT EXISTS article_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('tutorial', 'guide', 'news', 'reference', 'project', 'opinion')),
    difficulty_level INTEGER NOT NULL CHECK (difficulty_level BETWEEN 1 AND 4),
    learning_value_score FLOAT NOT NULL CHECK (learning_value_score >= 0.0 AND learning_value_score <= 1.0),
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    educational_features JSONB NOT NULL,
    estimated_reading_time INTEGER,
    prerequisite_skills TEXT[],
    classified_at TIMESTAMPTZ DEFAULT NOW(),
    classifier_version VARCHAR(10) DEFAULT '1.0'
);

CREATE INDEX IF NOT EXISTS idx_article_classifications_article ON article_classifications(article_id);

CREATE TABLE IF NOT EXISTS content_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    educational_value_rating INTEGER CHECK (educational_value_rating BETWEEN 1 AND 5),
    difficulty_accuracy BOOLEAN,
    content_type_accuracy BOOLEAN,
    completion_status VARCHAR(20) CHECK (completion_status IN ('completed', 'partial', 'abandoned')),
    time_spent_minutes INTEGER DEFAULT 0,
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_learning_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_content_types TEXT[] DEFAULT ARRAY['tutorial', 'guide'],
    preferred_difficulty_progression FLOAT DEFAULT 0.7,
    learning_style VARCHAR(20) DEFAULT 'balanced' CHECK (learning_style IN ('visual', 'hands-on', 'theoretical', 'balanced')),
    time_availability_minutes INTEGER DEFAULT 30,
    completion_rate_threshold FLOAT DEFAULT 0.8,
    preferences_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_preferences UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS content_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    average_rating FLOAT DEFAULT 0.0,
    completion_rate FLOAT DEFAULT 0.0,
    user_engagement_score FLOAT DEFAULT 0.0,
    recommendation_success_rate FLOAT DEFAULT 0.0,
    total_feedback_count INTEGER DEFAULT 0,
    last_calculated TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- SEMANTIC SEARCH FUNCTIONS
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION match_articles(
    query_embedding VECTOR(1024),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (id UUID, title TEXT, url TEXT, ai_summary TEXT, category TEXT, published_at TIMESTAMPTZ, similarity FLOAT)
LANGUAGE SQL STABLE AS $$
    SELECT a.id, a.title, a.url, a.ai_summary, a.category, a.published_at,
           1 - (a.embedding <=> query_embedding) AS similarity
    FROM articles a
    WHERE a.embedding IS NOT NULL
      AND 1 - (a.embedding <=> query_embedding) > match_threshold
    ORDER BY a.embedding <=> query_embedding
    LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION match_articles_by_embedding(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.6,
    match_count INT DEFAULT 5
)
RETURNS TABLE (id UUID, title TEXT, url TEXT, published_at TIMESTAMPTZ, similarity FLOAT)
LANGUAGE SQL STABLE AS $$
    SELECT a.id, a.title, a.url, a.published_at,
           1 - (a.embedding::vector(1024) <=> query_embedding) AS similarity
    FROM articles a
    WHERE a.embedding IS NOT NULL
      AND vector_dims(a.embedding) = 1024
      AND 1 - (a.embedding::vector(1024) <=> query_embedding) > match_threshold
    ORDER BY a.embedding::vector(1024) <=> query_embedding
    LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION hybrid_search_articles(
    query_text      TEXT,
    query_embedding VECTOR(1024),
    user_id         UUID,
    match_count     INT   DEFAULT 10,
    rrf_k           INT   DEFAULT 60,
    fts_weight      FLOAT DEFAULT 1.0,
    vec_weight      FLOAT DEFAULT 1.0
)
RETURNS TABLE (
    id           UUID,
    title        TEXT,
    url          TEXT,
    ai_summary   TEXT,
    category     TEXT,
    published_at TIMESTAMPTZ,
    rrf_score    FLOAT
)
LANGUAGE sql STABLE
AS $$
    WITH
    fts AS (
        SELECT a.id,
               ROW_NUMBER() OVER (ORDER BY ts_rank_cd(a.fts_vector, query) DESC) AS rank
        FROM articles a
        INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
        CROSS JOIN to_tsquery('english',
            websearch_to_tsquery('english', query_text)::text
        ) AS query
        WHERE us.user_id = hybrid_search_articles.user_id
          AND a.fts_vector @@ query
        LIMIT match_count * 5
    ),
    vec AS (
        SELECT a.id,
               ROW_NUMBER() OVER (ORDER BY a.embedding <=> query_embedding) AS rank
        FROM articles a
        INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
        WHERE us.user_id = hybrid_search_articles.user_id
          AND a.embedding IS NOT NULL
        LIMIT match_count * 5
    ),
    fused AS (
        SELECT
            coalesce(fts.id, vec.id) AS id,
            (
                CASE WHEN fts.rank IS NOT NULL
                     THEN fts_weight / (rrf_k + fts.rank) ELSE 0 END
                +
                CASE WHEN vec.rank IS NOT NULL
                     THEN vec_weight / (rrf_k + vec.rank) ELSE 0 END
            ) AS rrf_score
        FROM fts
        FULL OUTER JOIN vec ON fts.id = vec.id
    )
    SELECT a.id, a.title, a.url, a.ai_summary, a.category, a.published_at,
           f.rrf_score
    FROM fused f
    JOIN articles a ON a.id = f.id
    ORDER BY f.rrf_score DESC
    LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION auto_archive_inactive_conversations(inactivity_days INTEGER DEFAULT 30)
RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_archived_count INTEGER;
BEGIN
    UPDATE conversations SET is_archived = TRUE
    WHERE is_archived = FALSE AND last_message_at < now() - (inactivity_days || ' days')::INTERVAL;
    GET DIAGNOSTICS v_archived_count = ROW_COUNT;
    RETURN v_archived_count;
END;
$$;

-- ---------------------------------------------------------------------------
-- SEED DATA: built-in technical domains
-- ---------------------------------------------------------------------------

INSERT INTO technical_domains (name, display_name, description, icon, is_builtin) VALUES
    ('kubernetes', 'Kubernetes', 'Container orchestration platform', '⚙️', true),
    ('react', 'React', 'JavaScript UI library', '⚛️', true),
    ('python', 'Python', 'General-purpose programming language', '🐍', true),
    ('machine-learning', 'Machine Learning', 'ML algorithms and techniques', '🤖', true),
    ('devops', 'DevOps', 'Development and operations practices', '🔄', true),
    ('typescript', 'TypeScript', 'Typed JavaScript superset', '📘', true),
    ('docker', 'Docker', 'Container platform', '🐳', true),
    ('rust', 'Rust', 'Systems programming language', '🦀', true),
    ('golang', 'Go', 'Concurrent systems language', '🐹', true),
    ('nextjs', 'Next.js', 'React framework for production', '▲', true)
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- SEED DATA: default RSS feeds
-- ---------------------------------------------------------------------------

INSERT INTO feeds (name, url, category, is_active) VALUES
    ('Google AI Blog', 'http://googleresearch.blogspot.com/atom.xml', 'AI & Machine Learning', true),
    ('Simon Willison''s Weblog', 'https://simonwillison.net/atom/everything/', 'AI & Machine Learning', true),
    ('MIT Technology Review - AI', 'https://www.technologyreview.com/topic/artificial-intelligence/feed/', 'AI & Machine Learning', true),
    ('OpenAI Engineering', 'https://openai.com/news/engineering/rss.xml', 'Research & Academia', true),
    ('Lil''Log (Lilian Weng)', 'https://lilianweng.github.io/lil-log/feed.xml', 'Individual Engineers & Thought Leaders', true),
    ('ByteByteGo', 'https://blog.bytebytego.com/feed', 'Architecture & System Design', true),
    ('High Scalability', 'http://feeds.feedburner.com/HighScalability', 'Architecture & System Design', true),
    ('Martin Fowler Blog', 'https://martinfowler.com/feed.atom', 'Architecture & System Design', true),
    ('ACM Queue', 'https://queue.acm.org/rss/feeds/queuecontent.xml', 'Architecture & System Design', true),
    ('Netflix Tech Blog', 'https://netflixtechblog.medium.com/feed', 'Architecture & System Design', true),
    ('Stripe Engineering', 'https://stripe.com/blog/feed.rss', 'Architecture & System Design', true),
    ('Cloudflare Blog', 'https://blog.cloudflare.com/rss/', 'Cloud Native, DevOps & SRE', true),
    ('Uber Engineering', 'https://www.uber.com/blog/engineering/rss/', 'Engineering Blogs - Big Tech', true),
    ('Slack Engineering', 'https://slack.engineering/feed', 'Engineering Blogs - Big Tech', true),
    ('Spotify Engineering', 'https://engineering.atspotify.com/feed/', 'Engineering Blogs - Big Tech', true),
    ('Engineering at Meta', 'https://engineering.fb.com/feed/', 'Engineering Blogs - Big Tech', true),
    ('AWS Blog', 'https://aws.amazon.com/blogs/aws/feed/', 'Open Source & Developer Tools', true),
    ('Kubernetes Official Blog', 'https://kubernetes.io/feed.xml', 'Cloud Native, DevOps & SRE', true),
    ('SRE Weekly', 'https://sreweekly.com/feed', 'Cloud Native, DevOps & SRE', true),
    ('HashiCorp Blog', 'https://www.hashicorp.com/blog/feed.xml', 'Cloud Native, DevOps & SRE', true),
    ('Krebs on Security', 'https://krebsonsecurity.com/feed/', 'Cybersecurity & InfoSec', true),
    ('Google Project Zero', 'https://googleprojectzero.blogspot.com/feeds/posts/default', 'Cybersecurity & InfoSec', true),
    ('PortSwigger Research', 'https://portswigger.net/research/rss', 'Cybersecurity & InfoSec', true),
    ('The Rust Blog', 'https://blog.rust-lang.org/feed.xml', 'Core Programming Languages', true),
    ('This Week in Rust', 'https://this-week-in-rust.org/rss.xml', 'Core Programming Languages', true),
    ('The Go Blog', 'http://blog.golang.org/feeds/posts/default', 'Core Programming Languages', true),
    ('Go Weekly', 'https://golangweekly.com/rss/1jn0ck6', 'Core Programming Languages', true),
    ('TypeScript Blog', 'https://devblogs.microsoft.com/typescript/feed/', 'TypeScript & JavaScript Ecosystem', true),
    ('Next.js Blog', 'https://nextjs.org/feed.xml', 'Web Development & Programming', true),
    ('React Blog', 'https://react.dev/rss.xml', 'Official Documentation', true),
    ('Node.js Blog', 'https://nodejs.org/en/feed/blog.xml', 'Official Documentation', true),
    ('MDN Web Docs Blog', 'https://developer.mozilla.org/en-US/blog/rss.xml', 'Official Documentation', true),
    ('GitHub Blog', 'https://github.blog/feed/', 'Official Updates', true),
    ('The Pragmatic Engineer', 'https://blog.pragmaticengineer.com/rss/', 'Tech Strategy & Engineering Management', true),
    ('Stratechery', 'https://stratechery.com/feed/', 'Tech Strategy & Engineering Management', true),
    ('TLDR Tech', 'https://tldr.tech/api/rss/tech', 'Platform Aggregators', true)
ON CONFLICT (url) DO NOTHING;

-- ---------------------------------------------------------------------------
-- DISABLE ROW LEVEL SECURITY
-- The backend uses the service role key which should bypass RLS, but
-- PostgREST enforces RLS even for service role unless explicitly disabled.
-- ---------------------------------------------------------------------------

ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE feeds DISABLE ROW LEVEL SECURITY;
ALTER TABLE articles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions DISABLE ROW LEVEL SECURITY;
ALTER TABLE reading_list DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE dm_conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE dm_sent_articles DISABLE ROW LEVEL SECURITY;
ALTER TABLE feed_categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_notification_preferences DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_quiet_hours DISABLE ROW LEVEL SECURITY;
ALTER TABLE notification_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE notification_locks DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_platform_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE preference_model DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_patterns DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE article_embeddings DISABLE ROW LEVEL SECURITY;
ALTER TABLE article_classifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE article_graph DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_quality_metrics DISABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_nodes DISABLE ROW LEVEL SECURITY;
ALTER TABLE node_dependencies DISABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_insights DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE learning_goals DISABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE learning_paths DISABLE ROW LEVEL SECURITY;
ALTER TABLE learning_conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE learning_stages DISABLE ROW LEVEL SECURITY;
ALTER TABLE skill_tree DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_node_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_preferences DISABLE ROW LEVEL SECURITY;
ALTER TABLE technical_domains DISABLE ROW LEVEL SECURITY;
ALTER TABLE technology_registry DISABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- VERIFICATION
-- ---------------------------------------------------------------------------

DO $$
DECLARE tbl_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tbl_count FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    RAISE NOTICE '=== init_complete.sql finished. Tables: % ===', tbl_count;
END $$;
