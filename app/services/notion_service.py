import logging
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import List, Optional
from notion_client import AsyncClient
from app.core.config import settings
from app.core.exceptions import NotionServiceError
from app.schemas.article import RSSSource, ArticleSchema, ReadingListItem


def build_digest_title(dt: datetime) -> str:
    """Generate weekly digest title in format '週報 YYYY-WW' (ISO week number, zero-padded)."""
    iso_year, iso_week, _ = dt.isocalendar()
    return f"週報 {iso_year:04d}-{iso_week:02d}"

logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self):
        # Initialize async notion client
        self.client = AsyncClient(auth=settings.notion_token)
        self.feeds_db_id = settings.notion_feeds_db_id
        self.read_later_db_id = settings.notion_read_later_db_id
        
    async def create_weekly_digest_page(
        self,
        title: str,
        published_date: date,
        article_count: int,
    ) -> tuple[str, str]:
        """Create a new page in the Weekly Digests database.

        Returns (page_id, page_url). Raises NotionServiceError on failure.
        """
        db_id = settings.notion_weekly_digests_db_id
        if not db_id:
            raise NotionServiceError("notion_weekly_digests_db_id is not configured")

        try:
            logger.info(f"Creating weekly digest page: {title}")
            response = await self.client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Title": {
                        "title": [{"text": {"content": title}}]
                    },
                    "Published_Date": {
                        "date": {"start": published_date.isoformat()}
                    },
                    "Article_Count": {
                        "number": article_count
                    },
                },
            )
            page_id: str = response["id"]
            page_url: str = response.get("url", "")
            logger.info(f"Created weekly digest page: id={page_id}, url={page_url}")
            return page_id, page_url
        except NotionServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to create weekly digest page: {e}")
            raise NotionServiceError(f"Error creating weekly digest page: {e}")

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

    @staticmethod
    def build_digest_blocks(
        articles: List[ArticleSchema],
        intro_text: str,
        stats: dict,
    ) -> List[dict]:
        """Build a Notion-API-compatible block list for the weekly digest page.

        Block structure:
          1. paragraph  – intro_text
          2. callout    – stats summary (total_fetched, hardcore_count, run_date)
          3. For each source_category group:
               heading_2 + toggle blocks for each article
               Toggle title: "[折騰指數 N/5] 文章標題"
               Toggle children: bookmark, reason callout, optional takeaway callout
          4. divider
        """

        def _rich_text(content: str) -> list:
            return [{"type": "text", "text": {"content": content}}]

        blocks: List[dict] = []

        # 1. Intro paragraph
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": _rich_text(intro_text),
            },
        })

        # 2. Stats callout
        stats_text = (
            f"📊 本週統計\n"
            f"總抓取：{stats.get('total_fetched', 0)} 篇\n"
            f"精選：{stats.get('hardcore_count', 0)} 篇\n"
            f"執行日期：{stats.get('run_date', '')}"
        )
        blocks.append({
            "type": "callout",
            "callout": {
                "rich_text": _rich_text(stats_text),
                "icon": {"type": "emoji", "emoji": "📊"},
            },
        })

        # 3. Group articles by source_category (preserve insertion order)
        grouped: dict = defaultdict(list)
        for article in articles:
            grouped[article.source_category].append(article)

        for category, cat_articles in grouped.items():
            # heading_2 for the category
            blocks.append({
                "type": "heading_2",
                "heading_2": {
                    "rich_text": _rich_text(category),
                },
            })

            for article in cat_articles:
                tinkering_index = 0
                if article.ai_analysis:
                    tinkering_index = article.ai_analysis.tinkering_index

                toggle_title = f"[折騰指數 {tinkering_index}/5] {article.title}"

                # Build toggle children
                children: List[dict] = []

                # bookmark block
                children.append({
                    "type": "bookmark",
                    "bookmark": {
                        "url": str(article.url),
                    },
                })

                # reason callout
                reason = ""
                if article.ai_analysis:
                    reason = article.ai_analysis.reason
                children.append({
                    "type": "callout",
                    "callout": {
                        "rich_text": _rich_text(f"推薦原因：{reason}"),
                        "icon": {"type": "emoji", "emoji": "💡"},
                    },
                })

                # actionable_takeaway callout (only if non-empty)
                takeaway = ""
                if article.ai_analysis:
                    takeaway = article.ai_analysis.actionable_takeaway or ""
                if takeaway:
                    children.append({
                        "type": "callout",
                        "callout": {
                            "rich_text": _rich_text(f"行動價值：{takeaway}"),
                            "icon": {"type": "emoji", "emoji": "🎯"},
                        },
                    })

                blocks.append({
                    "type": "toggle",
                    "toggle": {
                        "rich_text": _rich_text(toggle_title),
                        "children": children,
                    },
                })

        # 4. Divider
        blocks.append({"type": "divider", "divider": {}})

        return blocks

    async def append_digest_blocks(
        self,
        page_id: str,
        blocks: List[dict],
    ) -> None:
        """Append blocks to a Notion page, batching at most 100 blocks per API call.

        Automatically splits blocks into batches of 100 and calls
        blocks.children.append for each batch.
        """
        import math
        batch_size = 100
        total = len(blocks)
        num_batches = math.ceil(total / batch_size) if total > 0 else 0
        logger.info(f"Appending {total} blocks to page {page_id} in {num_batches} batch(es).")
        for i in range(num_batches):
            batch = blocks[i * batch_size:(i + 1) * batch_size]
            await self.client.blocks.children.append(block_id=page_id, children=batch)
        logger.info(f"Successfully appended all blocks to page {page_id}.")

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
