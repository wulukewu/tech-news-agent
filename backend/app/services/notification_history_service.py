"""
Notification History Service

This service manages notification delivery history and statistics.
It tracks all notification attempts, their status, and provides analytics.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.core.exceptions import SupabaseServiceError
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification delivery channels."""

    DISCORD = "discord"
    EMAIL = "email"


class NotificationStatus(Enum):
    """Notification delivery status."""

    SENT = "sent"
    FAILED = "failed"
    QUEUED = "queued"
    CANCELLED = "cancelled"


class NotificationHistoryRecord:
    """Data class for notification history records."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        user_id: UUID = None,
        sent_at: Optional[datetime] = None,
        channel: str = NotificationChannel.DISCORD.value,
        status: str = NotificationStatus.QUEUED.value,
        content: Optional[str] = None,
        feed_source: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.sent_at = sent_at or datetime.utcnow()
        self.channel = channel
        self.status = status
        self.content = content
        self.feed_source = feed_source
        self.error_message = error_message
        self.retry_count = retry_count
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "channel": self.channel,
            "status": self.status,
            "content": self.content,
            "feed_source": self.feed_source,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "NotificationHistoryRecord":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if data.get("id") else None,
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            channel=data.get("channel", NotificationChannel.DISCORD.value),
            status=data.get("status", NotificationStatus.QUEUED.value),
            content=data.get("content"),
            feed_source=data.get("feed_source"),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
        )


class NotificationHistoryService:
    """Service for managing notification history and statistics."""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()

    async def record_notification(
        self,
        user_id: UUID,
        channel: str,
        status: str,
        content: Optional[str] = None,
        feed_source: Optional[str] = None,
        error_message: Optional[str] = None,
        sent_at: Optional[datetime] = None,
    ) -> NotificationHistoryRecord:
        """
        Record a notification delivery attempt.

        Args:
            user_id: The user's UUID
            channel: Delivery channel (discord, email)
            status: Delivery status (sent, failed, queued, cancelled)
            content: Notification content or summary
            feed_source: RSS feed source that triggered the notification
            error_message: Error details if delivery failed
            sent_at: When the notification was sent (defaults to now)

        Returns:
            NotificationHistoryRecord object
        """
        try:
            logger.info(f"Recording notification for user {user_id}: {channel} - {status}")

            # Validate inputs
            self._validate_channel(channel)
            self._validate_status(status)

            record_data = {
                "user_id": str(user_id),
                "sent_at": (sent_at or datetime.utcnow()).isoformat(),
                "channel": channel,
                "status": status,
                "content": content,
                "feed_source": feed_source,
                "error_message": error_message,
                "retry_count": 0,
            }

            result = (
                self.supabase_service.client.table("notification_history")
                .insert(record_data)
                .execute()
            )

            if not result.data:
                raise SupabaseServiceError("Failed to record notification")

            record = NotificationHistoryRecord.from_dict(result.data[0])
            logger.info(f"Recorded notification history: {record.id}")

            return record

        except Exception as e:
            logger.error(f"Failed to record notification for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to record notification: {e}")

    async def update_notification_status(
        self,
        record_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        increment_retry: bool = False,
    ) -> NotificationHistoryRecord:
        """
        Update the status of a notification record.

        Args:
            record_id: The notification record ID
            status: New delivery status
            error_message: Error details if status is failed
            increment_retry: Whether to increment retry count

        Returns:
            Updated NotificationHistoryRecord object
        """
        try:
            logger.info(f"Updating notification status {record_id}: {status}")

            self._validate_status(status)

            update_data = {"status": status, "error_message": error_message}

            if increment_retry:
                # Get current retry count and increment
                current = await self.get_notification_record(record_id)
                if current:
                    update_data["retry_count"] = current.retry_count + 1

            result = (
                self.supabase_service.client.table("notification_history")
                .update(update_data)
                .eq("id", str(record_id))
                .execute()
            )

            if not result.data:
                raise SupabaseServiceError("Failed to update notification status")

            record = NotificationHistoryRecord.from_dict(result.data[0])
            logger.info(f"Updated notification status: {record.id}")

            return record

        except Exception as e:
            logger.error(f"Failed to update notification status {record_id}: {e}")
            raise SupabaseServiceError(f"Failed to update notification status: {e}")

    async def get_notification_record(self, record_id: UUID) -> Optional[NotificationHistoryRecord]:
        """
        Get a specific notification record.

        Args:
            record_id: The notification record ID

        Returns:
            NotificationHistoryRecord object or None if not found
        """
        try:
            result = (
                self.supabase_service.client.table("notification_history")
                .select("*")
                .eq("id", str(record_id))
                .execute()
            )

            if not result.data:
                return None

            return NotificationHistoryRecord.from_dict(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get notification record {record_id}: {e}")
            return None

    async def get_notification_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        days_back: Optional[int] = None,
    ) -> Tuple[List[NotificationHistoryRecord], int]:
        """
        Get notification history for a user.

        Args:
            user_id: The user's UUID
            limit: Maximum number of records to return
            offset: Number of records to skip
            channel: Filter by delivery channel
            status: Filter by delivery status
            days_back: Only include records from the last N days

        Returns:
            Tuple of (records, total_count)
        """
        try:
            logger.info(f"Fetching notification history for user {user_id}")

            # Build query
            query = (
                self.supabase_service.client.table("notification_history")
                .select("*", count="exact")
                .eq("user_id", str(user_id))
            )

            # Apply filters
            if channel:
                self._validate_channel(channel)
                query = query.eq("channel", channel)

            if status:
                self._validate_status(status)
                query = query.eq("status", status)

            if days_back:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                query = query.gte("sent_at", cutoff_date.isoformat())

            # Apply pagination and ordering
            query = query.order("sent_at", desc=True).range(offset, offset + limit - 1)

            result = query.execute()

            records = [NotificationHistoryRecord.from_dict(data) for data in result.data]
            total_count = result.count or 0

            logger.info(f"Retrieved {len(records)} notification records for user {user_id}")

            return records, total_count

        except Exception as e:
            logger.error(f"Failed to get notification history for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to get notification history: {e}")

    async def get_notification_stats(self, user_id: UUID, days_back: int = 30) -> Dict:
        """
        Get notification statistics for a user.

        Args:
            user_id: The user's UUID
            days_back: Number of days to include in statistics

        Returns:
            Dictionary with notification statistics
        """
        try:
            logger.info(f"Fetching notification stats for user {user_id}")

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get all records for the time period
            result = (
                self.supabase_service.client.table("notification_history")
                .select("status, channel, sent_at")
                .eq("user_id", str(user_id))
                .gte("sent_at", cutoff_date.isoformat())
                .execute()
            )

            records = result.data or []

            # Calculate statistics
            total_notifications = len(records)
            sent_count = len([r for r in records if r["status"] == NotificationStatus.SENT.value])
            failed_count = len(
                [r for r in records if r["status"] == NotificationStatus.FAILED.value]
            )
            queued_count = len(
                [r for r in records if r["status"] == NotificationStatus.QUEUED.value]
            )
            cancelled_count = len(
                [r for r in records if r["status"] == NotificationStatus.CANCELLED.value]
            )

            # Channel breakdown
            discord_count = len(
                [r for r in records if r["channel"] == NotificationChannel.DISCORD.value]
            )
            email_count = len(
                [r for r in records if r["channel"] == NotificationChannel.EMAIL.value]
            )

            # Success rate
            success_rate = (
                (sent_count / total_notifications * 100) if total_notifications > 0 else 0
            )

            # Last notification
            last_notification = None
            if records:
                latest_record = max(records, key=lambda r: r["sent_at"])
                last_notification = latest_record["sent_at"]

            stats = {
                "period_days": days_back,
                "total_notifications": total_notifications,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "queued_count": queued_count,
                "cancelled_count": cancelled_count,
                "success_rate": round(success_rate, 1),
                "channel_breakdown": {"discord": discord_count, "email": email_count},
                "last_notification": last_notification,
            }

            logger.info(
                f"Retrieved notification stats for user {user_id}: {total_notifications} total"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get notification stats for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to get notification stats: {e}")

    async def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old notification history records.

        Args:
            days_to_keep: Number of days of history to keep

        Returns:
            Number of records deleted
        """
        try:
            logger.info(f"Cleaning up notification history older than {days_to_keep} days")

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            result = (
                self.supabase_service.client.table("notification_history")
                .delete()
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )

            deleted_count = len(result.data) if result.data else 0

            logger.info(f"Cleaned up {deleted_count} old notification records")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old notification records: {e}")
            raise SupabaseServiceError(f"Failed to cleanup old records: {e}")

    def _validate_channel(self, channel: str) -> None:
        """Validate notification channel."""
        valid_channels = [c.value for c in NotificationChannel]
        if channel not in valid_channels:
            raise ValueError(f"Invalid channel: {channel}. Must be one of: {valid_channels}")

    def _validate_status(self, status: str) -> None:
        """Validate notification status."""
        valid_statuses = [s.value for s in NotificationStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of: {valid_statuses}")

    @staticmethod
    def get_available_channels() -> List[Dict[str, str]]:
        """Get all available notification channels."""
        return [
            {
                "value": channel.value,
                "label": channel.value.title(),
                "description": f"{channel.value.title()} notifications",
            }
            for channel in NotificationChannel
        ]

    @staticmethod
    def get_available_statuses() -> List[Dict[str, str]]:
        """Get all available notification statuses."""
        descriptions = {
            NotificationStatus.SENT.value: "Successfully delivered",
            NotificationStatus.FAILED.value: "Delivery failed",
            NotificationStatus.QUEUED.value: "Waiting to be sent",
            NotificationStatus.CANCELLED.value: "Cancelled before sending",
        }

        return [
            {
                "value": status.value,
                "label": status.value.title(),
                "description": descriptions[status.value],
            }
            for status in NotificationStatus
        ]
