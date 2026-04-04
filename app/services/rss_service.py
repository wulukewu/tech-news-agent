import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
import httpx
import feedparser
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.schemas.article import RSSSource, ArticleSchema
from app.core.exceptions import RSSScrapingError

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
        """Attempt to parse date from various feed formats securely."""
        date_str = entry.get("published") or entry.get("updated") or entry.get("pubDate")
        if not date_str:
            return datetime.now(timezone.utc)
            
        try:
            # feedparser usually parses standard dates into `published_parsed` struct_time
            parsed_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if parsed_struct:
                return datetime(*parsed_struct[:6]).replace(tzinfo=timezone.utc)
            # If manual fallback is needed, one could add dateutil.parser here
            logger.debug(f"Failed to parse time struct for {date_str}, falling back to current time.")
            return datetime.now(timezone.utc)
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            return datetime.now(timezone.utc)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def _fetch_feed_content(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch XML content from URL with automatic retries."""
        logger.debug(f"Fetching RSS feed XML: {url}")
        response = await client.get(url, headers=BASE_HEADERS, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        return response.text

    async def _process_single_feed(
        self, 
        source: RSSSource, 
        client: httpx.AsyncClient,
        feed_id_map: dict = None
    ) -> list[ArticleSchema]:
        """Fetch and parse one specific RSS source.
        
        Args:
            source: RSS source to fetch
            client: HTTP client for requests
            feed_id_map: Optional mapping of feed URLs to feed IDs from database
        """
        articles = []
        filtered_count = 0
        try:
            xml_content = await self._fetch_feed_content(client, str(source.url))
            feed = feedparser.parse(xml_content)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_fetch)
            
            # Get feed_id from the provided map or generate a temporary one
            if feed_id_map and str(source.url) in feed_id_map:
                feed_id = feed_id_map[str(source.url)]
            else:
                # Fallback: generate temporary UUID (should not happen in production)
                from uuid import uuid4
                feed_id = uuid4()
                logger.warning(f"No feed_id found for {source.url}, using temporary UUID")
            
            for entry in feed.entries:
                published_date = self._parse_date(entry)
                
                # Filter old articles (Requirement 11.4)
                if published_date < cutoff_date:
                    filtered_count += 1
                    continue
                    
                # Extract URL securely
                url = entry.get("link", str(source.url))
                
                # If parsed successfully, create our Schema with updated fields
                articles.append(ArticleSchema(
                    title=entry.get("title", "No Title"),
                    url=url,
                    feed_id=feed_id,  # Should be from database
                    feed_name=source.name,
                    category=source.category,
                    published_at=published_date,
                ))
            
            # Log statistics (Requirement 11.7)
            logger.info(
                f"Fetched {len(articles)} fresh articles from '{source.name}' "
                f"(filtered {filtered_count} articles older than {self.days_to_fetch} days)"
            )
            return articles
            
        except Exception as e:
            logger.error(f"Failed to process feed '{source.name}' at {source.url}: {e}")
            # We don't raise here so one broken feed doesn't crash the whole batch
            return []

    async def fetch_all_feeds(
        self, 
        sources: list[RSSSource],
        feed_id_map: dict = None
    ) -> list[ArticleSchema]:
        """Concurrently fetch all RSS sources and aggregate results.
        
        Args:
            sources: List of RSS sources to fetch
            feed_id_map: Optional mapping of feed URLs to feed IDs from database
        """
        logger.info(f"Starting concurrent fetch for {len(sources)} RSS feeds.")
        
        all_articles = []
        
        # We use a single client for connection pooling benefits
        async with httpx.AsyncClient() as client:
            tasks = [
                self._process_single_feed(source, client, feed_id_map) 
                for source in sources
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Unexpected error in feed processing task: {result}")
                elif isinstance(result, list):
                    all_articles.extend(result)
                    
        logger.info(f"Total fresh articles aggregated: {len(all_articles)}")
        return all_articles

    async def fetch_new_articles(
        self,
        sources: list[RSSSource],
        supabase_service: 'SupabaseService'
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
            response = supabase_service.client.table('feeds')\
                .select('id, url')\
                .eq('is_active', True)\
                .execute()
            
            if response.data:
                for feed in response.data:
                    feed_id_map[feed['url']] = feed['id']
                logger.info(f"Built feed_id_map with {len(feed_id_map)} entries")
        except Exception as e:
            logger.error(f"Failed to build feed_id_map: {e}", exc_info=True)
            # Continue without feed_id_map - will use temporary UUIDs
        
        # Step 1: Fetch all articles from RSS feeds with feed_id_map
        all_articles = await self.fetch_all_feeds(sources, feed_id_map)
        total_fetched = len(all_articles)
        logger.info(f"Fetched {total_fetched} articles from RSS feeds")
        
        if not all_articles:
            logger.info("No articles fetched, returning empty list")
            return []
        
        # Step 2: Check each article against database for deduplication
        new_articles = []
        existing_count = 0
        
        for article in all_articles:
            try:
                # Check if article URL already exists in database
                exists = await supabase_service.check_article_exists(str(article.url))
                
                if exists:
                    existing_count += 1
                    logger.debug(f"Article already exists, skipping: {article.url}")
                else:
                    new_articles.append(article)
                    logger.debug(f"New article found: {article.url}")
                    
            except Exception as e:
                # Log error but continue processing other articles (Requirement 2.7)
                logger.error(
                    f"Failed to check existence for article {article.url}: {e}",
                    exc_info=True
                )
                # On error, assume article is new to avoid losing data
                new_articles.append(article)
        
        # Step 3: Log statistics
        new_count = len(new_articles)
        logger.info(
            f"Article deduplication complete - "
            f"Total fetched: {total_fetched}, "
            f"Already existing: {existing_count}, "
            f"New articles: {new_count}"
        )
        
        return new_articles
