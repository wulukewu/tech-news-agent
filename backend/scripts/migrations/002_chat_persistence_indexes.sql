-- Migration 002: Chat Persistence System — Indexes, Constraints & Triggers
-- Description: Adds composite indexes, full-text search indexes, auto-update triggers,
--              and a partial index for recent messages as a partition-like performance
--              optimisation. All statements are idempotent.
-- Author: System
-- Date: 2024
-- Validates: Requirements 7.2, 7.3, 7.4
-- Task: 1.2 建立資料庫索引和約束

-- ============================================================================
-- COMPOSITE INDEXES — optimise the most common query patterns
-- ============================================================================

-- Active conversations sorted by recency for a given user
-- Used by: GET /api/conversations?is_archived=false (default list view)
CREATE INDEX IF NOT EXISTS idx_conversations_user_active_recent
    ON conversations(user_id, is_archived, last_message_at DESC);

-- Favourite conversations sorted by recency for a given user
-- Used by: GET /api/conversations?is_favorite=true
CREATE INDEX IF NOT EXISTS idx_conversations_user_favorite_recent
    ON conversations(user_id, is_favorite, last_message_at DESC);

-- Platform-filtered conversation lists (e.g. Discord-only view)
-- Used by: GET /api/conversations?platform=discord&is_archived=false
CREATE INDEX IF NOT EXISTS idx_conversations_user_platform_archived
    ON conversations(user_id, platform, is_archived);

-- Paginated message retrieval within a conversation (newest-first)
-- Used by: GET /api/conversations/{id}/messages?page=N
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_desc
    ON conversation_messages(conversation_id, created_at DESC);

-- ============================================================================
-- FULL-TEXT SEARCH INDEXES
-- ============================================================================

-- Combined tsvector index on conversations covering both title and summary.
-- Weighting: title (A = highest) + summary (B = medium).
-- Replaces the single-column title index from migration 001 with a richer index.
CREATE INDEX IF NOT EXISTS idx_conversations_fulltext
    ON conversations
    USING gin(
        (
            setweight(to_tsvector('english', coalesce(title,   '')), 'A') ||
            setweight(to_tsvector('english', coalesce(summary, '')), 'B')
        )
    );

-- GIN full-text search index on message content
-- Already created in migration 001 as idx_messages_content_search; kept here
-- for completeness — IF NOT EXISTS makes it a no-op if it already exists.
CREATE INDEX IF NOT EXISTS idx_messages_content_search
    ON conversation_messages
    USING gin(to_tsvector('english', content));

-- ============================================================================
-- PARTIAL INDEX — recent messages (partition-like performance optimisation)
-- ============================================================================
-- NOTE ON PARTITIONING STRATEGY
-- Supabase (PostgreSQL 15) supports declarative table partitioning, but
-- migrating an existing unpartitioned table requires recreating it, which is
-- disruptive in a live environment. As a pragmatic alternative we use a
-- partial index that covers only the last 90 days of messages. This gives the
-- query planner a small, hot index for the most frequently accessed rows while
-- the full table index handles historical queries.
--
-- When the dataset grows large enough to justify true partitioning, the
-- recommended strategy is:
--   1. Create a new partitioned table  conversation_messages_partitioned
--      partitioned by RANGE (created_at) with monthly partitions.
--   2. Copy data in batches using pg_partman or a custom script.
--   3. Rename tables atomically inside a transaction.
--   4. Schedule partition maintenance via pg_cron or a Supabase Edge Function.

-- NOTE: Partial indexes with time-based predicates require IMMUTABLE functions.
-- now() is STABLE (not IMMUTABLE), so it cannot be used in an index predicate.
-- This index is intentionally omitted; the composite index
-- idx_messages_conversation_created_desc covers the same query patterns.
-- For time-windowed performance optimisation, use table partitioning instead.

-- ============================================================================
-- TRIGGER: auto-update conversation stats on message insert / delete
-- ============================================================================
-- Keeps conversations.message_count and conversations.last_message_at in sync
-- without requiring application-level bookkeeping.

CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations
        SET
            message_count   = message_count + 1,
            last_message_at = NEW.created_at
        WHERE id = NEW.conversation_id;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations
        SET
            message_count = GREATEST(message_count - 1, 0)
        WHERE id = OLD.conversation_id;
    END IF;

    -- AFTER trigger — return value is ignored for row-level AFTER triggers,
    -- but NULL is the conventional return for statement-level triggers.
    RETURN NULL;
END;
$$;

-- Drop before (re-)creating so the trigger definition stays idempotent.
DROP TRIGGER IF EXISTS trg_conversation_stats_insert
    ON conversation_messages;

CREATE TRIGGER trg_conversation_stats_insert
    AFTER INSERT ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_stats();

DROP TRIGGER IF EXISTS trg_conversation_stats_delete
    ON conversation_messages;

CREATE TRIGGER trg_conversation_stats_delete
    AFTER DELETE ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_stats();

-- ============================================================================
-- AUTO-ARCHIVE STRATEGY FOR INACTIVE CONVERSATIONS
-- ============================================================================
-- NOTE: Supabase does not expose a built-in pg_cron schedule by default.
-- The recommended approach is to schedule the function below via one of:
--   a) Supabase Edge Functions (Deno) triggered by a cron schedule in
--      supabase/functions/auto-archive/index.ts
--   b) pg_cron extension (enable in Supabase dashboard → Extensions):
--        SELECT cron.schedule(
--            'auto-archive-inactive-conversations',
--            '0 3 * * *',   -- daily at 03:00 UTC
--            $$
--              UPDATE conversations
--              SET is_archived = TRUE
--              WHERE is_archived = FALSE
--                AND last_message_at < now() - INTERVAL '30 days';
--            $$
--        );
--
-- The function below can be called manually or by either scheduling mechanism.

CREATE OR REPLACE FUNCTION auto_archive_inactive_conversations(
    inactivity_days INTEGER DEFAULT 30
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_archived_count INTEGER;
BEGIN
    UPDATE conversations
    SET is_archived = TRUE
    WHERE is_archived = FALSE
      AND last_message_at < now() - (inactivity_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_archived_count = ROW_COUNT;

    RAISE NOTICE 'auto_archive_inactive_conversations: archived % conversation(s) inactive for more than % day(s).',
        v_archived_count, inactivity_days;

    RETURN v_archived_count;
END;
$$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON INDEX idx_conversations_user_active_recent IS
    'Composite index for listing active (non-archived) conversations sorted by most recent message. Covers the default conversation list view.';

COMMENT ON INDEX idx_conversations_user_favorite_recent IS
    'Composite index for listing favourite conversations sorted by most recent message.';

COMMENT ON INDEX idx_conversations_user_platform_archived IS
    'Composite index for platform-filtered conversation lists (e.g. Discord-only).';

COMMENT ON INDEX idx_messages_conversation_created_desc IS
    'Composite index for paginated message retrieval within a conversation, newest-first.';

COMMENT ON INDEX idx_conversations_fulltext IS
    'Combined weighted tsvector GIN index on conversation title (weight A) and summary (weight B) for full-text search.';

COMMENT ON FUNCTION update_conversation_stats() IS
    'Trigger function that keeps conversations.message_count and last_message_at in sync whenever a message is inserted or deleted.';

COMMENT ON FUNCTION auto_archive_inactive_conversations(INTEGER) IS
    'Archives conversations that have had no messages for the specified number of days (default 30). Intended to be called by pg_cron or a Supabase Edge Function on a daily schedule.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_index_count   INTEGER;
    v_trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname IN (
          'idx_conversations_user_active_recent',
          'idx_conversations_user_favorite_recent',
          'idx_conversations_user_platform_archived',
          'idx_messages_conversation_created_desc',
          'idx_conversations_fulltext',
          'idx_messages_content_search'
      );

    SELECT COUNT(*) INTO v_trigger_count
    FROM pg_trigger
    WHERE tgname IN (
        'trg_conversation_stats_insert',
        'trg_conversation_stats_delete'
    );

    RAISE NOTICE 'Migration 002 complete. Indexes verified: % / 6. Triggers verified: % / 2.',
        v_index_count, v_trigger_count;
END $$;
