-- Migration: Create user_quiet_hours table (Simplified for manual execution)
-- Description: Add support for user-defined quiet hours when notifications should not be sent

-- Create user_quiet_hours table
CREATE TABLE user_quiet_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    weekdays INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7],
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_quiet_hours_user_id ON user_quiet_hours(user_id);
CREATE INDEX idx_user_quiet_hours_enabled ON user_quiet_hours(user_id, enabled);
CREATE UNIQUE INDEX idx_user_quiet_hours_unique_user ON user_quiet_hours(user_id);

-- Add constraints
ALTER TABLE user_quiet_hours
ADD CONSTRAINT chk_quiet_hours_timezone
CHECK (timezone ~ '^[A-Za-z_]+/[A-Za-z_]+$' OR timezone = 'UTC');

ALTER TABLE user_quiet_hours
ADD CONSTRAINT chk_quiet_hours_weekdays
CHECK (weekdays IS NOT NULL AND array_length(weekdays, 1) > 0 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_user_quiet_hours_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_update_user_quiet_hours_updated_at
    BEFORE UPDATE ON user_quiet_hours
    FOR EACH ROW
    EXECUTE FUNCTION update_user_quiet_hours_updated_at();
