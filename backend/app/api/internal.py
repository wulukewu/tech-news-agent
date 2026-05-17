"""Internal API endpoints — not exposed to external clients."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.core.logger import get_logger
from app.services.thread_memory_service import ThreadMemoryService

logger = get_logger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


class CompressThreadRequest(BaseModel):
    conversation_id: str
    thread_id: str


@router.post("/compress-thread", include_in_schema=False)
async def compress_thread(body: CompressThreadRequest, background_tasks: BackgroundTasks):
    """Enqueue a summary-buffer compression job via FastAPI BackgroundTasks."""
    service = ThreadMemoryService()
    background_tasks.add_task(service.compress_history, body.conversation_id, body.thread_id)
    logger.info(
        "Compression task enqueued",
        conversation_id=body.conversation_id,
        thread_id=body.thread_id,
    )
    return {"status": "queued"}
