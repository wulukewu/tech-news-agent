"""
Lock Manager Service

This module provides the LockManager class for atomic notification locking to prevent
duplicate notifications in multi-instance environments. Uses database transactions
for atomic lock operations and implements lock expiration and cleanup mechanisms.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class NotificationLock:
    """
    Represents a notification lock for preventing duplicate notifications.

    This class encapsulates the lock data and provides methods for checking
    lock validity and expiration status.
    """

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        notification_type: str,
        scheduled_time: datetime,
        status: str = "pending",
        instance_id: str = "",
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        """
        Initialize a NotificationLock.

        Args:
            id: Unique lock identifier
            user_id: User ID this lock belongs to
            notification_type: Type of notification being locked
            scheduled_time: When the notification was scheduled
            status: Lock status (pending, processing, completed, failed)
            instance_id: Backend instance that acquired the lock
            created_at: When the lock was created
            expires_at: When the lock expires
        """
        self.id = id
        self.user_id = user_id
        self.notification_type = notification_type
        self.scheduled_time = scheduled_time
        self.status = status
        self.instance_id = instance_id
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at

    @classmethod
    def create(
        cls,
        user_id: UUID,
        notification_type: str,
        scheduled_time: datetime,
        instance_id: str,
        ttl_minutes: int = 30,
    ) -> "NotificationLock":
        """
        Create a new notification lock with expiration.

        Args:
            user_id: User ID this lock belongs to
            notification_type: Type of notification being locked
            scheduled_time: When the notification was scheduled
            instance_id: Backend instance acquiring the lock
            ttl_minutes: Time to live in minutes (default: 30)

        Returns:
            NotificationLock: New lock instance
        """
        lock_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        return cls(
            id=lock_id,
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
            status="pending",
            instance_id=instance_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

    def is_expired(self) -> bool:
        """
        Check if the lock has expired.

        Returns:
            bool: True if the lock has expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def can_process(self, instance_id: str) -> bool:
        """
        Check if the lock can be processed by the given instance.

        Args:
            instance_id: Backend instance ID to check

        Returns:
            bool: True if the lock can be processed, False otherwise
        """
        return (
            self.status == "pending" and self.instance_id == instance_id and not self.is_expired()
        )

    def __repr__(self) -> str:
        return (
            f"NotificationLock(id={self.id}, user_id={self.user_id}, "
            f"type={self.notification_type}, status={self.status})"
        )


class LockManager(BaseService):
    """
    Manager for atomic notification locking to prevent duplicate notifications.

    This service provides:
    - Atomic lock acquisition using database transactions
    - Lock release with status updates
    - Cleanup of expired locks to prevent deadlocks
    - Multi-instance coordination through database-based locking

    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """

    def __init__(self, client: Client):
        """
        Initialize the LockManager.

        Args:
            client: Supabase client for database operations
        """
        super().__init__()
        self.client = client
        self.instance_id = self._get_instance_id()
        self.logger = get_logger(f"{__name__}.LockManager")

    def _get_instance_id(self) -> str:
        """
        Get a unique identifier for this backend instance.

        Returns:
            str: Unique instance identifier
        """
        # Use environment variable if available, otherwise generate one
        instance_id = os.environ.get("INSTANCE_ID")
        if not instance_id:
            # Generate a unique ID based on process ID and timestamp
            import time

            instance_id = f"instance_{os.getpid()}_{int(time.time())}"

        return instance_id

    async def acquire_notification_lock(
        self,
        user_id: UUID,
        notification_type: str,
        scheduled_time: datetime,
        ttl_minutes: int = 30,
    ) -> Optional[NotificationLock]:
        """
        Acquire a notification lock using atomic database operations.

        This method uses database transactions to ensure atomic lock acquisition,
        preventing race conditions when multiple backend instances attempt to
        send the same notification simultaneously.

        Args:
            user_id: User ID for the notification
            notification_type: Type of notification (e.g., 'weekly_digest')
            scheduled_time: When the notification was scheduled
            ttl_minutes: Lock expiration time in minutes (default: 30)

        Returns:
            NotificationLock: Acquired lock if successful, None if lock already exists

        Raises:
            ServiceError: If database operation fails

        Requirements: 10.1, 10.2
        """
        try:
            self.logger.info(
                "Attempting to acquire notification lock",
                user_id=str(user_id),
                notification_type=notification_type,
                scheduled_time=scheduled_time.isoformat(),
                instance_id=self.instance_id,
            )

            # Create the lock object
            lock = NotificationLock.create(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
                instance_id=self.instance_id,
                ttl_minutes=ttl_minutes,
            )

            # Prepare lock data for database insertion
            lock_data = {
                "id": str(lock.id),
                "user_id": str(lock.user_id),
                "notification_type": lock.notification_type,
                "scheduled_time": lock.scheduled_time.isoformat(),
                "status": lock.status,
                "instance_id": lock.instance_id,
                "created_at": lock.created_at.isoformat(),
                "expires_at": lock.expires_at.isoformat(),
            }

            # Use atomic insert with conflict handling
            # This will fail if a lock with the same (user_id, notification_type, scheduled_time) exists
            try:
                response = self.client.table("notification_locks").insert(lock_data).execute()

                if response.data and len(response.data) > 0:
                    self.logger.info(
                        "Successfully acquired notification lock",
                        lock_id=str(lock.id),
                        user_id=str(user_id),
                        notification_type=notification_type,
                        instance_id=self.instance_id,
                    )
                    return lock
                else:
                    self.logger.warning(
                        "Failed to acquire lock - no data returned",
                        user_id=str(user_id),
                        notification_type=notification_type,
                        instance_id=self.instance_id,
                    )
                    return None

            except Exception as insert_error:
                # Check if this is a unique constraint violation (lock already exists)
                error_message = str(insert_error).lower()
                if "unique" in error_message or "duplicate" in error_message:
                    self.logger.info(
                        "Lock already exists for this notification",
                        user_id=str(user_id),
                        notification_type=notification_type,
                        scheduled_time=scheduled_time.isoformat(),
                        instance_id=self.instance_id,
                    )
                    return None
                else:
                    # Re-raise other database errors
                    raise insert_error

        except Exception as e:
            self._handle_error(
                e,
                "Failed to acquire notification lock",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "notification_type": notification_type,
                    "scheduled_time": scheduled_time.isoformat(),
                    "instance_id": self.instance_id,
                },
            )

    async def release_lock(self, lock_id: UUID, status: str = "completed") -> None:
        """
        Release a notification lock by updating its status.

        Args:
            lock_id: ID of the lock to release
            status: Final status ('completed' or 'failed')

        Raises:
            ServiceError: If database operation fails

        Requirements: 10.3
        """
        try:
            self.logger.info(
                "Releasing notification lock",
                lock_id=str(lock_id),
                status=status,
                instance_id=self.instance_id,
            )

            # Validate status
            valid_statuses = ["completed", "failed"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
                )

            # Update lock status in database
            response = (
                self.client.table("notification_locks")
                .update(
                    {
                        "status": status,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", str(lock_id))
                .eq("instance_id", self.instance_id)  # Ensure only the owning instance can release
                .execute()
            )

            if response.data and len(response.data) > 0:
                self.logger.info(
                    "Successfully released notification lock",
                    lock_id=str(lock_id),
                    status=status,
                    instance_id=self.instance_id,
                )
            else:
                self.logger.warning(
                    "Lock not found or not owned by this instance",
                    lock_id=str(lock_id),
                    instance_id=self.instance_id,
                )

        except ValueError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to release notification lock",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "lock_id": str(lock_id),
                    "status": status,
                    "instance_id": self.instance_id,
                },
            )

    async def cleanup_expired_locks(self) -> int:
        """
        Clean up expired notification locks to prevent deadlocks.

        This method removes locks that have exceeded their expiration time,
        preventing the system from getting stuck with orphaned locks.

        Returns:
            int: Number of expired locks cleaned up

        Raises:
            ServiceError: If database operation fails

        Requirements: 10.4, 10.5
        """
        try:
            self.logger.info("Starting cleanup of expired notification locks")

            current_time = datetime.utcnow()

            # Delete expired locks
            response = (
                self.client.table("notification_locks")
                .delete()
                .lt("expires_at", current_time.isoformat())
                .execute()
            )

            cleaned_count = len(response.data) if response.data else 0

            self.logger.info(
                "Completed cleanup of expired notification locks",
                cleaned_count=cleaned_count,
                current_time=current_time.isoformat(),
            )

            return cleaned_count

        except Exception as e:
            self._handle_error(
                e,
                "Failed to cleanup expired notification locks",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"current_time": datetime.utcnow().isoformat()},
            )

    async def get_lock_status(
        self, user_id: UUID, notification_type: str, scheduled_time: datetime
    ) -> Optional[dict]:
        """
        Get the status of a notification lock.

        Args:
            user_id: User ID for the notification
            notification_type: Type of notification
            scheduled_time: When the notification was scheduled

        Returns:
            dict: Lock information if found, None otherwise

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.debug(
                "Getting lock status",
                user_id=str(user_id),
                notification_type=notification_type,
                scheduled_time=scheduled_time.isoformat(),
            )

            response = (
                self.client.table("notification_locks")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("notification_type", notification_type)
                .eq("scheduled_time", scheduled_time.isoformat())
                .execute()
            )

            if response.data and len(response.data) > 0:
                lock_data = response.data[0]

                # Parse expires_at to check if expired
                expires_at = datetime.fromisoformat(lock_data["expires_at"].replace("Z", "+00:00"))
                is_expired = datetime.utcnow() > expires_at.replace(tzinfo=None)

                return {
                    "id": lock_data["id"],
                    "status": lock_data["status"],
                    "instance_id": lock_data["instance_id"],
                    "created_at": lock_data["created_at"],
                    "expires_at": lock_data["expires_at"],
                    "is_expired": is_expired,
                }

            return None

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get lock status",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "notification_type": notification_type,
                    "scheduled_time": scheduled_time.isoformat(),
                },
            )

    async def force_release_lock(
        self, user_id: UUID, notification_type: str, scheduled_time: datetime
    ) -> bool:
        """
        Force release a notification lock (admin operation).

        This method can be used to manually release stuck locks.

        Args:
            user_id: User ID for the notification
            notification_type: Type of notification
            scheduled_time: When the notification was scheduled

        Returns:
            bool: True if lock was released, False if not found

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.warning(
                "Force releasing notification lock",
                user_id=str(user_id),
                notification_type=notification_type,
                scheduled_time=scheduled_time.isoformat(),
                instance_id=self.instance_id,
            )

            response = (
                self.client.table("notification_locks")
                .delete()
                .eq("user_id", str(user_id))
                .eq("notification_type", notification_type)
                .eq("scheduled_time", scheduled_time.isoformat())
                .execute()
            )

            released = len(response.data) > 0 if response.data else False

            if released:
                self.logger.info(
                    "Successfully force released notification lock",
                    user_id=str(user_id),
                    notification_type=notification_type,
                    instance_id=self.instance_id,
                )
            else:
                self.logger.info(
                    "No lock found to force release",
                    user_id=str(user_id),
                    notification_type=notification_type,
                    instance_id=self.instance_id,
                )

            return released

        except Exception as e:
            self._handle_error(
                e,
                "Failed to force release notification lock",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "notification_type": notification_type,
                    "scheduled_time": scheduled_time.isoformat(),
                    "instance_id": self.instance_id,
                },
            )

    async def get_lock_statistics(self) -> dict:
        """
        Get statistics about notification locks.

        Returns:
            dict: Lock statistics including counts by status

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.debug("Getting lock statistics")

            # Get all locks
            response = (
                self.client.table("notification_locks")
                .select("status, expires_at, created_at")
                .execute()
            )

            if not response.data:
                return {
                    "total_locks": 0,
                    "by_status": {},
                    "expired_locks": 0,
                    "active_locks": 0,
                }

            locks = response.data
            current_time = datetime.utcnow()

            # Count by status
            status_counts = {}
            expired_count = 0
            active_count = 0

            for lock in locks:
                status = lock["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

                # Check if expired
                expires_at = datetime.fromisoformat(lock["expires_at"].replace("Z", "+00:00"))
                if current_time > expires_at.replace(tzinfo=None):
                    expired_count += 1
                else:
                    active_count += 1

            return {
                "total_locks": len(locks),
                "by_status": status_counts,
                "expired_locks": expired_count,
                "active_locks": active_count,
                "instance_id": self.instance_id,
            }

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get lock statistics",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"instance_id": self.instance_id},
            )
