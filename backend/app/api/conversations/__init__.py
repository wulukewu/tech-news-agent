"""Conversations API package."""
from fastapi import APIRouter

from app.api.conversations.ai import router as ai_router
from app.api.conversations.crud import router as crud_router
from app.api.conversations.export import router as export_router
from app.api.conversations.insights import router as insights_router
from app.api.conversations.messages import router as messages_router
from app.api.conversations.related import router as related_router
from app.api.conversations.share import router as share_router

router = APIRouter(tags=["conversations"])
router.include_router(insights_router)
router.include_router(crud_router)
router.include_router(messages_router)
router.include_router(export_router)
router.include_router(ai_router)
router.include_router(related_router)
router.include_router(share_router)
