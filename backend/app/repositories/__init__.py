"""
Repository Layer

This module provides the repository pattern implementation for data access abstraction.
Repositories encapsulate all database-specific logic and provide a clean interface
for services to interact with data.

Validates: Requirements 3.1, 3.2, 3.4
"""

from app.repositories.analytics_event import AnalyticsEvent, AnalyticsEventRepository
from app.repositories.article import Article, ArticleRepository, PaginationMetadata
from app.repositories.base import BaseRepository, IRepository
from app.repositories.conversation import (
    ConversationFilters,
    ConversationRepository,
    ConversationSummary,
)
from app.repositories.feed import Feed, FeedRepository
from app.repositories.message import MessageRepository, MessageStats
from app.repositories.reading_list import ReadingListItem, ReadingListRepository
from app.repositories.user import User, UserRepository
from app.repositories.user_notification_preferences import (
    UserNotificationPreferences,
    UserNotificationPreferencesRepository,
)
from app.repositories.user_preferences import UserPreferences, UserPreferencesRepository
from app.repositories.user_subscription import UserSubscription, UserSubscriptionRepository

__all__ = [
    "AnalyticsEvent",
    "AnalyticsEventRepository",
    "Article",
    "ArticleRepository",
    "BaseRepository",
    "ConversationFilters",
    "ConversationRepository",
    "ConversationSummary",
    "Feed",
    "FeedRepository",
    "IRepository",
    "MessageRepository",
    "MessageStats",
    "PaginationMetadata",
    "ReadingListItem",
    "ReadingListRepository",
    "User",
    "UserNotificationPreferences",
    "UserNotificationPreferencesRepository",
    "UserPreferences",
    "UserPreferencesRepository",
    "UserRepository",
    "UserSubscription",
    "UserSubscriptionRepository",
]
