"""Notifications API package."""

from fastapi import APIRouter

from app.api.auth import get_current_user as get_current_user  # noqa: F401
from app.api.notifications.history import router as history_router
from app.api.notifications.preferences import router as preferences_router
from app.api.notifications.proactive import router as proactive_router
from app.api.notifications.quiet_hours import router as quiet_hours_router
from app.api.notifications.settings import router as settings_router
from app.api.notifications.tech_depth import router as tech_depth_router
from app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository as UserNotificationPreferencesRepository,  # noqa: F401
)
from app.services.notification_settings_service import (
    NotificationSettingsService as NotificationSettingsService,  # noqa: F401
)
from app.services.preference_service import PreferenceService as PreferenceService  # noqa: F401
from app.services.supabase_service import SupabaseService as SupabaseService  # noqa: F401
from app.tasks.scheduler import get_dynamic_scheduler as get_dynamic_scheduler  # noqa: F401

router = APIRouter(tags=["notifications"])
router.include_router(settings_router)
router.include_router(preferences_router)
router.include_router(quiet_hours_router)
router.include_router(tech_depth_router)
router.include_router(history_router)
router.include_router(proactive_router)
