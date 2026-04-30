-- 008_enhance_reminder_system.sql
-- Add reminder tracking and user feedback tables

-- Reminder logs for tracking effectiveness
CREATE TABLE IF NOT EXISTS reminder_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trigger_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    recommended_article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('add', 'rate')),
    similarity_score FLOAT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    clicked_at TIMESTAMP WITH TIME ZONE,
    user_feedback VARCHAR(20) CHECK (user_feedback IN ('accurate', 'inaccurate', 'not_interested')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_reminder_logs_user_id ON reminder_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_reminder_logs_sent_at ON reminder_logs(sent_at);
CREATE INDEX IF NOT EXISTS idx_reminder_logs_trigger_type ON reminder_logs(trigger_type);

-- Add last_reminder_sent to users table for cooldown tracking
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_reminder_sent TIMESTAMP WITH TIME ZONE;

-- Add user activity tracking for smart timing
CREATE TABLE IF NOT EXISTS user_activity_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day >= 0 AND hour_of_day <= 23),
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0=Sunday
    activity_count INTEGER DEFAULT 1,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, hour_of_day, day_of_week)
);

CREATE INDEX IF NOT EXISTS idx_user_activity_patterns_user_id ON user_activity_patterns(user_id);
