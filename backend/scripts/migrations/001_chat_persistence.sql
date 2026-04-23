-- Migration 001: Chat Persistence System Schema
-- Description: Creates and extends database schema for chat persistence and cross-platform sync
-- Author: System
-- Date: 2024
-- Validates: Requirements 1.1, 1.2, 5.1, 5.2
-- Task: 1.1 建立資料庫遷移腳本

-- ============================================================================
-- EXTEND CONVERSATIONS TABLE
-- ============================================================================

-- The conversations table may already exist (used by QA agent).
-- We add the new columns required for chat persistence if they don't exist yet.

DO $$
BEGIN
    -- title: human-readable conversation title
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'title'
    ) THEN
        ALTER TABLE conversations ADD COLUMN title VARCHAR(200);
        RAISE NOTICE 'Added column: conversations.title';
    END IF;

    -- platform: originating platform (web or discord)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'platform'
    ) THEN
        ALTER TABLE conversations ADD COLUMN platform VARCHAR(20) NOT NULL DEFAULT 'web';
        RAISE NOTICE 'Added column: conversations.platform';
    END IF;

    -- tags: JSONB array of tag strings
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'tags'
    ) THEN
        ALTER TABLE conversations ADD COLUMN tags JSONB DEFAULT '[]';
        RAISE NOTICE 'Added column: conversations.tags';
    END IF;

    -- summary: auto-generated or user-provided conversation summary
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'summary'
    ) THEN
        ALTER TABLE conversations ADD COLUMN summary TEXT;
        RAISE NOTICE 'Added column: conversations.summary';
    END IF;

    -- is_archived: soft-archive flag (archived conversations are hidden but searchable)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'is_archived'
    ) THEN
        ALTER TABLE conversations ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added column: conversations.is_archived';
    END IF;

    -- is_favorite: user-starred conversation flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'is_favorite'
    ) THEN
        ALTER TABLE conversations ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added column: conversations.is_favorite';
    END IF;

    -- message_count: denormalized count for fast list queries
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'message_count'
    ) THEN
        ALTER TABLE conversations ADD COLUMN message_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added column: conversations.message_count';
    END IF;

    -- last_message_at: timestamp of the most recent message (for sorting)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'last_message_at'
    ) THEN
        ALTER TABLE conversations ADD COLUMN last_message_at TIMESTAMPTZ DEFAULT now();
        RAISE NOTICE 'Added column: conversations.last_message_at';
    END IF;

    -- metadata: flexible JSONB bag for future extension
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE conversations ADD COLUMN metadata JSONB DEFAULT '{}';
        RAISE NOTICE 'Added column: conversations.metadata';
    END IF;
END $$;

-- Add platform check constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'conversations'
          AND constraint_name = 'conversations_valid_platform'
    ) THEN
        ALTER TABLE conversations
            ADD CONSTRAINT conversations_valid_platform
            CHECK (platform IN ('web', 'discord'));
        RAISE NOTICE 'Added constraint: conversations_valid_platform';
    END IF;
END $$;

-- Add message_count non-negative constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'conversations'
          AND constraint_name = 'conversations_message_count_non_negative'
    ) THEN
        ALTER TABLE conversations
            ADD CONSTRAINT conversations_message_count_non_negative
            CHECK (message_count >= 0);
        RAISE NOTICE 'Added constraint: conversations_message_count_non_negative';
    END IF;
END $$;

-- ============================================================================
-- CONVERSATIONS TABLE INDEXES (new columns)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_conversations_user_platform
    ON conversations(user_id, platform);

CREATE INDEX IF NOT EXISTS idx_conversations_last_message
    ON conversations(last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_tags
    ON conversations USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_conversations_title_search
    ON conversations USING gin(to_tsvector('english', coalesce(title, '')));

CREATE INDEX IF NOT EXISTS idx_conversations_archived
    ON conversations(user_id, is_archived);

CREATE INDEX IF NOT EXISTS idx_conversations_favorite
    ON conversations(user_id, is_favorite);

-- ============================================================================
-- CONVERSATION MESSAGES TABLE
-- ============================================================================

-- Stores individual messages within a conversation, with platform source tracking.
CREATE TABLE IF NOT EXISTS conversation_messages (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID        NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             VARCHAR(20) NOT NULL,
    content          TEXT        NOT NULL,
    platform         VARCHAR(20) NOT NULL,
    metadata         JSONB       DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT conversation_messages_valid_role
        CHECK (role IN ('user', 'assistant')),
    CONSTRAINT conversation_messages_valid_platform
        CHECK (platform IN ('web', 'discord')),
    CONSTRAINT conversation_messages_content_not_empty
        CHECK (content IS NOT NULL AND length(trim(content)) > 0)
);

-- Indexes for conversation_messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON conversation_messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
    ON conversation_messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_content_search
    ON conversation_messages USING gin(to_tsvector('english', content));

-- ============================================================================
-- USER PLATFORM LINKS TABLE
-- ============================================================================

-- Links a system user account to their identity on an external platform (e.g. Discord).
-- Supports one-to-many: a single user_id can have links to multiple platforms.
CREATE TABLE IF NOT EXISTS user_platform_links (
    user_id           UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform          VARCHAR(20) NOT NULL,
    platform_user_id  VARCHAR(100) NOT NULL,
    platform_username VARCHAR(100),
    linked_at         TIMESTAMPTZ DEFAULT now(),
    is_active         BOOLEAN     DEFAULT TRUE,
    verification_data JSONB       DEFAULT '{}',

    PRIMARY KEY (user_id, platform),
    UNIQUE (platform, platform_user_id),

    CONSTRAINT user_platform_links_valid_platform
        CHECK (platform IN ('web', 'discord'))
);

-- Indexes for user_platform_links
CREATE INDEX IF NOT EXISTS idx_platform_links_platform_user
    ON user_platform_links(platform, platform_user_id);

CREATE INDEX IF NOT EXISTS idx_platform_links_user_id
    ON user_platform_links(user_id);

CREATE INDEX IF NOT EXISTS idx_platform_links_active
    ON user_platform_links(user_id, is_active);

-- ============================================================================
-- CONVERSATION TAGS TABLE
-- ============================================================================

-- Manages the tag vocabulary per user, including display color and usage statistics.
CREATE TABLE IF NOT EXISTS conversation_tags (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag_name    VARCHAR(50) NOT NULL,
    color       VARCHAR(7),  -- hex color code, e.g. '#3B82F6'
    created_at  TIMESTAMPTZ DEFAULT now(),
    usage_count INTEGER     DEFAULT 0,

    UNIQUE (user_id, tag_name),

    CONSTRAINT conversation_tags_usage_count_non_negative
        CHECK (usage_count >= 0),
    CONSTRAINT conversation_tags_color_format
        CHECK (color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$')
);

-- Indexes for conversation_tags
CREATE INDEX IF NOT EXISTS idx_conversation_tags_user_id
    ON conversation_tags(user_id);

CREATE INDEX IF NOT EXISTS idx_conversation_tags_usage
    ON conversation_tags(user_id, usage_count DESC);

-- ============================================================================
-- TABLE AND COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE conversation_messages IS
    'Individual messages within a conversation, tracking role, content, and platform source';
COMMENT ON COLUMN conversation_messages.role IS
    'Message author role: user (human) or assistant (AI)';
COMMENT ON COLUMN conversation_messages.platform IS
    'Platform where this message was sent: web or discord';
COMMENT ON COLUMN conversation_messages.metadata IS
    'Flexible JSON bag for platform-specific data (e.g. Discord message ID, attachments)';

COMMENT ON TABLE user_platform_links IS
    'Maps system user accounts to their identities on external platforms (Discord, etc.)';
COMMENT ON COLUMN user_platform_links.platform_user_id IS
    'The user identifier on the external platform (e.g. Discord snowflake ID)';
COMMENT ON COLUMN user_platform_links.verification_data IS
    'Stores verification tokens and audit data used during the linking process';

COMMENT ON TABLE conversation_tags IS
    'User-defined tag vocabulary with display color and usage frequency tracking';
COMMENT ON COLUMN conversation_tags.color IS
    'Hex color code for UI display, e.g. #3B82F6. NULL means use default color.';
COMMENT ON COLUMN conversation_tags.usage_count IS
    'Denormalized count of conversations using this tag, updated on tag add/remove';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_table_count INTEGER;
    v_col_count   INTEGER;
BEGIN
    -- Verify new tables exist
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN (
          'conversation_messages',
          'user_platform_links',
          'conversation_tags'
      );

    -- Verify new columns on conversations
    SELECT COUNT(*) INTO v_col_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'conversations'
      AND column_name IN (
          'title', 'platform', 'tags', 'summary',
          'is_archived', 'is_favorite', 'message_count',
          'last_message_at', 'metadata'
      );

    RAISE NOTICE 'Migration 001 complete. New tables created: % / 3. New conversations columns present: % / 9.',
        v_table_count, v_col_count;
END $$;
