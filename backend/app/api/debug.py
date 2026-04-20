"""
Debug endpoints for checking scheduler status
"""

from fastapi import APIRouter

from app.core.logger import get_logger
from app.tasks.scheduler import get_dynamic_scheduler, get_scheduler

router = APIRouter(prefix="/debug", tags=["debug"])
logger = get_logger(__name__)


@router.get("/scheduler/jobs")
async def get_scheduler_jobs():
    """Get all scheduled jobs"""
    try:
        scheduler = get_scheduler()
        if not scheduler:
            return {"error": "Scheduler not initialized"}

        jobs = scheduler.get_jobs()

        job_list = []
        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
                "func": str(job.func),
            }
            job_list.append(job_info)

        return {
            "total_jobs": len(jobs),
            "scheduler_running": scheduler.running,
            "scheduler_state": str(scheduler.state),
            "jobs": job_list,
        }
    except Exception as e:
        logger.error(f"Error getting scheduler jobs: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        scheduler = get_scheduler()
        dynamic_scheduler = get_dynamic_scheduler()

        if not scheduler:
            return {"error": "Scheduler not initialized"}

        return {
            "scheduler_running": scheduler.running,
            "scheduler_state": str(scheduler.state),
            "total_jobs": len(scheduler.get_jobs()),
            "dynamic_scheduler_initialized": dynamic_scheduler is not None,
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        return {"error": str(e)}
