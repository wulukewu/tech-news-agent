# Article Fetching Troubleshooting Guide

## Overview

This guide helps diagnose and fix issues with the RSS article fetching and processing pipeline.

## Common Issues

### 1. Articles Failing to Insert

**Symptoms:**

```
Failed to insert/update article: https://example.com/article
```

**Common Causes:**

#### A. Missing tinkering_index (LLM Analysis Failed)

- **Cause**: LLM API call failed or timed out
- **Solution**: Check Groq API key and rate limits
- **Prevention**: Articles without tinkering_index are now automatically skipped

#### B. Invalid URL Format

- **Cause**: RSS feed contains malformed URLs
- **Solution**: Check RSS feed quality, consider adding URL validation
- **Prevention**: Validate URLs before processing

#### C. Database Constraints

- **Cause**: Violating unique constraints or data type mismatches
- **Solution**: Check database schema and article data format
- **Prevention**: Validate data before insertion

### 2. RSS Feed Failures

**Symptoms:**

```
Failed to process feed 'Feed Name' at https://example.com/rss.xml: Client error '404 Not Found'
```

**Solutions:**

1. **Update Feed URL**: Check if the feed has moved to a new URL
2. **Deactivate Feed**: If permanently unavailable, deactivate it:
   ```python
   python3 scripts/update_invalid_feeds.py
   ```
3. **Check Feed Format**: Some feeds may use non-standard formats

### 3. LLM Analysis Failures

**Symptoms:**

```
Failed to evaluate tinkering_index for article 'Title'
Failed to generate summary for article 'Title'
```

**Common Causes:**

#### A. Rate Limiting

- **Groq Free Tier**: 30 requests per minute
- **Solution**: Increase delay between requests in `llm_service.py`
- **Current Setting**: 4 seconds delay with 2 concurrent requests

#### B. API Timeout

- **Default**: 30 seconds
- **Solution**: Increase timeout for slow responses
- **Location**: `llm_service.py` - `API_TIMEOUT` constant

#### C. Invalid API Key

- **Solution**: Check `GROQ_API_KEY` in `.env` file
- **Verification**: Test with a simple API call

### 4. Reddit Articles Failing

**Special Considerations for Reddit RSS Feeds:**

Reddit RSS feeds have unique characteristics:

- URLs are very long (include full comment thread)
- Titles may contain special characters
- Content structure differs from standard blogs

**Solutions:**

1. Ensure URL length limits are sufficient (currently 2000 chars)
2. Handle special characters in titles properly
3. Consider Reddit-specific parsing if needed

## Debugging Tools

### 1. Manual Scheduler Test

Run the scheduler manually to see detailed logs:

```bash
cd backend
python3 scripts/test_scheduler.py
```

This will show:

- All RSS feeds being processed
- Articles being fetched
- LLM analysis results
- Database insertion results
- Detailed error messages

### 2. Check Database Directly

Query articles without tinkering_index:

```sql
SELECT id, title, url, tinkering_index, ai_summary
FROM articles
WHERE tinkering_index IS NULL
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Monitor Logs

Watch backend logs in real-time:

```bash
docker-compose logs -f backend
```

Filter for errors only:

```bash
docker-compose logs backend | grep -i error
```

## Monitoring Metrics

### Key Metrics to Track

1. **Fetch Success Rate**
   - Total feeds processed
   - Successful vs failed feeds
   - Articles fetched per feed

2. **LLM Analysis Success Rate**
   - Articles analyzed
   - Successful analyses
   - Failed analyses (by reason)

3. **Database Insertion Success Rate**
   - Articles attempted
   - Successfully inserted
   - Successfully updated
   - Failed insertions (by reason)

### Example Log Analysis

```bash
# Count successful article insertions
docker-compose logs backend | grep "Inserted article via UPSERT" | wc -l

# Count failed insertions
docker-compose logs backend | grep "Failed to insert/update article" | wc -l

# Count LLM failures
docker-compose logs backend | grep "Failed to evaluate tinkering_index" | wc -l
```

## Configuration Tuning

### Adjust Batch Size

In `backend/app/core/config.py`:

```python
batch_size: int = 50  # Reduce if experiencing timeouts
batch_split_threshold: int = 100  # Adjust based on memory
```

### Adjust LLM Concurrency

In `backend/app/services/llm_service.py`:

```python
semaphore = asyncio.Semaphore(2)  # Reduce to 1 if hitting rate limits
await asyncio.sleep(4)  # Increase delay if needed
```

### Adjust RSS Fetch Timeout

In `backend/app/services/rss_service.py`:

```python
response = await client.get(url, headers=BASE_HEADERS, timeout=15.0)
# Increase timeout for slow feeds
```

## Best Practices

1. **Regular Feed Audits**
   - Check for 404 errors weekly
   - Update or remove dead feeds
   - Add new quality feeds

2. **Monitor API Usage**
   - Track Groq API usage
   - Stay within rate limits
   - Consider upgrading if needed

3. **Database Maintenance**
   - Regularly check for orphaned articles
   - Monitor database size
   - Archive old articles if needed

4. **Error Handling**
   - Don't let one failed article stop the batch
   - Log detailed error information
   - Retry transient failures

## Emergency Procedures

### If Scheduler is Completely Broken

1. **Stop the scheduler**:

   ```bash
   docker-compose stop backend
   ```

2. **Check logs for root cause**:

   ```bash
   docker-compose logs backend | tail -100
   ```

3. **Fix the issue** (database, API keys, etc.)

4. **Test manually**:

   ```bash
   python3 scripts/test_scheduler.py
   ```

5. **Restart when confirmed working**:
   ```bash
   docker-compose start backend
   ```

### If Database is Corrupted

1. **Backup current data**
2. **Check for constraint violations**
3. **Clean up invalid data**
4. **Re-run migrations if needed**

## Contact & Support

For persistent issues:

1. Check GitHub issues
2. Review Supabase logs
3. Verify Groq API status
4. Check network connectivity
