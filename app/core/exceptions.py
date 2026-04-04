from typing import Optional


class TechNewsException(Exception):
    """Base exception for Tech News Agent."""
    pass

class ConfigurationError(TechNewsException):
    """Exception raised for configuration errors."""
    pass

class RSSScrapingError(TechNewsException):
    """Exception raised for errors during RSS/Atom feed scraping."""
    pass

class LLMServiceError(TechNewsException):
    """Exception raised for errors in LLM processing."""
    pass

class SupabaseServiceError(Exception):
    """Supabase 服務層例外"""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None
    ):
        """初始化例外

        Args:
            message: 使用者友善的錯誤訊息
            original_error: 原始例外（如果有）
            context: 額外的上下文資訊
        """
        self.message = message
        self.original_error = original_error
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """格式化錯誤訊息"""
        parts = [self.message]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.original_error:
            parts.append(f"Original error: {self.original_error}")
        return " | ".join(parts)
