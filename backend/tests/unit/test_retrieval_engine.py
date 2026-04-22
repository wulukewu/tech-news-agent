"""
Unit Tests for RetrievalEngine

Tests semantic search, hybrid search, result ranking, and user-preference
filtering for the RetrievalEngine class.

Requirements: 2.1, 2.3, 2.4, 8.2
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from backend.app.qa_agent.models import ArticleMatch, UserProfile
from backend.app.qa_agent.retrieval_engine import RetrievalEngine, RetrievalEngineError
from backend.app.qa_agent.vector_store import VectorMatch, VectorStoreError

# ---------------------------------------------------------------------------
# Helpers / Factories
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
) -> UserProfile:
    """Create a UserProfile test fixture."""
    return UserProfile(
        user_id=uuid4(),
        preferred_topics=preferred_topics or [],
        reading_history=reading_history or [],
    )


def make_article_match(
    article_id: Optional[UUID] = None,
    similarity_score: float = 0.8,
    keyword_score: float = 0.5,
    category: str = "programming",
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
# Tests: semantic_search
# ---------------------------------------------------------------------------


class TestSemanticSearch:
    """Tests for RetrievalEngine.semantic_search."""

    @pytest.mark.asyncio
    async def test_returns_article_matches(self, engine, mock_vector_store):
        """semantic_search should return a list of ArticleMatch objects."""
        vm = make_vector_match(similarity_score=0.9)
        mock_vector_store.search_similar.return_value = [vm]

        results = await engine.semantic_search(make_vector(), USER_ID)

        assert len(results) == 1
        assert isinstance(results[0], ArticleMatch)

    @pytest.mark.asyncio
    async def test_results_sorted_by_similarity_descending(self, engine, mock_vector_store):
        """Results must be sorted by similarity_score descending (Req 2.3)."""
        vms = [
            make_vector_match(similarity_score=0.5),
            make_vector_match(similarity_score=0.9),
            make_vector_match(similarity_score=0.7),
        ]
        mock_vector_store.search_similar.return_value = vms

        results = await engine.semantic_search(make_vector(), USER_ID)

        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_passes_user_id_as_uuid(self, engine, mock_vector_store):
        """The user_id string must be converted to UUID before calling VectorStore."""
        mock_vector_store.search_similar.return_value = []
        user_id = str(uuid4())

        await engine.semantic_search(make_vector(), user_id)

        call_kwargs = mock_vector_store.search_similar.call_args
        assert isinstance(call_kwargs.kwargs.get("user_id") or call_kwargs.args[1], UUID)

    @pytest.mark.asyncio
    async def test_passes_limit_to_vector_store(self, engine, mock_vector_store):
        """The limit parameter should be forwarded to VectorStore."""
        mock_vector_store.search_similar.return_value = []

        await engine.semantic_search(make_vector(), USER_ID, limit=5)

        call_kwargs = mock_vector_store.search_similar.call_args
        limit_val = call_kwargs.kwargs.get("limit") or call_kwargs.args[2]
        assert limit_val == 5

    @pytest.mark.asyncio
    async def test_empty_results_returns_empty_list(self, engine, mock_vector_store):
        """Empty VectorStore results should return an empty list."""
        mock_vector_store.search_similar.return_value = []

        results = await engine.semantic_search(make_vector(), USER_ID)

        assert results == []

    @pytest.mark.asyncio
    async def test_vector_store_error_raises_retrieval_error(self, engine, mock_vector_store):
        """VectorStoreError should be wrapped in RetrievalEngineError."""
        mock_vector_store.search_similar.side_effect = VectorStoreError("DB down")

        with pytest.raises(RetrievalEngineError):
            await engine.semantic_search(make_vector(), USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_user_id_raises_error(self, engine, mock_vector_store):
        """An invalid user_id string should raise RetrievalEngineError."""
        with pytest.raises(RetrievalEngineError):
            await engine.semantic_search(make_vector(), "not-a-uuid")

    @pytest.mark.asyncio
    async def test_similarity_scores_in_valid_range(self, engine, mock_vector_store):
        """All returned similarity scores must be in [0, 1]."""
        vms = [make_vector_match(similarity_score=s) for s in [0.3, 0.6, 0.95]]
        mock_vector_store.search_similar.return_value = vms

        results = await engine.semantic_search(make_vector(), USER_ID)

        for r in results:
            assert 0.0 <= r.similarity_score <= 1.0


# ---------------------------------------------------------------------------
# Tests: hybrid_search
# ---------------------------------------------------------------------------


class TestHybridSearch:
    """Tests for RetrievalEngine.hybrid_search."""

    @pytest.mark.asyncio
    async def test_returns_article_matches(self, engine, mock_vector_store):
        """hybrid_search should return ArticleMatch objects."""
        vm = make_vector_match(chunk_text="Python programming tutorial")
        mock_vector_store.search_similar.return_value = [vm]

        results = await engine.hybrid_search("Python tutorial", make_vector(), USER_ID)

        assert len(results) == 1
        assert isinstance(results[0], ArticleMatch)

    @pytest.mark.asyncio
    async def test_combined_score_formula(self, engine, mock_vector_store):
        """combined_score = similarity * 0.7 + keyword * 0.3 (Req 2.4)."""
        vm = make_vector_match(
            similarity_score=1.0,
            chunk_text="python programming",
        )
        mock_vector_store.search_similar.return_value = [vm]

        results = await engine.hybrid_search("python programming", make_vector(), USER_ID)

        assert len(results) == 1
        r = results[0]
        expected = r.similarity_score * 0.7 + r.keyword_score * 0.3
        assert abs(r.combined_score - expected) < 1e-6

    @pytest.mark.asyncio
    async def test_keyword_match_increases_combined_score(self, engine, mock_vector_store):
        """An article whose text matches query keywords should score higher."""
        matching_vm = make_vector_match(
            similarity_score=0.7,
            chunk_text="python programming frameworks tutorial",
        )
        non_matching_vm = make_vector_match(
            similarity_score=0.7,
            chunk_text="cooking recipes and food preparation",
        )
        mock_vector_store.search_similar.return_value = [non_matching_vm, matching_vm]

        results = await engine.hybrid_search("python frameworks", make_vector(), USER_ID)

        # The matching article should rank higher
        assert results[0].combined_score >= results[1].combined_score

    @pytest.mark.asyncio
    async def test_results_sorted_by_combined_score(self, engine, mock_vector_store):
        """Results must be sorted by combined_score descending."""
        vms = [
            make_vector_match(similarity_score=0.5, chunk_text="unrelated content"),
            make_vector_match(similarity_score=0.9, chunk_text="python tutorial"),
            make_vector_match(similarity_score=0.7, chunk_text="python guide"),
        ]
        mock_vector_store.search_similar.return_value = vms

        results = await engine.hybrid_search("python", make_vector(), USER_ID)

        scores = [r.combined_score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_respects_limit(self, engine, mock_vector_store):
        """hybrid_search should not return more than limit results."""
        vms = [make_vector_match() for _ in range(10)]
        mock_vector_store.search_similar.return_value = vms

        results = await engine.hybrid_search("python", make_vector(), USER_ID, limit=3)

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_vector_store_error_raises_retrieval_error(self, engine, mock_vector_store):
        """VectorStoreError during hybrid search should raise RetrievalEngineError."""
        mock_vector_store.search_similar.side_effect = VectorStoreError("timeout")

        with pytest.raises(RetrievalEngineError):
            await engine.hybrid_search("python", make_vector(), USER_ID)

    @pytest.mark.asyncio
    async def test_empty_query_still_returns_results(self, engine, mock_vector_store):
        """An empty query string should still return semantic results."""
        vm = make_vector_match()
        mock_vector_store.search_similar.return_value = [vm]

        results = await engine.hybrid_search("", make_vector(), USER_ID)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_combined_scores_in_valid_range(self, engine, mock_vector_store):
        """All combined_score values must be in [0, 1]."""
        vms = [make_vector_match(similarity_score=s) for s in [0.3, 0.7, 1.0]]
        mock_vector_store.search_similar.return_value = vms

        results = await engine.hybrid_search("test query", make_vector(), USER_ID)

        for r in results:
            assert 0.0 <= r.combined_score <= 1.0


# ---------------------------------------------------------------------------
# Tests: expand_search
# ---------------------------------------------------------------------------


class TestExpandSearch:
    """Tests for RetrievalEngine.expand_search."""

    @pytest.mark.asyncio
    async def test_returns_originals_when_sufficient(self, engine, mock_vector_store):
        """expand_search should return originals unchanged when count >= min_results."""
        matches = [make_article_match() for _ in range(5)]

        result = await engine.expand_search(matches, USER_ID, min_results=3)

        assert result == matches

    @pytest.mark.asyncio
    async def test_returns_originals_when_empty(self, engine, mock_vector_store):
        """expand_search with empty list should return empty list."""
        result = await engine.expand_search([], USER_ID)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_originals_when_insufficient(self, engine, mock_vector_store):
        """expand_search returns originals when insufficient (no query vector available)."""
        matches = [make_article_match()]

        result = await engine.expand_search(matches, USER_ID, min_results=3)

        # Should still return the original results
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# Tests: rank_by_user_preferences
# ---------------------------------------------------------------------------


class TestRankByUserPreferences:
    """Tests for RetrievalEngine.rank_by_user_preferences (Req 8.2)."""

    @pytest.mark.asyncio
    async def test_preferred_topic_boosts_score(self, engine):
        """Articles in preferred topics should receive a score boost."""
        profile = make_user_profile(preferred_topics=["programming"])
        match = make_article_match(similarity_score=0.6, category="programming")

        results = await engine.rank_by_user_preferences([match], profile)

        assert results[0].combined_score > match.combined_score

    @pytest.mark.asyncio
    async def test_read_article_penalized(self, engine):
        """Already-read articles should receive a score penalty."""
        article_id = uuid4()
        profile = make_user_profile(reading_history=[article_id])
        match = make_article_match(article_id=article_id, similarity_score=0.8)

        results = await engine.rank_by_user_preferences([match], profile)

        assert results[0].combined_score < match.combined_score

    @pytest.mark.asyncio
    async def test_preferred_topic_ranks_higher_than_non_preferred(self, engine):
        """Preferred-topic articles should rank above non-preferred ones."""
        profile = make_user_profile(preferred_topics=["programming"])
        preferred = make_article_match(similarity_score=0.7, category="programming")
        non_preferred = make_article_match(similarity_score=0.7, category="cooking")

        results = await engine.rank_by_user_preferences([non_preferred, preferred], profile)

        assert results[0].article_id == preferred.article_id

    @pytest.mark.asyncio
    async def test_scores_remain_in_valid_range(self, engine):
        """Adjusted scores must stay within [0, 1]."""
        profile = make_user_profile(preferred_topics=["programming"])
        matches = [
            make_article_match(similarity_score=0.95, category="programming"),
            make_article_match(similarity_score=0.1, category="other"),
        ]

        results = await engine.rank_by_user_preferences(matches, profile)

        for r in results:
            assert 0.0 <= r.combined_score <= 1.0

    @pytest.mark.asyncio
    async def test_empty_matches_returns_empty(self, engine):
        """Empty input should return empty list."""
        profile = make_user_profile()

        results = await engine.rank_by_user_preferences([], profile)

        assert results == []

    @pytest.mark.asyncio
    async def test_no_preferences_preserves_order(self, engine):
        """With no preferences, order should be preserved by combined_score."""
        profile = make_user_profile()
        matches = [
            make_article_match(similarity_score=0.9),
            make_article_match(similarity_score=0.6),
            make_article_match(similarity_score=0.3),
        ]

        results = await engine.rank_by_user_preferences(matches, profile)

        scores = [r.combined_score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_different_profiles_produce_different_rankings(self, engine):
        """Different user profiles should produce different result orderings."""
        article_a = make_article_match(similarity_score=0.7, category="programming")
        article_b = make_article_match(similarity_score=0.7, category="cooking")

        profile_programmer = make_user_profile(preferred_topics=["programming"])
        profile_chef = make_user_profile(preferred_topics=["cooking"])

        results_programmer = await engine.rank_by_user_preferences(
            [article_a, article_b], profile_programmer
        )
        results_chef = await engine.rank_by_user_preferences([article_a, article_b], profile_chef)

        assert results_programmer[0].article_id != results_chef[0].article_id


# ---------------------------------------------------------------------------
# Tests: private helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    """Tests for private helper methods."""

    def test_extract_keywords_removes_stop_words(self, engine):
        """Stop words should be filtered from keyword extraction."""
        keywords = engine._extract_keywords("What is the best Python framework?")
        stop_words = {"what", "is", "the", "best"}
        assert not any(kw in stop_words for kw in keywords)

    def test_extract_keywords_lowercases(self, engine):
        """Keywords should be lowercased."""
        keywords = engine._extract_keywords("Python Django Flask")
        assert all(kw == kw.lower() for kw in keywords)

    def test_extract_keywords_filters_short_words(self, engine):
        """Words shorter than 2 characters should be filtered."""
        keywords = engine._extract_keywords("a b cd efg")
        assert "a" not in keywords
        assert "b" not in keywords

    def test_compute_keyword_score_full_match(self, engine):
        """All keywords present in text should yield score 1.0."""
        score = engine._compute_keyword_score(
            keywords=["python", "tutorial"],
            chunk_text="python tutorial for beginners",
            metadata={},
        )
        assert score == 1.0

    def test_compute_keyword_score_no_match(self, engine):
        """No keywords present should yield score 0.0."""
        score = engine._compute_keyword_score(
            keywords=["python", "tutorial"],
            chunk_text="cooking recipes and food",
            metadata={},
        )
        assert score == 0.0

    def test_compute_keyword_score_partial_match(self, engine):
        """Partial keyword match should yield score between 0 and 1."""
        score = engine._compute_keyword_score(
            keywords=["python", "tutorial", "advanced"],
            chunk_text="python guide",
            metadata={},
        )
        assert 0.0 < score < 1.0

    def test_compute_keyword_score_empty_keywords(self, engine):
        """Empty keyword list should yield score 0.0."""
        score = engine._compute_keyword_score(
            keywords=[],
            chunk_text="some content",
            metadata={},
        )
        assert score == 0.0

    def test_compute_keyword_score_checks_title_in_metadata(self, engine):
        """Keyword matching should also check the title in metadata."""
        score = engine._compute_keyword_score(
            keywords=["python"],
            chunk_text="unrelated content",
            metadata={"title": "Python Programming Guide"},
        )
        assert score > 0.0

    def test_parse_user_id_valid_string(self, engine):
        """Valid UUID string should be parsed correctly."""
        uid = uuid4()
        result = engine._parse_user_id(str(uid))
        assert result == uid

    def test_parse_user_id_uuid_passthrough(self, engine):
        """UUID object should be returned as-is."""
        uid = uuid4()
        result = engine._parse_user_id(uid)
        assert result == uid

    def test_parse_user_id_invalid_raises(self, engine):
        """Invalid string should raise RetrievalEngineError."""
        with pytest.raises(RetrievalEngineError):
            engine._parse_user_id("not-a-valid-uuid")
