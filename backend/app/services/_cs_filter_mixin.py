"""Mixin: filter application for conversation search."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.conversation_search import SearchFilters


class _SearchFilterMixin:
    """Filter helpers for ConversationSearchService."""

    def _apply_filters(self, query: Any, filters: SearchFilters) -> Any:
        """Apply SearchFilters to a Supabase query builder."""
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
        """Return True if a conversation dict satisfies all active filters."""
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
