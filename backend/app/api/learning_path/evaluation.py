"""Learning Path API — shared models, dependencies, and router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.learning_path.effectiveness_evaluator import LearningEffectivenessEvaluator
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

router = APIRouter()


# Pydantic models for API
class CreateGoalRequest(BaseModel):
    goal_text: str  # Natural language goal like "我想學習 Kubernetes"


class CreateGoalResponse(BaseModel):
    goal_id: str
    parsed_goal: dict
    learning_path: dict
    success: bool
    message: str
    suggested_feeds: list = []


class LearningGoalResponse(BaseModel):
    id: str
    title: str
    description: str
    target_skill: str
    difficulty_level: int
    estimated_hours: int
    status: str
    created_at: str


class ProgressResponse(BaseModel):
    goal_id: str
    overall_completion: int
    current_stage: int
    stages: List[dict]
    recommendations: List[str]


class RecommendationResponse(BaseModel):
    articles: List[dict]
    stage_name: str
    total_count: int


class CompleteArticleRequest(BaseModel):
    time_spent_minutes: int = 0
    notes: str = ""
    stage_order: Optional[int] = None


class AdjustPlanRequest(BaseModel):
    adjustment_type: str
    reason: str


# Dependency injection
async def get_supabase_service() -> SupabaseService:
    return SupabaseService()


async def get_llm_service() -> LLMService:
    return LLMService()


@router.get("/goals/{goal_id}/evaluation")
async def get_learning_evaluation(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get comprehensive learning effectiveness evaluation"""
    try:
        user_id = str(current_user["user_id"])

        evaluator = LearningEffectivenessEvaluator(supabase)
        evaluation = await evaluator.generate_evaluation_report(user_id, goal_id)

        return {
            "goal_id": evaluation.goal_id,
            "overall_performance": evaluation.overall_performance.value,
            "efficiency_metrics": {
                "time_efficiency": evaluation.efficiency_metrics.time_efficiency,
                "completion_rate": evaluation.efficiency_metrics.completion_rate,
                "retention_score": evaluation.efficiency_metrics.retention_score,
                "consistency_score": evaluation.efficiency_metrics.consistency_score,
            },
            "strengths": evaluation.strength_weakness_analysis.strengths,
            "weaknesses": evaluation.strength_weakness_analysis.weaknesses,
            "recommendations": evaluation.recommendations,
            "next_steps": evaluation.next_steps,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"獲取學習評估失敗: {str(e)}"
        )
