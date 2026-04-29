"""
Core Data Models for Intelligent Q&A Agent

This module implements the core data structures for the RAG-based Q&A system,
including query parsing, article matching, response generation, and conversation management.

Requirements: 1.1, 3.1, 4.1
"""

from enum import Enum


class QueryIntent(str, Enum):
    """
    Enumeration of possible query intents for natural language processing.

    Requirements: 1.1, 1.2
    """

    SEARCH = "search"  # General search query
    QUESTION = "question"  # Direct question
    COMPARISON = "comparison"  # Comparing topics/articles
    SUMMARY = "summary"  # Request for summary
    RECOMMENDATION = "recommendation"  # Request for recommendations
    CLARIFICATION = "clarification"  # Follow-up clarification
    EXPLORATION = "exploration"  # Deep dive into topic
    UNKNOWN = "unknown"  # Unable to determine intent


class QueryLanguage(str, Enum):
    """
    Supported languages for query processing.

    Requirements: 1.2
    """

    CHINESE = "zh"
    ENGLISH = "en"
    AUTO_DETECT = "auto"


class ResponseType(str, Enum):
    """
    Types of responses the system can generate.

    Requirements: 3.1, 9.2, 9.4
    """

    STRUCTURED = "structured"  # Full structured response
    SIMPLE = "simple"  # Simple text response
    ERROR = "error"  # Error response
    CLARIFICATION = "clarification"  # Clarification request
    PARTIAL = "partial"  # Partial results due to timeout (Requirement 9.4)
    SEARCH_RESULTS = "search_results"  # Search results fallback (Requirement 9.2)


class ConversationStatus(str, Enum):
    """
    Status of conversation sessions.

    Requirements: 4.1
    """

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CLOSED = "closed"
