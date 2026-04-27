"""
Unit Tests for RetrievalEngine Enhancements (Task 5.2)

Tests search expansion, caching, and enhanced personalization features
added in Task 5.2.

Requirements: 2.5, 6.1, 8.4
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.qa_agent.models import ArticleMatch, UserProfile
from app.qa_agent.retrieval_engine import RetrievalEngine
from app.qa_agent.vector_store import VectorMatch

# ---------------------------------------------------------------------------
# Helpers / Factories (reused from main test file)
# ---------------------------------------------------------------------------


def make_vector(value: float = 0.5, dim: int = 1536) -> List[float]:
    """Create a dummy embedding vector."""
    return [value] * dim


def make_vector_match(
    article_id: Optional[UUID] = None,
    similarity_score: float = 0.8,
    chunk_text: str = "Sample article content about Python programming",
    metadata: Optional[Dict[str, Any]] = None,
) -> VectorMatch:
    """Create a VectorMatch test fixture."""
    return VectorMatch(
        article_id=article_id or uuid4(),
        similarity_score=similarity_score,
        metadata=metadata
        or {
            "title": "Python Programming Guide",
            "url": "https://example.com/python",
            "feed_name": "Tech Feed",
            "category": "programming",
            "content_preview": chunk_text,
        },
        chunk_index=0,
        chunk_text=chunk_text,
    )


def make_user_profile(
    preferred_topics: Optional[List[str]] = None,
    reading_history: Optional[List[UUID]] = None,
    query_history: Optional[List[str]] = None,
    satisfaction_scores: Optional[List[float]] = None,
) -> UserProfile:
    """Create a UserProfile test fixture."""
    return UserProfile(
        user_id=uuid4(),
        preferred_topics=preferred_topics or [],
        reading_history=reading_history or [],
        query_history=query_history or [],
        satisfaction_scores=satisfaction_scores or [],
    )


def make_article_match(
    article_id: Optional[UUID] = None,
    similarity_score: float = 0.8,
    keyword_score: float = 0.5,
    category: str = "programming",
    published_at: Optional[datetime] = None,
) -> ArticleMatch:
    """Create an ArticleMatch test fixture."""
    aid = article_id or uuid4()
    return ArticleMatch(
        article_id=aid,
        title="Test Article",
        content_preview="Content about Python and machine learning",
        similarity_score=similarity_score,
        keyword_score=keyword_score,
        url="https://example.com/article",
        feed_name="Tech Feed",
        category=category,
        published_at=published_at,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_vector_store():
    """Return a mock VectorStore."""
    store = MagicMock()
    store.search_similar = AsyncMock()
    return store


@pytest.fixture
def engine(mock_vector_store):
    """Return a RetrievalEngine backed by a mock VectorStore."""
    return RetrievalEngine(vector_store=mock_vector_store)


USER_ID = str(uuid4())


# ---------------------------------------------------------------------------
# Tests: Caching functionality
# ---------------------------------------------------------------------------


class TestCaching:
    """Tests for search result caching functionality."""

    @pytest.mark.asyncio
    async def test_semantic_search_caches_results(self, engine, mock_vector_store):
        """semantic_search should cache results for subsequent calls."""
        vm = make_vector_match(similarity_score=0.9)
        mock_vector_store.search_similar.return_value = [vm]

        # First call should hit the vector store
        results1 = await engine.semantic_search(make_vector(), USER_ID, use_cache=True)
        assert mock_vector_store.search_similar.call_count == 1

        # Second call with same parameters should use cache
        results2 = await engine.semantic_search(make_vector(), USER_ID, use_cache=True)
        assert mock_vector_store.search_similar.call_count == 1  # No additional call
        assert len(results1) == len(results2)

    @pytest.mark.asyncio
    async def test_hybrid_search_caches_results(self, engine, mock_vector_store):
        """hybrid_search should cache results for subsequent calls."""
        vm = make_vector_match(chunk_text="Python programming tutorial")
        mock_vector_store.search_similar.return_value = [vm]

        # First call should hit the vector store
        results1 = await engine.hybrid_search(
            "Python tutorial", make_vector(), USER_ID, use_cache=True
        )
        assert mock_vector_store.search_similar.call_count == 1

        # Second call with same parameters should use cache
        results2 = await engine.hybrid_search(
            "Python tutorial", make_vector(), USER_ID, use_cache=True
        )
        assert mock_vector_store.search_similar.call_count == 1  # No additional call
        assert len(results1) == len(results2)

    @pytest.mark.asyncio
    async def test_cache_can_be_disabled(self, engine, mock_vector_store):
        """Caching can be disabled with use_cache=False."""
        vm = make_vector_match()
        mock_vector_store.search_similar.return_value = [vm]

        # Two calls with caching disabled should both hit vector store
        await engine.semantic_search(make_vector(), USER_ID, use_cache=False)
        await engine.semantic_search(make_vector(), USER_ID, use_cache=False)
        assert mock_vector_store.search_similar.call_count == 2

    def test_cache_key_generation_consistent(self, engine):
        """Cache keys should be consistent for same parameters."""
        vector = make_vector()
        key1 = engine._generate_cache_key("semantic", vector, USER_ID, 10, 0.5)
        key2 = engine._generate_cache_key("semantic", vector, USER_ID, 10, 0.5)
        assert key1 == key2

    def test_cache_key_generation_different_for_different_params(self, engine):
        """Cache keys should be different for different parameters."""
        vector = make_vector()
        key1 = engine._generate_cache_key("semantic", vector, USER_ID, 10, 0.5)
        key2 = engine._generate_cache_key("semantic", vector, USER_ID, 20, 0.5)  # Different limit
        assert key1 != key2

    def test_cache_expiry(self, engine):
        """Cache entries should expire after TTL."""
        # Mock time to control expiry
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0

            # Cache a result
            results = [make_article_match()]
            cache_key = "test_key"
            engine._cache_result(cache_key, results)

            # Should be retrievable immediately
            cached = engine._get_cached_result(cache_key)
            assert cached == results

            # Move time forward beyond TTL
            mock_time.return_value = 1000.0 + engine._cache_ttl + 1

            # Should be expired now
            cached = engine._get_cached_result(cache_key)
            assert cached is None

    def test_cache_size_limit(self, engine):
        """Cache should respect size limits and evict oldest entries."""
        # Set a small cache size for testing
        engine._cache_max_size = 2

        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0

            # Add entries up to limit
            engine._cache_result("key1", [make_article_match()])
            engine._cache_result("key2", [make_article_match()])
            assert len(engine._search_cache) == 2

            # Adding another should evict the oldest
            mock_time.return_value = 1001.0  # Slightly later
            engine._cache_result("key3", [make_article_match()])
            assert len(engine._search_cache) == 2
            assert "key1" not in engine._search_cache  # Oldest should be evicted
            assert "key2" in engine._search_cache
            assert "key3" in engine._search_cache

    def test_clear_cache(self, engine):
        """clear_cache should remove all cached entries."""
        engine._cache_result("key1", [make_article_match()])
        engine._cache_result("key2", [make_article_match()])
        assert len(engine._search_cache) == 2

        engine.clear_cache()
        assert len(engine._search_cache) == 0

    def test_cache_stats(self, engine):
        """get_cache_stats should return accurate statistics."""
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0

            # Add some entries
            engine._cache_result("key1", [make_article_match()])
            engine._cache_result("key2", [make_article_match()])

            stats = engine.get_cache_stats()
            assert stats["total_entries"] == 2
            assert stats["valid_entries"] == 2
            assert stats["expired_entries"] == 0
            assert stats["max_size"] == engine._cache_max_size
            assert stats["ttl_seconds"] == engine._cache_ttl


# ---------------------------------------------------------------------------
# Tests: Enhanced search expansion
# ---------------------------------------------------------------------------


class TestSearchExpansion:
    """Tests for enhanced search expansion functionality."""

    @pytest.mark.asyncio
    async def test_expand_search_with_query_vector(self, engine, mock_vector_store):
        """expand_search should use query vector for broader semantic search."""
        # Setup: insufficient original results
        original = [make_article_match(similarity_score=0.9)]

        # Mock expanded search results
        expanded_vms = [
            make_vector_match(similarity_score=0.6),
            make_vector_match(similarity_score=0.5),
        ]
        mock_vector_store.search_similar.return_value = expanded_vms

        results = await engine.expand_search(
            original_results=original,
            user_id=USER_ID,
            query_vector=make_vector(),
            min_results=3,
        )

        # Should have original + expanded results
        assert len(results) >= len(original)
        # Should have called vector store for expansion
        assert mock_vector_store.search_similar.call_count >= 1

    @pytest.mark.asyncio
    async def test_expand_search_with_query_text(self, engine, mock_vector_store):
        """expand_search should use query text for keyword-based expansion."""
        original = [make_article_match()]

        # Mock results for keyword expansion
        keyword_vms = [
            make_vector_match(chunk_text="python programming guide"),
            make_vector_match(chunk_text="python tutorial basics"),
        ]
        mock_vector_store.search_similar.return_value = keyword_vms

        results = await engine.expand_search(
            original_results=original,
            user_id=USER_ID,
            query_text="python programming",
            min_results=3,
        )

        assert len(results) >= len(original)

    @pytest.mark.asyncio
    async def test_expand_search_no_expansion_when_sufficient(self, engine, mock_vector_store):
        """expand_search should not expand when results are sufficient."""
        # Sufficient results
        original = [make_article_match() for _ in range(5)]

        results = await engine.expand_search(
            original_results=original,
            user_id=USER_ID,
            min_results=3,
        )

        # Should return original results unchanged
        assert results == original
        # Should not call vector store
        assert mock_vector_store.search_similar.call_count == 0

    @pytest.mark.asyncio
    async def test_suggest_related_topics_with_results(self, engine):
        """suggest_related_topics should generate topics based on result categories."""
        results = [
            make_article_match(category="programming"),
            make_article_match(category="ai"),
        ]

        topics = await engine.suggest_related_topics(results)

        assert isinstance(topics, list)
        assert len(topics) > 0
        # Should include related topics for programming and AI
        assert any("algorithm" in topic or "software" in topic for topic in topics)

    @pytest.mark.asyncio
    async def test_suggest_related_topics_with_user_profile(self, engine):
        """suggest_related_topics should use user profile when no results."""
        profile = make_user_profile(preferred_topics=["machine-learning", "data-science"])

        topics = await engine.suggest_related_topics([], profile)

        assert isinstance(topics, list)
        assert len(topics) > 0
        # Should return user's preferred topics
        assert "machine-learning" in topics or "data-science" in topics

    @pytest.mark.asyncio
    async def test_suggest_related_topics_default_fallback(self, engine):
        """suggest_related_topics should provide default topics as fallback."""
        topics = await engine.suggest_related_topics([])

        assert isinstance(topics, list)
        assert len(topics) > 0
        # Should include common tech topics
        assert any(topic in ["programming", "ai", "technology"] for topic in topics)


# ---------------------------------------------------------------------------
# Tests: Enhanced personalization
# ---------------------------------------------------------------------------


class TestEnhancedPersonalization:
    """Tests for enhanced personalization features."""

    @pytest.mark.asyncio
    async def test_personalization_with_recency_boost(self, engine):
        """Recent articles should receive recency boost."""
        recent_date = datetime.utcnow() - timedelta(days=2)
        old_date = datetime.utcnow() - timedelta(days=30)

        profile = make_user_profile()
        matches = [
            make_article_match(similarity_score=0.7, published_at=recent_date),
            make_article_match(similarity_score=0.7, published_at=old_date),
        ]

        results = await engine.rank_by_user_preferences(matches, profile)

        # Recent article should rank higher due to recency boost
        recent_result = next(r for r in results if r.published_at == recent_date)
        old_result = next(r for r in results if r.published_at == old_date)
        assert recent_result.combined_score > old_result.combined_score

    @pytest.mark.asyncio
    async def test_personalization_diversity_penalty(self, engine):
        """Over-representation of same category should be penalized."""
        profile = make_user_profile()
        matches = [
            make_article_match(category="programming", similarity_score=0.8),
            make_article_match(category="programming", similarity_score=0.8),
            make_article_match(category="programming", similarity_score=0.8),
            make_article_match(category="design", similarity_score=0.8),
        ]

        results = await engine.rank_by_user_preferences(matches, profile)

        # Design article should rank higher due to diversity
        design_result = next(r for r in results if r.category == "design")
        programming_results = [r for r in results if r.category == "programming"]

        # At least one programming result should have lower score due to diversity penalty
        assert any(
            design_result.combined_score > prog.combined_score for prog in programming_results
        )

    @pytest.mark.asyncio
    async def test_personalization_query_pattern_matching(self, engine):
        """Articles matching user's query patterns should get boost."""
        profile = make_user_profile(query_history=["python tutorial", "machine learning basics"])

        # Create matches with different content that would match query patterns
        python_match = make_article_match(similarity_score=0.7)
        python_match.title = "Advanced Python Techniques"
        python_match.content_preview = "Learn advanced Python programming techniques"

        js_match = make_article_match(similarity_score=0.7)
        js_match.title = "JavaScript Frameworks"
        js_match.content_preview = "Overview of modern JavaScript frameworks"

        matches = [python_match, js_match]

        results = await engine.rank_by_user_preferences(matches, profile)

        # Python article should rank higher due to query pattern match
        python_result = next(r for r in results if "Python" in r.title)
        js_result = next(r for r in results if "JavaScript" in r.title)
        assert python_result.combined_score > js_result.combined_score

    @pytest.mark.asyncio
    async def test_personalization_strength_parameter(self, engine):
        """Personalization strength should control boost magnitude."""
        profile = make_user_profile(preferred_topics=["programming"])
        match = make_article_match(category="programming", similarity_score=0.5)

        # Test with different personalization strengths
        results_weak = await engine.rank_by_user_preferences(
            [match], profile, personalization_strength=0.5
        )
        results_strong = await engine.rank_by_user_preferences(
            [match], profile, personalization_strength=2.0
        )

        weak_boost = results_weak[0].metadata.get("personalization_boost", 0)
        strong_boost = results_strong[0].metadata.get("personalization_boost", 0)

        assert strong_boost > weak_boost

    @pytest.mark.asyncio
    async def test_personalization_metadata_tracking(self, engine):
        """Personalization should track detailed metadata."""
        recent_date = datetime.utcnow() - timedelta(days=1)
        profile = make_user_profile(preferred_topics=["programming"])
        match = make_article_match(
            category="programming", similarity_score=0.7, published_at=recent_date
        )

        results = await engine.rank_by_user_preferences([match], profile)

        metadata = results[0].metadata
        assert "personalization_boost" in metadata
        assert "topic_boost" in metadata
        assert "recency_days" in metadata
        assert "category_count" in metadata
        assert "is_read" in metadata


# ---------------------------------------------------------------------------
# Tests: Intelligent search integration
# ---------------------------------------------------------------------------


class TestIntelligentSearch:
    """Tests for the integrated intelligent_search method."""

    @pytest.mark.asyncio
    async def test_intelligent_search_basic_functionality(self, engine, mock_vector_store):
        """intelligent_search should perform hybrid search and return structured results."""
        vm = make_vector_match(chunk_text="Python programming tutorial")
        mock_vector_store.search_similar.return_value = [vm]

        result = await engine.intelligent_search(
            query="Python tutorial",
            query_vector=make_vector(),
            user_id=USER_ID,
        )

        assert "results" in result
        assert "expanded" in result
        assert "personalized" in result
        assert "suggested_topics" in result
        assert "search_time" in result
        assert "cache_hit" in result
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_intelligent_search_with_expansion(self, engine, mock_vector_store):
        """intelligent_search should trigger expansion when insufficient results."""
        # Return insufficient results initially
        vm = make_vector_match()
        mock_vector_store.search_similar.return_value = [vm]

        result = await engine.intelligent_search(
            query="Python tutorial",
            query_vector=make_vector(),
            user_id=USER_ID,
            min_results=3,
            use_expansion=True,
        )

        assert result["expanded"] is True
        assert len(result["suggested_topics"]) > 0  # Should suggest topics when still insufficient

    @pytest.mark.asyncio
    async def test_intelligent_search_with_personalization(self, engine, mock_vector_store):
        """intelligent_search should apply personalization when user profile provided."""
        vm = make_vector_match(chunk_text="Python programming tutorial")
        mock_vector_store.search_similar.return_value = [vm]

        profile = make_user_profile(preferred_topics=["programming"])

        result = await engine.intelligent_search(
            query="Python tutorial",
            query_vector=make_vector(),
            user_id=USER_ID,
            user_profile=profile,
            use_personalization=True,
        )

        assert result["personalized"] is True

    @pytest.mark.asyncio
    async def test_intelligent_search_performance_tracking(self, engine, mock_vector_store):
        """intelligent_search should track performance metrics."""
        vm = make_vector_match()
        mock_vector_store.search_similar.return_value = [vm]

        result = await engine.intelligent_search(
            query="test query",
            query_vector=make_vector(),
            user_id=USER_ID,
        )

        assert "search_time" in result
        assert isinstance(result["search_time"], float)
        assert result["search_time"] > 0

    @pytest.mark.asyncio
    async def test_intelligent_search_feature_flags(self, engine, mock_vector_store):
        """intelligent_search should respect feature flags."""
        vm = make_vector_match()
        mock_vector_store.search_similar.return_value = [vm]

        profile = make_user_profile(preferred_topics=["programming"])

        # Test with features disabled
        result = await engine.intelligent_search(
            query="test query",
            query_vector=make_vector(),
            user_id=USER_ID,
            user_profile=profile,
            use_expansion=False,
            use_personalization=False,
            use_cache=False,
        )

        assert result["expanded"] is False
        assert result["personalized"] is False
        assert result["cache_hit"] is False
