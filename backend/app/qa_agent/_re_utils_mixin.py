"""Mixin extracted from retrieval_engine.py."""
import logging
from typing import Any, Dict, List
from uuid import UUID

from app.qa_agent.models import ArticleMatch

logger = logging.getLogger(__name__)


class ReUtilsMixin:
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_user_id(user_id: str) -> UUID:
        """Convert a string user_id to UUID."""
        if isinstance(user_id, UUID):
            return user_id
        try:
            return UUID(user_id)
        except (ValueError, AttributeError) as exc:
            raise RetrievalEngineError(f"Invalid user_id format: {user_id}") from exc

    def _vector_match_to_article_match(
        self,
        vm: Any,
        keyword_score: float = 0.0,
    ) -> ArticleMatch:
        """
        Convert a VectorMatch to an ArticleMatch.

        Pulls article metadata from the VectorMatch.metadata dict.
        Returns None if the metadata lacks a valid URL.
        """
        meta = vm.metadata or {}
        url = meta.get("url") or meta.get("link")
        if not url:
            return None
        return ArticleMatch(
            article_id=vm.article_id,
            title=meta.get("title", ""),
            content_preview=vm.chunk_text or meta.get("content_preview", ""),
            similarity_score=float(vm.similarity_score),
            keyword_score=keyword_score,
            metadata=meta,
            url=url,
            published_at=meta.get("published_at"),
            feed_name=meta.get("feed_name", ""),
            category=meta.get("category", ""),
        )

    @staticmethod
    @staticmethod
    def _extract_keywords(query: str) -> List[str]:
        """
        Extract simple keywords from a query string for keyword scoring.

        Splits on whitespace, lowercases, and filters short/stop words.
        """
        import re

        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "of",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "from",
            "and",
            "or",
            "but",
            "not",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "that",
            "this",
            "these",
            "those",
            "best",
            "good",
            "great",
            "nice",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "的",
            "是",
            "了",
            "在",
            "和",
            "有",
            "我",
            "你",
            "他",
            "她",
        }

        # Remove punctuation and split
        clean_query = re.sub(r"[^\w\s]", " ", query)
        tokens = clean_query.lower().split()

        return [t for t in tokens if len(t) >= 2 and t not in stop_words]

    def _compute_keyword_score(
        self,
        keywords: List[str],
        chunk_text: str,
        metadata: Dict[str, Any],
    ) -> float:
        """
        Compute a keyword matching score in [0, 1].

        Checks how many query keywords appear in the chunk text and title.
        """
        if not keywords:
            return 0.0

        searchable = (chunk_text + " " + metadata.get("title", "")).lower()
        matches = sum(1 for kw in keywords if kw in searchable)
        return min(1.0, matches / len(keywords))
