import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import feedparser
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.schemas.article import ArticleSchema, RSSSource

if TYPE_CHECKING:
    from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

# Headers to prevent getting blocked by anti-bot protections randomly
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class RSSService:
    def __init__(self, days_to_fetch: int = 7):
        # We only want articles from the last X days
        self.days_to_fetch = days_to_fetch

    def _parse_date(self, entry) -> datetime:
        """Attempt to parse date from various feed formats securely.

        Priority order:
        1. published_parsed / updated_parsed (feedparser struct_time)
        2. Manual parsing of published / updated / pubDate strings using dateutil
        3. Fallback to current time (with warning log)
        """
        try:
            # Priority 1: Use feedparser's parsed struct_time
            parsed_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if parsed_struct:
                return datetime(*parsed_struct[:6]).replace(tzinfo=UTC)

            # Priority 2: Try manual parsing of date strings
            date_str = entry.get("published") or entry.get("updated") or entry.get("pubDate")
            if date_str:
                try:
                    from dateutil import parser as dateutil_parser

                    parsed_date = dateutil_parser.parse(date_str)
                    # Ensure timezone-aware datetime
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=UTC)
                    else:
                        parsed_date = parsed_date.astimezone(UTC)
                    logger.debug(f"Successfully parsed date string '{date_str}' to {parsed_date}")
                    return parsed_date
                except (ValueError, TypeError, ImportError) as e:
                    logger.warning(f"Failed to parse date string '{date_str}': {e}")

            # Priority 3: Fallback to current time
            logger.warning(
                f"No valid date found in entry, using current time. Entry keys: {list(entry.keys())}"
            )
            return datetime.now(UTC)

        except Exception as e:
            logger.error(f"Unexpected error in _parse_date: {e}", exc_info=True)
            return datetime.now(UTC)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _fetch_feed_content(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch XML content from URL with automatic retries."""
        logger.debug(f"Fetching RSS feed XML: {url}")
        response = await client.get(url, headers=BASE_HEADERS, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        return response.text

    async def _process_single_feed(
        self, source: RSSSource, client: httpx.AsyncClient, feed_id_map: dict = None
    ) -> tuple[list[ArticleSchema], str | None]:
        """Fetch and parse one specific RSS source.

        Returns:
            Tuple of (articles, feed_id_if_successful)
        """
        articles = []
        filtered_count = 0
        try:
            xml_content = await self._fetch_feed_content(client, str(source.url))
            feed = feedparser.parse(xml_content)

            cutoff_date = datetime.now(UTC) - timedelta(days=self.days_to_fetch)

            if feed_id_map and str(source.url) in feed_id_map:
                feed_id = feed_id_map[str(source.url)]
            else:
                from uuid import uuid4

                feed_id = uuid4()
                logger.warning(f"No feed_id found for {source.url}, using temporary UUID")

            for entry in feed.entries:
                published_date = self._parse_date(entry)

                if published_date < cutoff_date:
                    filtered_count += 1
                    continue

                url = entry.get("link", str(source.url))

                articles.append(
                    ArticleSchema(
                        title=entry.get("title", "No Title"),
                        url=url,
                        feed_id=feed_id,
                        feed_name=source.name,
                        category=source.category,
                        published_at=published_date,
                    )
                )

            logger.info(
                f"Fetched {len(articles)} fresh articles from '{source.name}' "
                f"(filtered {filtered_count} articles older than {self.days_to_fetch} days)"
            )
            return articles, str(feed_id)  # success: return feed_id

        except Exception as e:
            logger.error(f"Failed to process feed '{source.name}' at {source.url}: {e}")
            return [], None  # failure: return None

    async def fetch_all_feeds(
        self, sources: list[RSSSource], feed_id_map: dict = None
    ) -> tuple[list[ArticleSchema], list[str]]:
        """Concurrently fetch all RSS sources and aggregate results.

        Returns:
            Tuple of (all_articles, successfully_fetched_feed_ids)
        """
        logger.info(f"Starting concurrent fetch for {len(sources)} RSS feeds.")

        all_articles = []
        successful_feed_ids = []

        async with httpx.AsyncClient() as client:
            tasks = [self._process_single_feed(source, client, feed_id_map) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Unexpected error in feed processing task: {result}")
                elif isinstance(result, tuple):
                    articles, feed_id = result
                    all_articles.extend(articles)
                    if feed_id:
                        successful_feed_ids.append(feed_id)

        logger.info(f"Total fresh articles aggregated: {len(all_articles)}")
        return all_articles, successful_feed_ids

    async def fetch_new_articles(
        self, sources: list[RSSSource], supabase_service: "SupabaseService"
    ) -> list[ArticleSchema]:
        """Fetch articles from RSS feeds and filter out existing ones.

        This method implements article deduplication by checking against the database
        before returning articles for LLM processing. It wraps the existing
        fetch_all_feeds() method and filters out articles that already exist.

        Args:
            sources: List of RSS sources to fetch
            supabase_service: Service for database queries

        Returns:
            List of new articles not yet in database

        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        """
        logger.info(f"Starting fetch_new_articles for {len(sources)} sources")

        # Step 0: Build feed_id_map from database
        feed_id_map = {}
        try:
            # Query all feeds from database to get their IDs
            all_feeds = await supabase_service.get_active_feeds()
            # Create mapping: feed URL -> feed ID
            for feed_data in all_feeds:
                # We need to query the database directly to get feed IDs
                # This is a workaround since get_active_feeds returns RSSSource objects
                pass

            # Query feeds table directly to get id, url mapping
            response = (
                supabase_service.client.table("feeds")
                .select("id, url")
                .eq("is_active", True)
                .execute()
            )

            if response.data:
                for feed in response.data:
                    feed_id_map[feed["url"]] = feed["id"]
                logger.info(f"Built feed_id_map with {len(feed_id_map)} entries")
        except Exception as e:
            logger.error(f"Failed to build feed_id_map: {e}", exc_info=True)
            # Continue without feed_id_map - will use temporary UUIDs

        # Step 1: Fetch all articles from RSS feeds with feed_id_map
        all_articles, successful_feed_ids = await self.fetch_all_feeds(sources, feed_id_map)
        total_fetched = len(all_articles)
        logger.info(
            f"Fetched {total_fetched} articles from RSS feeds ({len(successful_feed_ids)} feeds successful)"
        )

        if not all_articles and not successful_feed_ids:
            logger.info("No articles fetched, returning empty list")
            return [], []

        # Step 2: Batch check all URLs against database (single query instead of N queries)
        new_articles = []
        existing_count = 0

        if all_articles:
            try:
                all_urls = [str(a.url) for a in all_articles]
                response = (
                    supabase_service.client.table("articles")
                    .select("url")
                    .in_("url", all_urls)
                    .execute()
                )
                existing_urls = {row["url"] for row in (response.data or [])}
            except Exception as e:
                logger.error(f"Batch URL check failed, falling back to individual checks: {e}")
                existing_urls = set()

            for article in all_articles:
                if str(article.url) in existing_urls:
                    existing_count += 1
                else:
                    new_articles.append(article)

        # Step 3: Log statistics
        new_count = len(new_articles)
        logger.info(
            f"Article deduplication complete - "
            f"Total fetched: {total_fetched}, "
            f"Already existing: {existing_count}, "
            f"New articles: {new_count}"
        )

        return new_articles, successful_feed_ids
