"""
User Notification Preferences Schemas

This module defines the Pydantic models for user notification preferences
related to the personalized notification frequency feature.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
"""

from datetime import datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserNotificationPreferences(BaseModel):
    """
    User notification preferences model.

    Represents individual user notification settings including frequency,
    timing, timezone, and channel preferences.
    """

    id: UUID = Field(..., description="Unique identifier for the preference record")
    user_id: UUID = Field(
        ..., description="User ID this preference belongs to", serialization_alias="userId"
    )
    frequency: Literal["daily", "weekly", "monthly", "disabled"] = Field(
        ..., description="Notification frequency"
    )
    notification_time: time = Field(
        ..., description="Time of day to send notifications", serialization_alias="notificationTime"
    )
    notification_day_of_week: int = Field(
        default=5,
        ge=0,
        le=6,
        description="Day of week for weekly notifications (0=Sunday, 6=Saturday)",
        serialization_alias="notificationDayOfWeek",
    )
    notification_day_of_month: int = Field(
        default=1,
        ge=1,
        le=31,
        description="Day of month for monthly notifications (1-31)",
        serialization_alias="notificationDayOfMonth",
    )
    timezone: str = Field(..., description="IANA timezone identifier")
    dm_enabled: bool = Field(
        ...,
        description="Whether Discord DM notifications are enabled",
        serialization_alias="dmEnabled",
    )
    email_enabled: bool = Field(
        ...,
        description="Whether email notifications are enabled",
        serialization_alias="emailEnabled",
    )
    created_at: datetime = Field(
        ..., description="When the preference was created", serialization_alias="createdAt"
    )
    updated_at: datetime = Field(
        ..., description="When the preference was last updated", serialization_alias="updatedAt"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @field_validator("notification_time", mode="before")
    @classmethod
    def parse_notification_time(cls, v):
        """Parse notification time from various formats."""
        if isinstance(v, str):
            # Handle HH:MM format
            if ":" in v:
                hour, minute = v.split(":")
                return time(int(hour), int(minute))
            # Handle HHMMSS format
            elif len(v) == 6:
                return time(int(v[:2]), int(v[2:4]), int(v[4:6]))
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a valid IANA timezone identifier."""
        try:
            import zoneinfo

            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            # Fallback for older Python versions or missing zoneinfo
            try:
                import pytz

                pytz.timezone(v)
                return v
            except Exception:
                raise ValueError(f"Invalid timezone identifier: {v}")


class CreateUserNotificationPreferencesRequest(BaseModel):
    """Request model for creating user notification preferences."""

    user_id: UUID = Field(..., description="User ID", serialization_alias="userId")
    frequency: Literal["daily", "weekly", "monthly", "disabled"] = Field(
        default="weekly", description="Notification frequency"
    )
    notification_time: str = Field(
        default="18:00", description="Time in HH:MM format", serialization_alias="notificationTime"
    )
    notification_day_of_week: int = Field(
        default=5,
        ge=0,
        le=6,
        description="Day of week for weekly notifications (0=Sunday, 6=Saturday)",
        serialization_alias="notificationDayOfWeek",
    )
    notification_day_of_month: int = Field(
        default=1,
        ge=1,
        le=31,
        description="Day of month for monthly notifications (1-31)",
        serialization_alias="notificationDayOfMonth",
    )
    timezone: str = Field(default="Asia/Taipei", description="IANA timezone identifier")
    dm_enabled: bool = Field(
        default=True, description="Enable Discord DM notifications", serialization_alias="dmEnabled"
    )
    email_enabled: bool = Field(
        default=False, description="Enable email notifications", serialization_alias="emailEnabled"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @field_validator("notification_time")
    @classmethod
    def validate_notification_time(cls, v):
        """Validate notification time format."""
        if not isinstance(v, str):
            raise ValueError("notification_time must be a string")

        if not v or ":" not in v:
            raise ValueError("notification_time must be in HH:MM format")

        try:
            hour, minute = v.split(":")
            hour_int = int(hour)
            minute_int = int(minute)

            if not (0 <= hour_int <= 23):
                raise ValueError("Hour must be between 0 and 23")
            if not (0 <= minute_int <= 59):
                raise ValueError("Minute must be between 0 and 59")

            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("notification_time must contain valid integers")
            raise

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a valid IANA timezone identifier."""
        try:
            import zoneinfo

            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            # Fallback for older Python versions or missing zoneinfo
            try:
                import pytz

                pytz.timezone(v)
                return v
            except Exception:
                raise ValueError(f"Invalid timezone identifier: {v}")


class UpdateUserNotificationPreferencesRequest(BaseModel):
    """Request model for updating user notification preferences."""

    frequency: Literal["daily", "weekly", "monthly", "disabled"] | None = Field(
        default=None, description="Notification frequency"
    )
    notification_time: str | None = Field(
        default=None,
        description="Time in HH:MM format",
        alias="notificationTime",
        serialization_alias="notificationTime",
    )
    notification_day_of_week: int | None = Field(
        default=None,
        ge=0,
        le=6,
        description="Day of week for weekly notifications (0=Sunday, 6=Saturday)",
        alias="notificationDayOfWeek",
        serialization_alias="notificationDayOfWeek",
    )
    notification_day_of_month: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="Day of month for monthly notifications (1-31)",
        alias="notificationDayOfMonth",
        serialization_alias="notificationDayOfMonth",
    )
    timezone: str | None = Field(default=None, description="IANA timezone identifier")
    dm_enabled: bool | None = Field(
        default=None,
        description="Enable Discord DM notifications",
        alias="dmEnabled",
        serialization_alias="dmEnabled",
    )
    email_enabled: bool | None = Field(
        default=None,
        description="Enable email notifications",
        alias="emailEnabled",
        serialization_alias="emailEnabled",
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("notification_time")
    @classmethod
    def validate_notification_time(cls, v):
        """Validate notification time format."""
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("notification_time must be a string")

        if not v or ":" not in v:
            raise ValueError("notification_time must be in HH:MM format")

        try:
            hour, minute = v.split(":")
            hour_int = int(hour)
            minute_int = int(minute)

            if not (0 <= hour_int <= 23):
                raise ValueError("Hour must be between 0 and 23")
            if not (0 <= minute_int <= 59):
                raise ValueError("Minute must be between 0 and 59")

            return v
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("notification_time must contain valid integers")
            raise

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a valid IANA timezone identifier."""
        if v is None:
            return v

        try:
            import zoneinfo

            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            # Fallback for older Python versions or missing zoneinfo
            try:
                import pytz

                pytz.timezone(v)
                return v
            except Exception:
                raise ValueError(f"Invalid timezone identifier: {v}")


class ValidationResult(BaseModel):
    """Result of preference validation."""

    is_valid: bool = Field(
        ..., description="Whether the validation passed", serialization_alias="isValid"
    )
    errors: list[str] = Field(default_factory=list, description="List of validation errors")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)
