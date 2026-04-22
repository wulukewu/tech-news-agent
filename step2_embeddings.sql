-- 步驟 4: 建立 article_embeddings 資料表
CREATE TABLE IF NOT EXISTS article_embeddings (
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    modified_by TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    PRIMARY KEY (article_id, chunk_index)
);

-- 步驟 5: 建立 embeddings 索引
CREATE INDEX IF NOT EXISTS idx_article_embeddings_cosine
ON article_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_created_at ON article_embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_article_embeddings_deleted_at ON article_embeddings(deleted_at) WHERE deleted_at IS NULL;
