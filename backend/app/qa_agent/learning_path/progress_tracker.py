"""
Progress Tracker

Tracks learning progress, calculates completion percentages, and identifies bottlenecks.
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from app.services.supabase_service import SupabaseService


class ProgressStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class StageProgress:
    """Progress information for a learning stage"""

    stage_name: str
    stage_order: int
    completion_percentage: int
    articles_completed: int
    articles_total: int
    time_spent_minutes: int
    estimated_hours: int
    status: ProgressStatus
    bottlenecks: List[str]


@dataclass
class LearningProgressReport:
    """Comprehensive progress report"""

    goal_id: str
    overall_completion: int
    stages: List[StageProgress]
    total_time_spent_hours: float
    estimated_total_hours: int
    learning_velocity: float  # articles per week
    bottlenecks: List[str]
    recommendations: List[str]


class ProgressTracker:
    """
    Tracks and analyzes learning progress across stages and articles.
    Identifies bottlenecks and provides progress insights.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    async def get_progress_report(self, user_id: str, goal_id: str) -> LearningProgressReport:
        """
        Generate comprehensive progress report for a learning goal.

        Args:
            user_id: User ID
            goal_id: Learning goal ID

        Returns:
            Detailed progress report
        """
        # Get learning path
        path_response = (
            self.supabase.client.table("learning_paths")
            .select("*")
            .eq("goal_id", goal_id)
            .single()
            .execute()
        )
        if not path_response.data:
            raise ValueError(f"Learning path not found for goal: {goal_id}")

        path_data = path_response.data["path_data"]

        # Get all progress records for this goal
        progress_response = (
            self.supabase.client.table("learning_progress")
            .select("*")
            .eq("user_id", user_id)
            .eq("goal_id", goal_id)
            .execute()
        )
        progress_records = progress_response.data

        # Calculate stage progress
        stages = []
        total_completion = 0
        total_time_spent = 0

        for stage_data in path_data["stages"]:
            stage_progress = await self._calculate_stage_progress(
                user_id, goal_id, stage_data, progress_records
            )
            stages.append(stage_progress)
            total_completion += stage_progress.completion_percentage
            total_time_spent += stage_progress.time_spent_minutes

        # Calculate overall metrics
        overall_completion = total_completion // len(stages) if stages else 0
        total_time_hours = total_time_spent / 60
        learning_velocity = await self._calculate_learning_velocity(user_id, goal_id)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(stages)

        # Generate recommendations
        recommendations = self._generate_recommendations(stages, learning_velocity)

        return LearningProgressReport(
            goal_id=goal_id,
            overall_completion=overall_completion,
            stages=stages,
            total_time_spent_hours=total_time_hours,
            estimated_total_hours=path_data["total_hours"],
            learning_velocity=learning_velocity,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )

    async def _calculate_stage_progress(
        self, user_id: str, goal_id: str, stage_data: Dict, progress_records: List[Dict]
    ) -> StageProgress:
        """Calculate progress for a single stage"""
        stage_name = stage_data["name"]
        stage_order = stage_data["order"]

        # All completed records for this goal — deduplicate by article_id
        seen_article_ids: set = set()
        all_completed = []
        for r in progress_records:
            if r["status"] == "completed" and r.get("article_id") not in seen_article_ids:
                seen_article_ids.add(r.get("article_id"))
                all_completed.append(r)

        # Use all completed articles for progress (stage_order is unreliable from frontend)
        stage_completed = all_completed

        articles_completed = len(stage_completed)
        articles_total = max(articles_completed, 10)  # default 10 articles per stage

        # Calculate completion percentage (capped at 100)
        completion_percentage = (
            min(articles_completed / articles_total * 100, 100) if articles_total > 0 else 0
        )

        # Sum time spent
        time_spent = sum(record.get("time_spent_minutes", 0) for record in stage_completed)

        # Determine status
        if completion_percentage == 0:
            status = ProgressStatus.NOT_STARTED
        elif completion_percentage == 100:
            status = ProgressStatus.COMPLETED
        else:
            status = ProgressStatus.IN_PROGRESS

        # Identify stage-specific bottlenecks
        bottlenecks = []
        if completion_percentage < 20 and time_spent > stage_data["estimated_hours"] * 60:
            bottlenecks.append(f"{stage_name}階段進度緩慢")

        return StageProgress(
            stage_name=stage_name,
            stage_order=stage_order,
            completion_percentage=int(completion_percentage),
            articles_completed=articles_completed,
            articles_total=articles_total,
            time_spent_minutes=time_spent,
            estimated_hours=stage_data["estimated_hours"],
            status=status,
            bottlenecks=bottlenecks,
        )

    async def _get_stage_articles(self, skill_names: List[str]) -> List[str]:
        """Get article IDs relevant to stage skills"""
        try:
            article_ids = []
            seen: set = set()
            for skill in skill_names:
                for field in ("title", "ai_summary", "category"):
                    resp = (
                        self.supabase.client.table("articles")
                        .select("id")
                        .ilike(field, f"%{skill}%")
                        .limit(10)
                        .execute()
                    )
                    for row in resp.data or []:
                        if row["id"] not in seen:
                            seen.add(row["id"])
                            article_ids.append(row["id"])
            return article_ids if article_ids else ["placeholder"]
        except Exception:
            return ["placeholder"]

    async def _calculate_learning_velocity(self, user_id: str, goal_id: str) -> float:
        """Calculate articles completed per week"""
        try:
            # Get completed articles in last 4 weeks
            four_weeks_ago = datetime.now() - timedelta(weeks=4)

            response = (
                self.supabase.client.table("learning_progress")
                .select("completed_at")
                .eq("user_id", user_id)
                .eq("goal_id", goal_id)
                .eq("status", "completed")
                .gte("completed_at", four_weeks_ago.isoformat())
                .execute()
            )

            completed_count = len(response.data)
            return completed_count / 4  # articles per week
        except Exception:
            return 0.0

    def _identify_bottlenecks(self, stages: List[StageProgress]) -> List[str]:
        """Identify learning bottlenecks across stages"""
        bottlenecks = []

        for stage in stages:
            # Stage taking too long
            if stage.time_spent_minutes > stage.estimated_hours * 60 * 1.5:
                bottlenecks.append(f"{stage.stage_name}階段耗時過長")

            # Stage with low completion but high time investment
            if (
                stage.completion_percentage < 30
                and stage.time_spent_minutes > stage.estimated_hours * 30
            ):
                bottlenecks.append(f"{stage.stage_name}階段效率偏低")

            # Extend stage-specific bottlenecks
            bottlenecks.extend(stage.bottlenecks)

        return bottlenecks

    def _generate_recommendations(self, stages: List[StageProgress], velocity: float) -> List[str]:
        """Generate learning recommendations based on progress"""
        recommendations = []

        # Velocity-based recommendations
        if velocity < 1:
            recommendations.append("建議增加學習頻率，每週至少完成2-3篇文章")
        elif velocity > 5:
            recommendations.append("學習進度很好！可以考慮挑戰更高難度的內容")

        # Stage-based recommendations
        for stage in stages:
            if stage.status == ProgressStatus.NOT_STARTED and stage.stage_order == 1:
                recommendations.append(f"建議開始{stage.stage_name}階段的學習")
            elif stage.completion_percentage > 80 and stage.stage_order < len(stages):
                recommendations.append(f"即將完成{stage.stage_name}階段，可以準備進入下一階段")

        return recommendations

    async def update_article_progress(
        self,
        user_id: str,
        goal_id: str,
        article_id: str,
        status: ProgressStatus,
        time_spent_minutes: int = 0,
        notes: str = "",
        stage_order: Optional[int] = None,
    ) -> None:
        """Update progress for a specific article"""
        try:
            progress_data = {
                "user_id": user_id,
                "goal_id": goal_id,
                "article_id": article_id,
                "status": status.value,
                "time_spent_minutes": time_spent_minutes,
                "notes": notes,
                "updated_at": datetime.now().isoformat(),
            }

            if stage_order is not None:
                progress_data["stage_order"] = stage_order

            if status == ProgressStatus.COMPLETED:
                progress_data["completed_at"] = datetime.now().isoformat()
                progress_data["completion_percentage"] = 100

            try:
                self.supabase.client.table("learning_progress").upsert(
                    progress_data,
                    on_conflict="user_id,goal_id,article_id",
                ).execute()
            except Exception:
                # Fallback: retry without stage_order if column doesn't exist yet
                progress_data.pop("stage_order", None)
                self.supabase.client.table("learning_progress").upsert(
                    progress_data,
                    on_conflict="user_id,goal_id,article_id",
                ).execute()

        except Exception as e:
            raise Exception(f"Failed to update article progress: {e}")

    async def get_current_stage(self, user_id: str, goal_id: str) -> Optional[int]:
        """Get user's current learning stage"""
        try:
            report = await self.get_progress_report(user_id, goal_id)

            # Find first incomplete stage
            for stage in report.stages:
                if stage.status != ProgressStatus.COMPLETED:
                    return stage.stage_order

            # All stages completed
            return len(report.stages)

        except Exception:
            return 1  # Default to first stage

    async def get_learning_streak(self, user_id: str, goal_id: str) -> int:
        """Calculate consecutive days of learning activity"""
        try:
            # Get recent completed articles
            response = (
                self.supabase.client.table("learning_progress")
                .select("completed_at")
                .eq("user_id", user_id)
                .eq("goal_id", goal_id)
                .eq("status", "completed")
                .order("completed_at", desc=True)
                .execute()
            )

            if not response.data:
                return 0

            # Count consecutive days
            streak = 0
            current_date = datetime.now().date()

            for record in response.data:
                completed_date = datetime.fromisoformat(
                    record["completed_at"].replace("Z", "+00:00")
                ).date()

                if completed_date == current_date or completed_date == current_date - timedelta(
                    days=streak
                ):
                    if completed_date == current_date - timedelta(days=streak):
                        streak += 1
                    current_date = completed_date
                else:
                    break

            return streak

        except Exception:
            return 0
