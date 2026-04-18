"""
Notification Pydantic Schemas

This module defines the Pydantic models for notification-related
API requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuietHours(BaseModel):
    """Quiet hours configuration"""

    enabled: bool = Field(..., description="Whether quiet hours are enabled")
    start: str = Field(..., description="Start time in HH:mm format")
    end: str = Field(..., description="End time in HH:mm format")


class FeedNotificationSettings(BaseModel):
    """Notification settings for a specific feed or category"""

    feed_id: str | None = Field(
        None, description="Feed ID (if feed-specific)", serialization_alias="feedId"
    )
    category: str | None = Field(None, description="Category name (if category-specific)")
    enabled: bool = Field(..., description="Whether notifications are enabled")
    min_tinkering_index: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Minimum tinkering index",
        serialization_alias="minTinkeringIndex",
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class NotificationSettings(BaseModel):
    """User notification preferences"""

    enabled: bool = Field(..., description="Global notification toggle")
    dm_enabled: bool = Field(
        ..., description="Discord DM notifications toggle", serialization_alias="dmEnabled"
    )
    email_enabled: bool = Field(
        default=False, description="Email notifications toggle", serialization_alias="emailEnabled"
    )
    frequency: str = Field(..., description="Notification frequency (immediate, daily, weekly)")
    quiet_hours: QuietHours = Field(
        ..., description="Quiet hours configuration", serialization_alias="quietHours"
    )
    min_tinkering_index: int = Field(
        ...,
        ge=1,
        le=5,
        description="Minimum tinkering index threshold",
        serialization_alias="minTinkeringIndex",
    )
    feed_settings: list[FeedNotificationSettings] = Field(
        default_factory=list,
        description="Per-feed notification settings",
        serialization_alias="feedSettings",
    )
    channels: list[str] = Field(
        default_factory=lambda: ["dm", "in-app"], description="Enabled notification channels"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class NotificationHistoryEntry(BaseModel):
    """Notification history entry"""

    id: str = Field(..., description="Notification ID")
    article_id: str = Field(..., description="Article ID", serialization_alias="articleId")
    article_title: str = Field(..., description="Article title", serialization_alias="articleTitle")
    sent_at: datetime = Field(
        ..., description="When notification was sent", serialization_alias="sentAt"
    )
    channel: str = Field(..., description="Notification channel")
    status: str = Field(..., description="Delivery status (sent, failed, pending)")
    error_message: str | None = Field(
        None, description="Error message if failed", serialization_alias="errorMessage"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class NotificationDeliveryStatus(BaseModel):
    """Notification delivery status"""

    total_sent: int = Field(
        ..., description="Total notifications sent", serialization_alias="totalSent"
    )
    total_failed: int = Field(
        ..., description="Total notifications failed", serialization_alias="totalFailed"
    )
    last_sent_at: datetime | None = Field(
        None, description="Last notification sent time", serialization_alias="lastSentAt"
    )
    recent_history: list[NotificationHistoryEntry] = Field(
        default_factory=list,
        description="Recent notification history",
        serialization_alias="recentHistory",
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class UpdateNotificationSettingsRequest(BaseModel):
    """Request to update notification settings"""

    enabled: bool | None = None
    dm_enabled: bool | None = Field(None, serialization_alias="dmEnabled")
    email_enabled: bool | None = Field(None, serialization_alias="emailEnabled")
    frequency: str | None = None
    quiet_hours: QuietHours | None = Field(None, serialization_alias="quietHours")
    min_tinkering_index: int | None = Field(
        None, ge=1, le=5, serialization_alias="minTinkeringIndex"
    )
    feed_settings: list[FeedNotificationSettings] | None = Field(
        None, serialization_alias="feedSettings"
    )
    channels: list[str] | None = None

    model_config = ConfigDict(populate_by_name=True, by_alias=True)
