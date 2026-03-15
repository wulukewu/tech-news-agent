import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.notion_service import NotionService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.bot.client import bot
from app.core.config import settings
from app.bot.cogs.interactions import ReadLaterView

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=settings.timezone)

async def weekly_news_job():
    """The cron job that mimics n8n's workflow: fetch, score, generate, post to Discord."""
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

        # 2. Scrape Articles
        rss = RSSService(days_to_fetch=7)
        all_articles = await rss.fetch_all_feeds(feeds)
        if not all_articles:
            logger.info("No fresh articles in the past 7 days.")
            return

        # 3. Evaluate Hardcore level
        llm = LLMService()
        hardcore_articles = await llm.evaluate_batch(all_articles)

        # 4. Generate Markdown
        draft = await llm.generate_weekly_newsletter(hardcore_articles)

        # 5. Send results back to Discord Channel
        view = ReadLaterView(articles=hardcore_articles[:7])
        
        await channel.send(content=draft, view=view)
        logger.info("Weekly news job broadcasted successfully.")

    except Exception as e:
        logger.error(f"Error during scheduled job execution: {e}", exc_info=True)

def setup_scheduler():
    """Register jobs to the scheduler."""
    # Run every Friday at 17:00
    scheduler.add_job(
        weekly_news_job,
        trigger=CronTrigger(day_of_week='fri', hour=17, minute=0, timezone="Asia/Taipei"),
        id='weekly_news',
        name='Send Weekly Tech News',
        replace_existing=True
    )
    logger.info("Scheduler jobs registered.")
