"""Learning Path API — shared models, dependencies, and router."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.learning_path import initialize_skill_tree
from app.qa_agent.learning_path.goal_parser import GoalParser
from app.qa_agent.learning_path.path_generator import LearningPathGenerator
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
            suggested_feeds=_get_suggested_feeds(parsed_goal.target_skill),
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


# Curated feed suggestions per skill keyword
_FEED_SUGGESTIONS: dict[str, list[dict]] = {
    "kubernetes": [
        {"name": "Kubernetes Blog", "url": "https://kubernetes.io/feed.xml", "category": "DevOps"},
        {"name": "CNCF Blog", "url": "https://www.cncf.io/feed/", "category": "DevOps"},
    ],
    "docker": [
        {"name": "Docker Blog", "url": "https://www.docker.com/blog/feed/", "category": "DevOps"},
    ],
    "react": [
        {"name": "React Blog", "url": "https://react.dev/rss.xml", "category": "Frontend"},
        {"name": "CSS-Tricks", "url": "https://css-tricks.com/feed/", "category": "Frontend"},
    ],
    "python": [
        {"name": "Real Python", "url": "https://realpython.com/atom.xml", "category": "Backend"},
        {
            "name": "Python Blog",
            "url": "https://blog.python.org/feeds/posts/default",
            "category": "Backend",
        },
    ],
    "nextjs": [
        {"name": "Vercel Blog", "url": "https://vercel.com/atom", "category": "Frontend"},
    ],
    "aws": [
        {"name": "AWS Blog", "url": "https://aws.amazon.com/blogs/aws/feed/", "category": "Cloud"},
    ],
    "machine-learning": [
        {
            "name": "Towards Data Science",
            "url": "https://towardsdatascience.com/feed",
            "category": "AI/ML",
        },
        {
            "name": "Google AI Blog",
            "url": "https://blog.google/technology/ai/rss/",
            "category": "AI/ML",
        },
    ],
    "postgresql": [
        {
            "name": "PostgreSQL News",
            "url": "https://www.postgresql.org/news.rss",
            "category": "Database",
        },
    ],
}


def _get_suggested_feeds(target_skill: str) -> list[dict]:
    """Return curated feed suggestions for a given skill."""
    skill_lower = target_skill.lower().replace(" ", "-")
    for key, feeds in _FEED_SUGGESTIONS.items():
        if key in skill_lower or skill_lower in key:
            return feeds
    return []
