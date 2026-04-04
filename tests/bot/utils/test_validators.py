"""
測試資料驗證模組

**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**
"""

import pytest
from uuid import uuid4

from app.bot.utils.validators import (
    validate_feed_url,
    validate_rating,
    validate_status,
    validate_uuid,
    truncate_text,
    sanitize_title,
    sanitize_summary,
    validate_and_sanitize_feed_data,
    MAX_TITLE_LENGTH,
    MAX_SUMMARY_LENGTH,
)


class TestValidateFeedUrl:
    """測試 feed URL 驗證"""
    
    def test_valid_http_url(self):
        """測試有效的 HTTP URL"""
        is_valid, error = validate_feed_url("http://example.com/feed.xml")
        assert is_valid is True
        assert error == ""
    
    def test_valid_https_url(self):
        """測試有效的 HTTPS URL"""
        is_valid, error = validate_feed_url("https://example.com/feed.xml")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_with_port(self):
        """測試帶端口的 URL"""
        is_valid, error = validate_feed_url("https://example.com:8080/feed.xml")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_with_path(self):
        """測試帶路徑的 URL"""
        is_valid, error = validate_feed_url("https://example.com/path/to/feed.xml")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_url_no_protocol(self):
        """測試無協議的 URL"""
        is_valid, error = validate_feed_url("example.com/feed.xml")
        assert is_valid is False
        assert "無效" in error
    
    def test_invalid_url_ftp_protocol(self):
        """測試 FTP 協議（不支援）"""
        is_valid, error = validate_feed_url("ftp://example.com/feed.xml")
        assert is_valid is False
        assert "無效" in error
    
    def test_invalid_url_empty(self):
        """測試空 URL"""
        is_valid, error = validate_feed_url("")
        assert is_valid is False
        assert "不能為空" in error
    
    def test_invalid_url_none(self):
        """測試 None URL"""
        is_valid, error = validate_feed_url(None)
        assert is_valid is False
        assert "不能為空" in error
    
    def test_invalid_url_too_long(self):
        """測試過長的 URL"""
        long_url = "https://example.com/" + "a" * 2100
        is_valid, error = validate_feed_url(long_url)
        assert is_valid is False
        assert "長度超過限制" in error


class TestValidateRating:
    """測試評分驗證"""
    
    def test_valid_rating_1(self):
        """測試有效評分 1"""
        is_valid, error = validate_rating(1)
        assert is_valid is True
        assert error == ""
    
    def test_valid_rating_5(self):
        """測試有效評分 5"""
        is_valid, error = validate_rating(5)
        assert is_valid is True
        assert error == ""
    
    def test_valid_rating_3(self):
        """測試有效評分 3"""
        is_valid, error = validate_rating(3)
        assert is_valid is True
        assert error == ""
    
    def test_invalid_rating_0(self):
        """測試無效評分 0"""
        is_valid, error = validate_rating(0)
        assert is_valid is False
        assert "1 到 5 之間" in error
    
    def test_invalid_rating_6(self):
        """測試無效評分 6"""
        is_valid, error = validate_rating(6)
        assert is_valid is False
        assert "1 到 5 之間" in error
    
    def test_invalid_rating_negative(self):
        """測試負數評分"""
        is_valid, error = validate_rating(-1)
        assert is_valid is False
        assert "1 到 5 之間" in error
    
    def test_invalid_rating_string(self):
        """測試字串評分"""
        is_valid, error = validate_rating("3")
        assert is_valid is False
        assert "必須是整數" in error
    
    def test_invalid_rating_float(self):
        """測試浮點數評分"""
        is_valid, error = validate_rating(3.5)
        assert is_valid is False
        assert "必須是整數" in error


class TestValidateStatus:
    """測試狀態驗證"""
    
    def test_valid_status_unread(self):
        """測試有效狀態 Unread"""
        is_valid, error = validate_status("Unread")
        assert is_valid is True
        assert error == ""
    
    def test_valid_status_read(self):
        """測試有效狀態 Read"""
        is_valid, error = validate_status("Read")
        assert is_valid is True
        assert error == ""
    
    def test_valid_status_archived(self):
        """測試有效狀態 Archived"""
        is_valid, error = validate_status("Archived")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_status_lowercase(self):
        """測試小寫狀態（無效）"""
        is_valid, error = validate_status("unread")
        assert is_valid is False
        assert "必須是以下之一" in error
    
    def test_invalid_status_random(self):
        """測試隨機狀態"""
        is_valid, error = validate_status("Invalid")
        assert is_valid is False
        assert "必須是以下之一" in error
    
    def test_invalid_status_empty(self):
        """測試空狀態"""
        is_valid, error = validate_status("")
        assert is_valid is False
        assert "必須是以下之一" in error
    
    def test_invalid_status_number(self):
        """測試數字狀態"""
        is_valid, error = validate_status(123)
        assert is_valid is False
        assert "必須是字串" in error


class TestValidateUuid:
    """測試 UUID 驗證"""
    
    def test_valid_uuid(self):
        """測試有效的 UUID"""
        valid_uuid = str(uuid4())
        is_valid, error = validate_uuid(valid_uuid)
        assert is_valid is True
        assert error == ""
    
    def test_valid_uuid_with_hyphens(self):
        """測試帶連字符的 UUID"""
        is_valid, error = validate_uuid("123e4567-e89b-12d3-a456-426614174000")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_uuid_format(self):
        """測試無效的 UUID 格式"""
        is_valid, error = validate_uuid("not-a-uuid")
        assert is_valid is False
        assert "格式無效" in error
    
    def test_invalid_uuid_empty(self):
        """測試空 UUID"""
        is_valid, error = validate_uuid("")
        assert is_valid is False
        assert "不能為空" in error
    
    def test_invalid_uuid_none(self):
        """測試 None UUID"""
        is_valid, error = validate_uuid(None)
        assert is_valid is False
        assert "不能為空" in error
    
    def test_invalid_uuid_number(self):
        """測試數字 UUID"""
        is_valid, error = validate_uuid(12345)
        assert is_valid is False
        assert "不能為空" in error


class TestTruncateText:
    """測試文字截斷"""
    
    def test_truncate_short_text(self):
        """測試短文字不被截斷"""
        text = "Short text"
        result = truncate_text(text, 100)
        assert result == text
    
    def test_truncate_long_text(self):
        """測試長文字被截斷"""
        text = "a" * 150
        result = truncate_text(text, 100)
        assert len(result) == 100
        assert result == "a" * 100
    
    def test_truncate_exact_length(self):
        """測試剛好長度的文字"""
        text = "a" * 100
        result = truncate_text(text, 100)
        assert result == text
    
    def test_truncate_empty_text(self):
        """測試空文字"""
        result = truncate_text("", 100)
        assert result == ""
    
    def test_truncate_none_text(self):
        """測試 None 文字"""
        result = truncate_text(None, 100)
        assert result is None


class TestSanitizeTitle:
    """測試標題清理"""
    
    def test_sanitize_normal_title(self):
        """測試正常標題"""
        title = "Normal Title"
        result = sanitize_title(title)
        assert result == title
    
    def test_sanitize_title_with_whitespace(self):
        """測試帶空白的標題"""
        title = "  Title with spaces  "
        result = sanitize_title(title)
        assert result == "Title with spaces"
    
    def test_sanitize_long_title(self):
        """測試過長的標題"""
        title = "a" * (MAX_TITLE_LENGTH + 100)
        result = sanitize_title(title)
        assert len(result) == MAX_TITLE_LENGTH
    
    def test_sanitize_empty_title(self):
        """測試空標題"""
        result = sanitize_title("")
        assert result == ""
    
    def test_sanitize_none_title(self):
        """測試 None 標題"""
        result = sanitize_title(None)
        assert result == ""


class TestSanitizeSummary:
    """測試摘要清理"""
    
    def test_sanitize_normal_summary(self):
        """測試正常摘要"""
        summary = "Normal summary text"
        result = sanitize_summary(summary)
        assert result == summary
    
    def test_sanitize_summary_with_whitespace(self):
        """測試帶空白的摘要"""
        summary = "  Summary with spaces  "
        result = sanitize_summary(summary)
        assert result == "Summary with spaces"
    
    def test_sanitize_long_summary(self):
        """測試過長的摘要"""
        summary = "a" * (MAX_SUMMARY_LENGTH + 100)
        result = sanitize_summary(summary)
        assert len(result) == MAX_SUMMARY_LENGTH
    
    def test_sanitize_empty_summary(self):
        """測試空摘要"""
        result = sanitize_summary("")
        assert result == ""
    
    def test_sanitize_none_summary(self):
        """測試 None 摘要"""
        result = sanitize_summary(None)
        assert result == ""


class TestValidateAndSanitizeFeedData:
    """測試 feed 資料驗證與清理"""
    
    def test_valid_feed_data(self):
        """測試有效的 feed 資料"""
        is_valid, data, error = validate_and_sanitize_feed_data(
            "Test Feed",
            "https://example.com/feed.xml",
            "Tech"
        )
        assert is_valid is True
        assert data["name"] == "Test Feed"
        assert data["url"] == "https://example.com/feed.xml"
        assert data["category"] == "Tech"
        assert error == ""
    
    def test_feed_data_with_whitespace(self):
        """測試帶空白的 feed 資料"""
        is_valid, data, error = validate_and_sanitize_feed_data(
            "  Test Feed  ",
            "  https://example.com/feed.xml  ",
            "  Tech  "
        )
        assert is_valid is True
        assert data["name"] == "Test Feed"
        assert data["url"] == "https://example.com/feed.xml"
        assert data["category"] == "Tech"
    
    def test_feed_data_empty_category(self):
        """測試空分類（應使用預設值）"""
        is_valid, data, error = validate_and_sanitize_feed_data(
            "Test Feed",
            "https://example.com/feed.xml",
            ""
        )
        assert is_valid is True
        assert data["category"] == "未分類"
    
    def test_feed_data_invalid_url(self):
        """測試無效的 URL"""
        is_valid, data, error = validate_and_sanitize_feed_data(
            "Test Feed",
            "not-a-url",
            "Tech"
        )
        assert is_valid is False
        assert "URL 格式無效" in error
    
    def test_feed_data_empty_name(self):
        """測試空名稱"""
        is_valid, data, error = validate_and_sanitize_feed_data(
            "",
            "https://example.com/feed.xml",
            "Tech"
        )
        assert is_valid is False
        assert "名稱不能為空" in error
    
    def test_feed_data_long_name(self):
        """測試過長的名稱（應被截斷）"""
        long_name = "a" * (MAX_TITLE_LENGTH + 100)
        is_valid, data, error = validate_and_sanitize_feed_data(
            long_name,
            "https://example.com/feed.xml",
            "Tech"
        )
        assert is_valid is True
        assert len(data["name"]) == MAX_TITLE_LENGTH
