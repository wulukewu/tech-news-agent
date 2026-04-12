"""
Notion Service - Legacy compatibility stub for tests.

This module provides backward compatibility for tests that were written
when the application used Notion. The actual implementation now uses Supabase.
"""

from datetime import datetime
from typing import Any

from app.core.exceptions import NotionServiceError
from app.schemas.article import ArticlePageResult

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
        pass

    async def get_active_feeds(self) -> list[dict[str, Any]]:
        """
        Get active RSS feeds.

        Returns:
            List of active feed configurations
        """
        raise NotImplementedError("NotionService is deprecated. Use SupabaseService instead.")

    async def add_feed(self, name: str, url: str, category: str) -> None:
        """
        Add a new RSS feed.

        Args:
            name: Feed name
            url: Feed URL
            category: Feed category
        """
        raise NotImplementedError("NotionService is deprecated. Use SupabaseService instead.")

    async def create_article_page(self, article: Any) -> tuple[str, str]:
        """
        Create an article page.

        Args:
            article: Article data

        Returns:
            Tuple of (page_id, page_url)
        """
        raise NotImplementedError("NotionService is deprecated. Use SupabaseService instead.")

    async def mark_article_as_read(self, page_id: str) -> None:
        """
        Mark an article as read.

        Args:
            page_id: The page ID to mark as read
        """
        raise NotImplementedError("NotionService is deprecated. Use SupabaseService instead.")

    async def add_to_read_later(self, article: Any) -> None:
        """
        Add an article to the read later list.

        Args:
            article: Article data
        """
        raise NotImplementedError("NotionService is deprecated. Use SupabaseService instead.")

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
