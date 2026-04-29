"""Learning Path API — shared models, dependencies, and router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.learning_path import initialize_skill_tree
from app.qa_agent.learning_path.article_recommender import ArticleRecommender
from app.qa_agent.learning_path.dynamic_adjuster import DynamicAdjuster
from app.qa_agent.learning_path.path_generator import LearningPathGenerator
from app.qa_agent.learning_path.progress_tracker import ProgressStatus, ProgressTracker
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

        # Get actual recommendation count to use as articles_total
        recs = []
        try:
            goal_resp = (
                supabase.client.table("learning_goals")
                .select("target_skill")
                .eq("id", goal_id)
                .single()
                .execute()
            )
            target_skill = goal_resp.data.get("target_skill", "") if goal_resp.data else ""
            skill_tree = await initialize_skill_tree(supabase)
            learning_path = await LearningPathGenerator(supabase, skill_tree).get_path_by_goal_id(
                goal_id
            )
            if learning_path:
                recommender = ArticleRecommender(supabase)
                recs = await recommender.get_recommendations(
                    user_id, learning_path, current_stage or 1, 100, target_skill=target_skill
                )
                rec_total = len(recs)
            else:
                rec_total = None
        except Exception:
            rec_total = None

        # Get completed article IDs for this goal (once, outside the loop)
        prog_resp = (
            supabase.client.table("learning_progress")
            .select("article_id")
            .eq("user_id", user_id)
            .eq("goal_id", goal_id)
            .eq("status", "completed")
            .execute()
        )
        completed_ids = {str(r["article_id"]) for r in (prog_resp.data or [])}
        rec_ids = {str(r.article.id) for r in recs} if (rec_total is not None and recs) else None

        stages_data = []
        for stage in progress_report.stages:
            total = rec_total if rec_total is not None else stage.articles_total
            # Count only completions that are in the recommendation list
            if rec_ids is not None:
                completed = len(rec_ids & completed_ids)
            else:
                completed = min(stage.articles_completed, total)
            pct = int(completed / total * 100) if total > 0 else 0
            if pct >= 100:
                status_val = "completed"
            elif pct > 0:
                status_val = "in_progress"
            else:
                status_val = "not_started"
            stages_data.append(
                {
                    "name": stage.stage_name,
                    "order": stage.stage_order,
                    "completion_percentage": pct,
                    "articles_completed": completed,
                    "articles_total": total,
                    "time_spent_hours": stage.time_spent_minutes / 60,
                    "status": status_val,
                }
            )

        overall = (
            int(sum(s["completion_percentage"] for s in stages_data) / len(stages_data))
            if stages_data
            else 0
        )

        return ProgressResponse(
            goal_id=goal_id,
            overall_completion=overall,
            current_stage=current_stage or 1,
            stages=stages_data,
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

        # Get goal's target_skill for keyword search
        goal_resp = (
            supabase.client.table("learning_goals")
            .select("target_skill, title")
            .eq("id", goal_id)
            .single()
            .execute()
        )
        target_skill = goal_resp.data.get("target_skill", "") if goal_resp.data else ""

        # Get learning path
        skill_tree = await initialize_skill_tree(supabase)
        path_generator = LearningPathGenerator(supabase, skill_tree)
        learning_path = await path_generator.get_path_by_goal_id(goal_id)

        if not learning_path:
            raise HTTPException(status_code=404, detail="學習路徑不存在")

        # Get recommendations
        recommender = ArticleRecommender(supabase)
        recommendations = await recommender.get_recommendations(
            user_id, learning_path, stage, limit, target_skill=target_skill
        )

        # Get completed article IDs for this goal
        completed_resp = (
            supabase.client.table("learning_progress")
            .select("article_id")
            .eq("user_id", user_id)
            .eq("goal_id", goal_id)
            .eq("status", "completed")
            .execute()
        )
        completed_ids = {str(r["article_id"]) for r in (completed_resp.data or [])}

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
                    "is_completed": str(rec.article.id) in completed_ids,
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
    """Toggle article completion status"""
    try:
        user_id = str(current_user["user_id"])

        # Check current status
        existing = (
            supabase.client.table("learning_progress")
            .select("status")
            .eq("user_id", user_id)
            .eq("goal_id", goal_id)
            .eq("article_id", article_id)
            .execute()
        )
        is_completed = existing.data and existing.data[0]["status"] == "completed"

        progress_tracker = ProgressTracker(supabase)
        if is_completed:
            # Uncheck: revert to not_started
            await progress_tracker.update_article_progress(
                user_id, goal_id, article_id, ProgressStatus.NOT_STARTED, 0, "", request.stage_order
            )
            return {"success": True, "completed": False, "message": "文章標記為未完成"}
        else:
            await progress_tracker.update_article_progress(
                user_id,
                goal_id,
                article_id,
                ProgressStatus.COMPLETED,
                request.time_spent_minutes,
                request.notes,
                request.stage_order,
            )
            recommender = ArticleRecommender(supabase)
            await recommender.mark_article_completed(user_id, article_id, goal_id)
            return {"success": True, "completed": True, "message": "文章標記為已完成"}

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
