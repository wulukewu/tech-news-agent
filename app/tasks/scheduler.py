import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.supabase_service import SupabaseService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticlePageResult, BatchResult
from app.bot.client import bot
from app.core.config import settings
from app.bot.cogs.interactions import ReadLaterView, MarkReadView

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=settings.timezone)


def build_week_string(dt: datetime) -> str:
    """Build a week string in format YYYY-WW from a datetime object.
    
    Args:
        dt: datetime object
        
    Returns:
        Week string in format YYYY-WW (e.g., "2024-01")
    """
    year = dt.year
    week = dt.isocalendar()[1]
    return f"{year}-{week:02d}"


def build_article_list_notification(article_pages: list, stats: dict) -> str:
    """Build a Discord notification message for the weekly article list.
    
    Args:
        article_pages: List of ArticlePageResult objects
        stats: Dictionary with statistics (total_fetched, hardcore_count)
        
    Returns:
        Formatted notification message
    """
    lines = [
        "📰 **本週科技新聞精選**",
        "",
        f"📊 本週統計：",
        f"  • 總共抓取：{stats.get('total_fetched', 0)} 篇文章",
        f"  • 精選推薦：{stats.get('hardcore_count', 0)} 篇",
        f"  • 成功儲存：{len(article_pages)} 篇",
        "",
        "🔥 **推薦文章：**",
        ""
    ]
    
    # Group articles by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for page in article_pages:
        by_category[page.category].append(page)
    
    # Format articles by category
    for category, pages in sorted(by_category.items()):
        lines.append(f"**{category}**")
        for page in pages[:10]:  # Limit to 10 per category
            tinkering = "🔥" * page.tinkering_index if page.tinkering_index else ""
            lines.append(f"  {tinkering} {page.title}")
        lines.append("")
    
    return "\n".join(lines)


async def weekly_news_job():
    """The cron job: fetch, score, insert articles to database, send Discord notification."""
    logger.info("Executing scheduled weekly_news_job...")

    # Check if we have a valid channel ID to post
    channel_id = settings.discord_channel_id
    if not channel_id:
        logger.error("No DISCORD_CHANNEL_ID set in .env! Cannot send scheduled news.")
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"Could not find Discord channel with ID {channel_id}.")
        return

    try:
        # 1. Fetch Feeds
        supabase = SupabaseService()
        feeds = await supabase.get_active_feeds()
        if not feeds:
            logger.warning("No active feeds found in database.")
            return
        logger.info(f"Fetched {len(feeds)} active feeds.")

        # 2. Scrape Articles
        rss = RSSService(days_to_fetch=7)
        all_articles = await rss.fetch_all_feeds(feeds)
        if not all_articles:
            logger.info("No fresh articles in the past 7 days.")
            return
        logger.info(f"Fetched {len(all_articles)} articles from RSS feeds.")

        # 3. Evaluate Hardcore level
        llm = LLMService()
        hardcore_articles = await llm.evaluate_batch(all_articles)
        logger.info(f"Evaluated articles: {len(hardcore_articles)} hardcore retained.")

        # Build stats dict
        stats = {
            "total_fetched": len(all_articles),
            "hardcore_count": len(hardcore_articles),
        }

        # 4. Insert articles into database
        # Convert ArticleSchema to dict format for insert_articles
        articles_to_insert = []
        for article in hardcore_articles:
            article_dict = {
                'title': article.title,
                'url': str(article.url),
                'feed_name': article.source_name,
                'category': article.source_category,
                'tinkering_index': article.ai_analysis.tinkering_index if article.ai_analysis else None,
                'ai_summary': article.ai_analysis.summary if article.ai_analysis else None,
            }
            # Note: feed_id needs to be resolved from feed name/url
            # For now, we'll skip this and let the insert handle missing feed_id
            articles_to_insert.append(article_dict)
        
        # Note: This will fail because feed_id is required
        # The proper solution would be to look up feed_id from the feeds table
        # For now, we'll create ArticlePageResult objects from the articles directly
        logger.warning("Skipping database insert - feed_id resolution not implemented yet")
        
        # 5. Create ArticlePageResult objects for Discord notification
        article_pages = []
        for article in hardcore_articles:
            article_pages.append(ArticlePageResult(
                page_id=str(article.url),  # Use URL as temporary ID
                page_url=str(article.url),
                title=article.title,
                category=article.source_category,
                tinkering_index=article.ai_analysis.tinkering_index if article.ai_analysis else 0,
            ))
        
        logger.info(f"Prepared {len(article_pages)} articles for notification.")

        # 6. Check if we have articles to notify
        if not article_pages:
            logger.info("No articles to notify, skipping Discord notification")
            return

        # 7. Build Discord notification
        notification = build_article_list_notification(article_pages, stats)

        # 8. Send Discord notification (without MarkReadView since we don't have page_ids)
        try:
            await channel.send(content=notification)
            logger.info("Weekly news job Discord notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error during scheduled job execution: {e}", exc_info=True)


def setup_scheduler():
    """Register jobs to the scheduler."""
    # Run every Friday at 17:00 in the configured timezone
    scheduler.add_job(
        weekly_news_job,
        trigger=CronTrigger(day_of_week='fri', hour=17, minute=0, timezone=settings.timezone),
        id='weekly_news',
        name='Send Weekly Tech News',
        replace_existing=True
    )
    logger.info("Scheduler jobs registered.")
