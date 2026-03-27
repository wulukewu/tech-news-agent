import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.notion_service import NotionService, build_digest_title
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import NotionServiceError
from app.schemas.article import WeeklyDigestResult
from app.bot.client import bot
from app.core.config import settings
from app.bot.cogs.interactions import ReadLaterView

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=settings.timezone)

DISCORD_LIMIT = 2000


def build_discord_notification(
    digest_result: WeeklyDigestResult | None,
    top_articles: list,
    stats: dict,
) -> str:
    """Build a Discord notification message (≤ 2000 chars).

    If digest_result is not None: normal notification with stats + Top 5 + Notion URL.
    If digest_result is None: degraded notification with stats + Top 5 + warning.
    """
    total = stats.get("total_fetched", 0)
    hardcore = stats.get("hardcore_count", 0)

    header = "本週技術週報已發布\n\n" if digest_result else "本週技術週報\n\n"
    stats_line = f"本週統計：抓取 {total} 篇，精選 {hardcore} 篇\n\n"

    # Build article lines (up to 5)
    articles_to_show = top_articles[:5]
    article_lines = []
    for i, article in enumerate(articles_to_show, 1):
        title = article.title
        url = str(article.url)
        article_lines.append(f"{i}. [{title}]({url})")

    top_section = "Top {} 精選：\n{}\n\n".format(
        len(articles_to_show),
        "\n".join(article_lines),
    )

    if digest_result:
        footer = f"完整週報：{digest_result.page_url}"
    else:
        footer = "（Notion 頁面建立失敗，請查看日誌）"

    message = header + stats_line + top_section + footer

    # Enforce 2000-char limit by truncating article list if needed
    if len(message) <= DISCORD_LIMIT:
        return message

    # Progressively reduce articles shown until it fits
    for n in range(len(articles_to_show) - 1, -1, -1):
        article_lines_trimmed = article_lines[:n]
        top_section_trimmed = "Top {} 精選：\n{}\n\n".format(
            n,
            "\n".join(article_lines_trimmed),
        )
        candidate = header + stats_line + top_section_trimmed + footer
        if len(candidate) <= DISCORD_LIMIT:
            return candidate

    # Last resort: just header + stats + footer, truncated
    base = header + stats_line + footer
    if len(base) > DISCORD_LIMIT:
        base = base[: DISCORD_LIMIT - 3] + "..."
    return base


async def weekly_news_job():
    """The cron job: fetch, score, build Notion digest, send Discord notification."""
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

        # Compute top articles (top 7 by tinkering_index descending)
        top_articles = sorted(
            hardcore_articles,
            key=lambda a: a.ai_analysis.tinkering_index if a.ai_analysis else 0,
            reverse=True,
        )[:7]

        # Build stats dict
        tz_taipei = timezone(timedelta(hours=8))
        dt = datetime.now(tz=tz_taipei)
        date_str = dt.strftime("%Y-%m-%d")
        stats = {
            "total_fetched": len(all_articles),
            "hardcore_count": len(hardcore_articles),
            "run_date": date_str,
        }

        # 4. Generate digest intro via LLM
        intro_text = await llm.generate_digest_intro(hardcore_articles)
        logger.info("Generated digest intro text.")

        # 5. Create Notion weekly digest page (graceful degradation)
        digest_result: WeeklyDigestResult | None = None
        title = build_digest_title(dt)
        published_date = dt.date()

        if not settings.notion_weekly_digests_db_id:
            logger.error("notion_weekly_digests_db_id is not configured; skipping Notion page creation.")
        else:
            try:
                page_id, page_url = await notion.create_weekly_digest_page(
                    title=title,
                    published_date=published_date,
                    article_count=len(hardcore_articles),
                )
                digest_result = WeeklyDigestResult(
                    page_id=page_id,
                    page_url=page_url,
                    article_count=len(hardcore_articles),
                    top_articles=top_articles,
                )
                logger.info(f"Created Notion weekly digest page: {page_url}")

                # 6. Build and append blocks to the Notion page
                blocks = notion.build_digest_blocks(top_articles, intro_text, stats)
                await notion.append_digest_blocks(page_id, blocks)
                logger.info("Appended digest blocks to Notion page.")

            except NotionServiceError as e:
                logger.error(f"Notion page creation failed, continuing with degraded notification: {e}")
                digest_result = None

        # 7. Send Discord notification
        notification = build_discord_notification(digest_result, top_articles, stats)
        view = ReadLaterView(articles=top_articles)
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
