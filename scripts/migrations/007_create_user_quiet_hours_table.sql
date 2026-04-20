-- Migration: Create user_quiet_hours table
-- Description: Add support for user-defined quiet hours when notifications should not be sent
-- Author: System
-- Date: 2026-04-20

-- Create user_quiet_hours table
CREATE TABLE IF NOT EXISTS user_quiet_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    weekdays INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7], -- 1=Monday, 7=Sunday
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_user_quiet_hours_user_id ON user_quiet_hours(user_id);
CREATE INDEX IF NOT EXISTS idx_user_quiet_hours_enabled ON user_quiet_hours(user_id, enabled);
CREATE INDEX IF NOT EXISTS idx_user_quiet_hours_time_range ON user_quiet_hours(user_id, start_time, end_time);

-- Add unique constraint to ensure one quiet hours setting per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_quiet_hours_unique_user ON user_quiet_hours(user_id);

-- Add check constraints
ALTER TABLE user_quiet_hours
ADD CONSTRAINT chk_quiet_hours_timezone
CHECK (timezone ~ '^[A-Za-z_]+/[A-Za-z_]+$' OR timezone = 'UTC');

ALTER TABLE user_quiet_hours
ADD CONSTRAINT chk_quiet_hours_weekdays
CHECK (
    weekdays IS NOT NULL
    AND array_length(weekdays, 1) > 0
    AND weekdays <@ ARRAY[1,2,3,4,5,6,7]
);

-- Add comments for documentation
COMMENT ON TABLE user_quiet_hours IS 'User-defined quiet hours when notifications should not be sent';
COMMENT ON COLUMN user_quiet_hours.user_id IS 'Reference to the user who owns these quiet hours settings';
COMMENT ON COLUMN user_quiet_hours.start_time IS 'Start time of quiet hours (local time)';
COMMENT ON COLUMN user_quiet_hours.end_time IS 'End time of quiet hours (local time)';
COMMENT ON COLUMN user_quiet_hours.timezone IS 'Timezone for interpreting start_time and end_time';
COMMENT ON COLUMN user_quiet_hours.weekdays IS 'Array of weekdays when quiet hours apply (1=Monday, 7=Sunday)';
COMMENT ON COLUMN user_quiet_hours.enabled IS 'Whether quiet hours are currently active';

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_quiet_hours_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_quiet_hours_updated_at
    BEFORE UPDATE ON user_quiet_hours
    FOR EACH ROW
    EXECUTE FUNCTION update_user_quiet_hours_updated_at();

-- Insert default quiet hours for existing users (disabled by default)
-- This ensures backward compatibility
INSERT INTO user_quiet_hours (user_id, start_time, end_time, timezone, weekdays, enabled)
SELECT
    id as user_id,
    '22:00'::TIME as start_time,
    '08:00'::TIME as end_time,
    COALESCE(
        (SELECT timezone FROM user_notification_preferences WHERE user_id = users.id LIMIT 1),
        'UTC'
    ) as timezone,
    ARRAY[1,2,3,4,5,6,7] as weekdays,
    false as enabled
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM user_quiet_hours WHERE user_quiet_hours.user_id = users.id
);

-- Verify the migration
DO $$
DECLARE
    table_exists BOOLEAN;
    index_count INTEGER;
    user_count INTEGER;
    quiet_hours_count INTEGER;
BEGIN
    -- Check if table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'user_quiet_hours'
    ) INTO table_exists;

    IF NOT table_exists THEN
        RAISE EXCEPTION 'Migration failed: user_quiet_hours table was not created';
    END IF;

    -- Check if indexes were created
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 'user_quiet_hours';

    IF index_count < 4 THEN
        RAISE EXCEPTION 'Migration failed: Expected at least 4 indexes, found %', index_count;
    END IF;

    -- Check if default records were created
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO quiet_hours_count FROM user_quiet_hours;

    IF user_count > 0 AND quiet_hours_count = 0 THEN
        RAISE EXCEPTION 'Migration failed: No default quiet hours created for existing users';
    END IF;

    RAISE NOTICE 'Migration completed successfully: user_quiet_hours table created with % records', quiet_hours_count;
END $$;
