"""
Property-based tests for ArticleSchema
Task 2.2: 撰寫 ArticleSchema 的屬性測試

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8**
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List

from app.schemas.article import ArticleSchema


# Custom strategies for generating valid test data
@st.composite
def valid_uuids(draw):
    """Generate valid UUIDs."""
    return draw(st.uuids())


@st.composite
def valid_urls(draw):
    """Generate valid HTTP/HTTPS URLs."""
    protocol = draw(st.sampled_from(['http', 'https']))
    domain = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
        min_size=3,
        max_size=20
    ))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'io', 'dev']))
    path = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
        min_size=0,
        max_size=50
    ))
    
    if path:
        return f"{protocol}://{domain}.{tld}/{path}"
    return f"{protocol}://{domain}.{tld}"


@st.composite
def valid_datetimes(draw):
    """Generate valid datetime objects."""
    return draw(st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))


@st.composite
def valid_tinkering_indices(draw):
    """Generate valid tinkering_index values (1-5 or None)."""
    return draw(st.one_of(
        st.none(),
        st.integers(min_value=1, max_value=5)
    ))


@st.composite
def valid_embeddings(draw):
    """Generate valid embedding vectors or None."""
    return draw(st.one_of(
        st.none(),
        st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=1536  # Common embedding dimension
        )
    ))


@st.composite
def valid_article_data(draw):
    """Generate valid ArticleSchema data."""
    return {
        "title": draw(st.text(min_size=1, max_size=2000)),
        "url": draw(valid_urls()),
        "feed_id": draw(valid_uuids()),
        "feed_name": draw(st.text(min_size=1, max_size=200)),
        "category": draw(st.text(min_size=1, max_size=100)),
        "published_at": draw(st.one_of(st.none(), valid_datetimes())),
        "tinkering_index": draw(valid_tinkering_indices()),
        "ai_summary": draw(st.one_of(st.none(), st.text(min_size=0, max_size=5000))),
        "embedding": draw(valid_embeddings())
    }


# Feature: data-access-layer-refactor, Property 1: Article Schema Structure Validation
@given(article_data=valid_article_data())
@settings(max_examples=5)
def test_property_1_article_schema_structure_validation(article_data):
    """
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8**
    
    For any ArticleSchema instance, it should contain all required fields
    (feed_id as UUID, published_at as Optional[datetime], tinkering_index as
    Optional[int] with range 1-5, ai_summary as Optional[str], embedding as
    Optional[List[float]], created_at as datetime) and should not contain
    the removed fields (content_preview, raw_data).
    """
    # Create ArticleSchema instance
    article = ArticleSchema(**article_data)
    
    # Requirement 2.1: THE Article_Schema SHALL contain a feed_id field of type UUID
    assert hasattr(article, 'feed_id'), "ArticleSchema must have feed_id field"
    assert isinstance(article.feed_id, UUID), f"feed_id must be UUID, got {type(article.feed_id)}"
    assert article.feed_id == article_data['feed_id']
    
    # Requirement 2.2: THE Article_Schema SHALL contain a published_at field of type Optional[datetime]
    assert hasattr(article, 'published_at'), "ArticleSchema must have published_at field"
    assert article.published_at is None or isinstance(article.published_at, datetime), \
        f"published_at must be Optional[datetime], got {type(article.published_at)}"
    
    # Requirement 2.3: THE Article_Schema SHALL contain a tinkering_index field of type Optional[int] with range constraint 1-5
    assert hasattr(article, 'tinkering_index'), "ArticleSchema must have tinkering_index field"
    if article.tinkering_index is not None:
        assert isinstance(article.tinkering_index, int), \
            f"tinkering_index must be Optional[int], got {type(article.tinkering_index)}"
        assert 1 <= article.tinkering_index <= 5, \
            f"tinkering_index must be between 1 and 5, got {article.tinkering_index}"
    
    # Requirement 2.4: THE Article_Schema SHALL contain an ai_summary field of type Optional[str]
    assert hasattr(article, 'ai_summary'), "ArticleSchema must have ai_summary field"
    assert article.ai_summary is None or isinstance(article.ai_summary, str), \
        f"ai_summary must be Optional[str], got {type(article.ai_summary)}"
    if article.ai_summary is not None:
        assert len(article.ai_summary) <= 5000, \
            f"ai_summary must be max 5000 chars, got {len(article.ai_summary)}"
    
    # Requirement 2.5: THE Article_Schema SHALL contain an embedding field of type Optional[List[float]]
    assert hasattr(article, 'embedding'), "ArticleSchema must have embedding field"
    if article.embedding is not None:
        assert isinstance(article.embedding, list), \
            f"embedding must be Optional[List[float]], got {type(article.embedding)}"
        assert all(isinstance(x, float) for x in article.embedding), \
            "embedding must contain only floats"
    
    # Requirement 2.6: THE Article_Schema SHALL contain a created_at field of type datetime
    assert hasattr(article, 'created_at'), "ArticleSchema must have created_at field"
    assert isinstance(article.created_at, datetime), \
        f"created_at must be datetime, got {type(article.created_at)}"
    
    # Requirement 2.7: THE Article_Schema SHALL remove the content_preview field
    assert not hasattr(article, 'content_preview'), \
        "ArticleSchema must not have content_preview field (removed)"
    
    # Requirement 2.8: THE Article_Schema SHALL remove the raw_data field
    assert not hasattr(article, 'raw_data'), \
        "ArticleSchema must not have raw_data field (removed)"
    
    # Additional validation: Verify other required fields exist
    assert hasattr(article, 'title'), "ArticleSchema must have title field"
    assert isinstance(article.title, str), f"title must be str, got {type(article.title)}"
    assert len(article.title) <= 2000, f"title must be max 2000 chars, got {len(article.title)}"
    
    assert hasattr(article, 'url'), "ArticleSchema must have url field"
    assert hasattr(article, 'feed_name'), "ArticleSchema must have feed_name field"
    assert hasattr(article, 'category'), "ArticleSchema must have category field"


# Additional property test: Verify renamed fields
@given(article_data=valid_article_data())
@settings(max_examples=5)
def test_article_schema_renamed_fields(article_data):
    """
    **Validates: Requirements 2.9, 2.10**
    
    Verify that ArticleSchema uses the renamed fields (category, feed_name)
    and does not contain the old field names (source_category, source_name).
    """
    article = ArticleSchema(**article_data)
    
    # Requirement 2.9: THE Article_Schema SHALL rename source_category to category
    assert hasattr(article, 'category'), "ArticleSchema must have category field"
    assert not hasattr(article, 'source_category'), \
        "ArticleSchema must not have source_category field (renamed to category)"
    
    # Requirement 2.10: THE Article_Schema SHALL rename source_name to feed_name
    assert hasattr(article, 'feed_name'), "ArticleSchema must have feed_name field"
    assert not hasattr(article, 'source_name'), \
        "ArticleSchema must not have source_name field (renamed to feed_name)"


# Edge case property test: Minimal required fields
@given(
    title=st.text(min_size=1, max_size=2000),
    url=valid_urls(),
    feed_id=valid_uuids(),
    feed_name=st.text(min_size=1, max_size=200),
    category=st.text(min_size=1, max_size=100)
)
@settings(max_examples=5)
def test_article_schema_minimal_fields(title, url, feed_id, feed_name, category):
    """
    Verify ArticleSchema works with only required fields,
    and optional fields default to None or appropriate defaults.
    """
    data = {
        "title": title,
        "url": url,
        "feed_id": feed_id,
        "feed_name": feed_name,
        "category": category
    }
    
    article = ArticleSchema(**data)
    
    # Required fields should be set
    assert article.title == title
    # URL comparison: Pydantic HttpUrl may normalize URLs (add trailing slash)
    assert str(article.url).rstrip('/') == url.rstrip('/')
    assert article.feed_id == feed_id
    assert article.feed_name == feed_name
    assert article.category == category
    
    # Optional fields should be None
    assert article.published_at is None
    assert article.tinkering_index is None
    assert article.ai_summary is None
    assert article.embedding is None
    
    # created_at should have a default value
    assert article.created_at is not None
    assert isinstance(article.created_at, datetime)
