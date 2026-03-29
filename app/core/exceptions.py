class TechNewsException(Exception):
    """Base exception for Tech News Agent."""
    pass

class ConfigurationError(TechNewsException):
    """Exception raised for configuration errors."""
    pass

class NotionServiceError(TechNewsException):
    """Exception raised for errors in the Notion Service."""
    pass

class RSSScrapingError(TechNewsException):
    """Exception raised for errors during RSS/Atom feed scraping."""
    pass

class LLMServiceError(TechNewsException):
    """Exception raised for errors in LLM processing."""
    pass
