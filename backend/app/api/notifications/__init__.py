"""Notifications API package."""
from fastapi import APIRouter

from app.api.notifications.history import router as history_router
from app.api.notifications.preferences import router as preferences_router
from app.api.notifications.proactive import router as proactive_router
from app.api.notifications.quiet_hours import router as quiet_hours_router
from app.api.notifications.settings import router as settings_router
from app.api.notifications.tech_depth import router as tech_depth_router

router = APIRouter(tags=["notifications"])
router.include_router(settings_router)
router.include_router(preferences_router)
router.include_router(quiet_hours_router)
router.include_router(tech_depth_router)
router.include_router(history_router)
router.include_router(proactive_router)
