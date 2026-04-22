"""
Retrieval Engine for Intelligent Q&A Agent

Implements semantic search, hybrid search (semantic + keyword), result
ranking/filtering based on user preferences, search expansion, and caching
for performance optimization using the VectorStore.

Requirements: 2.1, 2.3, 2.4, 2.5, 6.1, 8.2, 8.4
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from .constants import CacheConfig, ScoringThresholds
from .models import ArticleMatch, UserProfile
from .vector_store import VectorStore, VectorStoreError, get_vector_store

logger = logging.getLogger(__name__)


class RetrievalEngineError(Exception):
    """Base exception for RetrievalEngine operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class RetrievalEngine:
    """
    Performs semantic and hybrid search across the article vector store,
    ranking and filtering results based on relevance and user preferences.
    Includes search expansion, personalization, and caching for performance.

    Requirements: 2.1, 2.3, 2.4, 2.5, 6.1, 8.2, 8.4
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize the RetrievalEngine.

        Args:
            vector_store: Optional VectorStore instance (creates one if not provided)
        """
        self._vector_store = vector_store or get_vector_store()
        self._similarity_weight = ScoringThresholds.SIMILARITY_WEIGHT  # 0.7
        self._keyword_weight = ScoringThresholds.KEYWORD_WEIGHT  # 0.3

        # Initialize caching system
        self._search_cache: Dict[str, Tuple[List[ArticleMatch], float]] = {}
        self._cache_max_size = CacheConfig.QUERY_CACHE_MAX_SIZE
        self._cache_ttl = CacheConfig.QUERY_CACHE_TTL_SECONDS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def intelligent_search(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        user_profile: Optional[UserProfile] = None,
        limit: int = 10,
        min_results: int = 3,
        use_expansion: bool = True,
        use_personalization: bool = True,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform intelligent search with automatic expansion, personalization, and optimization.

        This is the main search method that combines all optimization features:
        - Hybrid semantic + keyword search
        - Automatic search expansion when insufficient results
        - User preference-based personalization
        - Result caching for performance
        - Related topic suggestions

        Args:
            query: Raw query text
            query_vector: Embedding vector for the query
            user_id: User identifier for access isolation
            user_profile: Optional user profile for personalization
            limit: Maximum number of results to return
            min_results: Minimum results before triggering expansion
            use_expansion: Whether to use search expansion (default: True)
            use_personalization: Whether to apply personalization (default: True)
            use_cache: Whether to use caching (default: True)

        Returns:
            Dictionary containing:
            - results: List of ArticleMatch objects
            - expanded: Whether search expansion was used
            - personalized: Whether personalization was applied
            - suggested_topics: List of related topic suggestions
            - search_time: Total search time in seconds
            - cache_hit: Whether result came from cache

        Validates: Requirements 2.1, 2.4, 2.5, 6.1, 8.2, 8.4
        """
        start_time = time.time()
        cache_hit = False

        # Step 1: Perform hybrid search
        results = await self.hybrid_search(
            query=query,
            query_vector=query_vector,
            user_id=user_id,
            limit=limit * 2 if use_expansion else limit,  # Get more if we might expand
            use_cache=use_cache,
        )

        # Check if we got results from cache
        if use_cache:
            cache_key = self._generate_cache_key(
                "hybrid",
                query_vector,
                user_id,
                limit,
                ScoringThresholds.MIN_SIMILARITY_THRESHOLD,
                query,
            )
            cache_hit = cache_key in self._search_cache

        # Step 2: Apply search expansion if needed
        expanded = False
        if use_expansion and len(results) < min_results:
            logger.info(f"Triggering search expansion: {len(results)} < {min_results}")
            results = await self.expand_search(
                original_results=results,
                user_id=user_id,
                query_vector=query_vector,
                query_text=query,
                min_results=min_results,
                expanded_limit=limit * 2,
            )
            expanded = True

        # Step 3: Apply personalization if user profile available
        personalized = False
        if use_personalization and user_profile:
            results = await self.rank_by_user_preferences(
                matches=results,
                user_profile=user_profile,
                personalization_strength=1.0,
            )
            personalized = True

        # Step 4: Trim to final limit
        final_results = results[:limit]

        # Step 5: Generate topic suggestions if results are still insufficient
        suggested_topics = []
        if len(final_results) < min_results:
            suggested_topics = await self.suggest_related_topics(
                original_results=final_results,
                user_profile=user_profile,
            )

        search_time = time.time() - start_time

        logger.info(
            f"Intelligent search completed in {search_time:.3f}s: "
            f"{len(final_results)} results, expanded={expanded}, "
            f"personalized={personalized}, cache_hit={cache_hit}"
        )

        return {
            "results": final_results,
            "expanded": expanded,
            "personalized": personalized,
            "suggested_topics": suggested_topics,
            "search_time": search_time,
            "cache_hit": cache_hit,
            "total_found": len(results),
        }

    async def semantic_search(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = ScoringThresholds.MIN_SIMILARITY_THRESHOLD,
        use_cache: bool = True,
    ) -> List[ArticleMatch]:
        """
        Perform vector similarity search and return ranked ArticleMatch results.
        Includes caching for performance optimization.

        Args:
            query_vector: Embedding vector for the query
            user_id: User identifier for access isolation
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold
            use_cache: Whether to use caching (default: True)

        Returns:
            List of ArticleMatch objects sorted by similarity score (descending)

        Validates: Requirements 2.1, 2.3, 6.1
        """
        user_uuid = self._parse_user_id(user_id)

        # Check cache first if enabled
        if use_cache:
            cache_key = self._generate_cache_key(
                "semantic", query_vector, user_id, limit, threshold
            )
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for semantic search: {cache_key[:16]}...")
                return cached_result

        start_time = time.time()

        try:
            vector_matches = await self._vector_store.search_similar(
                query_vector=query_vector,
                user_id=user_uuid,
                limit=limit,
                threshold=threshold,
            )
        except VectorStoreError as exc:
            logger.error(f"Vector store error during semantic search: {exc}")
            raise RetrievalEngineError("Semantic search failed", original_error=exc) from exc
        except Exception as exc:
            logger.error(f"Unexpected error during semantic search: {exc}")
            raise RetrievalEngineError("Semantic search failed", original_error=exc) from exc

        article_matches = [self._vector_match_to_article_match(vm) for vm in vector_matches]

        # Sort by similarity score descending (Requirement 2.3)
        article_matches.sort(key=lambda m: m.similarity_score, reverse=True)

        # Cache the result if enabled
        if use_cache:
            self._cache_result(cache_key, article_matches)

        search_time = time.time() - start_time
        logger.debug(
            f"Semantic search completed in {search_time:.3f}s, found {len(article_matches)} results"
        )

        return article_matches

    async def hybrid_search(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = ScoringThresholds.MIN_SIMILARITY_THRESHOLD,
        use_cache: bool = True,
    ) -> List[ArticleMatch]:
        """
        Combine semantic vector search with keyword matching for hybrid results.
        Includes caching for performance optimization.

        Combined score formula: similarity_score * 0.7 + keyword_score * 0.3

        Args:
            query: Raw query text for keyword matching
            query_vector: Embedding vector for semantic search
            user_id: User identifier for access isolation
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold for semantic search
            use_cache: Whether to use caching (default: True)

        Returns:
            List of ArticleMatch objects sorted by combined score (descending)

        Validates: Requirements 2.4, 6.1
        """
        user_uuid = self._parse_user_id(user_id)

        # Check cache first if enabled
        if use_cache:
            cache_key = self._generate_cache_key(
                "hybrid", query_vector, user_id, limit, threshold, query
            )
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for hybrid search: {cache_key[:16]}...")
                return cached_result

        start_time = time.time()

        # 1. Semantic search
        try:
            vector_matches = await self._vector_store.search_similar(
                query_vector=query_vector,
                user_id=user_uuid,
                limit=limit * 2,  # Fetch more to allow re-ranking
                threshold=threshold,
            )
        except VectorStoreError as exc:
            logger.error(f"Vector store error during hybrid search: {exc}")
            raise RetrievalEngineError(
                "Hybrid search failed at semantic stage", original_error=exc
            ) from exc
        except Exception as exc:
            logger.error(f"Unexpected error during hybrid search: {exc}")
            raise RetrievalEngineError(
                "Hybrid search failed at semantic stage", original_error=exc
            ) from exc

        # 2. Compute keyword scores for each match
        keywords = self._extract_keywords(query)
        article_matches: List[ArticleMatch] = []

        for vm in vector_matches:
            keyword_score = self._compute_keyword_score(
                keywords=keywords,
                chunk_text=vm.chunk_text or "",
                metadata=vm.metadata,
            )
            match = self._vector_match_to_article_match(vm, keyword_score=keyword_score)
            article_matches.append(match)

        # 3. Sort by combined score descending and trim to limit
        article_matches.sort(key=lambda m: m.combined_score, reverse=True)
        result = article_matches[:limit]

        # Cache the result if enabled
        if use_cache:
            self._cache_result(cache_key, result)

        search_time = time.time() - start_time
        logger.debug(f"Hybrid search completed in {search_time:.3f}s, found {len(result)} results")

        return result

    async def expand_search(
        self,
        original_results: List[ArticleMatch],
        user_id: str,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        min_results: int = 3,
        expanded_limit: int = 20,
    ) -> List[ArticleMatch]:
        """
        Expand search results when insufficient matches are found.

        Uses multiple expansion strategies:
        1. Lower similarity threshold for broader semantic search
        2. Related topic expansion based on existing results
        3. Keyword-based fallback search
        4. Suggest related topics when no expansion possible

        Args:
            original_results: Results from a previous search call
            user_id: User identifier for access isolation
            query_vector: Original query vector for re-search (optional)
            query_text: Original query text for keyword expansion (optional)
            min_results: Minimum desired number of results
            expanded_limit: Maximum results to return after expansion

        Returns:
            Expanded list of ArticleMatch objects (may include originals)

        Validates: Requirements 2.5
        """
        if len(original_results) >= min_results:
            logger.debug(
                f"Sufficient results ({len(original_results)} >= {min_results}), no expansion needed"
            )
            return original_results

        logger.info(f"Expanding search: {len(original_results)} results < {min_results} minimum")
        user_uuid = self._parse_user_id(user_id)
        existing_ids = {m.article_id for m in original_results}
        expanded_results = list(original_results)  # Start with originals

        try:
            # Strategy 1: Lower similarity threshold for broader semantic search
            if query_vector and len(expanded_results) < min_results:
                logger.debug("Strategy 1: Lowering similarity threshold")
                lowered_threshold = max(0.1, ScoringThresholds.MIN_SIMILARITY_THRESHOLD - 0.2)

                broader_matches = await self.semantic_search(
                    query_vector=query_vector,
                    user_id=user_id,
                    limit=expanded_limit,
                    threshold=lowered_threshold,
                    use_cache=False,  # Don't cache expanded searches
                )

                # Add new results not in original set
                for match in broader_matches:
                    if (
                        match.article_id not in existing_ids
                        and len(expanded_results) < expanded_limit
                    ):
                        expanded_results.append(match)
                        existing_ids.add(match.article_id)

            # Strategy 2: Related topic expansion based on existing results
            if len(expanded_results) < min_results and original_results:
                logger.debug("Strategy 2: Related topic expansion")
                related_results = await self._expand_by_related_topics(
                    original_results,
                    user_uuid,
                    existing_ids,
                    expanded_limit - len(expanded_results),
                )
                expanded_results.extend(related_results)
                existing_ids.update(r.article_id for r in related_results)

            # Strategy 3: Keyword-based fallback search
            if len(expanded_results) < min_results and query_text:
                logger.debug("Strategy 3: Keyword-based fallback")
                keyword_results = await self._expand_by_keywords(
                    query_text, user_uuid, existing_ids, expanded_limit - len(expanded_results)
                )
                expanded_results.extend(keyword_results)

            # Sort final results by combined score
            expanded_results.sort(key=lambda m: m.combined_score, reverse=True)
            final_results = expanded_results[:expanded_limit]

            logger.info(
                f"Search expansion completed: {len(original_results)} → {len(final_results)} results"
            )
            return final_results

        except Exception as exc:
            logger.error(f"Error during search expansion: {exc}")
            # Return original results if expansion fails
            return original_results

    async def rank_by_user_preferences(
        self,
        matches: List[ArticleMatch],
        user_profile: UserProfile,
        personalization_strength: float = 1.0,
    ) -> List[ArticleMatch]:
        """
        Re-rank article matches based on user preferences and reading history.
        Enhanced with sophisticated personalization including recency, diversity,
        and interaction patterns.

        Args:
            matches: List of ArticleMatch objects to re-rank
            user_profile: UserProfile containing preferences and reading history
            personalization_strength: Strength of personalization (0.0-2.0, default 1.0)

        Returns:
            Re-ranked list of ArticleMatch objects with personalized scoring

        Validates: Requirements 8.2, 8.4
        """
        if not matches:
            return matches

        logger.debug(f"Personalizing {len(matches)} results for user {user_profile.user_id}")

        preferred_topics = {t.lower() for t in user_profile.preferred_topics}
        read_ids = set(user_profile.reading_history)

        # Analyze user interaction patterns
        avg_satisfaction = user_profile.get_average_satisfaction()
        recent_queries = user_profile.query_history[-10:] if user_profile.query_history else []

        ranked: List[ArticleMatch] = []
        category_counts = {}  # Track category diversity

        for match in matches:
            boost = 0.0

            # 1. Preferred topic boost (enhanced)
            article_category = match.category.lower()
            topic_boost = 0.0
            for topic in preferred_topics:
                if topic in article_category:
                    topic_boost = max(topic_boost, ScoringThresholds.PERSONALIZATION_WEIGHT)
                elif any(word in article_category for word in topic.split()):
                    topic_boost = max(topic_boost, ScoringThresholds.PERSONALIZATION_WEIGHT * 0.5)

            boost += topic_boost * personalization_strength

            # 2. Reading history penalty (graduated)
            if match.article_id in read_ids:
                boost -= 0.15 * personalization_strength  # Stronger penalty for read articles

            # 3. Recency boost for recent articles
            if match.published_at:
                from datetime import datetime

                days_old = (datetime.utcnow() - match.published_at).days
                if days_old <= 7:  # Recent articles get boost
                    recency_boost = ScoringThresholds.RECENCY_WEIGHT * (1 - days_old / 7)
                    boost += recency_boost * personalization_strength

            # 4. Diversity boost (avoid too many articles from same category)
            category_count = category_counts.get(article_category, 0)
            if category_count >= 2:  # Penalize over-representation
                boost -= 0.05 * category_count * personalization_strength
            category_counts[article_category] = category_count + 1

            # 5. Query pattern matching boost
            if recent_queries:
                query_keywords = set()
                for query in recent_queries:
                    query_keywords.update(self._extract_keywords(query))

                title_keywords = set(self._extract_keywords(match.title))
                content_keywords = set(self._extract_keywords(match.content_preview))

                keyword_overlap = len(
                    query_keywords.intersection(title_keywords | content_keywords)
                )
                if keyword_overlap > 0:
                    pattern_boost = min(0.1, keyword_overlap * 0.02)
                    boost += pattern_boost * personalization_strength

            # 6. User satisfaction adjustment
            if avg_satisfaction > 0.7:  # High satisfaction users get more diverse content
                boost += 0.05 * personalization_strength
            elif avg_satisfaction < 0.4:  # Low satisfaction users get safer, popular content
                boost -= 0.05 * personalization_strength

            # Apply boost by adjusting combined_score (clamped to [0, 1])
            adjusted_score = min(1.0, max(0.0, match.combined_score + boost))

            # Create a new ArticleMatch with the adjusted combined_score and personalization metadata
            personalization_metadata = {
                **match.metadata,
                "personalization_boost": boost,
                "topic_boost": topic_boost,
                "recency_days": (datetime.utcnow() - match.published_at).days
                if match.published_at
                else None,
                "category_count": category_counts[article_category],
                "is_read": match.article_id in read_ids,
            }

            adjusted = ArticleMatch(
                article_id=match.article_id,
                title=match.title,
                content_preview=match.content_preview,
                similarity_score=match.similarity_score,
                keyword_score=match.keyword_score,
                metadata=personalization_metadata,
                url=match.url,
                published_at=match.published_at,
                feed_name=match.feed_name,
                category=match.category,
            )
            # Override combined_score after construction
            object.__setattr__(adjusted, "combined_score", adjusted_score)
            ranked.append(adjusted)

        # Final sort by personalized combined score
        ranked.sort(key=lambda m: m.combined_score, reverse=True)

        logger.debug(
            f"Personalization complete: avg boost = {sum(r.metadata.get('personalization_boost', 0) for r in ranked) / len(ranked):.3f}"
        )
        return ranked

    # ------------------------------------------------------------------
    # Caching methods
    # ------------------------------------------------------------------

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

    async def _expand_by_related_topics(
        self, original_results: List[ArticleMatch], user_uuid: UUID, existing_ids: set, limit: int
    ) -> List[ArticleMatch]:
        """Expand search by finding articles in related topics/categories."""
        if not original_results or limit <= 0:
            return []

        # Extract categories from original results
        categories = {match.category for match in original_results if match.category}
        if not categories:
            return []

        try:
            # This would ideally use a more sophisticated topic similarity search
            # For now, we'll use a simple category-based expansion
            related_matches = []

            # Search for articles in the same categories with lower threshold
            for category in categories:
                if len(related_matches) >= limit:
                    break

                # This is a simplified implementation - in a real system,
                # you'd want to search by category metadata or use topic modeling
                category_results = await self._vector_store.search_similar(
                    query_vector=[0.0] * 1536,  # Placeholder - would use category embeddings
                    user_id=user_uuid,
                    limit=limit - len(related_matches),
                    threshold=0.1,  # Very low threshold for category expansion
                )

                for vm in category_results:
                    if (
                        vm.article_id not in existing_ids
                        and vm.metadata
                        and vm.metadata.get("category") == category
                    ):
                        match = self._vector_match_to_article_match(vm)
                        related_matches.append(match)
                        if len(related_matches) >= limit:
                            break

            logger.debug(f"Found {len(related_matches)} related topic results")
            return related_matches

        except Exception as exc:
            logger.error(f"Error in related topic expansion: {exc}")
            return []

    async def _expand_by_keywords(
        self, query_text: str, user_uuid: UUID, existing_ids: set, limit: int
    ) -> List[ArticleMatch]:
        """Expand search using keyword-based fallback when semantic search fails."""
        if not query_text or limit <= 0:
            return []

        try:
            keywords = self._extract_keywords(query_text)
            if not keywords:
                return []

            # This is a simplified keyword search - in a real system,
            # you'd want to implement full-text search in the database
            keyword_results = []

            # Search with very low threshold to get more results for keyword filtering
            broad_results = await self._vector_store.search_similar(
                query_vector=[0.0] * 1536,  # Placeholder vector
                user_id=user_uuid,
                limit=limit * 3,  # Get more to filter by keywords
                threshold=0.05,  # Very low threshold
            )

            for vm in broad_results:
                if vm.article_id in existing_ids:
                    continue

                # Check if any keywords match in title or content
                searchable_text = (
                    vm.metadata.get("title", "") + " " + (vm.chunk_text or "")
                ).lower()

                keyword_matches = sum(1 for kw in keywords if kw in searchable_text)
                if keyword_matches > 0:
                    match = self._vector_match_to_article_match(vm)
                    # Adjust score based on keyword matches
                    keyword_score = keyword_matches / len(keywords)
                    object.__setattr__(
                        match, "combined_score", keyword_score * 0.5
                    )  # Lower score for fallback
                    keyword_results.append(match)

                    if len(keyword_results) >= limit:
                        break

            # Sort by keyword relevance
            keyword_results.sort(key=lambda m: m.combined_score, reverse=True)
            logger.debug(f"Found {len(keyword_results)} keyword-based results")
            return keyword_results[:limit]

        except Exception as exc:
            logger.error(f"Error in keyword expansion: {exc}")
            return []

    async def suggest_related_topics(
        self, original_results: List[ArticleMatch], user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """
        Suggest related topics when search expansion cannot find enough results.

        Args:
            original_results: Original search results to analyze
            user_profile: Optional user profile for personalized suggestions

        Returns:
            List of suggested topic strings

        Validates: Requirements 2.5
        """
        if not original_results:
            # Default suggestions based on user profile or general topics
            if user_profile and user_profile.preferred_topics:
                return user_profile.preferred_topics[:5]
            return ["programming", "ai", "web-development", "data-science", "technology"]

        # Extract topics from original results
        categories = [match.category for match in original_results if match.category]

        # Simple topic suggestion based on categories
        # In a real system, this would use topic modeling or knowledge graphs
        topic_suggestions = []

        for category in set(categories):
            # Add related topics based on category
            if "programming" in category.lower():
                topic_suggestions.extend(["algorithms", "software-engineering", "code-review"])
            elif "ai" in category.lower():
                topic_suggestions.extend(["machine-learning", "deep-learning", "neural-networks"])
            elif "web" in category.lower():
                topic_suggestions.extend(["frontend", "backend", "full-stack"])
            elif "data" in category.lower():
                topic_suggestions.extend(["analytics", "visualization", "statistics"])

        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(topic_suggestions))[:10]

        logger.debug(f"Generated {len(unique_suggestions)} topic suggestions")
        return unique_suggestions

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
        """
        meta = vm.metadata or {}
        return ArticleMatch(
            article_id=vm.article_id,
            title=meta.get("title", ""),
            content_preview=vm.chunk_text or meta.get("content_preview", ""),
            similarity_score=float(vm.similarity_score),
            keyword_score=keyword_score,
            metadata=meta,
            url=meta.get("url", "https://example.com"),
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
