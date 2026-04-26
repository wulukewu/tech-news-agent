"""
Learning Path API Router

REST API endpoints for learning path planning agent.
Requirements: 6.1, 6.2, 6.3, 6.4
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.learning_path import initialize_skill_tree
from app.qa_agent.learning_path.article_recommender import ArticleRecommender
from app.qa_agent.learning_path.dynamic_adjuster import DynamicAdjuster
from app.qa_agent.learning_path.effectiveness_evaluator import (
    LearningEffectivenessEvaluator,
)
from app.qa_agent.learning_path.goal_parser import GoalParser
from app.qa_agent.learning_path.path_generator import LearningPathGenerator
from app.qa_agent.learning_path.progress_tracker import (
    ProgressStatus,
    ProgressTracker,
)
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])


# Pydantic models for API
class CreateGoalRequest(BaseModel):
    goal_text: str  # Natural language goal like "我想學習 Kubernetes"


class CreateGoalResponse(BaseModel):
    goal_id: str
    parsed_goal: dict
    learning_path: dict
    success: bool
    message: str


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


class AdjustPlanRequest(BaseModel):
    adjustment_type: str
    reason: str


# Dependency injection
async def get_supabase_service() -> SupabaseService:
    return SupabaseService()


async def get_llm_service() -> LLMService:
    return LLMService()


@router.post("/goals", response_model=CreateGoalResponse)
async def create_learning_goal(
    request: CreateGoalRequest,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
    llm: LLMService = Depends(get_llm_service),
):
    """Create a new learning goal and generate learning path"""
    try:
        user_id = str(current_user["user_id"])

        # Initialize skill tree
        skill_tree = await initialize_skill_tree(supabase)

        # Parse goal
        goal_parser = GoalParser(llm, skill_tree)
        parsed_goal = await goal_parser.parse_goal(request.goal_text)

        if not parsed_goal.is_valid:
            return CreateGoalResponse(
                goal_id="",
                parsed_goal=parsed_goal.__dict__,
                learning_path={},
                success=False,
                message=parsed_goal.clarification_needed or "無法解析學習目標",
            )

        # Create goal in database
        goal_id = str(uuid.uuid4())
        supabase.client.table("learning_goals").insert(
            {
                "id": goal_id,
                "user_id": user_id,
                "title": parsed_goal.display_title,
                "description": parsed_goal.description,
                "target_skill": parsed_goal.target_skill,
                "difficulty_level": parsed_goal.difficulty_level,
                "estimated_hours": parsed_goal.estimated_hours,
                "status": "active",
            }
        ).execute()

        # Generate learning path
        path_generator = LearningPathGenerator(supabase, skill_tree)
        learning_path = await path_generator.generate_path(goal_id, parsed_goal.target_skill)

        return CreateGoalResponse(
            goal_id=goal_id,
            parsed_goal=parsed_goal.__dict__,
            learning_path={
                "id": learning_path.id,
                "stages": [
                    {
                        "name": stage.stage_name,
                        "order": stage.stage_order,
                        "description": stage.description,
                        "estimated_hours": stage.estimated_hours,
                        "skills": [skill.display_name for skill in stage.skills],
                    }
                    for stage in learning_path.stages
                ],
                "total_hours": learning_path.total_estimated_hours,
            },
            success=True,
            message="學習目標創建成功",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"創建學習目標失敗: {str(e)}"
        )


@router.get("/goals", response_model=List[LearningGoalResponse])
async def get_learning_goals(
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get all learning goals for current user"""
    try:
        user_id = str(current_user["user_id"])

        response = (
            supabase.client.table("learning_goals")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        goals = []
        for record in response.data:
            goals.append(
                LearningGoalResponse(
                    id=record["id"],
                    title=record["title"],
                    description=record["description"],
                    target_skill=record["target_skill"],
                    difficulty_level=record["difficulty_level"],
                    estimated_hours=record["estimated_hours"],
                    status=record["status"],
                    created_at=record["created_at"],
                )
            )

        return goals

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"獲取學習目標失敗: {str(e)}"
        )


@router.get("/goals/{goal_id}", response_model=dict)
async def get_learning_goal_details(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get detailed information about a specific learning goal"""
    try:
        user_id = str(current_user["user_id"])

        # Get goal
        goal_response = (
            supabase.client.table("learning_goals")
            .select("*")
            .eq("id", goal_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not goal_response.data:
            raise HTTPException(status_code=404, detail="學習目標不存在")

        # Get learning path
        skill_tree = await initialize_skill_tree(supabase)
        path_generator = LearningPathGenerator(supabase, skill_tree)
        learning_path = await path_generator.get_path_by_goal_id(goal_id)

        goal_data = goal_response.data
        path_data = None

        if learning_path:
            path_data = {
                "id": learning_path.id,
                "stages": [
                    {
                        "name": stage.stage_name,
                        "order": stage.stage_order,
                        "description": stage.description,
                        "estimated_hours": stage.estimated_hours,
                        "skills": [skill.display_name for skill in stage.skills],
                    }
                    for stage in learning_path.stages
                ],
                "total_hours": learning_path.total_estimated_hours,
            }

        return {"goal": goal_data, "learning_path": path_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取學習目標詳情失敗: {str(e)}",
        )


@router.get("/goals/{goal_id}/progress", response_model=ProgressResponse)
async def get_learning_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get learning progress for a specific goal"""
    try:
        user_id = str(current_user["user_id"])

        progress_tracker = ProgressTracker(supabase)
        progress_report = await progress_tracker.get_progress_report(user_id, goal_id)
        current_stage = await progress_tracker.get_current_stage(user_id, goal_id)

        return ProgressResponse(
            goal_id=goal_id,
            overall_completion=progress_report.overall_completion,
            current_stage=current_stage or 1,
            stages=[
                {
                    "name": stage.stage_name,
                    "order": stage.stage_order,
                    "completion_percentage": stage.completion_percentage,
                    "articles_completed": stage.articles_completed,
                    "articles_total": stage.articles_total,
                    "time_spent_hours": stage.time_spent_minutes / 60,
                    "status": stage.status.value,
                }
                for stage in progress_report.stages
            ],
            recommendations=progress_report.recommendations,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"獲取學習進度失敗: {str(e)}"
        )


@router.get("/goals/{goal_id}/recommendations", response_model=RecommendationResponse)
async def get_article_recommendations(
    goal_id: str,
    stage: Optional[int] = 1,
    limit: Optional[int] = 10,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Get article recommendations for current learning stage"""
    try:
        user_id = str(current_user["user_id"])

        # Get learning path
        skill_tree = await initialize_skill_tree(supabase)
        path_generator = LearningPathGenerator(supabase, skill_tree)
        learning_path = await path_generator.get_path_by_goal_id(goal_id)

        if not learning_path:
            raise HTTPException(status_code=404, detail="學習路徑不存在")

        # Get recommendations
        recommender = ArticleRecommender(supabase)
        recommendations = await recommender.get_recommendations(
            user_id, learning_path, stage, limit
        )

        stage_name = ""
        if stage <= len(learning_path.stages):
            stage_name = learning_path.stages[stage - 1].stage_name

        return RecommendationResponse(
            articles=[
                {
                    "id": str(rec.article.id),
                    "title": rec.article.title,
                    "url": rec.article.url,
                    "category": rec.article.category,
                    "published_at": (
                        rec.article.published_at.isoformat() if rec.article.published_at else None
                    ),
                    "relevance_score": rec.relevance_score,
                    "difficulty_match": rec.difficulty_match,
                    "reason": rec.reason,
                }
                for rec in recommendations
            ],
            stage_name=stage_name,
            total_count=len(recommendations),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"獲取文章推薦失敗: {str(e)}"
        )


@router.post("/goals/{goal_id}/articles/{article_id}/complete")
async def mark_article_complete(
    goal_id: str,
    article_id: str,
    request: CompleteArticleRequest,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Mark an article as completed"""
    try:
        user_id = str(current_user["user_id"])

        progress_tracker = ProgressTracker(supabase)
        await progress_tracker.update_article_progress(
            user_id,
            goal_id,
            article_id,
            ProgressStatus.COMPLETED,
            request.time_spent_minutes,
            request.notes,
        )

        # Also mark in article recommender
        recommender = ArticleRecommender(supabase)
        await recommender.mark_article_completed(user_id, article_id, goal_id)

        return {"success": True, "message": "文章標記為已完成"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"標記文章完成失敗: {str(e)}"
        )


@router.put("/goals/{goal_id}/adjust")
async def adjust_learning_plan(
    goal_id: str,
    request: AdjustPlanRequest,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Manually adjust learning plan"""
    try:
        user_id = str(current_user["user_id"])

        adjuster = DynamicAdjuster(supabase)
        adjusted_plan = await adjuster.analyze_and_adjust(user_id, goal_id)

        return {
            "success": True,
            "message": "學習計劃已調整",
            "adjustments": [
                {
                    "type": adj.adjustment_type.value,
                    "target": adj.target_stage,
                    "reason": adj.reason,
                    "actions": adj.recommended_actions,
                }
                for adj in adjusted_plan.adjustments
            ],
            "next_recommendations": adjusted_plan.next_recommendations,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"調整學習計劃失敗: {str(e)}"
        )


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


@router.delete("/goals/{goal_id}")
async def delete_learning_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """Delete a learning goal and its associated data"""
    try:
        user_id = str(current_user["user_id"])

        # Verify ownership
        goal_response = (
            supabase.client.table("learning_goals")
            .select("id")
            .eq("id", goal_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not goal_response.data:
            raise HTTPException(status_code=404, detail="學習目標不存在")

        # Delete goal (cascading deletes will handle related records)
        supabase.client.table("learning_goals").delete().eq("id", goal_id).execute()

        return {"success": True, "message": "學習目標已刪除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"刪除學習目標失敗: {str(e)}"
        )
