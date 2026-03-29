import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.notion_service import NotionService, build_week_string
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import NotionServiceError
from app.schemas.article import ArticlePageResult
from app.bot.client import bot
from app.core.config import settings
from app.bot.cogs.interactions import ReadLaterView, MarkReadView

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=settings.timezone)


async def weekly_news_job():
    """The cron job: fetch, score, create article pages, send Discord notification."""
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
        notion = NotionService()
        feeds = await notion.get_active_feeds()
        if not feeds:
            logger.warning("No active feeds found in Notion.")
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

        # 4. Calculate current week
        tz_taipei = timezone(timedelta(hours=8))
        dt = datetime.now(tz=tz_taipei)
        published_week = build_week_string(dt)
        logger.info(f"Current week: {published_week}")

        # 5. Batch create article Pages (limit concurrency to 5)
        article_pages = []
        semaphore = asyncio.Semaphore(5)

        async def create_with_semaphore(article):
            async with semaphore:
                try:
                    page_id, page_url = await notion.create_article_page(article, published_week)
                    return ArticlePageResult(
                        page_id=page_id,
                        page_url=page_url,
                        title=article.title,
                        category=article.source_category,
                        tinkering_index=article.ai_analysis.tinkering_index if article.ai_analysis else 0,
                    )
                except NotionServiceError as e:
                    logger.error(f"Failed to create page for '{article.title}': {e}")
                    return None

        results = await asyncio.gather(*(create_with_semaphore(a) for a in hardcore_articles))
        article_pages = [r for r in results if r is not None]
        logger.info(f"Created {len(article_pages)} article pages out of {len(hardcore_articles)} articles.")

        # 6. Check if all articles failed
        if hardcore_articles and not article_pages:
            logger.error("All article pages failed to create, skipping Discord notification")
            return

        # 7. Build Discord notification
        notification = notion.build_article_list_notification(article_pages, stats)

        # 8. Send Discord notification with MarkReadView (limit 25 buttons)
        view = MarkReadView(article_pages[:25])
        try:
            await channel.send(content=notification, view=view)
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
