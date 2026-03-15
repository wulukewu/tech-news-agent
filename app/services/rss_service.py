import logging
import asyncio
from datetime import datetime, timedelta, timezone
import httpx
import feedparser
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.schemas.article import RSSSource, ArticleSchema
from app.core.exceptions import RSSScrapingError

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

    async def _process_single_feed(self, source: RSSSource, client: httpx.AsyncClient) -> list[ArticleSchema]:
        """Fetch and parse one specific RSS source."""
        articles = []
        try:
            xml_content = await self._fetch_feed_content(client, str(source.url))
            feed = feedparser.parse(xml_content)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_fetch)
            
            for entry in feed.entries:
                published_date = self._parse_date(entry)
                
                # Filter old articles
                if published_date < cutoff_date:
                    continue
                    
                # Robustly extract content
                content_preview = entry.get("summary") or entry.get("description") or ""
                # Occasionally feeds embed the whole HTML
                if "content" in entry and entry.content:
                    content_preview = entry.content[0].value
                
                # Cleanup preview and limit size to optimize LLM usage (first 800 chars)
                # Removing heavy HTML tags isn't strictly necessary since Llama is good at ignoring it,
                # but good for token limits.
                content_preview = content_preview[:800]
                
                # Extract URL securely
                url = entry.get("link", str(source.url))
                
                # If parsed successfully, create our Schema
                articles.append(ArticleSchema(
                    title=entry.get("title", "No Title"),
                    url=url,
                    content_preview=content_preview,
                    published_date=published_date,
                    source_category=source.category,
                    source_name=source.name,
                    raw_data=entry # Save raw entry just in case
                ))
                
            logger.info(f"Fetched {len(articles)} fresh articles from '{source.name}'")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to process feed '{source.name}' at {source.url}: {e}")
            # We don't raise here so one broken feed doesn't crash the whole batch
            return []

    async def fetch_all_feeds(self, sources: list[RSSSource]) -> list[ArticleSchema]:
        """Concurrently fetch all RSS sources and aggregate results."""
        logger.info(f"Starting concurrent fetch for {len(sources)} RSS feeds.")
        
        all_articles = []
        
        # We use a single client for connection pooling benefits
        async with httpx.AsyncClient() as client:
            tasks = [self._process_single_feed(source, client) for source in sources]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Unexpected error in feed processing task: {result}")
                elif isinstance(result, list):
                    all_articles.extend(result)
                    
        logger.info(f"Total fresh articles aggregated: {len(all_articles)}")
        return all_articles
