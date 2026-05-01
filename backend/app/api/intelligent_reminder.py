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
    status: Optional[str] = None,
    sort_by: Optional[str] = "sent_at",
    sort_order: Optional[str] = "desc",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get pending reminders for the current user with filtering and sorting

    Args:
        status: Filter by status (pending, sent, read, dismissed, all)
        sort_by: Sort field (sent_at, priority_score)
        sort_order: Sort order (asc, desc)
    """
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = str(current_user["user_id"])

        # Build query
        query = supabase_service.client.table("reminder_log").select("*").eq("user_id", user_id)

        # Apply status filter
        if status and status != "all":
            query = query.eq("status", status)
        else:
            # Default: show all except dismissed
            query = query.in_("status", ["pending", "sent", "delivered", "read"])

        # Apply sorting
        if sort_by == "priority_score":
            # For priority_score, we need to sort by the JSONB field
            # This is a workaround - fetch all and sort in Python
            result = query.execute()
            reminders_data = result.data or []

            # Sort by priority_score in reminder_context
            reminders_data.sort(
                key=lambda x: x.get("reminder_context", {}).get("priority_score", 0),
                reverse=(sort_order == "desc"),
            )
        else:
            # Default: sort by sent_at
            query = query.order("sent_at", desc=(sort_order == "desc"))
            result = query.limit(50).execute()
            reminders_data = result.data or []

        reminders = []
        for reminder_data in reminders_data:
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

        user_id = str(current_user["user_id"])

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

        user_id = str(current_user["user_id"])

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


@router.post("/{reminder_id}/unread")
async def mark_reminder_unread(
    reminder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Mark a reminder as unread (sent)"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = str(current_user["user_id"])

        # Update reminder status back to sent
        supabase_service.client.table("reminder_log").update({"status": "sent"}).eq(
            "id", reminder_id
        ).eq("user_id", user_id).execute()

        return {"message": "Reminder marked as unread"}

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

        user_id = str(current_user["user_id"])

        # Get settings from database (get the most recent one)
        result = (
            supabase_service.client.table("reminder_settings")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
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

        user_id = str(current_user["user_id"])

        # Build update data (without user_id for update operation)
        update_data = {}

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

        # Check if settings exist
        existing = (
            supabase_service.client.table("reminder_settings")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            # Update existing settings
            supabase_service.client.table("reminder_settings").update(update_data).eq(
                "user_id", user_id
            ).execute()
        else:
            # Create new settings (include user_id for insert)
            insert_data = {**update_data, "user_id": user_id}
            supabase_service.client.table("reminder_settings").insert(insert_data).execute()

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
    """Get reminder statistics for the current user"""
    try:
        from collections import Counter

        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = str(current_user["user_id"])

        # Get all reminders for stats
        result = (
            supabase_service.client.table("reminder_log")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        reminders = result.data or []

        # Calculate stats
        total_sent = len([r for r in reminders if r["status"] in ["sent", "delivered", "read"]])
        total_clicked = len([r for r in reminders if r["status"] == "read"])
        total_read = total_clicked  # Same as clicked for now
        total_dismissed = len([r for r in reminders if r["status"] == "dismissed"])
        total_pending = len([r for r in reminders if r["status"] == "pending"])

        click_rate = total_clicked / total_sent if total_sent > 0 else 0
        read_rate = total_read / total_sent if total_sent > 0 else 0

        # Calculate category distribution
        categories = []
        for r in reminders:
            context = r.get("reminder_context", {})
            if "category" in context:
                categories.append(context["category"])

        category_counts = Counter(categories)
        top_categories = [
            {"name": cat, "count": count} for cat, count in category_counts.most_common(5)
        ]

        # Calculate average priority
        priorities = [r.get("reminder_context", {}).get("priority_score", 0) for r in reminders]
        avg_priority = sum(priorities) / len(priorities) if priorities else 0

        # This week stats (last 7 days)
        from datetime import datetime, timedelta, timezone

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        this_week = [
            r
            for r in reminders
            if r.get("sent_at")
            and datetime.fromisoformat(r["sent_at"].replace("Z", "+00:00")) > week_ago
        ]

        return {
            "total_sent": total_sent,
            "total_clicked": total_clicked,
            "total_read": total_read,
            "total_dismissed": total_dismissed,
            "total_pending": total_pending,
            "click_rate": round(click_rate, 2),
            "read_rate": round(read_rate, 2),
            "avg_priority": round(avg_priority, 2),
            "this_week_count": len(this_week),
            "top_categories": top_categories,
            "most_effective_channel": "discord",
            "most_effective_time": 10,
            "recommendations": [
                "持續閱讀文章以改善推薦品質" if total_read < 5 else "推薦系統運作良好",
                f"本週收到 {len(this_week)} 個提醒" if this_week else "本週尚未收到提醒",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting reminder stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder statistics")


class BatchOperationRequest(BaseModel):
    reminder_ids: List[str]
    action: str  # "read", "dismiss"


@router.post("/batch")
async def batch_operation(
    request: BatchOperationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Perform batch operations on reminders"""
    try:
        from ..services.supabase_service import SupabaseService

        supabase_service = SupabaseService()

        user_id = str(current_user["user_id"])

        if not request.reminder_ids:
            raise HTTPException(status_code=400, detail="No reminder IDs provided")

        if request.action not in ["read", "dismiss"]:
            raise HTTPException(
                status_code=400, detail="Invalid action. Must be 'read' or 'dismiss'"
            )

        # Update status for all reminders
        status = "read" if request.action == "read" else "dismissed"

        for reminder_id in request.reminder_ids:
            supabase_service.client.table("reminder_log").update({"status": status}).eq(
                "id", reminder_id
            ).eq("user_id", user_id).execute()

        return {
            "message": f"Successfully {request.action} {len(request.reminder_ids)} reminders",
            "count": len(request.reminder_ids),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing batch operation: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform batch operation")


@router.post("/generate")
async def trigger_reminder_generation(current_user: dict = Depends(get_current_user)) -> dict:
    """Manually trigger reminder generation for current user"""
    try:
        from ..services.intelligent_reminder_generator import IntelligentReminderGenerator

        user_id = str(current_user["user_id"])
        generator = IntelligentReminderGenerator()

        reminders = await generator.generate_reminders_for_user(user_id)

        return {
            "message": "Reminders generated successfully",
            "count": len(reminders),
            "reminders": [
                {
                    "id": r["id"],
                    "title": r["reminder_context"]["title"],
                    "priority_score": r["reminder_context"]["priority_score"],
                }
                for r in reminders
            ],
        }

    except Exception as e:
        logger.error(f"Error generating reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate reminders")
