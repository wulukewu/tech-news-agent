"""
Notification History Schema Definitions

This module defines Pydantic schemas for notification history API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationHistoryRecord(BaseModel):
    """Schema for notification history record."""

    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    sent_at: Optional[datetime] = None
    channel: str = Field(..., description="Delivery channel (discord, email)")
    status: str = Field(..., description="Delivery status (sent, failed, queued, cancelled)")
    content: Optional[str] = Field(None, description="Notification content or summary")
    feed_source: Optional[str] = Field(None, description="RSS feed source")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    retry_count: int = Field(0, description="Number of retry attempts")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationHistoryResponse(BaseModel):
    """Schema for notification history list response."""

    records: List[NotificationHistoryRecord]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics response."""

    period_days: int
    total_notifications: int
    sent_count: int
    failed_count: int
    queued_count: int
    cancelled_count: int
    success_rate: float
    channel_breakdown: dict
    last_notification: Optional[datetime] = None


class NotificationHistoryFilters(BaseModel):
    """Schema for notification history filters."""

    channel: Optional[str] = Field(None, description="Filter by channel")
    status: Optional[str] = Field(None, description="Filter by status")
    days_back: Optional[int] = Field(None, description="Only include last N days")
    search: Optional[str] = Field(None, description="Search in content")


class CreateNotificationRecordRequest(BaseModel):
    """Schema for creating a notification record."""

    channel: str = Field(..., description="Delivery channel")
    status: str = Field(..., description="Delivery status")
    content: Optional[str] = Field(None, description="Notification content")
    feed_source: Optional[str] = Field(None, description="RSS feed source")
    error_message: Optional[str] = Field(None, description="Error details")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")


class UpdateNotificationStatusRequest(BaseModel):
    """Schema for updating notification status."""

    status: str = Field(..., description="New delivery status")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    increment_retry: bool = Field(False, description="Whether to increment retry count")


class NotificationChannelsResponse(BaseModel):
    """Schema for available notification channels."""

    channels: List[dict]


class NotificationStatusesResponse(BaseModel):
    """Schema for available notification statuses."""

    statuses: List[dict]
