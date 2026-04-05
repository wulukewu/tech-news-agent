"""
Unit tests for ArticlePageResult schema
Task 1.1: Validate field completeness and type correctness
"""
import pytest
from pydantic import ValidationError

from app.schemas.article import ArticlePageResult


class TestArticlePageResult:
    """Test ArticlePageResult schema validation."""
    
    def test_valid_article_page_result(self):
        """ArticlePageResult accepts valid data with all required fields."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": 3
        }
        result = ArticlePageResult(**data)
        
        assert result.page_id == "abc123"
        assert result.page_url == "https://notion.so/abc123"
        assert result.title == "Test Article"
        assert result.category == "AI"
        assert result.tinkering_index == 3
    
    def test_missing_page_id_raises_error(self):
        """ArticlePageResult raises ValidationError when page_id is missing."""
        data = {
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "page_id" in str(exc_info.value)
    
    def test_missing_page_url_raises_error(self):
        """ArticlePageResult raises ValidationError when page_url is missing."""
        data = {
            "page_id": "abc123",
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "page_url" in str(exc_info.value)
    
    def test_missing_title_raises_error(self):
        """ArticlePageResult raises ValidationError when title is missing."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "title" in str(exc_info.value)
    
    def test_missing_category_raises_error(self):
        """ArticlePageResult raises ValidationError when category is missing."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "category" in str(exc_info.value)
    
    def test_missing_tinkering_index_raises_error(self):
        """ArticlePageResult raises ValidationError when tinkering_index is missing."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": "AI"
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "tinkering_index" in str(exc_info.value)
    
    def test_page_id_type_validation(self):
        """ArticlePageResult validates page_id is a string."""
        data = {
            "page_id": 123,  # Invalid: should be string
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "page_id" in str(exc_info.value)
    
    def test_page_url_type_validation(self):
        """ArticlePageResult validates page_url is a string."""
        data = {
            "page_id": "abc123",
            "page_url": 12345,  # Invalid: should be string
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "page_url" in str(exc_info.value)
    
    def test_title_type_validation(self):
        """ArticlePageResult validates title is a string."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": 12345,  # Invalid: should be string
            "category": "AI",
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "title" in str(exc_info.value)
    
    def test_category_type_validation(self):
        """ArticlePageResult validates category is a string."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": 12345,  # Invalid: should be string
            "tinkering_index": 3
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "category" in str(exc_info.value)
    
    def test_tinkering_index_type_validation(self):
        """ArticlePageResult validates tinkering_index is an integer."""
        data = {
            "page_id": "abc123",
            "page_url": "https://notion.so/abc123",
            "title": "Test Article",
            "category": "AI",
            "tinkering_index": "three"  # Invalid: should be int
        }
        with pytest.raises(ValidationError) as exc_info:
            ArticlePageResult(**data)
        
        assert "tinkering_index" in str(exc_info.value)
