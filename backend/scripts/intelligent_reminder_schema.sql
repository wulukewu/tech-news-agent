-- Intelligent Reminder Agent Database Schema
-- This script creates the necessary tables for the intelligent reminder system

-- Article relationship graph table
CREATE TABLE IF NOT EXISTS article_graph (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    target_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('prerequisite', 'follow_up', 'related', 'update')),
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    analysis_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_article_id, target_article_id, relationship_type)
);

-- Technology version registry
CREATE TABLE IF NOT EXISTS technology_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technology_name VARCHAR(255) NOT NULL,
    current_version VARCHAR(100) NOT NULL,
    previous_version VARCHAR(100),
    version_type VARCHAR(20) NOT NULL CHECK (version_type IN ('major', 'minor', 'patch')),
    release_date TIMESTAMP WITH TIME ZONE,
    release_notes TEXT,
    importance_level INTEGER NOT NULL CHECK (importance_level >= 1 AND importance_level <= 5),
    source_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(technology_name, current_version)
);

-- User reminder settings
CREATE TABLE IF NOT EXISTS reminder_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    max_daily_reminders INTEGER DEFAULT 5 CHECK (max_daily_reminders >= 0 AND max_daily_reminders <= 20),
    preferred_channels JSONB DEFAULT '["discord"]', -- ["discord", "web", "email"]
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    reminder_frequency VARCHAR(20) DEFAULT 'smart' CHECK (reminder_frequency IN ('smart', 'daily', 'weekly', 'disabled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Reminder log for tracking effectiveness
CREATE TABLE IF NOT EXISTS reminder_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL CHECK (reminder_type IN ('article_relation', 'version_update', 'learning_path')),
    content_id UUID, -- Can reference articles, technology_registry, etc.
    reminder_context JSONB NOT NULL DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('discord', 'web', 'email')),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'read', 'clicked', 'dismissed', 'failed')),
    response_time INTERVAL, -- Time between sent and first interaction
    effectiveness_score FLOAT CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User behavior patterns for timing optimization
CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('reading_time', 'active_hours', 'response_rate')),
    pattern_data JSONB NOT NULL DEFAULT '{}',
    confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, pattern_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_article_graph_source ON article_graph(source_article_id);
CREATE INDEX IF NOT EXISTS idx_article_graph_target ON article_graph(target_article_id);
CREATE INDEX IF NOT EXISTS idx_article_graph_type ON article_graph(relationship_type);
CREATE INDEX IF NOT EXISTS idx_technology_registry_name ON technology_registry(technology_name);
CREATE INDEX IF NOT EXISTS idx_technology_registry_updated ON technology_registry(updated_at);
CREATE INDEX IF NOT EXISTS idx_reminder_log_user_sent ON reminder_log(user_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_reminder_log_status ON reminder_log(status);
CREATE INDEX IF NOT EXISTS idx_user_behavior_user_type ON user_behavior_patterns(user_id, pattern_type);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_article_graph_updated_at BEFORE UPDATE ON article_graph FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_technology_registry_updated_at BEFORE UPDATE ON technology_registry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reminder_settings_updated_at BEFORE UPDATE ON reminder_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reminder_log_updated_at BEFORE UPDATE ON reminder_log FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
