import logging
from datetime import datetime, timezone
from typing import List
from notion_client import AsyncClient
from app.core.config import settings
from app.core.exceptions import NotionServiceError
from app.schemas.article import RSSSource, ArticleSchema

logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self):
        # Initialize async notion client
        self.client = AsyncClient(auth=settings.notion_token)
        self.feeds_db_id = settings.notion_feeds_db_id
        self.read_later_db_id = settings.notion_read_later_db_id
        
    async def get_active_feeds(self) -> List[RSSSource]:
        """Fetch all active RSS feeds from the Feeds Database."""
        try:
            logger.info("Fetching active RSS feeds from Notion...")
            results = await self.client.databases.query(
                database_id=self.feeds_db_id,
                filter={
                    "property": "Active",
                    "checkbox": {
                        "equals": True
                    }
                }
            )
            
            feeds = []
            for page in results.get("results", []):
                props = page.get("properties", {})
                
                # Parsing Notion properties carefully
                title_prop = props.get("Name", {}).get("title", [])
                name = title_prop[0].get("plain_text", "Unknown") if title_prop else "Unknown"
                
                url = props.get("URL", {}).get("url")
                if not url:
                    logger.warning(f"Feed '{name}' is missing a URL. Skipping.")
                    continue
                    
                category_prop = props.get("Category", {}).get("select", {})
                category = category_prop.get("name", "Uncategorized") if category_prop else "Uncategorized"
                
                feeds.append(RSSSource(name=name, url=url, category=category))
                
            logger.info(f"Found {len(feeds)} active feeds.")
            return feeds
            
        except Exception as e:
            logger.error(f"Failed to fetch active feeds from Notion: {e}")
            raise NotionServiceError(f"Error communicating with Notion: {e}")
            
    async def add_to_read_later(self, article: ArticleSchema):
        """Save a curated article to the Read Later database."""
        try:
            logger.info(f"Saving article to Read Later: {article.title}")
            
            # Format the current time in ISO8601
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Ensure URL fits in the url property limitation (2000 chars), though highly unlikely to exceed
            safe_url = article.url[:2000] if article.url else ""

            await self.client.pages.create(
                parent={"database_id": self.read_later_db_id},
                properties={
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": article.title[:2000] # Text content limit
                                }
                            }
                        ]
                    },
                    "URL": {
                        "url": safe_url
                    },
                    "Added_At": {
                        "date": {
                            "start": now_iso
                        }
                    },
                    "Source_Category": {
                        "select": {
                            "name": article.source_category
                        }
                    },
                    "Status": {
                        "status": {
                            "name": "Unread"
                        }
                    }
                }
            )
            logger.info(f"Successfully saved '{article.title}' to Read Later.")
            
        except Exception as e:
            logger.error(f"Failed to save article to Read Later: {e}")
            raise NotionServiceError(f"Error saving to Notion Read Later DB: {e}")
