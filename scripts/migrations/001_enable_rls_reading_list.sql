-- Migration: Enable Row Level Security (RLS) on reading_list table
-- This migration implements RLS policies to ensure users can only access their own reading list data
-- Validates: Requirements 10.8

-- Enable Row Level Security on reading_list table
ALTER TABLE reading_list ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only SELECT their own reading list entries
-- Ensures user_id = auth.uid() for all SELECT operations
CREATE POLICY reading_list_select_policy ON reading_list
    FOR SELECT
    USING (user_id = auth.uid());

-- Policy: Users can only INSERT entries with their own user_id
-- Ensures user_id = auth.uid() for all INSERT operations
CREATE POLICY reading_list_insert_policy ON reading_list
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can only UPDATE their own reading list entries
-- Ensures user_id = auth.uid() for all UPDATE operations
CREATE POLICY reading_list_update_policy ON reading_list
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can only DELETE their own reading list entries
-- Ensures user_id = auth.uid() for all DELETE operations
CREATE POLICY reading_list_delete_policy ON reading_list
    FOR DELETE
    USING (user_id = auth.uid());

-- Verify RLS is enabled
DO $
BEGIN
    IF NOT (SELECT relrowsecurity FROM pg_class WHERE relname = 'reading_list') THEN
        RAISE EXCEPTION 'RLS is not enabled on reading_list table';
    END IF;
END $;
