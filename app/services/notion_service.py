import logging
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional
from notion_client import AsyncClient
from app.core.config import settings
from app.core.exceptions import NotionServiceError
from app.schemas.article import RSSSource, ArticleSchema, ReadingListItem




def build_week_string(dt: datetime) -> str:
    """Generate week string in format 'YYYY-WW' (ISO week number, zero-padded).
    
    Args:
        dt: datetime object to extract week from
        
    Returns:
        Week string in format 'YYYY-WW' (e.g., '2024-01', '2024-52')
    """
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year:04d}-{iso_week:02d}"

logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self):
        # Initialize async notion client
        self.client = AsyncClient(auth=settings.notion_token)
        self.feeds_db_id = settings.notion_feeds_db_id
        self.read_later_db_id = settings.notion_read_later_db_id
        

    async def create_article_page(
        self,
        article: ArticleSchema,
        published_week: str,
    ) -> tuple[str, str]:
        """Create a new article page in the Weekly Digests database.

        Args:
            article: ArticleSchema with ai_analysis populated
            published_week: Week string in format "YYYY-WW"

        Returns:
            Tuple of (page_id, page_url)

        Raises:
            NotionServiceError: On API failure
        """
        db_id = settings.notion_weekly_digests_db_id
        if not db_id:
            raise NotionServiceError("notion_weekly_digests_db_id is not configured")

        try:
            logger.info(f"Creating article page: {article.title}")
            
            # Get current date in UTC+8
            from datetime import timedelta
            utc_plus_8 = timezone(timedelta(hours=8))
            now_utc8 = datetime.now(utc_plus_8)
            added_at_iso = now_utc8.date().isoformat()
            
            # Build page properties
            properties = {
                "Title": {
                    "title": [{"text": {"content": article.title[:2000]}}]
                },
                "URL": {
                    "url": str(article.url)[:2000]
                },
                "Source_Category": {
                    "select": {"name": article.source_category}
                },
                "Published_Week": {
                    "rich_text": [{"text": {"content": published_week}}]
                },
                "Tinkering_Index": {
                    "number": article.ai_analysis.tinkering_index if article.ai_analysis else 0
                },
                "Status": {
                    "status": {"name": "Unread"}
                },
                "Added_At": {
                    "date": {"start": added_at_iso}
                },
            }
            
            # Build page body blocks
            children = []
            
            # Callout: recommendation reason
            if article.ai_analysis and article.ai_analysis.reason:
                children.append({
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"推薦原因：{article.ai_analysis.reason}"}}],
                        "icon": {"type": "emoji", "emoji": "💡"},
                    },
                })
            
            # Callout: actionable takeaway (only if non-empty)
            if article.ai_analysis and article.ai_analysis.actionable_takeaway:
                children.append({
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"行動價值：{article.ai_analysis.actionable_takeaway}"}}],
                        "icon": {"type": "emoji", "emoji": "🎯"},
                    },
                })
            
            # Bookmark: article link
            children.append({
                "type": "bookmark",
                "bookmark": {
                    "url": str(article.url),
                },
            })
            
            # Create the page
            response = await self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                children=children,
            )
            
            page_id: str = response["id"]
            page_url: str = response.get("url", "")
            logger.info(f"Created article page: id={page_id}, url={page_url}")
            return page_id, page_url
            
        except NotionServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to create article page: {e}")
            raise NotionServiceError(f"Error creating article page: {e}")

    async def get_active_feeds(self) -> List[RSSSource]:
        """Fetch all active RSS feeds from the Feeds Database."""
        try:
            logger.info("Fetching active RSS feeds from Notion...")
            results = await self.client.request(
                path=f"databases/{self.feeds_db_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "Active",
                        "checkbox": {"equals": True}
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
            safe_url = str(article.url)[:2000] if article.url else ""

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

    async def add_feed(self, name: str, url: str, category: str) -> None:
        """新增一個 RSS 訂閱源至 Notion Feeds 資料庫。"""
        try:
            logger.info(f"Adding new feed to Notion: {name} ({category}) - {url}")
            await self.client.pages.create(
                parent={"database_id": self.feeds_db_id},
                properties={
                    "Name": {
                        "title": [{"text": {"content": name[:2000]}}]
                    },
                    "URL": {
                        "url": url[:2000]
                    },
                    "Category": {
                        "select": {"name": category}
                    },
                    "Active": {
                        "checkbox": True
                    },
                }
            )
            logger.info(f"Successfully added feed '{name}' to Notion.")
        except Exception as e:
            logger.error(f"Failed to add feed to Notion: {e}")
            raise NotionServiceError(f"Error adding feed to Notion: {e}")

    def _parse_reading_list_item(self, page: dict) -> Optional[ReadingListItem]:
        """Parse a Notion page dict into a ReadingListItem. Returns None if required fields are missing."""
        try:
            props = page.get("properties", {})

            title_prop = props.get("Title", {}).get("title", [])
            title = title_prop[0].get("plain_text", "") if title_prop else ""

            url = props.get("URL", {}).get("url")
            if not url:
                return None

            source_category_prop = props.get("Source_Category", {}).get("select") or {}
            source_category = source_category_prop.get("name", "Uncategorized")

            added_at = None
            date_prop = props.get("Added_At", {}).get("date")
            if date_prop and date_prop.get("start"):
                try:
                    added_at = datetime.fromisoformat(date_prop["start"])
                except ValueError:
                    added_at = None

            rating = None
            rating_prop = props.get("Rating", {}).get("number")
            if rating_prop is not None:
                rating = int(rating_prop)

            return ReadingListItem(
                page_id=page["id"],
                title=title,
                url=url,
                source_category=source_category,
                added_at=added_at,
                rating=rating,
            )
        except Exception as e:
            logger.warning(f"Failed to parse reading list item: {e}")
            return None

    async def get_reading_list(self) -> List[ReadingListItem]:
        """Query Read_Later_DB for all articles with Status = 'Unread'."""
        try:
            logger.info("Fetching unread articles from Read Later DB...")
            results = await self.client.databases.query(
                database_id=self.read_later_db_id,
                filter={
                    "property": "Status",
                    "status": {"equals": "Unread"}
                }
            )
            items = []
            for page in results.get("results", []):
                item = self._parse_reading_list_item(page)
                if item:
                    items.append(item)
            logger.info(f"Found {len(items)} unread articles.")
            return items
        except Exception as e:
            logger.error(f"Failed to fetch reading list: {e}")
            raise NotionServiceError(f"Error fetching reading list from Notion: {e}")

    async def mark_as_read(self, page_id: str) -> None:
        """Update the Status property of the given page to 'Read'."""
        try:
            logger.info(f"Marking page {page_id} as read...")
            await self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {"name": "Read"}
                    }
                }
            )
            logger.info(f"Successfully marked page {page_id} as read.")
        except Exception as e:
            logger.error(f"Failed to mark page {page_id} as read: {e}")
            raise NotionServiceError(f"Error updating page status in Notion: {e}")

    async def rate_article(self, page_id: str, rating: int) -> None:
        """Update the Rating property (Number type, 1-5) of the given page."""
        try:
            logger.info(f"Rating page {page_id} with {rating}...")
            await self.client.pages.update(
                page_id=page_id,
                properties={
                    "Rating": {
                        "number": rating
                    }
                }
            )
            logger.info(f"Successfully rated page {page_id} with {rating}.")
        except Exception as e:
            logger.error(f"Failed to rate page {page_id}: {e}")
            raise NotionServiceError(f"Error updating page rating in Notion: {e}")

    async def mark_article_as_read(self, page_id: str) -> None:
        """Update the Status property of the given article page to 'Read'.
        
        Args:
            page_id: The Notion page ID of the article
            
        Raises:
            NotionServiceError: On API failure
        """
        try:
            logger.info(f"Marking article page {page_id} as read...")
            await self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {"name": "Read"}
                    }
                }
            )
            logger.info(f"Successfully marked article page {page_id} as read.")
        except Exception as e:
            logger.error(f"Failed to mark article page {page_id} as read: {e}")
            raise NotionServiceError(f"Error updating article page status in Notion: {e}")



    async def get_highly_rated_articles(self, threshold: int = 4) -> List[ReadingListItem]:
        """Query Read_Later_DB for articles with Rating >= threshold."""
        try:
            logger.info(f"Fetching articles with rating >= {threshold}...")
            results = await self.client.databases.query(
                database_id=self.read_later_db_id,
                filter={
                    "property": "Rating",
                    "number": {"greater_than_or_equal_to": threshold}
                }
            )
            items = []
            for page in results.get("results", []):
                item = self._parse_reading_list_item(page)
                if item:
                    items.append(item)
            logger.info(f"Found {len(items)} highly rated articles.")
            return items
        except Exception as e:
            logger.error(f"Failed to fetch highly rated articles: {e}")
            raise NotionServiceError(f"Error fetching highly rated articles from Notion: {e}")

    @staticmethod
    def build_article_list_notification(
        article_pages: List['ArticlePageResult'],
        stats: dict,
    ) -> str:
        """Build Discord notification message (≤ 2000 chars).

        Format:
        本週技術週報已發布

        本週統計：抓取 {total} 篇，精選 {hardcore} 篇

        精選文章：
        1. [{category}] {title}
           {notion_page_url}
        2. ...

        If exceeds 2000 chars, truncate and add "...（共 N 篇，查看 Notion 資料庫以瀏覽完整列表）".

        Args:
            article_pages: List of ArticlePageResult
            stats: Dict with 'total_fetched' and 'hardcore_count' keys

        Returns:
            Discord notification message string (≤ 2000 chars)
        """
        from app.schemas.article import ArticlePageResult
        
        MAX_LENGTH = 2000
        
        # Build header
        header = "本週技術週報已發布\n\n"
        total_fetched = stats.get("total_fetched", 0)
        hardcore_count = stats.get("hardcore_count", 0)
        stats_line = f"本週統計：抓取 {total_fetched} 篇，精選 {hardcore_count} 篇\n\n"
        articles_header = "精選文章：\n"
        
        base_message = header + stats_line + articles_header
        
        # If no articles, return base message
        if not article_pages:
            return base_message
        
        # Build article list
        article_lines = []
        for idx, page in enumerate(article_pages, start=1):
            article_line = f"{idx}. [{page.category}] {page.title}\n   {page.page_url}\n"
            article_lines.append(article_line)
        
        # Try to fit all articles
        full_message = base_message + "".join(article_lines)
        
        if len(full_message) <= MAX_LENGTH:
            return full_message
        
        # Need to truncate - add articles one by one until we hit the limit
        truncation_suffix = f"\n\n...（共 {len(article_pages)} 篇，查看 Notion 資料庫以瀏覽完整列表）"
        available_space = MAX_LENGTH - len(base_message) - len(truncation_suffix)
        
        truncated_articles = []
        current_length = 0
        
        for article_line in article_lines:
            if current_length + len(article_line) <= available_space:
                truncated_articles.append(article_line)
                current_length += len(article_line)
            else:
                break
        
        # Build final truncated message
        truncated_message = base_message + "".join(truncated_articles) + truncation_suffix
        
        return truncated_message
