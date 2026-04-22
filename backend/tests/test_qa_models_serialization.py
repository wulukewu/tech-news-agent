"""
Unit tests for QA Agent model serialization/deserialization functionality.

Tests the JSON serialization and deserialization methods for UserProfile,
Article, and ArticleSummary models.

Requirements: 8.1, 8.2, 3.2
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.qa_agent.article_models import Article, ArticleMetadata
from app.qa_agent.models import ArticleSummary, QueryLanguage, UserProfile


class TestUserProfileSerialization:
    """Test UserProfile serialization and deserialization."""

    def test_user_profile_to_dict(self):
        """Test UserProfile to_dict conversion."""
        user_id = uuid4()
        article_id1 = uuid4()
        article_id2 = uuid4()

        profile = UserProfile(
            user_id=user_id,
            reading_history=[article_id1, article_id2],
            preferred_topics=["AI", "Machine Learning"],
            language_preference=QueryLanguage.ENGLISH,
            interaction_patterns={"search_frequency": "high"},
            query_history=["What is AI?", "Machine learning basics"],
            satisfaction_scores=[0.8, 0.9],
        )

        data = profile.to_dict()

        # Verify structure
        assert isinstance(data, dict)
        assert data["user_id"] == str(user_id)
        assert data["reading_history"] == [str(article_id1), str(article_id2)]
        assert data["preferred_topics"] == ["AI", "Machine Learning"]
        assert data["language_preference"] == "en"
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    def test_user_profile_from_dict(self):
        """Test UserProfile from_dict conversion."""
        user_id = uuid4()
        article_id = uuid4()

        data = {
            "user_id": str(user_id),
            "reading_history": [str(article_id)],
            "preferred_topics": ["Technology"],
            "language_preference": "zh",
            "interaction_patterns": {},
            "query_history": [],
            "satisfaction_scores": [0.7],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        profile = UserProfile.from_dict(data)

        # Verify reconstruction
        assert profile.user_id == user_id
        assert profile.reading_history == [article_id]
        assert profile.preferred_topics == ["Technology"]
        assert profile.language_preference == QueryLanguage.CHINESE
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_user_profile_to_json(self):
        """Test UserProfile to_json conversion."""
        user_id = uuid4()

        profile = UserProfile(user_id=user_id, preferred_topics=["Python", "Testing"])

        json_str = profile.to_json()

        # Verify JSON format
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["user_id"] == str(user_id)
        assert data["preferred_topics"] == ["Python", "Testing"]

    def test_user_profile_from_json(self):
        """Test UserProfile from_json conversion."""
        user_id = uuid4()

        json_str = json.dumps(
            {
                "user_id": str(user_id),
                "reading_history": [],
                "preferred_topics": ["Data Science"],
                "language_preference": "en",
                "interaction_patterns": {},
                "query_history": [],
                "satisfaction_scores": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

        profile = UserProfile.from_json(json_str)

        # Verify reconstruction
        assert profile.user_id == user_id
        assert profile.preferred_topics == ["Data Science"]

    def test_user_profile_roundtrip(self):
        """Test complete serialization roundtrip."""
        user_id = uuid4()
        article_ids = [uuid4() for _ in range(3)]

        original = UserProfile(
            user_id=user_id,
            reading_history=article_ids,
            preferred_topics=["AI", "ML", "DL"],
            language_preference=QueryLanguage.CHINESE,
            interaction_patterns={"key": "value"},
            query_history=["query1", "query2"],
            satisfaction_scores=[0.8, 0.9, 0.7],
        )

        # Serialize and deserialize
        json_str = original.to_json()
        restored = UserProfile.from_json(json_str)

        # Verify all fields match
        assert restored.user_id == original.user_id
        assert restored.reading_history == original.reading_history
        assert restored.preferred_topics == original.preferred_topics
        assert restored.language_preference == original.language_preference
        assert restored.query_history == original.query_history
        assert restored.satisfaction_scores == original.satisfaction_scores


class TestArticleSummarySerialization:
    """Test ArticleSummary serialization and deserialization."""

    def test_article_summary_to_dict(self):
        """Test ArticleSummary to_dict conversion."""
        article_id = uuid4()
        published_at = datetime.utcnow()

        summary = ArticleSummary(
            article_id=article_id,
            title="Test Article",
            summary="This is a test summary. It has multiple sentences. Very informative.",
            url="https://example.com/article",
            relevance_score=0.85,
            reading_time=5,
            key_insights=["Insight 1", "Insight 2"],
            published_at=published_at,
            category="Technology",
        )

        data = summary.to_dict()

        # Verify structure
        assert isinstance(data, dict)
        assert data["article_id"] == str(article_id)
        assert data["title"] == "Test Article"
        assert data["relevance_score"] == 0.85
        assert data["published_at"] == published_at.isoformat()

    def test_article_summary_from_dict(self):
        """Test ArticleSummary from_dict conversion."""
        article_id = uuid4()

        data = {
            "article_id": str(article_id),
            "title": "Another Article",
            "summary": "Short summary here. With two sentences.",
            "url": "https://example.com/another",
            "relevance_score": 0.75,
            "reading_time": 3,
            "key_insights": ["Key point"],
            "published_at": datetime.utcnow().isoformat(),
            "category": "Science",
        }

        summary = ArticleSummary.from_dict(data)

        # Verify reconstruction
        assert summary.article_id == article_id
        assert summary.title == "Another Article"
        assert summary.relevance_score == 0.75
        assert isinstance(summary.published_at, datetime)

    def test_article_summary_to_json(self):
        """Test ArticleSummary to_json conversion."""
        article_id = uuid4()

        summary = ArticleSummary(
            article_id=article_id,
            title="JSON Test",
            summary="Testing JSON serialization. Works well.",
            url="https://example.com/json",
            relevance_score=0.9,
            reading_time=2,
            category="Testing",
        )

        json_str = summary.to_json()

        # Verify JSON format
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["article_id"] == str(article_id)
        assert data["title"] == "JSON Test"

    def test_article_summary_from_json(self):
        """Test ArticleSummary from_json conversion."""
        article_id = uuid4()

        json_str = json.dumps(
            {
                "article_id": str(article_id),
                "title": "From JSON",
                "summary": "Created from JSON. Successfully.",
                "url": "https://example.com/from-json",
                "relevance_score": 0.88,
                "reading_time": 4,
                "category": "Development",
            }
        )

        summary = ArticleSummary.from_json(json_str)

        # Verify reconstruction
        assert summary.article_id == article_id
        assert summary.title == "From JSON"

    def test_article_summary_roundtrip(self):
        """Test complete serialization roundtrip."""
        article_id = uuid4()
        published_at = datetime.utcnow()

        original = ArticleSummary(
            article_id=article_id,
            title="Roundtrip Test",
            summary="Testing roundtrip serialization. Should work perfectly. No data loss.",
            url="https://example.com/roundtrip",
            relevance_score=0.92,
            reading_time=6,
            key_insights=["Insight A", "Insight B", "Insight C"],
            published_at=published_at,
            category="Quality Assurance",
        )

        # Serialize and deserialize
        json_str = original.to_json()
        restored = ArticleSummary.from_json(json_str)

        # Verify all fields match
        assert restored.article_id == original.article_id
        assert restored.title == original.title
        assert restored.summary == original.summary
        assert str(restored.url) == str(original.url)
        assert restored.relevance_score == original.relevance_score
        assert restored.reading_time == original.reading_time
        assert restored.key_insights == original.key_insights
        assert restored.category == original.category
        # Note: datetime comparison might have microsecond differences
        assert abs((restored.published_at - original.published_at).total_seconds()) < 1


class TestArticleSerialization:
    """Test Article model serialization (already implemented in article_models.py)."""

    def test_article_to_dict(self):
        """Test Article to_dict conversion."""
        article_id = uuid4()
        feed_id = uuid4()

        article = Article(
            id=article_id,
            title="Test Article",
            content="This is the full content of the article.",
            url="https://example.com/article",
            feed_id=feed_id,
            feed_name="Test Feed",
            category="Technology",
            metadata=ArticleMetadata(author="John Doe", tags=["python", "testing"]),
        )

        data = article.to_dict()

        # Verify structure
        assert isinstance(data, dict)
        assert data["id"] == str(article_id)
        assert data["feed_id"] == str(feed_id)
        assert data["title"] == "Test Article"

    def test_article_from_dict(self):
        """Test Article from_dict conversion."""
        article_id = uuid4()
        feed_id = uuid4()

        data = {
            "id": str(article_id),
            "title": "From Dict",
            "content": "Content here",
            "url": "https://example.com/dict",
            "feed_id": str(feed_id),
            "feed_name": "Dict Feed",
            "category": "Testing",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "is_processed": False,
            "processing_status": "pending",
        }

        article = Article.from_dict(data)

        # Verify reconstruction
        assert article.id == article_id
        assert article.feed_id == feed_id
        assert article.title == "From Dict"

    def test_article_roundtrip(self):
        """Test complete Article serialization roundtrip."""
        article_id = uuid4()
        feed_id = uuid4()

        original = Article(
            id=article_id,
            title="Roundtrip Article",
            content="Full article content for roundtrip testing.",
            url="https://example.com/roundtrip",
            feed_id=feed_id,
            feed_name="Roundtrip Feed",
            category="Testing",
            metadata=ArticleMetadata(
                author="Jane Smith", tags=["roundtrip", "test"], technical_depth=3
            ),
        )

        # Serialize and deserialize
        json_str = original.to_json()
        restored = Article.from_json(json_str)

        # Verify all fields match
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.content == original.content
        assert str(restored.url) == str(original.url)
        assert restored.feed_id == original.feed_id
        assert restored.feed_name == original.feed_name
        assert restored.category == original.category


class TestSerializationEdgeCases:
    """Test edge cases in serialization."""

    def test_user_profile_empty_lists(self):
        """Test UserProfile with empty lists."""
        user_id = uuid4()

        profile = UserProfile(user_id=user_id)

        json_str = profile.to_json()
        restored = UserProfile.from_json(json_str)

        assert restored.reading_history == []
        assert restored.preferred_topics == []
        assert restored.query_history == []
        assert restored.satisfaction_scores == []

    def test_article_summary_without_optional_fields(self):
        """Test ArticleSummary without optional fields."""
        article_id = uuid4()

        summary = ArticleSummary(
            article_id=article_id,
            title="Minimal Summary",
            summary="Just the basics. Nothing more.",
            url="https://example.com/minimal",
            relevance_score=0.5,
            reading_time=1,
            category="Minimal",
        )

        json_str = summary.to_json()
        restored = ArticleSummary.from_json(json_str)

        assert restored.article_id == article_id
        assert restored.key_insights == []
        assert restored.published_at is None

    def test_unicode_content_serialization(self):
        """Test serialization with Unicode content (Chinese characters)."""
        user_id = uuid4()

        profile = UserProfile(
            user_id=user_id,
            preferred_topics=["人工智能", "機器學習"],
            query_history=["什麼是AI？", "機器學習基礎"],
            language_preference=QueryLanguage.CHINESE,
        )

        json_str = profile.to_json()
        restored = UserProfile.from_json(json_str)

        assert restored.preferred_topics == ["人工智能", "機器學習"]
        assert restored.query_history == ["什麼是AI？", "機器學習基礎"]

        # Verify JSON contains actual Unicode characters (not escaped)
        assert "人工智能" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
