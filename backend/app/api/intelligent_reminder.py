"""
REST API endpoints for the Intelligent Reminder Agent.
Provides endpoints for managing reminders, settings, and viewing statistics.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..api.auth import get_current_user
from ..qa_agent.intelligent_reminder import (
    IntelligentReminderAgent,
)
from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["intelligent-reminders"])


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


# Dependency injection
def get_supabase_service() -> SupabaseService:
    return SupabaseService()


def get_reminder_agent(
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> IntelligentReminderAgent:
    return IntelligentReminderAgent(supabase_service=supabase_service)


@router.get("/pending", response_model=List[ReminderResponse])
async def get_pending_reminders(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Get pending reminders for the current user"""
    try:
        user_id = current_user["id"]

        # Get pending reminders from database
        result = (
            await supabase_service.client.table("reminder_log")
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
                ReminderResponse(
                    id=reminder_data["id"],
                    reminder_type=reminder_data["reminder_type"],
                    title=context.get("title", "Reminder"),
                    description=context.get("description", ""),
                    sent_at=datetime.fromisoformat(reminder_data["sent_at"]),
                    status=reminder_data["status"],
                    priority_score=context.get("priority_score", 0.5),
                    reading_time_estimate=context.get("reading_time_estimate"),
                    action_url=context.get("action_url"),
                )
            )

        return reminders

    except Exception as e:
        logger.error(f"Error getting pending reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending reminders")


@router.post("/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Dismiss a reminder"""
    try:
        user_id = current_user["id"]

        # Verify reminder belongs to user
        reminder = await reminder_agent._get_reminder_by_id(UUID(reminder_id))
        if not reminder or reminder["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Reminder not found")

        # Track interaction
        await reminder_agent.track_reminder_interaction(UUID(reminder_id), "dismissed")

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
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Mark a reminder as read"""
    try:
        user_id = current_user["id"]

        # Verify reminder belongs to user
        reminder = await reminder_agent._get_reminder_by_id(UUID(reminder_id))
        if not reminder or reminder["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Reminder not found")

        # Track interaction
        await reminder_agent.track_reminder_interaction(UUID(reminder_id), "read")

        return {"message": "Reminder marked as read"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reminder ID")
    except Exception as e:
        logger.error(f"Error marking reminder {reminder_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark reminder as read")


@router.get("/settings", response_model=ReminderSettingsResponse)
async def get_reminder_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Get user's reminder settings"""
    try:
        user_id = UUID(current_user["id"])

        # Get settings from timing engine
        settings = await reminder_agent.timing_engine._get_user_settings(user_id)

        if not settings:
            # Return default settings
            return ReminderSettingsResponse(
                enabled=True,
                max_daily_reminders=5,
                preferred_channels=["discord"],
                timezone="UTC",
                reminder_frequency="smart",
            )

        return ReminderSettingsResponse(
            enabled=settings.enabled,
            max_daily_reminders=settings.max_daily_reminders,
            preferred_channels=[
                ch.value if hasattr(ch, "value") else ch for ch in settings.preferred_channels
            ],
            quiet_hours_start=settings.quiet_hours_start.strftime("%H:%M")
            if settings.quiet_hours_start
            else None,
            quiet_hours_end=settings.quiet_hours_end.strftime("%H:%M")
            if settings.quiet_hours_end
            else None,
            timezone=settings.timezone,
            reminder_frequency=settings.reminder_frequency.value
            if hasattr(settings.reminder_frequency, "value")
            else settings.reminder_frequency,
        )

    except Exception as e:
        logger.error(f"Error getting reminder settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder settings")


@router.put("/settings")
async def update_reminder_settings(
    settings_request: ReminderSettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Update user's reminder settings"""
    try:
        user_id = current_user["id"]

        # Build update data
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
            # Validate channels
            valid_channels = ["discord", "web", "email"]
            for channel in settings_request.preferred_channels:
                if channel not in valid_channels:
                    raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
            update_data["preferred_channels"] = settings_request.preferred_channels

        if settings_request.quiet_hours_start is not None:
            # Validate time format
            try:
                from datetime import time

                time.fromisoformat(settings_request.quiet_hours_start)
                update_data["quiet_hours_start"] = settings_request.quiet_hours_start
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid quiet_hours_start format. Use HH:MM"
                )

        if settings_request.quiet_hours_end is not None:
            try:
                from datetime import time

                time.fromisoformat(settings_request.quiet_hours_end)
                update_data["quiet_hours_end"] = settings_request.quiet_hours_end
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid quiet_hours_end format. Use HH:MM"
                )

        if settings_request.timezone is not None:
            update_data["timezone"] = settings_request.timezone

        if settings_request.reminder_frequency is not None:
            valid_frequencies = ["smart", "daily", "weekly", "disabled"]
            if settings_request.reminder_frequency not in valid_frequencies:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid reminder_frequency: {settings_request.reminder_frequency}",
                )
            update_data["reminder_frequency"] = settings_request.reminder_frequency

        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()

            # Upsert settings
            await supabase_service.client.table("reminder_settings").upsert(
                {**update_data, "user_id": user_id}
            ).execute()

        return {"message": "Settings updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update reminder settings")


@router.get("/stats", response_model=ReminderStatsResponse)
async def get_reminder_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Get reminder effectiveness statistics for the current user"""
    try:
        user_id = UUID(current_user["id"])

        # Generate effectiveness report
        report = await reminder_agent.generate_effectiveness_report(user_id)

        return ReminderStatsResponse(
            total_sent=report.total_sent,
            total_clicked=report.total_clicked,
            total_read=report.total_read,
            total_dismissed=report.total_dismissed,
            click_rate=report.click_rate,
            read_rate=report.read_rate,
            most_effective_channel=report.most_effective_channel,
            most_effective_time=report.most_effective_time,
            recommendations=report.recommendations,
        )

    except Exception as e:
        logger.error(f"Error getting reminder stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder statistics")


@router.post("/trigger-analysis")
async def trigger_manual_analysis(
    article_id: Optional[str] = Query(None, description="Specific article ID to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Manually trigger reminder analysis (admin/testing endpoint)"""
    try:
        if article_id:
            # Analyze specific article
            await reminder_agent.process_new_article(UUID(article_id))
            return {"message": f"Analysis triggered for article {article_id}"}
        else:
            # Check version updates
            await reminder_agent.check_version_updates()
            return {"message": "Version update check triggered"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")
    except Exception as e:
        logger.error(f"Error triggering manual analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger analysis")


@router.post("/send-pending")
async def send_pending_reminders(
    current_user: Dict[str, Any] = Depends(get_current_user),
    reminder_agent: IntelligentReminderAgent = Depends(get_reminder_agent),
):
    """Manually trigger sending of pending reminders (admin/testing endpoint)"""
    try:
        await reminder_agent.send_pending_reminders()
        return {"message": "Pending reminders processing triggered"}

    except Exception as e:
        logger.error(f"Error sending pending reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to send pending reminders")
