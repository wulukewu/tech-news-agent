# 🚨 URGENT: Database Migration Required

## The Problem

Your QA Agent is failing because the `conversations` table is missing:

```
Could not find the table 'public.conversations' in the schema cache
```

## The Solution

Apply migration `007_create_intelligent_qa_schema.sql` immediately.

## Quick Fix Steps

### 1. Open Supabase Dashboard

- Go to https://supabase.com/dashboard
- Select your project: `ieqskggdhlvepuslouxy`

### 2. Open SQL Editor

- Click "SQL Editor" in left sidebar
- Click "New query"

### 3. Copy & Paste Migration

- Open file: `backend/scripts/migrations/007_create_intelligent_qa_schema.sql`
- Copy ALL contents (it's a long file)
- Paste into SQL Editor

### 4. Run Migration

- Click "Run" button
- Wait for "Success" message

### 5. Restart Backend

```bash
docker-compose restart tech-news-agent-backend-dev
```

## What This Creates

- ✅ `conversations` table (fixes the error)
- ✅ `article_embeddings` table (for semantic search)
- ✅ `user_profiles` table (for personalization)
- ✅ `query_logs` table (for analytics)
- ✅ pgvector extension (for AI search)

## Verification

After migration, test the QA feature:

1. Go to http://localhost:3000/chat
2. Ask a question
3. Should work without errors

---

**This is blocking your AI agent functionality - please apply immediately!**
