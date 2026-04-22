"""
Intelligent Q&A Agent Module

This module implements the RAG (Retrieval-Augmented Generation) architecture
for the intelligent Q&A agent system.

Core Components:
- QA Agent Controller: Central orchestrator for the intelligent Q&A system
- Data Models: ParsedQuery, ArticleMatch, StructuredResponse, ConversationContext
- Validators: Comprehensive validation for all data structures
- Constants: System-wide constants and configuration values
- Database: High-performance database connection management
- Vector Store: pgvector-based semantic search and embedding storage
"""

from .constants import (
    APIConfig,
    CacheConfig,
    ConfigMappings,
    ContentLimits,
    DefaultValues,
    ErrorCodes,
    FeatureFlags,
    LanguageConstants,
    MessageTemplates,
    MetricsConfig,
    PerformanceLimits,
    RetryConfig,
    ScoringThresholds,
    SecurityConfig,
)
from .database import DatabaseManager, get_database_manager, get_db_connection
from .models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ConversationStatus,
    ConversationTurn,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
    UserProfile,
    validate_embedding_vector,
    validate_query_text,
    validate_similarity_score,
)
from .qa_agent_controller import QAAgentController, QAAgentControllerError
from .validators import (
    ArticleValidator,
    ConversationValidator,
    EmbeddingValidator,
    QueryValidator,
    ResponseValidator,
    UserProfileValidator,
    ValidationError,
    validate_batch_articles,
    validate_batch_queries,
    validate_conversation_continuity,
    validate_response_completeness,
)
from .vector_store import VectorMatch, VectorStore, VectorStoreError, get_vector_store

__all__ = [
    # QA Agent Controller
    "QAAgentController",
    "QAAgentControllerError",
    # Core Models
    "ParsedQuery",
    "ArticleMatch",
    "ArticleSummary",
    "StructuredResponse",
    "ConversationContext",
    "ConversationTurn",
    "UserProfile",
    # Enums
    "QueryIntent",
    "QueryLanguage",
    "ResponseType",
    "ConversationStatus",
    # Validators
    "QueryValidator",
    "ArticleValidator",
    "ResponseValidator",
    "ConversationValidator",
    "UserProfileValidator",
    "EmbeddingValidator",
    "ValidationError",
    # Validation Utilities
    "validate_batch_queries",
    "validate_batch_articles",
    "validate_response_completeness",
    "validate_conversation_continuity",
    "validate_query_text",
    "validate_embedding_vector",
    "validate_similarity_score",
    # Database
    "DatabaseManager",
    "get_database_manager",
    "get_db_connection",
    # Vector Store
    "VectorStore",
    "VectorMatch",
    "VectorStoreError",
    "get_vector_store",
    # Constants
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
