-- Migration: Create notification_history table
-- Description: Add support for tracking notification delivery history

-- Create notification_history table
CREATE TABLE notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('discord', 'email')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('sent', 'failed', 'queued', 'cancelled')),
    content TEXT,
    feed_source VARCHAR(255),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX idx_notification_history_user_sent_at ON notification_history(user_id, sent_at DESC);
CREATE INDEX idx_notification_history_status ON notification_history(user_id, status);
CREATE INDEX idx_notification_history_channel ON notification_history(user_id, channel);

-- Add constraints
ALTER TABLE notification_history
ADD CONSTRAINT chk_notification_history_retry_count
CHECK (retry_count >= 0 AND retry_count <= 5);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_notification_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_update_notification_history_updated_at
    BEFORE UPDATE ON notification_history
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_history_updated_at();

-- Add comments for documentation
COMMENT ON TABLE notification_history IS 'Tracks notification delivery history and status';
COMMENT ON COLUMN notification_history.channel IS 'Delivery channel: discord or email';
COMMENT ON COLUMN notification_history.status IS 'Delivery status: sent, failed, queued, cancelled';
COMMENT ON COLUMN notification_history.content IS 'Notification content or summary';
COMMENT ON COLUMN notification_history.feed_source IS 'RSS feed source that triggered the notification';
COMMENT ON COLUMN notification_history.error_message IS 'Error details if delivery failed';
COMMENT ON COLUMN notification_history.retry_count IS 'Number of retry attempts (max 5)';
