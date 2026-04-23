"""
Conversation Search Service

Provides full-text and filtered search across conversations and their messages.
Uses Supabase's ``ilike`` operator for case-insensitive substring matching
(REST-API compatible alternative to raw PostgreSQL ``tsvector`` queries).

Search strategy:
1. Search the ``conversations`` table by title and summary.
2. Search the ``conversation_messages`` table by content.
3. Merge and deduplicate results, boosting score for multiple match sources.
4. Apply advanced filters (platform, is_favorite, is_archived, tags, date range).
5. Sort by relevance score descending, then paginate.

Validates: Requirements 3.1, 3.3
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.errors import DatabaseError, ErrorCode
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Score constants
# ---------------------------------------------------------------------------

_SCORE_TITLE = 1.0
_SCORE_SUMMARY = 0.7
_SCORE_MESSAGE = 0.5
_SCORE_MULTI_BOOST = 0.1  # added when more than one source matches


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SearchFilters:
    """Advanced filters for conversation search.

    Attributes:
        platform: Restrict results to a specific platform.
        is_favorite: Filter by favourite status.
        is_archived: When ``False`` (default) archived conversations are
            excluded.
        tags: Restrict to conversations that carry all of the listed tags.
        date_from: Inclusive lower bound on ``last_message_at``.
        date_to: Inclusive upper bound on ``last_message_at``.
    """

    platform: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = False
    tags: Optional[list[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class ConversationSearchResult:
    """A single search result returned by ConversationSearchService.

    Attributes:
        conversation_id: UUID string of the matching conversation.
        title: Conversation title.
        summary: Optional auto-generated summary.
        platform: Source platform.
        last_message_at: Timestamp of the most recent message.
        message_count: Total number of messages.
        tags: List of tag strings.
        is_favorite: Whether the conversation is marked as favourite.
        is_archived: Whether the conversation is archived.
        relevance_score: Float in [0.0, 1.0] indicating match quality.
        matched_content: Raw text snippets that matched the query.
        highlight_snippets: Snippets with matching terms in <mark> tags.
    """

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
    matched_content: list[str]
    highlight_snippets: list[str]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ConversationSearchService:
    """Search engine for user conversations.

    Combines full-text substring search (via Supabase ilike) with
    advanced metadata filtering to return ranked, highlighted results.

    Validates: Requirements 3.1, 3.3
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ) -> None:
        """Initialise the search service.

        Args:
            conversation_repo: Repository for conversation data access.
            message_repo: Repository for message data access.
        """
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.logger = get_logger(f"{__name__}.ConversationSearchService")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_conversations(
        self,
        user_id: str | UUID,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationSearchResult]:
        """Search conversations for a user by keyword with optional filters.

        The search is performed in two passes:
        1. Conversation pass - searches title and summary columns.
        2. Message pass - searches content in conversation_messages.

        Results are merged, deduplicated, scored, sorted by relevance, and
        paginated.

        Args:
            user_id: UUID of the requesting user.
            query: Search string (case-insensitive substring match).
            filters: Optional SearchFilters for advanced filtering.
            limit: Maximum number of results to return. Defaults to 20.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            Sorted, paginated list of ConversationSearchResult.

        Raises:
            DatabaseError: If any underlying database operation fails.

        Validates: Requirements 3.1, 3.3
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

    # ------------------------------------------------------------------
    # Private helpers - database queries
    # ------------------------------------------------------------------

    async def _search_conversations_table(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Search the conversations table by title and summary.

        Args:
            user_id: UUID string of the user.
            query: Search string.
            filters: Active search filters.

        Returns:
            List of raw match dicts.
        """
        client = self.conversation_repo.client
        results: list[dict[str, Any]] = []

        base_select = (
            "id, title, summary, platform, last_message_at, "
            "message_count, tags, is_favorite, is_archived"
        )

        for field_name, match_source in [("title", "title"), ("summary", "summary")]:
            try:
                q = (
                    client.table("conversations")
                    .select(base_select)
                    .eq("user_id", user_id)
                    .ilike(field_name, f"%{query}%")
                )
                q = self._apply_filters(q, filters)
                response = q.execute()

                for row in response.data or []:
                    results.append(
                        {
                            **row,
                            "conversation_id": row["id"],
                            "match_source": match_source,
                            "matched_text": row.get(field_name) or "",
                        }
                    )
            except Exception as exc:
                self.logger.warning(
                    "Failed to search conversations table",
                    field=field_name,
                    error=str(exc),
                )

        return results

    async def _search_messages_table(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Search conversation_messages by content, then fetch parent metadata.

        Attempts a join query first; falls back to a two-step query if the
        join is not supported by the Supabase client version.

        Args:
            user_id: UUID string of the user.
            query: Search string.
            filters: Active search filters.

        Returns:
            List of raw match dicts.
        """
        client = self.conversation_repo.client
        results: list[dict[str, Any]] = []

        try:
            msg_response = (
                client.table("conversation_messages")
                .select(
                    "conversation_id, content, "
                    "conversations!inner(id, user_id, title, summary, platform, "
                    "last_message_at, message_count, tags, is_favorite, is_archived)"
                )
                .eq("conversations.user_id", user_id)
                .ilike("content", f"%{query}%")
                .limit(100)
                .execute()
            )

            for row in msg_response.data or []:
                conv = row.get("conversations") or {}
                if not conv:
                    continue
                if not self._passes_filters(conv, filters):
                    continue

                results.append(
                    {
                        "conversation_id": row["conversation_id"],
                        "id": row["conversation_id"],
                        "title": conv.get("title", ""),
                        "summary": conv.get("summary"),
                        "platform": conv.get("platform", "web"),
                        "last_message_at": conv.get("last_message_at"),
                        "message_count": conv.get("message_count", 0),
                        "tags": conv.get("tags") or [],
                        "is_favorite": conv.get("is_favorite", False),
                        "is_archived": conv.get("is_archived", False),
                        "match_source": "message",
                        "matched_text": row.get("content", ""),
                    }
                )

        except Exception as exc:
            self.logger.warning(
                "Join query failed, falling back to two-step search",
                error=str(exc),
            )
            results = await self._search_messages_fallback(user_id, query, filters)

        return results

    async def _search_messages_fallback(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Fallback message search without a join.

        Fetches matching messages first, then retrieves their parent
        conversations individually to enforce ownership.

        Args:
            user_id: UUID string of the user.
            query: Search string.
            filters: Active search filters.

        Returns:
            List of raw match dicts.
        """
        client = self.conversation_repo.client
        results: list[dict[str, Any]] = []

        try:
            msg_response = (
                client.table("conversation_messages")
                .select("conversation_id, content")
                .ilike("content", f"%{query}%")
                .limit(100)
                .execute()
            )

            conv_id_to_content: dict[str, str] = {}
            for row in msg_response.data or []:
                cid = row["conversation_id"]
                if cid not in conv_id_to_content:
                    conv_id_to_content[cid] = row["content"]

            for conv_id, content in conv_id_to_content.items():
                conv = await self.conversation_repo.get_conversation(
                    conversation_id=conv_id,
                    user_id=user_id,
                )
                if conv is None:
                    continue

                conv_dict = {
                    "is_archived": conv.is_archived,
                    "is_favorite": conv.is_favorite,
                    "platform": conv.platform,
                    "tags": conv.tags,
                    "last_message_at": conv.last_message_at,
                }
                if not self._passes_filters(conv_dict, filters):
                    continue

                results.append(
                    {
                        "conversation_id": conv_id,
                        "id": conv_id,
                        "title": conv.title,
                        "summary": conv.summary,
                        "platform": conv.platform,
                        "last_message_at": conv.last_message_at,
                        "message_count": conv.message_count,
                        "tags": conv.tags,
                        "is_favorite": conv.is_favorite,
                        "is_archived": conv.is_archived,
                        "match_source": "message",
                        "matched_text": content,
                    }
                )

        except Exception as exc:
            self.logger.warning(
                "Fallback message search also failed",
                error=str(exc),
            )

        return results

    # ------------------------------------------------------------------
    # Private helpers - filtering
    # ------------------------------------------------------------------

    def _apply_filters(self, query: Any, filters: SearchFilters) -> Any:
        """Apply SearchFilters to a Supabase query builder.

        Args:
            query: Supabase query builder instance.
            filters: Filters to apply.

        Returns:
            Updated query builder.
        """
        if filters.platform is not None:
            query = query.eq("platform", filters.platform)
        if filters.is_archived is not None:
            query = query.eq("is_archived", filters.is_archived)
        if filters.is_favorite is not None:
            query = query.eq("is_favorite", filters.is_favorite)
        if filters.tags:
            for tag in filters.tags:
                query = query.contains("tags", [tag])
        if filters.date_from is not None:
            query = query.gte("last_message_at", filters.date_from.isoformat())
        if filters.date_to is not None:
            query = query.lte("last_message_at", filters.date_to.isoformat())
        return query

    @staticmethod
    def _passes_filters(conv: dict[str, Any], filters: SearchFilters) -> bool:
        """Check whether a conversation dict satisfies the given filters.

        Used for in-memory filtering in the message fallback path.

        Args:
            conv: Dictionary with conversation fields.
            filters: Filters to evaluate.

        Returns:
            True if the conversation passes all active filters.
        """
        if filters.platform is not None and conv.get("platform") != filters.platform:
            return False
        if filters.is_archived is not None and conv.get("is_archived") != filters.is_archived:
            return False
        if filters.is_favorite is not None and conv.get("is_favorite") != filters.is_favorite:
            return False
        if filters.tags:
            conv_tags: list[str] = conv.get("tags") or []
            if not all(t in conv_tags for t in filters.tags):
                return False
        lma = conv.get("last_message_at")
        if lma is not None and isinstance(lma, datetime):
            if filters.date_from is not None:
                date_from = filters.date_from
                if date_from.tzinfo is not None and lma.tzinfo is None:
                    lma = lma.replace(tzinfo=timezone.utc)
                elif date_from.tzinfo is None and lma.tzinfo is not None:
                    date_from = date_from.replace(tzinfo=timezone.utc)
                if lma < date_from:
                    return False
            if filters.date_to is not None:
                date_to = filters.date_to
                if date_to.tzinfo is not None and lma.tzinfo is None:
                    lma = lma.replace(tzinfo=timezone.utc)
                elif date_to.tzinfo is None and lma.tzinfo is not None:
                    date_to = date_to.replace(tzinfo=timezone.utc)
                if lma > date_to:
                    return False
        return True

    # ------------------------------------------------------------------
    # Private helpers - merging and scoring
    # ------------------------------------------------------------------

    def _merge_results(
        self,
        query: str,
        conv_matches: list[dict[str, Any]],
        msg_matches: list[dict[str, Any]],
    ) -> list[ConversationSearchResult]:
        """Merge conversation and message matches into scored result objects.

        Conversations appearing in both passes receive a score boost.
        Duplicate conversation IDs are collapsed into a single result.

        Args:
            query: Original search string (used for highlight generation).
            conv_matches: Raw dicts from the conversations table search.
            msg_matches: Raw dicts from the messages table search.

        Returns:
            List of ConversationSearchResult objects.
        """
        accumulated: dict[str, dict[str, Any]] = {}

        def _add(raw: dict[str, Any]) -> None:
            cid = raw["conversation_id"]
            source = raw["match_source"]
            text = raw.get("matched_text", "")

            if cid not in accumulated:
                accumulated[cid] = {
                    "raw": raw,
                    "sources": set(),
                    "matched_texts": [],
                }

            entry = accumulated[cid]
            entry["sources"].add(source)
            if text:
                entry["matched_texts"].append((source, text))

        for r in conv_matches:
            _add(r)
        for r in msg_matches:
            _add(r)

        results: list[ConversationSearchResult] = []
        for cid, entry in accumulated.items():
            raw = entry["raw"]
            sources: set[str] = entry["sources"]
            matched_texts: list[tuple[str, str]] = entry["matched_texts"]

            base_score = 0.0
            if "title" in sources:
                base_score = _SCORE_TITLE
            elif "summary" in sources:
                base_score = _SCORE_SUMMARY
            elif "message" in sources:
                base_score = _SCORE_MESSAGE

            if len(sources) > 1:
                base_score = min(1.0, base_score + _SCORE_MULTI_BOOST)

            matched_content = [text for _, text in matched_texts]
            highlight_snippets = [
                self._generate_highlights(text, query) for _, text in matched_texts
            ]

            lma_raw = raw.get("last_message_at")
            last_message_at = _parse_datetime(lma_raw) if lma_raw else datetime.now(timezone.utc)

            results.append(
                ConversationSearchResult(
                    conversation_id=cid,
                    title=raw.get("title", ""),
                    summary=raw.get("summary"),
                    platform=raw.get("platform", "web"),
                    last_message_at=last_message_at,
                    message_count=raw.get("message_count", 0),
                    tags=raw.get("tags") or [],
                    is_favorite=raw.get("is_favorite", False),
                    is_archived=raw.get("is_archived", False),
                    relevance_score=round(base_score, 4),
                    matched_content=matched_content,
                    highlight_snippets=highlight_snippets,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Private helpers - highlight generation
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_highlights(text: str, query: str) -> str:
        """Wrap occurrences of query terms in ``<mark>`` tags.

        The match is case-insensitive.  Each distinct word in ``query`` is
        highlighted independently.  The original casing of the source text
        is preserved.

        Args:
            text: Source text to highlight.
            query: Search query string.

        Returns:
            Text with matching terms wrapped in ``<mark>...</mark>``.

        Example:
            >>> ConversationSearchService._generate_highlights(
            ...     "Hello World", "world"
            ... )
            'Hello <mark>World</mark>'
        """
        if not query or not text:
            return text

        # Split query into individual words, escape regex special chars
        terms = [re.escape(term) for term in query.split() if term]
        if not terms:
            return text

        pattern = re.compile(
            "(" + "|".join(terms) + ")",
            re.IGNORECASE,
        )
        return pattern.sub(r"<mark>\1</mark>", text)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _parse_datetime(value: Any) -> datetime:
    """Parse a datetime value from a Supabase response.

    Args:
        value: Raw value from the database row.

    Returns:
        A timezone-aware datetime object.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    raise ValueError(f"Cannot parse datetime from value: {value!r}")
