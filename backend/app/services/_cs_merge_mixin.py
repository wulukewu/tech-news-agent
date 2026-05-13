"""Mixin: result merging, scoring, and highlight generation for conversation search."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.conversation_search import ConversationSearchResult

_SCORE_TITLE = 1.0
_SCORE_SUMMARY = 0.7
_SCORE_MESSAGE = 0.5
_SCORE_MULTI_BOOST = 0.1


class _SearchMergeMixin:
    """Merge, score, and highlight helpers for ConversationSearchService."""

    def _merge_results(
        self,
        query: str,
        conv_matches: list[dict[str, Any]],
        msg_matches: list[dict[str, Any]],
    ) -> list[ConversationSearchResult]:
        """Merge conversation and message matches into scored result objects."""
        from app.services.conversation_search import ConversationSearchResult, _parse_datetime

        accumulated: dict[str, dict[str, Any]] = {}

        def _add(raw: dict[str, Any]) -> None:
            cid = raw["conversation_id"]
            entry = accumulated.setdefault(cid, {"raw": raw, "sources": set(), "matched_texts": []})
            entry["sources"].add(raw["match_source"])
            if raw.get("matched_text"):
                entry["matched_texts"].append((raw["match_source"], raw["matched_text"]))

        for r in conv_matches:
            _add(r)
        for r in msg_matches:
            _add(r)

        results: list[ConversationSearchResult] = []
        for cid, entry in accumulated.items():
            raw = entry["raw"]
            sources: set[str] = entry["sources"]
            matched_texts: list[tuple[str, str]] = entry["matched_texts"]

            if "title" in sources:
                base_score = _SCORE_TITLE
            elif "summary" in sources:
                base_score = _SCORE_SUMMARY
            else:
                base_score = _SCORE_MESSAGE

            if len(sources) > 1:
                base_score = min(1.0, base_score + _SCORE_MULTI_BOOST)

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
                    matched_content=[text for _, text in matched_texts],
                    highlight_snippets=[
                        self._generate_highlights(text, query) for _, text in matched_texts
                    ],
                )
            )
        return results

    @staticmethod
    def _generate_highlights(text: str, query: str) -> str:
        """Wrap query terms in <mark> tags (case-insensitive, preserves original casing)."""
        if not query or not text:
            return text
        terms = [re.escape(t) for t in query.split() if t]
        if not terms:
            return text
        return re.compile("(" + "|".join(terms) + ")", re.IGNORECASE).sub(r"<mark>\1</mark>", text)
