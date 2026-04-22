"""
Constants and configuration values for the QA Agent system.

This module defines system-wide constants, limits, and configuration values
used throughout the intelligent Q&A agent implementation.

Requirements: 1.1, 3.1, 4.1, 6.1, 6.2
"""


# System Performance Constants
class PerformanceLimits:
    """Performance limits and thresholds for the QA system."""

    # Response time requirements (Requirements: 6.1, 6.2)
    MAX_SEARCH_TIME_MS = 500  # Maximum search time in milliseconds
    MAX_RESPONSE_TIME_SECONDS = 3.0  # Maximum total response time
    MAX_CONCURRENT_USERS = 50  # Maximum concurrent users supported

    # Database and vector store limits
    MAX_ARTICLES_SUPPORTED = 100000  # Maximum articles in vector store
    MAX_EMBEDDING_DIMENSION = 1536  # OpenAI embedding dimension
    MAX_VECTOR_SEARCH_RESULTS = 100  # Maximum results from vector search

    # Query processing limits
    MAX_QUERY_LENGTH = 2000  # Maximum query length in characters
    MAX_KEYWORDS_PER_QUERY = 20  # Maximum keywords extracted per query
    MAX_FILTERS_PER_QUERY = 10  # Maximum filters per query

    # Response generation limits
    MAX_ARTICLES_PER_RESPONSE = 5  # Maximum articles in structured response
    MAX_INSIGHTS_PER_RESPONSE = 10  # Maximum insights per response
    MAX_RECOMMENDATIONS_PER_RESPONSE = 10  # Maximum recommendations per response

    # Conversation limits
    MAX_CONVERSATION_TURNS = 10  # Maximum turns per conversation
    MAX_CONVERSATION_DURATION_HOURS = 24  # Maximum conversation duration
    CONVERSATION_CLEANUP_DAYS = 7  # Days before conversation cleanup


# Content Processing Constants
class ContentLimits:
    """Limits for content processing and validation."""

    # Article content limits
    MAX_ARTICLE_TITLE_LENGTH = 2000
    MAX_ARTICLE_PREVIEW_LENGTH = 1000
    MAX_ARTICLE_SUMMARY_LENGTH = 500
    MIN_ARTICLE_SUMMARY_LENGTH = 10

    # User profile limits
    MAX_READING_HISTORY_SIZE = 1000
    MAX_PREFERRED_TOPICS = 20
    MAX_QUERY_HISTORY_SIZE = 100
    MAX_SATISFACTION_SCORES = 50

    # Text processing limits
    MAX_INSIGHT_LENGTH = 500
    MAX_RECOMMENDATION_LENGTH = 300
    MAX_TOPIC_NAME_LENGTH = 100
    MAX_KEY_INSIGHTS_PER_ARTICLE = 5


# Scoring and Threshold Constants
class ScoringThresholds:
    """Thresholds for scoring and relevance calculations."""

    # Similarity and relevance thresholds
    MIN_SIMILARITY_THRESHOLD = 0.3  # Minimum similarity for article relevance
    HIGH_SIMILARITY_THRESHOLD = 0.8  # High similarity threshold
    MIN_CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence for responses
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # High confidence threshold

    # Query processing thresholds
    MIN_INTENT_CONFIDENCE = 0.3  # Minimum confidence for intent classification
    CLARIFICATION_THRESHOLD = 0.5  # Below this, request clarification

    # Personalization weights
    SIMILARITY_WEIGHT = 0.7  # Weight for semantic similarity
    KEYWORD_WEIGHT = 0.3  # Weight for keyword matching
    RECENCY_WEIGHT = 0.1  # Weight for article recency
    PERSONALIZATION_WEIGHT = 0.2  # Weight for user preferences


# Language and Localization Constants
class LanguageConstants:
    """Language-specific constants and patterns."""

    # Supported languages
    SUPPORTED_LANGUAGES = ["zh", "en"]
    DEFAULT_LANGUAGE = "zh"

    # Language detection patterns
    CHINESE_CHAR_PATTERN = r"[\u4e00-\u9fff]"
    ENGLISH_CHAR_PATTERN = r"[a-zA-Z]"

    # Text processing patterns
    SENTENCE_SEPARATORS = [".", "。", "!", "！", "?", "？"]
    WORD_SEPARATORS = [" ", "，", ",", "、"]

    # Reading time estimation (words per minute)
    READING_SPEED_WPM = {
        "zh": 250,  # Chinese characters per minute
        "en": 200,  # English words per minute
    }


# Error and Status Constants
class ErrorCodes:
    """Error codes for the QA system."""

    # Query processing errors
    INVALID_QUERY = "INVALID_QUERY"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    LANGUAGE_DETECTION_FAILED = "LANGUAGE_DETECTION_FAILED"
    INTENT_CLASSIFICATION_FAILED = "INTENT_CLASSIFICATION_FAILED"

    # Search and retrieval errors
    VECTOR_STORE_UNAVAILABLE = "VECTOR_STORE_UNAVAILABLE"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"
    NO_RESULTS_FOUND = "NO_RESULTS_FOUND"
    INSUFFICIENT_RESULTS = "INSUFFICIENT_RESULTS"

    # Response generation errors
    RESPONSE_GENERATION_FAILED = "RESPONSE_GENERATION_FAILED"
    LLM_SERVICE_UNAVAILABLE = "LLM_SERVICE_UNAVAILABLE"
    RESPONSE_TIMEOUT = "RESPONSE_TIMEOUT"

    # Conversation errors
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    CONVERSATION_EXPIRED = "CONVERSATION_EXPIRED"
    MAX_TURNS_EXCEEDED = "MAX_TURNS_EXCEEDED"

    # System errors
    DATABASE_ERROR = "DATABASE_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


# Default Values and Templates
class DefaultValues:
    """Default values for various system components."""

    # Query processing defaults
    DEFAULT_CONFIDENCE_SCORE = 0.0
    DEFAULT_SIMILARITY_THRESHOLD = 0.5
    DEFAULT_MAX_RESULTS = 10

    # Response generation defaults
    DEFAULT_RESPONSE_CONFIDENCE = 0.5
    DEFAULT_READING_TIME = 5  # minutes

    # Conversation defaults
    DEFAULT_CONVERSATION_EXPIRY_HOURS = 24
    DEFAULT_CONTEXT_SUMMARY = "New conversation"

    # User profile defaults
    DEFAULT_LANGUAGE_PREFERENCE = "zh"
    DEFAULT_SATISFACTION_SCORE = 0.5


# Message Templates
class MessageTemplates:
    """Templates for system messages and responses."""

    # Error messages
    ERROR_MESSAGES = {
        ErrorCodes.INVALID_QUERY: {
            "zh": "抱歉，我無法理解您的問題。請嘗試重新表達您的問題。",
            "en": "Sorry, I couldn't understand your question. Please try rephrasing it.",
        },
        ErrorCodes.NO_RESULTS_FOUND: {
            "zh": "抱歉，我沒有找到相關的文章。請嘗試使用不同的關鍵詞。",
            "en": "Sorry, I couldn't find any relevant articles. Please try different keywords.",
        },
        ErrorCodes.SEARCH_TIMEOUT: {
            "zh": "搜尋超時，請稍後再試。",
            "en": "Search timed out, please try again later.",
        },
        ErrorCodes.CONVERSATION_EXPIRED: {
            "zh": "對話已過期，請開始新的對話。",
            "en": "Conversation has expired, please start a new conversation.",
        },
    }

    # Clarification requests
    CLARIFICATION_REQUESTS = {
        "zh": ["您能更具體地描述您想了解什麼嗎？", "請提供更多細節，這樣我能更好地幫助您。", "您是想了解哪個特定方面的資訊？"],
        "en": [
            "Could you be more specific about what you'd like to know?",
            "Please provide more details so I can better help you.",
            "Which specific aspect would you like to learn about?",
        ],
    }

    # Follow-up suggestions
    FOLLOW_UP_SUGGESTIONS = {
        "zh": ["您想了解更多相關內容嗎？", "還有其他問題嗎？", "需要我推薦相關文章嗎？"],
        "en": [
            "Would you like to learn more about related topics?",
            "Do you have any other questions?",
            "Would you like me to recommend related articles?",
        ],
    }


# Configuration Mappings
class ConfigMappings:
    """Configuration mappings for various system components."""

    # Intent to query type mapping
    INTENT_QUERY_TYPES = {
        "search": ["semantic", "keyword"],
        "question": ["semantic", "qa"],
        "comparison": ["semantic", "comparative"],
        "summary": ["semantic", "summarization"],
        "recommendation": ["personalized", "semantic"],
        "clarification": ["contextual", "semantic"],
        "exploration": ["semantic", "related"],
    }

    # Category to technical depth mapping
    CATEGORY_DEPTH_MAPPING = {
        "programming": 4,
        "ai": 4,
        "data-science": 4,
        "web-development": 3,
        "mobile-development": 3,
        "devops": 4,
        "security": 4,
        "design": 2,
        "business": 2,
        "general": 1,
    }

    # Language to embedding model mapping
    LANGUAGE_EMBEDDING_MODELS = {
        "zh": "text-embedding-ada-002",
        "en": "text-embedding-ada-002",
        "multilingual": "text-embedding-ada-002",
    }


# Retry and Timeout Configuration
class RetryConfig:
    """Configuration for retry mechanisms and timeouts."""

    # Database retry configuration
    DB_MAX_RETRIES = 3
    DB_RETRY_DELAY_MS = 100
    DB_RETRY_BACKOFF_MULTIPLIER = 2.0

    # LLM service retry configuration
    LLM_MAX_RETRIES = 3
    LLM_RETRY_DELAY_MS = 500
    LLM_RETRY_BACKOFF_MULTIPLIER = 1.5

    # Vector store retry configuration
    VECTOR_MAX_RETRIES = 2
    VECTOR_RETRY_DELAY_MS = 200

    # Timeout configurations
    DATABASE_TIMEOUT_SECONDS = 10.0
    LLM_TIMEOUT_SECONDS = 30.0
    VECTOR_SEARCH_TIMEOUT_SECONDS = 5.0
    EMBEDDING_TIMEOUT_SECONDS = 10.0


# Cache Configuration
class CacheConfig:
    """Configuration for caching mechanisms."""

    # Query result cache
    QUERY_CACHE_TTL_SECONDS = 300  # 5 minutes
    QUERY_CACHE_MAX_SIZE = 1000

    # Embedding cache
    EMBEDDING_CACHE_TTL_SECONDS = 3600  # 1 hour
    EMBEDDING_CACHE_MAX_SIZE = 10000

    # User profile cache
    PROFILE_CACHE_TTL_SECONDS = 1800  # 30 minutes
    PROFILE_CACHE_MAX_SIZE = 500

    # Conversation cache
    CONVERSATION_CACHE_TTL_SECONDS = 7200  # 2 hours
    CONVERSATION_CACHE_MAX_SIZE = 1000


# Monitoring and Metrics
class MetricsConfig:
    """Configuration for monitoring and metrics collection."""

    # Performance metrics
    TRACK_RESPONSE_TIMES = True
    TRACK_SEARCH_ACCURACY = True
    TRACK_USER_SATISFACTION = True

    # Metric collection intervals
    METRICS_COLLECTION_INTERVAL_SECONDS = 60
    METRICS_RETENTION_DAYS = 30

    # Alert thresholds
    RESPONSE_TIME_ALERT_THRESHOLD_MS = 5000
    ERROR_RATE_ALERT_THRESHOLD = 0.05  # 5%
    SEARCH_ACCURACY_ALERT_THRESHOLD = 0.7  # 70%


# Feature Flags
class FeatureFlags:
    """Feature flags for enabling/disabling system features."""

    # Core features
    ENABLE_SEMANTIC_SEARCH = True
    ENABLE_KEYWORD_SEARCH = True
    ENABLE_HYBRID_SEARCH = True

    # Advanced features
    ENABLE_PERSONALIZATION = True
    ENABLE_CONVERSATION_CONTEXT = True
    ENABLE_QUERY_EXPANSION = True
    ENABLE_RESULT_RERANKING = True

    # Experimental features
    ENABLE_QUERY_SUGGESTIONS = False
    ENABLE_AUTOMATIC_SUMMARIZATION = False
    ENABLE_MULTILINGUAL_SEARCH = False

    # Monitoring features
    ENABLE_DETAILED_LOGGING = True
    ENABLE_PERFORMANCE_TRACKING = True
    ENABLE_USER_ANALYTICS = True


# API Configuration
class APIConfig:
    """Configuration for API endpoints and responses."""

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_BURST_SIZE = 10

    # Response formatting
    INCLUDE_METADATA_IN_RESPONSES = True
    INCLUDE_DEBUG_INFO = False  # Set to True in development

    # CORS configuration
    ALLOWED_ORIGINS = ["*"]  # Configure appropriately for production
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]
    ALLOWED_HEADERS = ["*"]


# Security Configuration
class SecurityConfig:
    """Security-related configuration constants."""

    # Input validation
    MAX_INPUT_LENGTH = 10000
    ALLOWED_FILE_TYPES = [".txt", ".md", ".pdf"]

    # Rate limiting
    MAX_REQUESTS_PER_USER_PER_HOUR = 1000
    MAX_CONVERSATIONS_PER_USER = 10

    # Data retention
    CONVERSATION_RETENTION_DAYS = 30
    QUERY_LOG_RETENTION_DAYS = 90
    USER_DATA_RETENTION_DAYS = 365

    # Encryption
    ENCRYPT_CONVERSATION_DATA = True
    ENCRYPT_QUERY_LOGS = True
    ENCRYPT_USER_PROFILES = False  # Profile data is not sensitive


# Export all constants for easy importing
__all__ = [
    "PerformanceLimits",
    "ContentLimits",
    "ScoringThresholds",
    "LanguageConstants",
    "ErrorCodes",
    "DefaultValues",
    "MessageTemplates",
    "ConfigMappings",
    "RetryConfig",
    "CacheConfig",
    "MetricsConfig",
    "FeatureFlags",
    "APIConfig",
    "SecurityConfig",
]
