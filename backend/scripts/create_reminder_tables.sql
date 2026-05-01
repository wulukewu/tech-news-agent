-- Intelligent Reminder Agent - Simplified Schema for Testing
-- Execute this in Supabase SQL Editor

-- Article relationship graph table
CREATE TABLE IF NOT EXISTS article_graph (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_article_id UUID NOT NULL,
    target_article_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    analysis_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Technology version registry
CREATE TABLE IF NOT EXISTS technology_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technology_name VARCHAR(255) NOT NULL,
    current_version VARCHAR(100) NOT NULL,
    previous_version VARCHAR(100),
    version_type VARCHAR(20) NOT NULL,
    release_date TIMESTAMP WITH TIME ZONE,
    release_notes TEXT,
    importance_level INTEGER NOT NULL,
    source_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User reminder settings
CREATE TABLE IF NOT EXISTS reminder_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    enabled BOOLEAN DEFAULT true,
    max_daily_reminders INTEGER DEFAULT 5,
    preferred_channels JSONB DEFAULT '["discord"]',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    reminder_frequency VARCHAR(20) DEFAULT 'smart',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reminder log for tracking effectiveness
CREATE TABLE IF NOT EXISTS reminder_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    reminder_type VARCHAR(50) NOT NULL,
    content_id UUID,
    reminder_context JSONB NOT NULL DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'sent',
    response_time INTERVAL,
    effectiveness_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User behavior patterns for timing optimization
CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL DEFAULT '{}',
    confidence_level FLOAT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_article_graph_source ON article_graph(source_article_id);
CREATE INDEX IF NOT EXISTS idx_article_graph_target ON article_graph(target_article_id);
CREATE INDEX IF NOT EXISTS idx_reminder_log_user_sent ON reminder_log(user_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_reminder_log_status ON reminder_log(status);
