# 🚨 Critical Database Migration Required

## Issue

The conversations table is missing from your database, causing the QA functionality to fail with this error:

```
Could not find the table 'public.conversations' in the schema cache
```

## Solution

You need to apply migration `007_create_intelligent_qa_schema.sql` manually.

## Steps to Apply Migration

### Option 1: Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Copy and Paste Migration**
   - Open the file: `backend/scripts/migrations/007_create_intelligent_qa_schema.sql`
   - Copy the entire contents
   - Paste into the SQL Editor

4. **Run the Migration**
   - Click "Run" button
   - Wait for completion (should show "Success")

### Option 2: Command Line (If you have DATABASE_URL)

If you have the full PostgreSQL connection string:

```bash
# Add this to your .env file:
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Then run:
python3 backend/scripts/migrations/apply_migration_sql.py backend/scripts/migrations/007_create_intelligent_qa_schema.sql
```

## What This Migration Creates

The migration will create these tables:

- ✅ `conversations` - For multi-turn chat context
- ✅ `article_embeddings` - For semantic search
- ✅ `user_profiles` - For user preferences
- ✅ `query_logs` - For analytics

## Verification

After applying the migration, restart your backend service:

```bash
# In your docker-compose or development environment
docker-compose restart tech-news-agent-backend-dev
```

The error should disappear and QA functionality should work.

## Need Help?

If you encounter issues:

1. Check the Supabase Dashboard logs
2. Ensure you're using the service_role key (not anon key)
3. Verify your Supabase project has the required permissions

---

**⚠️ This migration is required for the AI agent enhancements to work properly!**
