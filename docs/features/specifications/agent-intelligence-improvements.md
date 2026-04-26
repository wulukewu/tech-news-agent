# Agent Intelligence Improvements

## Overview

This document specifies four improvements to make the personalization agent smarter and more effective. Each improvement is independent and can be implemented separately.

---

## Improvement 1: Add `category` to Articles

### Problem

The `articles` table has no `category` column. The entire `category_weights` preference system is therefore useless — weights are stored but never populated because there is no category data to learn from.

### Solution

1. Add `category` column to `articles` table in Supabase.
2. Populate it during RSS fetch: extract category from the feed's `<category>` tag, or fall back to the feed's own `category` field in the `feeds` table.
3. Backfill existing articles using the feed's category.

### Schema Change

```sql
ALTER TABLE articles ADD COLUMN category TEXT;
UPDATE articles SET category = feeds.category
FROM feeds WHERE articles.feed_id = feeds.id;
```

### Code Changes

- `backend/app/services/rss_service.py`: extract `<category>` from feed entries, fall back to `feeds.category`
- `backend/app/tasks/scheduler.py`: pass category when inserting articles
- `backend/app/api/qa.py`: include `category` in `_search_articles_by_query` select

### Acceptance Criteria

- New articles have a non-null `category` after fetch
- `/my_profile` shows populated category weights after user rates articles
- Proactive DM recommendations show correct category in embed footer

---

## Improvement 2: Auto-update `preference_summary` After DM Preference Statements

### Problem

When a user says "I like Rust and system design" in DM, the message is stored in `dm_conversations` but `preference_summary` is only updated when the user manually runs `/update_profile`. Most users will never do this.

### Solution

After storing a preference statement in `dm_conversations`, automatically call `update_preference_summary` in the background — but only if:
- At least 3 new preference messages have accumulated since the last summary update, **OR**
- It has been more than 24 hours since the last update

This avoids calling the LLM on every single message.

### Code Changes

- `backend/app/bot/cogs/dm_conversation_listener.py`: after `_store_dm()` for preference intent, check the condition and call `update_preference_summary` as a background task
- `backend/app/api/qa.py`: same logic in `_process_query_with_intent` for preference intent on web

### Trigger Condition (pseudo-code)

```python
async def _maybe_update_summary(user_id, supabase):
    # Count unsummarized messages since last update
    last_update = get_summary_updated_at(user_id)
    new_count = count_dm_conversations_since(user_id, last_update)
    hours_since = hours_since_last_update(user_id)

    if new_count >= 3 or hours_since >= 24:
        asyncio.create_task(update_preference_summary(user_id, supabase))
```

### Acceptance Criteria

- After 3 preference statements in DM, `preference_summary` updates automatically within the same session
- No LLM call on every single message
- `/my_profile` reflects updated summary without manual `/update_profile`

---

## Improvement 3: Close the Proactive Learning Loop

### Problem

`proactive_learning_job` generates questions and stores them in `learning_conversations`. When a user answers, the response is saved with `status="answered"`. But nothing reads those answers and updates the preference model. The loop is broken.

### Solution

After a user answers a learning conversation, run a `FeedbackProcessor` that:
1. Parses the answer text to extract category signals
2. Adjusts `category_weights` accordingly
3. Optionally triggers a `preference_summary` update

### Code Changes

- `backend/app/api/proactive_learning.py` — `respond_to_conversation` endpoint: after marking answered, call `FeedbackProcessor.process_response(user_id, question, answer)`
- `backend/app/qa_agent/proactive_learning/feedback_processor.py`: implement `process_response` — use simple keyword matching to map answer to category adjustments (no LLM needed)

### Feedback Processing Logic

```python
async def process_response(user_id: str, question: str, answer: str):
    # Extract category signals from answer
    # e.g. answer="I prefer Rust over Python" → boost "Rust", slight reduce "Python"
    adjustments = extract_category_signals(answer)
    if adjustments:
        await PreferenceModel().apply_adjustments(user_id, adjustments)
```

### Acceptance Criteria

- After answering a proactive question, `category_weights` changes are visible in `/my_profile`
- No LLM call required for basic keyword-based signal extraction
- Works for both option-based and free-text answers

---

## Improvement 4: Semantic Search with pgvector

### Problem

Current search uses `ilike` keyword matching. Searching "Rust articles" only finds articles with the literal word "Rust" in title or summary. It misses semantically related articles about "memory safety", "systems programming", "ownership model", etc.

The `articles` table already has an `embedding vector` column — it just isn't populated or used.

### Solution

Use `sentence-transformers` (free, runs locally/on server, no API key needed) to generate embeddings and store them in `articles.embedding`. Then use pgvector's `<=>` cosine similarity operator for search.

### Technical Approach

**Embedding model**: `all-MiniLM-L6-v2` from `sentence-transformers`
- Free, open source, no API key
- 384-dimension vectors
- Fast enough to run on CPU during RSS fetch

**Embedding generation**: during `background_fetch_job`, after LLM analysis, generate embedding from `title + ai_summary` and store in `articles.embedding`

**Search**: replace `ilike` in `_search_articles_by_query` with pgvector similarity search

```sql
SELECT id, title, url, ai_summary, published_at,
       1 - (embedding <=> query_embedding) AS similarity
FROM articles
WHERE embedding IS NOT NULL
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

### Code Changes

- `backend/requirements.txt`: add `sentence-transformers`
- `backend/app/services/embedding_service.py`: new service wrapping `sentence-transformers`
- `backend/app/tasks/scheduler.py`: generate and store embedding after article analysis
- `backend/app/api/qa.py` — `_search_articles_by_query`: if query embedding available, use vector search; fall back to `ilike` if embedding column is empty

### Graceful Fallback

If `sentence-transformers` is not installed or embedding fails, fall back to existing `ilike` search. This ensures zero regression.

### Acceptance Criteria

- Searching "memory safety" returns Rust-related articles even without the word "Rust"
- Searching "大型語言模型" returns articles about LLMs even if they use English terms
- Existing `ilike` fallback still works when embeddings are not available
- No Groq API calls required for embeddings

---

## Implementation Order

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| 1 | Add `category` to articles | Low | High — unblocks the entire weights system |
| 2 | Auto-update preference summary | Low | High — removes friction from learning loop |
| 3 | Close proactive learning loop | Medium | Medium — makes the question system actually useful |
| 4 | Semantic search (pgvector) | Medium | High — dramatically improves search quality |

Start with 1 and 2 as they are low effort and unblock everything else.
