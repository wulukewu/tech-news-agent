"""Learning Path API package — combines all sub-routers."""

from fastapi import APIRouter

from app.api.learning_path.evaluation import router as evaluation_router
from app.api.learning_path.goals import router as goals_router
from app.api.learning_path.progress import router as progress_router

router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])
router.include_router(goals_router)
router.include_router(progress_router)
router.include_router(evaluation_router)
