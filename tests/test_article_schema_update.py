"""
Unit tests for updated ArticleSchema
Task 2.1: Validate ArticleSchema matches Supabase structure
"""
import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from app.schemas.article import ArticleSchema, AIAnalysis


class TestArticleSchemaUpdate:
    """Test updated ArticleSchema validation."""
    
    def test_article_schema_with_all_new_fields(self):
        """ArticleSchema accepts all new fields matching Supabase structure."""
        feed_id = uuid4()
        now = datetime.utcnow()
        
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI",
            "published_at": now,
            "created_at": now,
            "tinkering_index": 3,
            "ai_summary": "This is a test summary",
            "embedding": [0.1, 0.2, 0.3]
        }
        
        article = ArticleSchema(**data)
        
        assert article.title == "Test Article"
        assert str(article.url) == "https://example.com/article"
        assert article.feed_id == feed_id
        assert article.feed_name == "Tech Blog"
        assert article.category == "AI"
        assert article.published_at == now
        assert article.created_at == now
        assert article.tinkering_index == 3
        assert article.ai_summary == "This is a test summary"
        assert article.embedding == [0.1, 0.2, 0.3]
    
    def test_article_schema_with_minimal_required_fields(self):
        """ArticleSchema works with only required fields."""
        feed_id = uuid4()
        
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI"
        }
        
        article = ArticleSchema(**data)
        
        assert article.title == "Test Article"
        assert article.feed_id == feed_id
        assert article.feed_name == "Tech Blog"
        assert article.category == "AI"
        assert article.published_at is None
        assert article.tinkering_index is None
        assert article.ai_summary is None
        assert article.embedding is None
        assert article.created_at is not None  # Has default
    
    def test_feed_id_must_be_uuid(self):
        """ArticleSchema validates feed_id is a UUID."""
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": "not-a-uuid",
            "feed_name": "Tech Blog",
            "category": "AI"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleSchema(**data)
        
        assert "feed_id" in str(exc_info.value)
    
    def test_tinkering_index_range_validation(self):
        """ArticleSchema validates tinkering_index is between 1 and 5."""
        feed_id = uuid4()
        
        # Test below range
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI",
            "tinkering_index": 0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleSchema(**data)
        
        assert "tinkering_index" in str(exc_info.value)
        
        # Test above range
        data["tinkering_index"] = 6
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleSchema(**data)
        
        assert "tinkering_index" in str(exc_info.value)
    
    def test_tinkering_index_valid_range(self):
        """ArticleSchema accepts tinkering_index values 1-5."""
        feed_id = uuid4()
        
        for index in range(1, 6):
            data = {
                "title": "Test Article",
                "url": "https://example.com/article",
                "feed_id": feed_id,
                "feed_name": "Tech Blog",
                "category": "AI",
                "tinkering_index": index
            }
            
            article = ArticleSchema(**data)
            assert article.tinkering_index == index
    
    def test_title_max_length_validation(self):
        """ArticleSchema validates title max length is 2000 characters."""
        feed_id = uuid4()
        long_title = "A" * 2001
        
        data = {
            "title": long_title,
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleSchema(**data)
        
        assert "title" in str(exc_info.value)
    
    def test_ai_summary_max_length_validation(self):
        """ArticleSchema validates ai_summary max length is 5000 characters."""
        feed_id = uuid4()
        long_summary = "A" * 5001
        
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI",
            "ai_summary": long_summary
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleSchema(**data)
        
        assert "ai_summary" in str(exc_info.value)
    
    def test_removed_fields_not_accepted(self):
        """ArticleSchema does not accept removed fields (content_preview, raw_data)."""
        feed_id = uuid4()
        
        # This should work without the removed fields
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI"
        }
        
        article = ArticleSchema(**data)
        
        # Verify removed fields don't exist
        assert not hasattr(article, "content_preview")
        assert not hasattr(article, "raw_data")
        assert not hasattr(article, "published_date")  # renamed to published_at
    
    def test_renamed_fields(self):
        """ArticleSchema uses renamed fields (category, feed_name instead of source_category, source_name)."""
        feed_id = uuid4()
        
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI"
        }
        
        article = ArticleSchema(**data)
        
        # Verify new field names work
        assert article.category == "AI"
        assert article.feed_name == "Tech Blog"
        
        # Verify old field names don't exist
        assert not hasattr(article, "source_category")
        assert not hasattr(article, "source_name")
    
    def test_ai_analysis_still_works(self):
        """ArticleSchema still supports ai_analysis field."""
        feed_id = uuid4()
        
        ai_analysis = AIAnalysis(
            is_hardcore=True,
            reason="Great technical content",
            actionable_takeaway="Learn about new tech"
        )
        
        data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "feed_id": feed_id,
            "feed_name": "Tech Blog",
            "category": "AI",
            "ai_analysis": ai_analysis
        }
        
        article = ArticleSchema(**data)
        
        assert article.ai_analysis is not None
        assert article.ai_analysis.is_hardcore is True
        assert article.ai_analysis.reason == "Great technical content"
