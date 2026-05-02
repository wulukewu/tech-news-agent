-- Migration: add embedding to knowledge_nodes for semantic article matching
-- Voyage AI uses 1024 dimensions; articles.embedding is VECTOR(1536) but
-- we use a separate column here to avoid dimension mismatch.
-- TODO: migrate articles.embedding to 1024 dims when convenient.

ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS embedding VECTOR(1024);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_embedding
    ON knowledge_nodes USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

-- RPC function for semantic article search
-- articles.embedding is VECTOR(1536), so this only works once articles have embeddings.
-- For now the function exists but will return empty until embeddings are populated.
CREATE OR REPLACE FUNCTION match_articles_by_embedding(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.6,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        a.id,
        a.title,
        a.url,
        a.published_at,
        1 - (a.embedding::vector(1024) <=> query_embedding) AS similarity
    FROM articles a
    WHERE
        a.embedding IS NOT NULL
        AND vector_dims(a.embedding) = 1024
        AND 1 - (a.embedding::vector(1024) <=> query_embedding) > match_threshold
    ORDER BY a.embedding::vector(1024) <=> query_embedding
    LIMIT match_count;
$$;
