-- Migration 027: Discord Threads + Summary Buffer Memory
-- Adds thread-aware conversation linking and summarized memory fields.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'thread_id'
    ) THEN
        ALTER TABLE conversations ADD COLUMN thread_id TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'summary_buffer'
    ) THEN
        ALTER TABLE conversations ADD COLUMN summary_buffer TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'summary_updated_at'
    ) THEN
        ALTER TABLE conversations ADD COLUMN summary_updated_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'summarized_until_message_at'
    ) THEN
        ALTER TABLE conversations ADD COLUMN summarized_until_message_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'approx_token_count'
    ) THEN
        ALTER TABLE conversations ADD COLUMN approx_token_count INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages' AND column_name = 'thread_id'
    ) THEN
        ALTER TABLE conversation_messages ADD COLUMN thread_id TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages' AND column_name = 'approx_tokens'
    ) THEN
        ALTER TABLE conversation_messages ADD COLUMN approx_tokens INTEGER NOT NULL DEFAULT 0;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages' AND column_name = 'is_summarized'
    ) THEN
        ALTER TABLE conversation_messages ADD COLUMN is_summarized BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conversations_thread_id
    ON conversations(thread_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_conversations_discord_thread_unique
    ON conversations(thread_id)
    WHERE platform = 'discord' AND thread_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread_created
    ON conversation_messages(thread_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread_unsummarized
    ON conversation_messages(thread_id, is_summarized, created_at);
