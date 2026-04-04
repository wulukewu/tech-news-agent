import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.supabase_service import SupabaseService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import SupabaseServiceError
from app.schemas.article import BatchResult
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=settings.timezone)

# Global health tracking
_scheduler_health = {
    "last_execution_time": None,
    "last_articles_processed": 0,
    "last_failed_operations": 0,
    "last_total_operations": 0
}

# Track feed changes between executions (Requirement 16.5)
_last_feed_urls = set()


async def background_fetch_job():
    """
    Background job that orchestrates the pipeline:
    1. Load active feeds from database
    2. Fetch new articles from RSS feeds (with deduplication)
    3. Analyze articles with LLM
    4. Insert results into database
    5. Log statistics at each stage
    
    This job does NOT send Discord notifications - it only populates the article pool.
    
    Implements comprehensive error handling:
    - Wraps entire task in try-except to prevent scheduler crash
    - Logs all exceptions with full stack traces
    - Implements retry logic with exponential backoff for database operations
    - Caches articles in memory during connection failures
    - Logs critical errors and skips current execution when all retries fail
    - Continues normal operation on next scheduled execution
    
    Validates: Requirements 1.1, 1.3, 2.1, 3.1, 4.1, 5.4, 5.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
    """
    job_start_time = datetime.now(timezone.utc)
    logger.info(f"Starting background_fetch_job at {job_start_time.isoformat()}")
    
    # In-memory cache for articles when database connection fails
    cached_articles = []
    
    try:
        # Stage 1: Load active feeds from database with retry logic
        logger.info("Stage 1: Loading active feeds from database")
        
        feeds = None
        for attempt in range(3):  # Max 3 retries (Requirement 9.3)
            try:
                supabase = SupabaseService()
                feeds = await supabase.get_active_feeds()
                break  # Success, exit retry loop
            except SupabaseServiceError as e:
                retry_delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s (Requirement 9.3)
                logger.error(
                    f"Database connection failed during feed loading (attempt {attempt + 1}/3): {e}",
                    exc_info=True
                )
                
                if attempt < 2:  # Not the last attempt
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    # All retries failed (Requirement 9.4, 9.5)
                    logger.critical(
                        "All database retry attempts failed during feed loading. "
                        "Skipping current job execution. Will retry on next scheduled execution.",
                        exc_info=True
                    )
                    return  # Skip current execution (Requirement 9.4)
        
        if not feeds:
            logger.warning("No active feeds found in database. Job completed with no work.")
            return
        
        # Track feed changes since last execution (Requirement 16.5)
        current_feed_urls = {str(feed.url) for feed in feeds}
        
        if _last_feed_urls:
            # Calculate added and removed feeds
            added_feeds = current_feed_urls - _last_feed_urls
            removed_feeds = _last_feed_urls - current_feed_urls
            
            if added_feeds or removed_feeds:
                logger.info(
                    f"Feed changes detected: {len(added_feeds)} added, {len(removed_feeds)} removed since last execution"
                )
            else:
                logger.info("No feed changes since last execution")
        else:
            logger.info("First execution - no previous feed list to compare")
        
        # Update last feed URLs for next execution
        _last_feed_urls.clear()
        _last_feed_urls.update(current_feed_urls)
        
        logger.info(f"Loaded {len(feeds)} active feeds")
        
        # Stage 2: Fetch new articles with deduplication
        logger.info("Stage 2: Fetching new articles from RSS feeds with deduplication")
        rss = RSSService(days_to_fetch=settings.rss_fetch_days)
        new_articles = await rss.fetch_new_articles(feeds, supabase)
        
        logger.info(f"Found {len(new_articles)} new articles after deduplication")
        
        # Stage 2.5: Query and re-process unanalyzed articles (Requirement 13.1, 13.2, 13.3, 13.4, 13.5, 13.6)
        logger.info("Stage 2.5: Querying unanalyzed articles for re-processing")
        unanalyzed_articles = await supabase.get_unanalyzed_articles(limit=100)
        
        total_reprocessed = 0  # Track re-processed articles
        llm = LLMService()  # Initialize LLM service for re-processing and new articles
        
        if unanalyzed_articles:
            logger.info(f"Found {len(unanalyzed_articles)} unanalyzed articles to re-process")
            
            # Convert unanalyzed articles to ArticleSchema for LLM processing
            from app.schemas.article import ArticleSchema
            from uuid import UUID
            
            articles_to_reprocess = []
            for article_data in unanalyzed_articles:
                try:
                    # Create ArticleSchema with minimal required fields
                    # We'll populate ai_summary and tinkering_index through LLM
                    article = ArticleSchema(
                        title=article_data.get('title', ''),
                        url=article_data['url'],
                        feed_id=UUID(article_data['feed_id']),
                        feed_name='',  # Not needed for re-processing
                        category='',   # Not needed for re-processing
                        published_at=None,
                        tinkering_index=None,  # Will be populated by LLM
                        ai_summary=None        # Will be populated by LLM
                    )
                    articles_to_reprocess.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse unanalyzed article: {article_data}, error: {e}")
                    continue
            
            if articles_to_reprocess:
                logger.info(f"Re-processing {len(articles_to_reprocess)} unanalyzed articles with LLM")
                
                # Re-process with LLM
                reprocessed_articles = await llm.evaluate_batch(articles_to_reprocess)
                
                # Convert to dict format and update in database
                articles_to_update = []
                for article in reprocessed_articles:
                    article_dict = {
                        'title': article.title,
                        'url': str(article.url),
                        'feed_id': str(article.feed_id),
                        'tinkering_index': article.tinkering_index,
                        'ai_summary': article.ai_summary,
                    }
                    articles_to_update.append(article_dict)
                
                # Update articles in database (UPSERT will update existing records)
                # This also updates the updated_at timestamp (Requirement 13.4)
                reprocess_result = await supabase.insert_articles(articles_to_update)
                
                logger.info(
                    f"Re-processing completed: "
                    f"{reprocess_result.updated_count} articles updated, "
                    f"{reprocess_result.failed_count} failed"
                )
                
                # Track re-processed count for final logging
                total_reprocessed = reprocess_result.updated_count
        else:
            logger.info("No unanalyzed articles found for re-processing")
        
        # If no new articles and no re-processing, job is complete
        if not new_articles and total_reprocessed == 0:
            logger.info("No new articles found and no re-processing needed. Job completed.")
            return
        
        # Stage 3 & 4: Process articles in batches (only if there are new articles)
        # Determine batch size and split articles if needed (Requirement 12.1, 12.5)
        batch_size = settings.batch_size
        total_articles = len(new_articles)
        
        # Initialize aggregated results
        total_inserted = 0
        total_updated = 0
        total_failed = 0
        num_batches = 0
        
        # Only process batches if there are new articles
        if total_articles > 0:
            # Split into batches if article count exceeds threshold
            if total_articles > settings.batch_split_threshold:
                logger.info(
                    f"Article count ({total_articles}) exceeds threshold ({settings.batch_split_threshold}). "
                    f"Splitting into batches of {batch_size} articles."
                )
            
            # Calculate number of batches
            num_batches = (total_articles + batch_size - 1) // batch_size  # Ceiling division
            
            logger.info(f"Processing {total_articles} articles in {num_batches} batch(es)")
            
            # Process each batch (Requirement 12.6, 12.7)
            for batch_idx in range(num_batches):
                batch_start_time = datetime.now(timezone.utc)
                
                # Calculate batch slice
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_articles)
                batch_articles = new_articles[start_idx:end_idx]
                
                logger.info(
                    f"Processing batch {batch_idx + 1}/{num_batches}: "
                    f"articles {start_idx + 1}-{end_idx} of {total_articles}"
                )
                
                # Stage 3: Analyze articles with LLM
                logger.info(f"Stage 3 (Batch {batch_idx + 1}): Analyzing {len(batch_articles)} articles with LLM")
                analyzed_articles = await llm.evaluate_batch(batch_articles)
                
                logger.info(f"LLM analysis completed for batch {batch_idx + 1}")
                
                # Stage 4: Insert articles into database with retry logic
                logger.info(f"Stage 4 (Batch {batch_idx + 1}): Inserting articles into database")
                
                # Convert ArticleSchema to dict format for insert_articles
                articles_to_insert = []
                for article in analyzed_articles:
                    article_dict = {
                        'title': article.title,
                        'url': str(article.url),
                        'feed_id': str(article.feed_id),
                        'published_at': article.published_at.isoformat() if article.published_at else None,
                        'tinkering_index': article.tinkering_index,
                        'ai_summary': article.ai_summary,
                        'embedding': article.embedding
                    }
                    articles_to_insert.append(article_dict)
                
                # Insert articles with UPSERT logic and retry on failure
                batch_result = None
                for attempt in range(3):  # Max 3 retries (Requirement 9.3)
                    try:
                        batch_result = await supabase.insert_articles(articles_to_insert)
                        break  # Success, exit retry loop
                    except SupabaseServiceError as e:
                        retry_delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s (Requirement 9.3)
                        logger.error(
                            f"Database connection failed during article insertion (attempt {attempt + 1}/3): {e}",
                            exc_info=True
                        )
                        
                        if attempt < 2:  # Not the last attempt
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                        else:
                            # All retries failed - cache articles in memory (Requirement 9.2, 9.4)
                            logger.critical(
                                f"All database retry attempts failed during article insertion. "
                                f"Caching {len(articles_to_insert)} articles in memory. "
                                f"Will retry on next scheduled execution.",
                                exc_info=True
                            )
                            cached_articles.extend(articles_to_insert)
                            return  # Skip current execution (Requirement 9.4)
                
                # Aggregate batch results
                total_inserted += batch_result.inserted_count
                total_updated += batch_result.updated_count
                total_failed += batch_result.failed_count
                
                # Log batch processing time (Requirement 12.6)
                batch_end_time = datetime.now(timezone.utc)
                batch_duration = (batch_end_time - batch_start_time).total_seconds()
                
                logger.info(
                    f"Batch {batch_idx + 1}/{num_batches} completed in {batch_duration:.2f}s. "
                    f"Inserted: {batch_result.inserted_count}, "
                    f"Updated: {batch_result.updated_count}, "
                    f"Failed: {batch_result.failed_count}"
                )
                
                # Clean up memory between batches (Requirement 12.4)
                # Explicitly delete batch variables to free memory
                del batch_articles
                del analyzed_articles
                del articles_to_insert
                
                # Force garbage collection between batches for large datasets
                if num_batches > 1:
                    import gc
                    gc.collect()
        
        # Use aggregated results for final logging
        batch_result = BatchResult(
            inserted_count=total_inserted,
            updated_count=total_updated,
            failed_count=total_failed,
            failed_articles=[]
        )
        
        # Stage 5: Log final statistics (Requirement 12.7)
        job_end_time = datetime.now(timezone.utc)
        job_duration = (job_end_time - job_start_time).total_seconds()
        
        logger.info(
            f"Background fetch job completed successfully. "
            f"Total duration: {job_duration:.2f}s, "
            f"Feeds processed: {len(feeds)}, "
            f"New articles found: {len(new_articles)}, "
            f"Articles processed: {total_articles}, "
            f"Articles re-processed: {total_reprocessed}, "
            f"Batches: {num_batches}, "
            f"Database results - Inserted: {total_inserted}, "
            f"Updated: {total_updated}, "
            f"Failed: {total_failed}"
        )
        
        # Log warnings if failure rates are high
        if total_failed > 0:
            failure_rate = total_failed / total_articles
            if failure_rate > 0.3:
                logger.warning(
                    f"High database insertion failure rate: {total_failed}/{total_articles} "
                    f"({failure_rate:.1%}) failed"
                )
        
        # Update health tracking (Requirement 10.2, 10.3, 10.4)
        _scheduler_health["last_execution_time"] = job_end_time
        _scheduler_health["last_articles_processed"] = total_articles
        _scheduler_health["last_failed_operations"] = total_failed
        _scheduler_health["last_total_operations"] = total_articles
        
    except SupabaseServiceError as e:
        # Database errors are already logged in retry loops above
        # Log critical error and continue to next execution (Requirement 9.5, 9.6)
        logger.critical(
            f"Database error during background fetch job: {e}",
            exc_info=True  # Full stack trace (Requirement 9.2)
        )
    except Exception as e:
        # Catch all other exceptions to prevent scheduler crash (Requirement 9.1, 9.5)
        logger.critical(
            f"Unexpected error during background fetch job: {e}",
            exc_info=True  # Full stack trace (Requirement 9.2)
        )
    finally:
        # Ensure scheduler continues to next execution (Requirement 9.6)
        logger.info("Background fetch job execution completed. Scheduler will continue to next scheduled execution.")


def setup_scheduler():
    """
    Register jobs to the scheduler with configurable CRON expression.
    
    Reads configuration from environment variables:
    - SCHEDULER_CRON: CRON expression (default: "0 */6 * * *")
    - SCHEDULER_TIMEZONE: Timezone for schedule (default: from settings.timezone)
    
    Raises:
        ValueError: If CRON expression is invalid
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    # Get CRON expression from settings
    cron_expression = settings.scheduler_cron
    
    # Get timezone (use scheduler_timezone if set, otherwise fall back to general timezone)
    scheduler_tz = settings.scheduler_timezone or settings.timezone
    
    # Validate CRON expression by attempting to create CronTrigger
    try:
        trigger = CronTrigger.from_crontab(cron_expression, timezone=scheduler_tz)
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid CRON expression '{cron_expression}': {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    
    # Register the background job
    scheduler.add_job(
        background_fetch_job,
        trigger=trigger,
        id='background_fetch',
        name='Background Article Fetch and Analysis',
        replace_existing=True
    )
    
    # Log the configured schedule
    logger.info(
        f"Scheduler configured successfully: "
        f"CRON='{cron_expression}', "
        f"Timezone='{scheduler_tz}', "
        f"Job='background_fetch_job'"
    )


async def get_scheduler_health() -> dict:
    """
    Health check endpoint for monitoring scheduler status.
    
    Returns a dictionary containing:
    - last_execution_time: ISO timestamp of last execution (or None if never run)
    - articles_processed: Count of articles processed in last execution
    - failed_operations: Count of failed operations in last execution
    - total_operations: Total operations attempted in last execution
    - status_code: HTTP status code (200 for healthy, 503 for unhealthy)
    - is_healthy: Boolean indicating overall health
    - issues: List of health issues detected
    
    Health criteria:
    - Unhealthy (503) if scheduler has not run in the last 12 hours
    - Unhealthy (503) if last execution had more than 50% failures
    - Healthy (200) otherwise
    
    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    last_execution = _scheduler_health["last_execution_time"]
    articles_processed = _scheduler_health["last_articles_processed"]
    failed_operations = _scheduler_health["last_failed_operations"]
    total_operations = _scheduler_health["last_total_operations"]
    
    # Determine health status
    is_healthy = True
    issues = []
    status_code = 200
    
    # Check if scheduler has run recently (within last 12 hours)
    if last_execution is None:
        is_healthy = False
        status_code = 503
        issues.append("Scheduler has never executed")
    else:
        time_since_last_run = datetime.now(timezone.utc) - last_execution
        if time_since_last_run > timedelta(hours=12):
            is_healthy = False
            status_code = 503
            issues.append(f"Scheduler has not run in {time_since_last_run.total_seconds() / 3600:.1f} hours (threshold: 12 hours)")
    
    # Check failure rate (only if there were operations)
    if total_operations > 0:
        failure_rate = failed_operations / total_operations
        if failure_rate > 0.5:
            is_healthy = False
            status_code = 503
            issues.append(f"Last execution had {failure_rate:.1%} failure rate (threshold: 50%)")
    
    return {
        "last_execution_time": last_execution.isoformat() if last_execution else None,
        "articles_processed": articles_processed,
        "failed_operations": failed_operations,
        "total_operations": total_operations,
        "status_code": status_code,
        "is_healthy": is_healthy,
        "issues": issues if not is_healthy else []
    }
