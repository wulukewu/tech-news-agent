"""
Validation utilities for QA Agent data models.

This module provides comprehensive validation functions for all QA agent data structures,
ensuring data integrity and consistency across the system.

Requirements: 1.1, 3.1, 4.1
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    StructuredResponse,
    UserProfile,
)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class QueryValidator:
    """Validator for query-related data structures."""

    @staticmethod
    def validate_query_text(query: str) -> bool:
        """
        Validate query text format and content.

        Requirements: 1.1, 1.2
        """
        if not query or not isinstance(query, str):
            return False

        query = query.strip()

        # Check length constraints
        if not (1 <= len(query) <= 2000):
            return False

        # Check for meaningful content (not just punctuation/whitespace)
        has_letters = bool(re.search(r"[a-zA-Z\u4e00-\u9fff]", query))
        if not has_letters:
            return False

        # Check for suspicious patterns (too many repeated characters)
        if re.search(r"(.)\1{10,}", query):  # More than 10 repeated characters
            return False

        return True

    @staticmethod
    def validate_keywords(keywords: List[str]) -> bool:
        """Validate extracted keywords list."""
        if not isinstance(keywords, list):
            return False

        if len(keywords) > 20:  # Too many keywords
            return False

        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                return False

            if len(keyword) > 100:  # Individual keyword too long
                return False

        return True

    @staticmethod
    def validate_language_detection(language: str, query: str) -> bool:
        """Validate language detection accuracy."""
        if language not in [lang.value for lang in QueryLanguage]:
            return False

        # Basic heuristics for language validation
        if language == QueryLanguage.CHINESE:
            # Should contain Chinese characters
            return bool(re.search(r"[\u4e00-\u9fff]", query))
        elif language == QueryLanguage.ENGLISH:
            # Should contain English letters
            return bool(re.search(r"[a-zA-Z]", query))

        return True  # AUTO_DETECT is always valid

    @staticmethod
    def validate_intent_confidence(intent: QueryIntent, confidence: float) -> bool:
        """Validate intent classification confidence."""
        if not (0.0 <= confidence <= 1.0):
            return False

        # Unknown intent should have low confidence
        if intent == QueryIntent.UNKNOWN and confidence > 0.5:
            return False

        # Known intents should have reasonable confidence
        if intent != QueryIntent.UNKNOWN and confidence < 0.1:
            return False

        return True

    @staticmethod
    def validate_parsed_query(parsed_query: ParsedQuery) -> List[str]:
        """
        Comprehensive validation of ParsedQuery object.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Validate query text
        if not QueryValidator.validate_query_text(parsed_query.original_query):
            errors.append("Invalid query text format or content")

        # Validate keywords
        if not QueryValidator.validate_keywords(parsed_query.keywords):
            errors.append("Invalid keywords list")

        # Validate language detection
        if not QueryValidator.validate_language_detection(
            parsed_query.language, parsed_query.original_query
        ):
            errors.append("Language detection inconsistent with query content")

        # Validate intent confidence
        if not QueryValidator.validate_intent_confidence(
            parsed_query.intent, parsed_query.confidence
        ):
            errors.append("Intent confidence score inconsistent with classification")

        # Validate filters structure
        if parsed_query.filters:
            filter_errors = QueryValidator.validate_filters(parsed_query.filters)
            errors.extend(filter_errors)

        return errors

    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> List[str]:
        """Validate query filters structure."""
        errors = []

        if "time_range" in filters:
            time_range = filters["time_range"]
            if not isinstance(time_range, dict):
                errors.append("time_range filter must be a dictionary")
            elif "start" not in time_range or "end" not in time_range:
                errors.append("time_range filter must have 'start' and 'end' keys")
            else:
                try:
                    start = datetime.fromisoformat(time_range["start"])
                    end = datetime.fromisoformat(time_range["end"])
                    if start >= end:
                        errors.append("time_range start must be before end")
                except (ValueError, TypeError):
                    errors.append("time_range values must be valid ISO datetime strings")

        if "categories" in filters:
            categories = filters["categories"]
            if not isinstance(categories, list):
                errors.append("categories filter must be a list")
            elif len(categories) > 10:
                errors.append("categories filter cannot have more than 10 items")
            elif not all(isinstance(cat, str) and cat.strip() for cat in categories):
                errors.append("categories filter must contain non-empty strings")

        if "technical_depth" in filters:
            depth = filters["technical_depth"]
            if isinstance(depth, int):
                if not (1 <= depth <= 5):
                    errors.append("technical_depth must be between 1 and 5")
            elif isinstance(depth, str):
                if depth not in ["beginner", "intermediate", "advanced", "expert"]:
                    errors.append("technical_depth string must be valid level")
            else:
                errors.append("technical_depth must be integer (1-5) or string level")

        return errors


class ArticleValidator:
    """Validator for article-related data structures."""

    @staticmethod
    def validate_similarity_score(score: float) -> bool:
        """Validate similarity score range and type."""
        return isinstance(score, (int, float)) and 0.0 <= score <= 1.0

    @staticmethod
    def validate_article_match(article_match: ArticleMatch) -> List[str]:
        """
        Comprehensive validation of ArticleMatch object.

        Requirements: 2.2, 2.3
        """
        errors = []

        # Validate similarity scores
        if not ArticleValidator.validate_similarity_score(article_match.similarity_score):
            errors.append("Invalid similarity_score: must be float between 0.0 and 1.0")

        if not ArticleValidator.validate_similarity_score(article_match.keyword_score):
            errors.append("Invalid keyword_score: must be float between 0.0 and 1.0")

        if not ArticleValidator.validate_similarity_score(article_match.combined_score):
            errors.append("Invalid combined_score: must be float between 0.0 and 1.0")

        # Validate content preview length
        if len(article_match.content_preview) > 1000:
            errors.append("content_preview exceeds maximum length of 1000 characters")

        # Validate title length
        if not (1 <= len(article_match.title) <= 2000):
            errors.append("title must be between 1 and 2000 characters")

        # Validate metadata structure
        if article_match.metadata and not isinstance(article_match.metadata, dict):
            errors.append("metadata must be a dictionary")

        # Validate publication date
        if article_match.published_at and article_match.published_at > datetime.utcnow():
            errors.append("published_at cannot be in the future")

        return errors

    @staticmethod
    def validate_article_summary(article_summary: ArticleSummary) -> List[str]:
        """
        Comprehensive validation of ArticleSummary object.

        Requirements: 3.2, 3.3
        """
        errors = []

        # Validate summary content
        summary = article_summary.summary.strip()
        if not (10 <= len(summary) <= 500):
            errors.append("summary must be between 10 and 500 characters")

        # Validate summary structure (should be 2-3 sentences)
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        if len(sentences) < 2:
            errors.append("summary must contain at least 2 sentences")
        elif len(sentences) > 4:
            errors.append("summary should not exceed 4 sentences")

        # Validate relevance score
        if not ArticleValidator.validate_similarity_score(article_summary.relevance_score):
            errors.append("Invalid relevance_score: must be float between 0.0 and 1.0")

        # Validate reading time
        if article_summary.reading_time < 1:
            errors.append("reading_time must be at least 1 minute")
        elif article_summary.reading_time > 120:  # 2 hours seems reasonable max
            errors.append("reading_time seems unreasonably high (>120 minutes)")

        # Validate key insights
        if len(article_summary.key_insights) > 5:
            errors.append("key_insights cannot have more than 5 items")

        for insight in article_summary.key_insights:
            if not isinstance(insight, str) or not insight.strip():
                errors.append("key_insights must contain non-empty strings")
                break
            if len(insight) > 200:
                errors.append("individual key_insights cannot exceed 200 characters")
                break

        return errors


class ResponseValidator:
    """Validator for response-related data structures."""

    @staticmethod
    def validate_structured_response(response: StructuredResponse) -> List[str]:
        """
        Comprehensive validation of StructuredResponse object.

        Requirements: 3.1, 3.2, 3.3, 3.5
        """
        errors = []

        # Validate articles count and order
        if len(response.articles) > 5:
            errors.append("articles list cannot contain more than 5 items")

        # Check if articles are sorted by relevance
        if len(response.articles) > 1:
            for i in range(len(response.articles) - 1):
                if response.articles[i].relevance_score < response.articles[i + 1].relevance_score:
                    errors.append("articles must be sorted by relevance_score in descending order")
                    break

        # Validate individual articles
        for i, article in enumerate(response.articles):
            article_errors = ArticleValidator.validate_article_summary(article)
            for error in article_errors:
                errors.append(f"Article {i + 1}: {error}")

        # Validate insights
        if len(response.insights) > 10:
            errors.append("insights list cannot contain more than 10 items")

        for insight in response.insights:
            if not isinstance(insight, str) or not insight.strip():
                errors.append("insights must contain non-empty strings")
                break
            if len(insight) > 500:
                errors.append("individual insights cannot exceed 500 characters")
                break

        # Validate recommendations
        if len(response.recommendations) > 10:
            errors.append("recommendations list cannot contain more than 10 items")

        for rec in response.recommendations:
            if not isinstance(rec, str) or not rec.strip():
                errors.append("recommendations must contain non-empty strings")
                break
            if len(rec) > 300:
                errors.append("individual recommendations cannot exceed 300 characters")
                break

        # Validate response time
        if response.response_time < 0:
            errors.append("response_time cannot be negative")
        elif response.response_time > 30:  # 30 seconds seems like a reasonable max
            errors.append("response_time seems unreasonably high (>30 seconds)")

        # Validate confidence score
        if not (0.0 <= response.confidence <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")

        return errors


class ConversationValidator:
    """Validator for conversation-related data structures."""

    @staticmethod
    def validate_conversation_context(context: ConversationContext) -> List[str]:
        """
        Comprehensive validation of ConversationContext object.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        errors = []

        # Validate turns count
        if len(context.turns) > 10:
            errors.append("conversation cannot have more than 10 turns")

        # Validate turn numbering
        for i, turn in enumerate(context.turns):
            expected_number = i + 1
            if turn.turn_number != expected_number:
                errors.append(f"turn {i + 1} has incorrect turn_number: {turn.turn_number}")

        # Validate timestamps are in order
        if len(context.turns) > 1:
            for i in range(len(context.turns) - 1):
                if context.turns[i].timestamp > context.turns[i + 1].timestamp:
                    errors.append("turn timestamps must be in chronological order")
                    break

        # Validate conversation timestamps
        if context.created_at > context.last_updated:
            errors.append("created_at cannot be after last_updated")

        if context.expires_at and context.expires_at <= context.created_at:
            errors.append("expires_at must be after created_at")

        # Validate current topic
        if context.current_topic and len(context.current_topic) > 200:
            errors.append("current_topic cannot exceed 200 characters")

        return errors

    @staticmethod
    def validate_conversation_turn_query(query: str) -> bool:
        """Validate conversation turn query."""
        return QueryValidator.validate_query_text(query)


class UserProfileValidator:
    """Validator for user profile data structures."""

    @staticmethod
    def validate_user_profile(profile: UserProfile) -> List[str]:
        """
        Comprehensive validation of UserProfile object.

        Requirements: 8.1, 8.2, 8.3
        """
        errors = []

        # Validate reading history size
        if len(profile.reading_history) > 1000:
            errors.append("reading_history cannot exceed 1000 items")

        # Validate preferred topics
        if len(profile.preferred_topics) > 20:
            errors.append("preferred_topics cannot exceed 20 items")

        for topic in profile.preferred_topics:
            if not isinstance(topic, str) or not topic.strip():
                errors.append("preferred_topics must contain non-empty strings")
                break
            if len(topic) > 100:
                errors.append("individual preferred_topics cannot exceed 100 characters")
                break

        # Validate query history size
        if len(profile.query_history) > 100:
            errors.append("query_history cannot exceed 100 items")

        # Validate satisfaction scores
        if len(profile.satisfaction_scores) > 50:
            errors.append("satisfaction_scores cannot exceed 50 items")

        for score in profile.satisfaction_scores:
            if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                errors.append("satisfaction_scores must be floats between 0.0 and 1.0")
                break

        # Validate timestamps
        if profile.created_at > profile.updated_at:
            errors.append("created_at cannot be after updated_at")

        return errors


class EmbeddingValidator:
    """Validator for embedding vectors and related operations."""

    @staticmethod
    def validate_embedding_vector(embedding: List[float], expected_dim: int = 1536) -> bool:
        """
        Validate embedding vector format and dimensions.

        Requirements: 7.1, 7.4
        """
        if not isinstance(embedding, list):
            return False

        # Check dimension
        if len(embedding) != expected_dim:
            return False

        # Check for valid float values
        try:
            for val in embedding:
                if not isinstance(val, (int, float)):
                    return False
                # Check for reasonable range (embeddings are typically normalized)
                if not (-2.0 <= val <= 2.0):
                    return False
        except (TypeError, ValueError):
            return False

        return True

    @staticmethod
    def validate_vector_similarity(similarity: float) -> bool:
        """Validate vector similarity score."""
        return isinstance(similarity, (int, float)) and 0.0 <= similarity <= 1.0


# Utility functions for batch validation


def validate_batch_queries(queries: List[str]) -> Dict[int, List[str]]:
    """
    Validate a batch of queries and return errors by index.

    Returns:
        Dictionary mapping query index to list of validation errors
    """
    errors = {}

    for i, query in enumerate(queries):
        if not QueryValidator.validate_query_text(query):
            errors[i] = ["Invalid query text format or content"]

    return errors


def validate_batch_articles(articles: List[ArticleMatch]) -> Dict[int, List[str]]:
    """
    Validate a batch of article matches and return errors by index.

    Returns:
        Dictionary mapping article index to list of validation errors
    """
    errors = {}

    for i, article in enumerate(articles):
        article_errors = ArticleValidator.validate_article_match(article)
        if article_errors:
            errors[i] = article_errors

    return errors


def validate_response_completeness(response: StructuredResponse) -> bool:
    """
    Validate that a structured response contains sufficient content.

    Requirements: 3.1, 3.2
    """
    # Must have at least one article
    if not response.articles:
        return False

    # Must have reasonable confidence
    if response.confidence < 0.3:
        return False

    # Articles must have summaries
    for article in response.articles:
        if not article.summary or len(article.summary.strip()) < 10:
            return False

    return True


def validate_conversation_continuity(context: ConversationContext, new_query: str) -> bool:
    """
    Validate that a new query is appropriate for the conversation context.

    Requirements: 4.2, 4.3
    """
    # Basic query validation
    if not QueryValidator.validate_query_text(new_query):
        return False

    # If conversation is expired or closed, new queries are not valid
    if context.is_expired() or not context.is_active():
        return False

    # Check for reasonable time gap (no more than 24 hours since last turn)
    if context.turns:
        last_turn = context.turns[-1]
        time_gap = datetime.utcnow() - last_turn.timestamp
        if time_gap > timedelta(hours=24):
            return False

    return True
