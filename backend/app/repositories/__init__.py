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
from app.repositories.feed import Feed, FeedRepository
from app.repositories.reading_list import ReadingListItem, ReadingListRepository
from app.repositories.user import User, UserRepository
from app.repositories.user_preferences import UserPreferences, UserPreferencesRepository
from app.repositories.user_subscription import UserSubscription, UserSubscriptionRepository

__all__ = [
    "AnalyticsEvent",
    "AnalyticsEventRepository",
    "Article",
    "ArticleRepository",
    "BaseRepository",
    "Feed",
    "FeedRepository",
    "IRepository",
    "PaginationMetadata",
    "ReadingListItem",
    "ReadingListRepository",
    "User",
    "UserPreferences",
    "UserPreferencesRepository",
    "UserRepository",
    "UserSubscription",
    "UserSubscriptionRepository",
]
