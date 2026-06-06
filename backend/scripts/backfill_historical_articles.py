#!/usr/bin/env python3
"""
Backfill historical articles missing actionable_takeaway and content_type using LLaMA evaluation.
Handles API limit errors smoothly by sleeping and retrying.
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.article import ArticleSchema
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from app.services.web_scraper import scrape_article

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_historical")


async def main():
    supabase = SupabaseService()
    llm = LLMService()

    # Query all articles without actionable_takeaway
    logger.info("Fetching articles missing actionable_takeaway from database...")
    resp = (
        supabase.client.table("articles")
        .select("id, title, url, published_at, category, ai_summary, feed_id, tinkering_index")
        .is_("actionable_takeaway", "null")
        .order("published_at", desc=True)
        .execute()
    )
    articles = resp.data or []
    total_articles = len(articles)
    logger.info(f"Found {total_articles} articles that need backfilling.")

    if not articles:
        logger.info("All articles are already backfilled!")
        return

    success_count = 0
    fail_count = 0

    for idx, a in enumerate(articles):
        title = a.get("title", "No Title")
        url = a.get("url")
        ai_summary = a.get("ai_summary") or ""
        logger.info(f"\n[{idx + 1}/{total_articles}] Processing: {title}")
        logger.info(f"URL: {url}")

        # Decide if we need to scrape
        content_preview = ai_summary.strip()
        # If the summary is short or missing, try scraping
        if len(content_preview) < 500:
            logger.info(
                f"Current summary length ({len(content_preview)}) is short. Attempting to scrape webpage..."
            )
            try:
                scraped = await scrape_article(url)
                if scraped and len(scraped) > len(content_preview):
                    content_preview = scraped
                    logger.info(
                        f"Scraped full webpage content successfully: {len(content_preview)} chars."
                    )
                else:
                    logger.info(
                        "Scraped text was empty or shorter than existing summary. Falling back to original summary."
                    )
            except Exception as e:
                logger.warning(f"Scrape request failed: {e}. Falling back to original summary.")
        else:
            logger.info(f"Using existing rich summary of {len(content_preview)} characters.")

        # Build schema object for LLM
        article_obj = ArticleSchema(
            id=a["id"],
            title=title,
            url=url,
            feed_id=a["feed_id"],
            feed_name="",
            category=a.get("category") or "",
            content_preview=content_preview,
        )

        # Call LLM with tenacity retry wrapper built-in, but handle overall exceptions just in case
        analysis = None
        for attempt in range(3):
            try:
                analysis = await llm.evaluate_article(article_obj)
                break
            except Exception as e:
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/3): {e}. Sleeping 10s before retry..."
                )
                await asyncio.sleep(10)

        if analysis:
            try:
                # Update database
                update_data = {
                    "actionable_takeaway": analysis.actionable_takeaway,
                    "content_type": analysis.content_type,
                }
                # If tinkering_index is missing or 0, update it to be aligned with the LLM analysis
                if not a.get("tinkering_index") or a.get("tinkering_index") == 0:
                    update_data["tinkering_index"] = analysis.tinkering_index

                supabase.client.table("articles").update(update_data).eq("id", a["id"]).execute()
                logger.info(
                    f"Successfully updated! Tinkering Index: {analysis.tinkering_index}, Content Type: {analysis.content_type}"
                )
                logger.info(f"Takeaway: {analysis.actionable_takeaway}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to update database for article {a['id']}: {e}")
                fail_count += 1
        else:
            logger.error(f"Failed to generate evaluation for: {title}")
            fail_count += 1

        # Polite delay to stay within Groq API rate limits (RPM / TPM)
        # 3 seconds is safe for Groq Free tier LLaMA model
        await asyncio.sleep(3.0)

    logger.info("\n==========================================")
    logger.info("Backfill Job Completed.")
    logger.info(f"Total processed: {total_articles}")
    logger.info(f"Successfully updated: {success_count}")
    logger.info(f"Failed: {fail_count}")


if __name__ == "__main__":
    asyncio.run(main())
