-- Migration 011: Create Security Audit Log Table
-- Description: Creates security audit log table for tracking security events
-- Author: System
-- Date: 2024
-- Validates: Requirements 10.1, 10.3, 10.4, 10.5
-- Task: 11.1 Implement data encryption and access control

-- ============================================================================
-- SECURITY AUDIT LOG TABLE
-- ============================================================================

-- Create security_audit_log table for tracking security events
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- access_denied, secure_delete, etc.
    resource_type VARCHAR(50) NOT NULL,  -- conversation, query_log, profile, etc.
    resource_id UUID,  -- ID of the resource involved (nullable for bulk operations)
    reason VARCHAR(100) NOT NULL,  -- Reason for the event
    metadata JSONB DEFAULT '{}',  -- Additional event metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,  -- Optional IP address tracking
    user_agent TEXT  -- Optional user agent tracking
);

-- Create indexes for security_audit_log
CREATE INDEX IF NOT EXISTS idx_security_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_event_type ON security_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_resource_type ON security_audit_log(resource_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_created_at ON security_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_resource_id ON security_audit_log(resource_id) WHERE resource_id IS NOT NULL;

-- ============================================================================
-- READING HISTORY TABLE (Enhanced for Task 11.1)
-- ============================================================================

-- Create reading_history table for detailed reading tracking
CREATE TABLE IF NOT EXISTS reading_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    read_at TIMESTAMPTZ DEFAULT NOW(),
    read_duration_seconds INTEGER,
    completion_rate FLOAT CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    satisfaction_score FLOAT CHECK (satisfaction_score >= 0.0 AND satisfaction_score <= 1.0),
    feedback_type VARCHAR(20) DEFAULT 'implicit',  -- explicit or implicit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, article_id, read_at)
);

-- Create indexes for reading_history
CREATE INDEX IF NOT EXISTS idx_reading_history_user_id ON reading_history(user_id);
CREATE INDEX IF NOT EXISTS idx_reading_history_article_id ON reading_history(article_id);
CREATE INDEX IF NOT EXISTS idx_reading_history_read_at ON reading_history(read_at);
CREATE INDEX IF NOT EXISTS idx_reading_history_satisfaction ON reading_history(satisfaction_score) WHERE satisfaction_score IS NOT NULL;

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

-- Create trigger for reading_history updated_at
CREATE TRIGGER update_reading_history_updated_at
    BEFORE UPDATE ON reading_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

-- Table comments
COMMENT ON TABLE security_audit_log IS 'Audit log for security events (access control, deletions, etc.)';
COMMENT ON TABLE reading_history IS 'Detailed reading history with engagement metrics';

-- Column comments for security_audit_log
COMMENT ON COLUMN security_audit_log.event_type IS 'Type of security event (access_denied, secure_delete, etc.)';
COMMENT ON COLUMN security_audit_log.resource_type IS 'Type of resource involved (conversation, query_log, profile, etc.)';
COMMENT ON COLUMN security_audit_log.resource_id IS 'ID of the resource involved (nullable for bulk operations)';
COMMENT ON COLUMN security_audit_log.reason IS 'Reason for the security event';
COMMENT ON COLUMN security_audit_log.metadata IS 'Additional event metadata (JSON)';

-- Column comments for reading_history
COMMENT ON COLUMN reading_history.read_duration_seconds IS 'Time spent reading the article in seconds';
COMMENT ON COLUMN reading_history.completion_rate IS 'Percentage of article read (0.0-1.0)';
COMMENT ON COLUMN reading_history.satisfaction_score IS 'User satisfaction score (0.0-1.0)';
COMMENT ON COLUMN reading_history.feedback_type IS 'Type of feedback (explicit or implicit)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('security_audit_log', 'reading_history')
    AND table_schema = 'public';

    RAISE NOTICE 'Successfully created security tables. Tables created: %', table_count;
END $$;
