-- Migration: 029_enable_rls.sql
-- Description: Enable Row Level Security (RLS) and establish explicit access policies.
-- 1. Restricts direct write/delete access for anonymous (anon) and authenticated users to prevent data modification vulnerabilities.
-- 2. Explicitly grants full access (ALL) to service_role to guarantee backend and Discord bot operations.
-- 3. Grants SELECT (read-only) access to anonymous (anon) and authenticated users for global/public tables to guarantee seamless data fetching even with anon keys.

-- =========================================================================
-- 1. ENABLE ROW LEVEL SECURITY ON ALL TABLES
-- =========================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reading_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE dm_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE dm_sent_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE feed_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_quiet_hours ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_locks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_platform_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE preference_model ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_graph ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_tree ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_node_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE technical_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE technology_registry ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- 2. CREATE SERVICE_ROLE EXPLICIT POLICIES (FULL BYPASS SAFEGUARD)
-- =========================================================================

-- Helper to safely recreate service_role policies on all tables
DO $$
DECLARE
    t text;
    tables_list text[] := ARRAY[
        'users', 'feeds', 'articles', 'user_subscriptions', 'reading_list',
        'conversations', 'conversation_messages', 'conversation_tags', 'dm_conversations',
        'dm_sent_articles', 'feed_categories', 'user_notification_preferences', 'user_quiet_hours',
        'notification_history', 'notification_locks', 'user_profiles', 'user_platform_links',
        'preference_model', 'user_behavior_patterns', 'user_behavior_events', 'article_embeddings',
        'article_classifications', 'article_graph', 'content_feedback', 'content_quality_metrics',
        'knowledge_nodes', 'node_dependencies', 'query_logs', 'weekly_insights', 'reminder_settings',
        'reminder_log', 'learning_goals', 'learning_progress', 'learning_paths', 'learning_conversations',
        'learning_stages', 'skill_tree', 'user_node_progress', 'user_achievements',
        'user_learning_preferences', 'technical_domains', 'technology_registry'
    ];
BEGIN
    FOREACH t IN ARRAY tables_list LOOP
        EXECUTE format('DROP POLICY IF EXISTS "service_role_full_access" ON %I', t);
        EXECUTE format('CREATE POLICY "service_role_full_access" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)', t);
    END LOOP;
END $$;

-- =========================================================================
-- 3. CREATE READ-ONLY (SELECT) POLICIES FOR PUBLIC GLOBAL DATA
-- =========================================================================

-- Helper to safely create read policies for anon and authenticated on public tables
DO $$
DECLARE
    t text;
    public_tables text[] := ARRAY[
        'articles', 'feeds', 'technical_domains', 'skill_tree', 'knowledge_nodes',
        'node_dependencies', 'feed_categories', 'article_classifications', 'article_graph',
        'content_quality_metrics'
    ];
BEGIN
    FOREACH t IN ARRAY public_tables LOOP
        EXECUTE format('DROP POLICY IF EXISTS "public_read_access" ON %I', t);
        EXECUTE format('CREATE POLICY "public_read_access" ON %I FOR SELECT TO anon, authenticated USING (true)', t);
    END LOOP;
END $$;
