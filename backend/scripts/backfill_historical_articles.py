#!/usr/bin/env python3
"""
Backfill historical articles missing actionable_takeaway and content_type using LLaMA evaluation.
Handles API limit errors smoothly by sleeping and retrying.
"""
import asyncio
import logging
import os
import re
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

    while True:
        # Query articles without actionable_takeaway
        logger.info("Fetching articles missing actionable_takeaway from database...")
        resp = (
            supabase.client.table("articles")
            .select("id, title, url, published_at, category, ai_summary, feed_id, tinkering_index")
            .is_("actionable_takeaway", "null")
            .order("published_at", desc=True)
            .limit(50)  # Grab in batches of 50
            .execute()
        )
        articles = resp.data or []

        if not articles:
            logger.info("All articles are fully backfilled! Job complete.")
            break

        logger.info(f"Found {len(articles)} articles needing backfilling in this batch.")

        for idx, a in enumerate(articles):
            title = a.get("title", "No Title")
            url = a.get("url")
            ai_summary = a.get("ai_summary") or ""
            logger.info(f"\nProcessing: {title}")
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

            # Call LLM. Handle rate limit errors by waiting and repeating the SAME article
            success = False
            while not success:
                try:
                    analysis = await llm.evaluate_article(article_obj)
                    if analysis:
                        # Update database
                        update_data = {
                            "actionable_takeaway": analysis.actionable_takeaway,
                            "content_type": analysis.content_type,
                        }
                        # If tinkering_index is missing or 0, update it to be aligned with the LLM analysis
                        if not a.get("tinkering_index") or a.get("tinkering_index") == 0:
                            update_data["tinkering_index"] = analysis.tinkering_index

                        supabase.client.table("articles").update(update_data).eq(
                            "id", a["id"]
                        ).execute()
                        logger.info(
                            f"Successfully updated! Tinkering Index: {analysis.tinkering_index}, Content Type: {analysis.content_type}"
                        )
                        logger.info(f"Takeaway: {analysis.actionable_takeaway}")
                        success = True
                    else:
                        logger.info(
                            "Evaluation returned None. Verifying if it is a rate limit or a structural issue..."
                        )
                        # Run a tiny dummy request to see if Groq is alive or rate-limiting us
                        try:
                            await llm.client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=[{"role": "user", "content": "ping"}],
                                max_tokens=1,
                            )
                            # If this succeeds, the API is healthy, so the None was a structural error.
                            logger.error(
                                f"Failed to generate evaluation for: {title} (returned None). Skipping to next article."
                            )
                            success = True  # Move on
                        except Exception as dummy_e:
                            # If the dummy call fails, raise it to be handled by the rate limit handler
                            logger.warning(f"Dummy validation request failed: {dummy_e}")
                            raise dummy_e
                except Exception as e:
                    err_msg = str(e).lower()
                    if "429" in err_msg or "rate limit" in err_msg:
                        # Extract sleep time or use default (5 minutes)
                        sleep_time = 300
                        # Try to match e.g. "try again in 5m28.4928s" or "4m53.0688s"
                        match = re.search(r"try again in (?:([0-9]+)m)?(?:([0-9\.]+)s)?", err_msg)
                        if match:
                            m_group = match.group(1)
                            s_group = match.group(2)
                            minutes = int(m_group) if m_group else 0
                            seconds = float(s_group) if s_group else 0
                            if minutes or seconds:
                                sleep_time = int(minutes * 60 + seconds) + 15

                        logger.warning(
                            f"Rate limit hit: {e}. Sleeping for {sleep_time} seconds before retrying this article..."
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(f"Unexpected error: {e}. Sleeping 10s before retry...")
                        await asyncio.sleep(10)

            # Polite delay to stay within Groq API rate limits (RPM / TPM)
            await asyncio.sleep(3.0)


if __name__ == "__main__":
    asyncio.run(main())
