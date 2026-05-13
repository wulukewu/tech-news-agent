"""Mixin: database query strategies for conversation search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.logger import get_logger

if TYPE_CHECKING:
    from app.services.conversation_search import SearchFilters

logger = get_logger(__name__)


class _SearchQueryMixin:
    """Database query methods for ConversationSearchService."""

    async def _search_conversations_table(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Search conversations table by title and summary."""
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
                logger.warning(
                    "Failed to search conversations table", field=field_name, error=str(exc)
                )
        return results

    async def _search_messages_table(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Search conversation_messages by content; falls back to two-step query."""
        client = self.conversation_repo.client
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
            results: list[dict[str, Any]] = []
            for row in msg_response.data or []:
                conv = row.get("conversations") or {}
                if not conv or not self._passes_filters(conv, filters):
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
            return results
        except Exception as exc:
            logger.warning("Join query failed, falling back to two-step search", error=str(exc))
            return await self._search_messages_fallback(user_id, query, filters)

    async def _search_messages_fallback(
        self,
        user_id: str,
        query: str,
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        """Fallback: fetch matching messages then retrieve parent conversations."""
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
                    conversation_id=conv_id, user_id=user_id
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
            logger.warning("Fallback message search also failed", error=str(exc))
        return results
