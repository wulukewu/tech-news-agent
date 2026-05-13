"""
Conversation Search Service

Full-text and filtered search across conversations and messages.

Search strategy:
1. Search conversations table by title and summary.
2. Search conversation_messages table by content.
3. Merge, deduplicate, and score results (multi-source boost).
4. Apply advanced filters (platform, favorite, archived, tags, date range).
5. Sort by relevance score, then paginate.

Implementation is split across three mixins:
- _cs_query_mixin._SearchQueryMixin   — database queries
- _cs_filter_mixin._SearchFilterMixin — filter application
- _cs_merge_mixin._SearchMergeMixin   — merge, score, highlight

Validates: Requirements 3.1, 3.3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.errors import DatabaseError, ErrorCode
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services._cs_filter_mixin import _SearchFilterMixin
from app.services._cs_merge_mixin import _SearchMergeMixin
from app.services._cs_query_mixin import _SearchQueryMixin

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Score constants (re-exported for tests that import them directly)
# ---------------------------------------------------------------------------

_SCORE_TITLE = 1.0
_SCORE_SUMMARY = 0.7
_SCORE_MESSAGE = 0.5
_SCORE_MULTI_BOOST = 0.1


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SearchFilters:
    """Advanced filters for conversation search."""

    platform: Optional[str] = None
    is_archived: Optional[bool] = False
    is_favorite: Optional[bool] = None
    tags: Optional[list[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class ConversationSearchResult:
    """A single search result with relevance metadata."""

    conversation_id: str
    title: str
    summary: Optional[str]
    platform: str
    last_message_at: datetime
    message_count: int
    tags: list[str]
    is_favorite: bool
    is_archived: bool
    relevance_score: float
    matched_content: list[str] = field(default_factory=list)
    highlight_snippets: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ConversationSearchService(_SearchQueryMixin, _SearchFilterMixin, _SearchMergeMixin):
    """Search engine for user conversations.

    Combines full-text substring search (via Supabase ilike) with advanced
    metadata filtering to return ranked, highlighted results.

    Validates: Requirements 3.1, 3.3
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.logger = get_logger(f"{__name__}.ConversationSearchService")

    async def search_conversations(
        self,
        user_id: str | UUID,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationSearchResult]:
        """Search conversations by keyword with optional filters.

        Args:
            user_id: UUID of the requesting user.
            query: Search string (case-insensitive substring match).
            filters: Optional advanced filters.
            limit: Max results to return.
            offset: Results to skip.

        Returns:
            Sorted, paginated list of ConversationSearchResult.

        Raises:
            DatabaseError: If any underlying database operation fails.
        """
        if filters is None:
            filters = SearchFilters()

        user_id_str = str(user_id)
        query_stripped = query.strip()

        self.logger.info(
            "Searching conversations",
            user_id=user_id_str,
            query=query_stripped,
            limit=limit,
            offset=offset,
        )

        try:
            conv_matches = await self._search_conversations_table(
                user_id_str, query_stripped, filters
            )
            msg_matches = await self._search_messages_table(user_id_str, query_stripped, filters)

            merged = self._merge_results(query_stripped, conv_matches, msg_matches)
            merged.sort(key=lambda r: r.relevance_score, reverse=True)
            paginated = merged[offset : offset + limit]

            self.logger.info(
                "Search complete",
                user_id=user_id_str,
                query=query_stripped,
                total_results=len(merged),
                returned=len(paginated),
            )
            return paginated

        except DatabaseError:
            raise
        except Exception as exc:
            self.logger.error(
                "Conversation search failed",
                exc_info=True,
                user_id=user_id_str,
                query=query_stripped,
                error=str(exc),
            )
            raise DatabaseError(
                f"Conversation search failed: {exc}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details={"user_id": user_id_str, "query": query_stripped},
                original_error=exc,
            ) from exc


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _parse_datetime(value: Any) -> datetime:
    """Parse a datetime value from a Supabase response."""
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    raise ValueError(f"Cannot parse datetime from value: {value!r}")
