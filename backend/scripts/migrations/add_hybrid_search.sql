-- =============================================================================
-- Migration: Hybrid Search (Full-Text + pgvector) with RRF Fusion
-- Run this in Supabase SQL Editor
-- =============================================================================

-- 1. Add tsvector generated column (auto-maintained, no app-layer updates needed)
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS fts_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(ai_summary, '')), 'B')
        ) STORED;

-- 2. GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_articles_fts ON articles USING gin(fts_vector);

-- 3. Hybrid search RPC using Reciprocal Rank Fusion
CREATE OR REPLACE FUNCTION hybrid_search_articles(
    query_text      TEXT,
    query_embedding VECTOR(1024),
    user_id         UUID,
    match_count     INT   DEFAULT 10,
    rrf_k           INT   DEFAULT 60,
    fts_weight      FLOAT DEFAULT 1.0,
    vec_weight      FLOAT DEFAULT 1.0
)
RETURNS TABLE (
    id           UUID,
    title        TEXT,
    url          TEXT,
    ai_summary   TEXT,
    category     TEXT,
    published_at TIMESTAMPTZ,
    rrf_score    FLOAT
)
LANGUAGE sql STABLE
AS $$
    WITH

    -- Full-text candidates (top 5x pool)
    fts AS (
        SELECT a.id,
               ROW_NUMBER() OVER (ORDER BY ts_rank_cd(a.fts_vector, query) DESC) AS rank
        FROM articles a
        INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
        CROSS JOIN to_tsquery('english',
            websearch_to_tsquery('english', query_text)::text
        ) AS query
        WHERE us.user_id = hybrid_search_articles.user_id
          AND a.fts_vector @@ query
        LIMIT match_count * 5
    ),

    -- Vector candidates (top 5x pool)
    vec AS (
        SELECT a.id,
               ROW_NUMBER() OVER (ORDER BY a.embedding <=> query_embedding) AS rank
        FROM articles a
        INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
        WHERE us.user_id = hybrid_search_articles.user_id
          AND a.embedding IS NOT NULL
        LIMIT match_count * 5
    ),

    -- RRF fusion: score = fts_weight/(k+fts_rank) + vec_weight/(k+vec_rank)
    fused AS (
        SELECT
            coalesce(fts.id, vec.id) AS id,
            (
                CASE WHEN fts.rank IS NOT NULL
                     THEN fts_weight / (rrf_k + fts.rank) ELSE 0 END
                +
                CASE WHEN vec.rank IS NOT NULL
                     THEN vec_weight / (rrf_k + vec.rank) ELSE 0 END
            ) AS rrf_score
        FROM fts
        FULL OUTER JOIN vec ON fts.id = vec.id
    )

    SELECT a.id, a.title, a.url, a.ai_summary, a.category, a.published_at,
           f.rrf_score
    FROM fused f
    JOIN articles a ON a.id = f.id
    ORDER BY f.rrf_score DESC
    LIMIT match_count;
$$;
