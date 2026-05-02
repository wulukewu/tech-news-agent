# DM Conversation Memory System - Quick Deployment Guide

## 🚀 5-Minute Deployment

### Step 1: Apply Database Migration

**Option A: Supabase Dashboard (Recommended)**

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor"
4. Copy and paste the content of `backend/scripts/migrations/017_dm_conversation_memory.sql`
5. Click "Run"
6. Verify success (should see "Success. No rows returned")

**Option B: Command Line**

```bash
cd backend/scripts/migrations
psql $DATABASE_URL -f 017_dm_conversation_memory.sql
```

### Step 2: Verify Migration

Run this SQL to check:

```sql
-- Check dm_conversations table
SELECT COUNT(*) FROM dm_conversations;

-- Check preference_summary column
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'preference_model'
  AND column_name IN ('preference_summary', 'summary_updated_at');
```

Expected output:
- `dm_conversations` count: 0 (empty table)
- 2 rows returned (both columns exist)

### Step 3: Restart Services

**Docker Compose:**
```bash
docker-compose restart backend
docker-compose restart frontend
```

**PM2:**
```bash
pm2 restart backend
pm2 restart frontend
```

**Manual:**
```bash
# Backend
cd backend
python -m app.main

# Frontend (in another terminal)
cd frontend
npm run build && npm start
```

### Step 4: Verify Bot is Running

Check logs for:
```
INFO: Loading Discord Cogs...
INFO: DM conversation listener enabled
```

If you see "DM conversation listener disabled", check your `.env`:
```bash
# Should be true or not set (defaults to true)
ENABLE_DM_LISTENER=true
```

### Step 5: Test End-to-End

#### Test 1: Send a DM

1. Open Discord
2. Send a DM to your bot: `我喜歡 Rust 和系統程式設計`
3. Bot should reply: `✅ 已記錄你的偏好！偏好摘要將自動更新 🎯`

#### Test 2: Update Profile

1. In Discord, run: `/update_profile`
2. Bot should show your preference summary
3. If "沒有足夠的 DM 對話", send 2-3 more DMs first

#### Test 3: View Profile

1. In Discord, run: `/my_profile`
2. Should see:
   - 💬 偏好摘要 (your summary)
   - 📊 分類權重 (category weights)

#### Test 4: Web UI

1. Go to `http://localhost:3000/preferences` (or your domain)
2. Should see:
   - Preference summary (if generated)
   - Category weights visualization
   - Learning settings toggle

#### Test 5: Check Recommendations

1. Wait for next proactive DM (or trigger manually with `/trigger_fetch`)
2. Recommendations should mention your preferences
3. Example: "根據你的偏好描述，這篇 Rust 文章符合你的興趣方向"

---

## ✅ Success Checklist

- [ ] Migration 017 applied successfully
- [ ] Backend restarted without errors
- [ ] Bot loads DM conversation listener cog
- [ ] DM messages are stored in database
- [ ] `/update_profile` generates summary
- [ ] `/my_profile` displays summary
- [ ] Web UI shows preferences page
- [ ] Recommendations use preference summary

---

## 🐛 Troubleshooting

### Issue: Bot doesn't respond to DMs

**Check:**
1. `ENABLE_DM_LISTENER=true` in `.env`
2. Bot has `message_content` intent enabled in Discord Developer Portal
3. Bot logs show "DM conversation listener enabled"

**Fix:**
```bash
# Check .env
grep ENABLE_DM_LISTENER .env

# Restart bot
docker-compose restart backend
```

### Issue: Migration fails

**Error**: `relation "dm_conversations" already exists`

**Solution**: Migration already applied, skip to Step 3

**Error**: `column "preference_summary" already exists`

**Solution**: Migration already applied, skip to Step 3

**Error**: `permission denied`

**Solution**: Use service_role key, not anon key

### Issue: `/update_profile` says "沒有足夠的 DM 對話"

**Cause**: No DM conversations in database

**Fix**: Send 2-3 DMs to the bot first, then try again

### Issue: Preference summary is empty

**Check:**
```sql
SELECT * FROM dm_conversations WHERE user_id = 'YOUR_USER_ID';
```

If empty, DMs aren't being stored. Check bot logs for errors.

### Issue: Scheduler not running

**Check:**
```bash
# Backend logs should show:
# "Starting preference summary job..."
# "Preference summary job complete: X summaries updated"
```

**Fix:**
```bash
# Check scheduler is enabled
grep ENABLE_SCHEDULER .env

# Should be true or not set
ENABLE_SCHEDULER=true
```

### Issue: LLM API errors

**Error**: `429 Too Many Requests`

**Cause**: Groq API rate limit exceeded

**Fix**: Adjust rate limits in `.env`:
```bash
LLM_CONCURRENT_LIMIT=1
LLM_REQUEST_DELAY=5
```

**Error**: `401 Unauthorized`

**Cause**: Invalid Groq API key

**Fix**: Check `GROQ_API_KEY` in `.env`

---

## 📊 Monitoring

### Check System Health

```sql
-- Total DM conversations
SELECT COUNT(*) FROM dm_conversations;

-- Users with preference summaries
SELECT COUNT(*) FROM preference_model WHERE preference_summary IS NOT NULL;

-- Recent conversations (last 7 days)
SELECT COUNT(*) FROM dm_conversations WHERE created_at > NOW() - INTERVAL '7 days';

-- Summary freshness
SELECT
  user_id,
  LENGTH(preference_summary) as summary_length,
  summary_updated_at,
  NOW() - summary_updated_at as age
FROM preference_model
WHERE preference_summary IS NOT NULL
ORDER BY summary_updated_at DESC
LIMIT 10;
```

### Check Scheduler Logs

```bash
# Docker
docker-compose logs -f backend | grep "preference_summary_job"

# PM2
pm2 logs backend | grep "preference_summary_job"
```

Expected output (daily at 11:00):
```
INFO: Starting preference summary job...
INFO: Updated preference summary for user abc123...
INFO: Preference summary job complete: 5 summaries updated
```

---

## 🎯 Next Steps

After successful deployment:

1. **Monitor for 24 hours**
   - Check DM conversations are being stored
   - Verify scheduler runs at 11:00
   - Watch for LLM API errors

2. **Gather User Feedback**
   - Are summaries accurate?
   - Do recommendations improve?
   - Any confusion about how to use?

3. **Optimize**
   - Adjust LLM prompt if needed
   - Tune auto-update thresholds
   - Add more languages if needed

4. **Scale**
   - Monitor LLM API usage
   - Consider caching strategies
   - Add rate limiting if needed

---

## 📚 Additional Resources

- **Full Status Report**: `docs/implementation/dm-conversation-memory-status.md`
- **Requirements**: `.kiro/specs/dm-conversation-memory/requirements.md`
- **API Docs**: `http://localhost:8000/docs` (when backend is running)
- **Frontend**: `http://localhost:3000/preferences`

---

**Deployment Time**: ~5 minutes
**Difficulty**: Easy
**Risk**: Low (all changes are additive)

---

*Last updated: 2026-05-02*
