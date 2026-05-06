# Knowledge Graph — Article Linking

## 現狀

知識節點目前是 AI 憑空生成的抽象概念，與用戶實際訂閱的 RSS 文章完全沒有連結。

## 已實作（輕量版）

用關鍵字匹配將文章連結到知識節點：
- 節點名稱 / display_name 與文章 title、feed category 做字串比對
- 每個節點顯示「相關文章 N 篇」
- 點擊節點可看到相關文章列表
- 讀過至少 1 篇相關文章（reading_list status = 'read'）即可標記節點完成

## 待升級（語意搜尋版）

**前提條件：**
- `articles.embedding` 欄位已存在（VECTOR(1536)，pgvector）
- `EmbeddingService` 已存在（`backend/app/qa_agent/embedding_service.py`）
- 但 RSS fetch 時目前**沒有**生成 embedding，欄位大多為 NULL

**升級步驟：**
1. RSS fetch 後自動呼叫 EmbeddingService 生成文章 embedding
2. 知識節點建立時也生成 embedding（節點 display_name + description）
3. 將節點 embedding 存入新欄位 `knowledge_nodes.embedding VECTOR(1536)`
4. 用 pgvector cosine similarity 取代關鍵字匹配
5. 節點完成條件可升級為：相關文章（similarity > 0.75）中已讀比例 ≥ 閾值

**參考：**
- pgvector 查詢：`ORDER BY embedding <=> $1 LIMIT 5`
- 現有 embedding index：`idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops)`
