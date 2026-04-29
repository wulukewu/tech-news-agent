"""Mixin extracted from retrieval_engine.py."""
import logging
from typing import Any, Dict, List, Optional

from app.qa_agent.models import ArticleMatch

logger = logging.getLogger(__name__)


class ReCacheMixin:
    def _generate_cache_key(
        self,
        search_type: str,
        query_vector: List[float],
        user_id: str,
        limit: int,
        threshold: float,
        query_text: Optional[str] = None,
    ) -> str:
        """Generate a cache key for search results."""
        # Create a hash of the query vector for consistent key generation
        vector_hash = hashlib.md5(json.dumps(query_vector, sort_keys=True).encode()).hexdigest()[
            :16
        ]

        key_parts = [
            search_type,
            vector_hash,
            user_id,
            str(limit),
            f"{threshold:.3f}",
        ]

        if query_text:
            text_hash = hashlib.md5(query_text.encode()).hexdigest()[:8]
            key_parts.append(text_hash)

        return ":".join(key_parts)

    def _get_cached_result(self, cache_key: str) -> Optional[List[ArticleMatch]]:
        """Retrieve cached search results if still valid."""
        if cache_key not in self._search_cache:
            return None

        cached_results, timestamp = self._search_cache[cache_key]

        # Check if cache entry has expired
        if time.time() - timestamp > self._cache_ttl:
            del self._search_cache[cache_key]
            return None

        return cached_results

    def _cache_result(self, cache_key: str, results: List[ArticleMatch]) -> None:
        """Cache search results with timestamp."""
        # Implement LRU eviction if cache is full
        if len(self._search_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = min(self._search_cache.keys(), key=lambda k: self._search_cache[k][1])
            del self._search_cache[oldest_key]

        self._search_cache[cache_key] = (results, time.time())

    def clear_cache(self) -> None:
        """Clear all cached search results."""
        self._search_cache.clear()
        logger.info("Search cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        current_time = time.time()
        valid_entries = sum(
            1
            for _, timestamp in self._search_cache.values()
            if current_time - timestamp <= self._cache_ttl
        )

        return {
            "total_entries": len(self._search_cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._search_cache) - valid_entries,
            "max_size": self._cache_max_size,
            "ttl_seconds": self._cache_ttl,
            "hit_rate": getattr(self, "_cache_hits", 0)
            / max(getattr(self, "_cache_requests", 1), 1),
        }

    # ------------------------------------------------------------------
    # Search expansion methods
    # ------------------------------------------------------------------
