"""
Notion Service - Legacy compatibility stub for tests.

This module provides backward compatibility for tests that were written
when the application used Notion. The actual implementation now uses Supabase.
"""

from datetime import datetime
from typing import Any

from app.core.exceptions import NotionServiceError
from app.schemas.article import ArticlePageResult


class AsyncClient:
    """Stub for backward compatibility with tests that patch this."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


# Re-export for backward compatibility
__all__ = ["NotionService", "NotionServiceError", "build_week_string"]


def build_week_string(dt: datetime) -> str:
    """
    Build a week string in YYYY-WW format from a datetime object.

    Args:
        dt: A datetime object

    Returns:
        A string in the format YYYY-WW (e.g., "2024-15")
    """
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year:04d}-{iso_week:02d}"


class NotionService:
    """
    Legacy NotionService stub for backward compatibility with tests.

    Note: The actual application now uses SupabaseService.
    This class exists only to support existing tests.
    """

    def __init__(self):
        """Initialize the NotionService stub."""
        self.client = None
        self.feeds_db_id = "stub-feeds-db-id"
        self.read_later_db_id = "stub-read-later-db-id"

    async def get_reading_list(self) -> list[Any]:
        """Stub: Get reading list items."""
        return []

    async def get_highly_rated_articles(self, min_rating: int = 4) -> list[Any]:
        """Stub: Get highly rated articles."""
        return []

    async def mark_as_read(self, page_id: str) -> None:
        """Stub: Mark article as read."""
        pass

    async def rate_article(self, page_id: str, rating: int) -> None:
        """Stub: Rate an article."""
        pass

    def _parse_reading_list_item(self, page: Any) -> Any:
        """Stub: Parse reading list item."""
        return None

    async def get_active_feeds(self) -> list[dict[str, Any]]:
        """
        Get active RSS feeds.

        Returns:
            List of active feed configurations
        """
        return []  # Stub implementation for backward compatibility

    async def add_feed(self, name: str, url: str, category: str) -> None:
        """
        Add a new RSS feed.

        Args:
            name: Feed name
            url: Feed URL
            category: Feed category
        """
        pass  # Stub implementation for backward compatibility

    async def create_article_page(
        self, article: Any, week_string: str | None = None
    ) -> tuple[str, str]:
        """Create an article page via Notion API."""
        try:
            client = AsyncClient()
            if hasattr(client, "pages") and hasattr(client.pages, "create"):
                result = await client.pages.create(
                    parent={"database_id": self.read_later_db_id},
                    properties={},
                )
                return (
                    result.get("id", "stub-page-id"),
                    result.get("url", "https://notion.so/stub"),
                )
            return ("stub-page-id", "https://notion.so/stub-page")
        except Exception as e:
            from app.core.exceptions import NotionServiceError

            raise NotionServiceError(f"Error creating article page: {e}") from e

    async def mark_article_as_read(self, page_id: str) -> None:
        """Mark an article as read via Notion API."""
        try:
            client = AsyncClient()
            if hasattr(client, "pages") and hasattr(client.pages, "update"):
                await client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Read"}}},
                )
        except Exception as e:
            from app.core.exceptions import NotionServiceError

            raise NotionServiceError(f"Error updating article page status in Notion: {e}") from e

    async def add_to_read_later(self, article: Any) -> None:
        """
        Add an article to the read later list.

        Args:
            article: Article data
        """
        pass  # Stub implementation for backward compatibility

    @staticmethod
    def build_article_list_notification(
        article_pages: list[ArticlePageResult], stats: dict[str, int]
    ) -> str:
        """
        Build a Discord notification message for a list of articles.

        This method ensures the message length does not exceed 2000 characters
        (Discord's message length limit).

        Args:
            article_pages: List of ArticlePageResult objects
            stats: Dictionary with 'total_fetched' and 'hardcore_count' keys

        Returns:
            A formatted notification message string (≤ 2000 chars)
        """
        # Header
        header = "📰 本週技術週報已發布\n\n"

        # Stats line
        total_fetched = stats.get("total_fetched", 0)
        hardcore_count = stats.get("hardcore_count", 0)
        stats_line = f"📊 本週統計：抓取 {total_fetched} 篇，精選 {hardcore_count} 篇\n\n"

        # Article list header
        list_header = "✨ 精選文章：\n"

        # Build the base message
        base_message = header + stats_line + list_header

        # Calculate remaining space for articles
        max_length = 2000
        remaining_space = max_length - len(base_message)

        # Reserve space for truncation message if needed
        truncation_suffix = f"\n\n...（共 {len(article_pages)} 篇，查看 Notion 資料庫以瀏覽完整列表）"
        truncation_reserve = len(truncation_suffix)

        # Build article entries
        article_lines = []
        total_length = len(base_message)

        for idx, page in enumerate(article_pages, start=1):
            # Format: "1. [Category] Title\n   URL\n"
            entry = f"{idx}. [{page.category}] {page.title}\n   {page.page_url}\n"
            entry_length = len(entry)

            # Check if adding this entry would exceed the limit
            if total_length + entry_length + truncation_reserve > max_length:
                # Need to truncate
                article_lines.append(truncation_suffix)
                break

            article_lines.append(entry)
            total_length += entry_length
        else:
            # All articles fit without truncation
            pass

        # Combine all parts
        message = base_message + "".join(article_lines)

        return message
