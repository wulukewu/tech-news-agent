-- Semantic search function for articles using pgvector cosine similarity
-- Run this in Supabase SQL Editor

-- First resize the embedding column to 1024 dimensions (Voyage AI voyage-3 model)
ALTER TABLE articles ALTER COLUMN embedding TYPE VECTOR(1024);
DROP INDEX IF EXISTS idx_articles_embedding;
CREATE INDEX idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);

-- Create the match_articles function for semantic search
CREATE OR REPLACE FUNCTION match_articles(
  query_embedding VECTOR(1024),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  url TEXT,
  ai_summary TEXT,
  category TEXT,
  published_at TIMESTAMPTZ,
  similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
  SELECT
    a.id,
    a.title,
    a.url,
    a.ai_summary,
    a.category,
    a.published_at,
    1 - (a.embedding <=> query_embedding) AS similarity
  FROM articles a
  WHERE a.embedding IS NOT NULL
  ORDER BY a.embedding <=> query_embedding
  LIMIT match_count;
$$;
