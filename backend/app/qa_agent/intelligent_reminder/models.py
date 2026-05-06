"""
Models for the Intelligent Reminder Agent system.
"""
from datetime import datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    PREREQUISITE = "prerequisite"
    FOLLOW_UP = "follow_up"
    RELATED = "related"
    UPDATE = "update"


class VersionType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class ReminderType(str, Enum):
    ARTICLE_RELATION = "article_relation"
    VERSION_UPDATE = "version_update"
    LEARNING_PATH = "learning_path"


class ReminderChannel(str, Enum):
    DISCORD = "discord"
    WEB = "web"
    EMAIL = "email"


class ReminderStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    FAILED = "failed"


class ReminderFrequency(str, Enum):
    SMART = "smart"
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"


class PatternType(str, Enum):
    READING_TIME = "reading_time"
    ACTIVE_HOURS = "active_hours"
    RESPONSE_RATE = "response_rate"


class ArticleRelationship(BaseModel):
    id: UUID
    source_article_id: UUID
    target_article_id: UUID
    relationship_type: RelationshipType
    confidence_score: float = Field(ge=0, le=1)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TechnologyVersion(BaseModel):
    id: UUID
    technology_name: str
    current_version: str
    previous_version: Optional[str] = None
    version_type: VersionType
    release_date: Optional[datetime] = None
    release_notes: Optional[str] = None
    importance_level: int = Field(ge=1, le=5)
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReminderSettings(BaseModel):
    id: UUID
    user_id: UUID
    enabled: bool = True
    max_daily_reminders: int = Field(default=5, ge=0, le=20)
    preferred_channels: List[ReminderChannel] = Field(default=[ReminderChannel.DISCORD])
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    timezone: str = "UTC"
    reminder_frequency: ReminderFrequency = ReminderFrequency.SMART
    created_at: datetime
    updated_at: datetime


class ReminderContext(BaseModel):
    """Context information for a reminder"""

    title: str
    description: str
    related_articles: List[Dict[str, Any]] = Field(default_factory=list)
    version_info: Optional[Dict[str, Any]] = None
    reading_time_estimate: Optional[int] = None  # in minutes
    priority_score: float = Field(default=0.5, ge=0, le=1)
    action_url: Optional[str] = None


class ReminderLog(BaseModel):
    id: UUID
    user_id: UUID
    reminder_type: ReminderType
    content_id: Optional[UUID] = None
    reminder_context: ReminderContext
    sent_at: datetime
    channel: ReminderChannel
    status: ReminderStatus = ReminderStatus.SENT
    response_time: Optional[int] = None  # seconds
    effectiveness_score: Optional[float] = Field(None, ge=0, le=1)
    created_at: datetime
    updated_at: datetime


class UserBehaviorPattern(BaseModel):
    id: UUID
    user_id: UUID
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    confidence_level: float = Field(ge=0, le=1)
    last_updated: datetime
    created_at: datetime


class UserProfile(BaseModel):
    """Extended user profile for intelligent reminders"""

    user_id: UUID
    active_hours: List[int] = Field(default_factory=list)  # Hours 0-23
    preferred_reading_time: Optional[int] = None  # minutes
    response_rate_by_type: Dict[str, float] = Field(default_factory=dict)
    ignored_reminder_count: int = 0
    last_reminder_sent: Optional[datetime] = None
    learning_velocity: float = 0.5  # How quickly user consumes content
    technical_interests: List[str] = Field(default_factory=list)


class TimingDecision(BaseModel):
    """Decision about when to send a reminder"""

    should_send: bool
    optimal_time: Optional[datetime] = None
    confidence: float = Field(ge=0, le=1)
    reason: str
    delay_until: Optional[datetime] = None


class ReminderEffectivenessReport(BaseModel):
    """Weekly effectiveness report"""

    user_id: UUID
    week_start: datetime
    total_sent: int
    total_clicked: int
    total_read: int
    total_dismissed: int
    click_rate: float = Field(ge=0, le=1)
    read_rate: float = Field(ge=0, le=1)
    average_response_time: Optional[float] = None  # seconds
    most_effective_channel: Optional[ReminderChannel] = None
    most_effective_time: Optional[int] = None  # hour of day
    recommendations: List[str] = Field(default_factory=list)
