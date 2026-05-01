"""
REST API endpoints for the Intelligent Reminder Agent.
Provides endpoints for managing reminders, settings, and viewing statistics.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligent-reminders", tags=["intelligent-reminders"])


# Request/Response Models
class ReminderResponse(BaseModel):
    id: str
    reminder_type: str
    title: str
    description: str
    sent_at: datetime
    status: str
    priority_score: float
    reading_time_estimate: Optional[int] = None
    action_url: Optional[str] = None


class ReminderSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    max_daily_reminders: Optional[int] = None
    preferred_channels: Optional[List[str]] = None
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None  # HH:MM format
    timezone: Optional[str] = None
    reminder_frequency: Optional[str] = None


class ReminderSettingsResponse(BaseModel):
    enabled: bool
    max_daily_reminders: int
    preferred_channels: List[str]
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str
    reminder_frequency: str


class ReminderStatsResponse(BaseModel):
    total_sent: int
    total_clicked: int
    total_read: int
    total_dismissed: int
    click_rate: float
    read_rate: float
    most_effective_channel: Optional[str] = None
    most_effective_time: Optional[int] = None
    recommendations: List[str]


# Dependency injection - use singleton pattern to avoid thread issues
_supabase_service = None


def get_supabase_service():
    from ..services.supabase_service import SupabaseService

    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service


@router.get("/pending")
async def get_pending_reminders(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get pending reminders for the current user"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Get pending reminders from database
        result = (
            supabase_service.client.table("reminder_log")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["pending", "sent", "delivered"])
            .order("sent_at", desc=True)
            .limit(20)
            .execute()
        )

        reminders = []
        for reminder_data in result.data or []:
            context = reminder_data.get("reminder_context", {})

            reminders.append(
                {
                    "id": reminder_data["id"],
                    "reminder_type": reminder_data["reminder_type"],
                    "reminder_context": {
                        "title": context.get("title", "Reminder"),
                        "description": context.get("description", ""),
                        "priority_score": context.get("priority_score", 0.5),
                        "reading_time_estimate": context.get("reading_time_estimate"),
                        "action_url": context.get("action_url"),
                        "related_articles": context.get("related_articles", []),
                    },
                    "sent_at": reminder_data["sent_at"],
                    "channel": reminder_data["channel"],
                    "status": reminder_data["status"],
                }
            )

        return {"reminders": reminders}

    except Exception as e:
        logger.error(f"Error getting pending reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending reminders")


@router.post("/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Dismiss a reminder"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Update reminder status
        supabase_service.client.table("reminder_log").update({"status": "dismissed"}).eq(
            "id", reminder_id
        ).eq("user_id", user_id).execute()

        return {"message": "Reminder dismissed successfully"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reminder ID")
    except Exception as e:
        logger.error(f"Error dismissing reminder {reminder_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to dismiss reminder")


@router.post("/{reminder_id}/read")
async def mark_reminder_read(
    reminder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Mark a reminder as read"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Update reminder status
        supabase_service.client.table("reminder_log").update({"status": "read"}).eq(
            "id", reminder_id
        ).eq("user_id", user_id).execute()

        return {"message": "Reminder marked as read"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reminder ID")
    except Exception as e:
        logger.error(f"Error marking reminder {reminder_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark reminder as read")


@router.get("/settings")
async def get_reminder_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get user's reminder settings"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Get settings from database
        result = (
            supabase_service.client.table("reminder_settings")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            # Return default settings
            return {
                "enabled": True,
                "max_daily_reminders": 5,
                "preferred_channels": ["discord"],
                "timezone": "UTC",
                "reminder_frequency": "smart",
            }

        settings = result.data[0]
        return {
            "enabled": settings.get("enabled", True),
            "max_daily_reminders": settings.get("max_daily_reminders", 5),
            "preferred_channels": settings.get("preferred_channels", ["discord"]),
            "quiet_hours_start": settings.get("quiet_hours_start"),
            "quiet_hours_end": settings.get("quiet_hours_end"),
            "timezone": settings.get("timezone", "UTC"),
            "reminder_frequency": settings.get("reminder_frequency", "smart"),
        }

    except Exception as e:
        logger.error(f"Error getting reminder settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder settings")


@router.put("/settings")
async def update_reminder_settings(
    settings_request: ReminderSettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update user's reminder settings"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Build update data
        update_data = {"user_id": user_id}

        if settings_request.enabled is not None:
            update_data["enabled"] = settings_request.enabled

        if settings_request.max_daily_reminders is not None:
            if not 0 <= settings_request.max_daily_reminders <= 20:
                raise HTTPException(
                    status_code=400, detail="max_daily_reminders must be between 0 and 20"
                )
            update_data["max_daily_reminders"] = settings_request.max_daily_reminders

        if settings_request.preferred_channels is not None:
            update_data["preferred_channels"] = settings_request.preferred_channels

        if settings_request.quiet_hours_start is not None:
            update_data["quiet_hours_start"] = settings_request.quiet_hours_start

        if settings_request.quiet_hours_end is not None:
            update_data["quiet_hours_end"] = settings_request.quiet_hours_end

        if settings_request.timezone is not None:
            update_data["timezone"] = settings_request.timezone

        if settings_request.reminder_frequency is not None:
            update_data["reminder_frequency"] = settings_request.reminder_frequency

        # Upsert settings
        supabase_service.client.table("reminder_settings").upsert(update_data).execute()

        return {"message": "Settings updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update reminder settings")


@router.get("/stats")
async def get_reminder_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get reminder effectiveness statistics for the current user"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = current_user["id"]

        # Get basic stats from reminder_log
        result = (
            supabase_service.client.table("reminder_log")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        reminders = result.data or []
        total_sent = len(reminders)
        total_clicked = len([r for r in reminders if r.get("status") == "clicked"])
        total_read = len([r for r in reminders if r.get("status") == "read"])
        total_dismissed = len([r for r in reminders if r.get("status") == "dismissed"])

        click_rate = total_clicked / total_sent if total_sent > 0 else 0
        read_rate = total_read / total_sent if total_sent > 0 else 0

        return {
            "total_sent": total_sent,
            "total_clicked": total_clicked,
            "total_read": total_read,
            "total_dismissed": total_dismissed,
            "click_rate": click_rate,
            "read_rate": read_rate,
            "most_effective_channel": "discord",
            "most_effective_time": 10,
            "recommendations": ["Try reading more articles to improve recommendations"],
        }

    except Exception as e:
        logger.error(f"Error getting reminder stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder statistics")
