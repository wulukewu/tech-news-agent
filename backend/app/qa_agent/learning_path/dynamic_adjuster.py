"""
Dynamic Adjuster

Dynamically adjusts learning plans based on user progress and performance.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List

from app.qa_agent.learning_path.article_recommender import ArticleRecommender
from app.qa_agent.learning_path.progress_tracker import (
    LearningProgressReport,
    ProgressStatus,
    ProgressTracker,
)
from app.services.supabase_service import SupabaseService


class AdjustmentType(Enum):
    ACCELERATE = "accelerate"
    DECELERATE = "decelerate"
    ADD_FOUNDATION = "add_foundation"
    SKIP_REDUNDANT = "skip_redundant"
    EXTEND_PRACTICE = "extend_practice"


@dataclass
class LearningAdjustment:
    """Represents a dynamic adjustment to the learning plan"""

    adjustment_type: AdjustmentType
    target_stage: str
    reason: str
    recommended_actions: List[str]
    priority: int  # 1-5, higher is more urgent


@dataclass
class AdjustedLearningPlan:
    """Learning plan with dynamic adjustments applied"""

    goal_id: str
    original_plan: Dict
    adjustments: List[LearningAdjustment]
    modified_timeline: Dict
    next_recommendations: List[str]


class DynamicAdjuster:
    """
    Dynamically adjusts learning plans based on user progress and performance.
    Handles acceleration, deceleration, and content modification.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.progress_tracker = ProgressTracker(supabase_service)
        self.article_recommender = ArticleRecommender(supabase_service)

    async def analyze_and_adjust(self, user_id: str, goal_id: str) -> AdjustedLearningPlan:
        """
        Analyze user progress and generate dynamic adjustments.

        Args:
            user_id: User ID
            goal_id: Learning goal ID

        Returns:
            Adjusted learning plan with recommendations
        """
        # Get current progress report
        progress_report = await self.progress_tracker.get_progress_report(user_id, goal_id)

        # Get original learning path
        original_plan = await self._get_original_plan(goal_id)

        # Analyze performance patterns
        adjustments = await self._analyze_performance(user_id, progress_report)

        # Generate modified timeline
        modified_timeline = self._calculate_adjusted_timeline(original_plan, adjustments)

        # Generate next recommendations
        next_recommendations = await self._generate_next_actions(user_id, goal_id, adjustments)

        return AdjustedLearningPlan(
            goal_id=goal_id,
            original_plan=original_plan,
            adjustments=adjustments,
            modified_timeline=modified_timeline,
            next_recommendations=next_recommendations,
        )

    async def _get_original_plan(self, goal_id: str) -> Dict:
        """Get original learning path data"""
        try:
            response = (
                self.supabase.client.table("learning_paths")
                .select("path_data")
                .eq("goal_id", goal_id)
                .single()
                .execute()
            )
            return response.data["path_data"] if response.data else {}
        except Exception:
            return {}

    async def _analyze_performance(
        self, user_id: str, progress_report: LearningProgressReport
    ) -> List[LearningAdjustment]:
        """Analyze user performance and identify needed adjustments"""
        adjustments = []

        # Check overall velocity
        if progress_report.learning_velocity > 3:  # Fast learner
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.ACCELERATE,
                    target_stage="all",
                    reason="學習速度超前，可以加快進度",
                    recommended_actions=["跳過部分基礎內容", "提前接觸進階主題", "增加實戰項目"],
                    priority=3,
                )
            )
        elif progress_report.learning_velocity < 1:  # Slow learner
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.DECELERATE,
                    target_stage="current",
                    reason="學習進度較慢，需要調整節奏",
                    recommended_actions=["延長當前階段時間", "增加基礎練習", "降低學習強度"],
                    priority=4,
                )
            )

        # Analyze stage-specific issues
        for stage in progress_report.stages:
            stage_adjustments = self._analyze_stage_performance(stage)
            adjustments.extend(stage_adjustments)

        # Check for bottlenecks
        if progress_report.bottlenecks:
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.ADD_FOUNDATION,
                    target_stage="current",
                    reason="發現學習瓶頸，需要加強基礎",
                    recommended_actions=["回顧前置技能", "增加基礎練習文章", "尋求額外學習資源"],
                    priority=5,
                )
            )

        return adjustments

    def _analyze_stage_performance(self, stage) -> List[LearningAdjustment]:
        """Analyze performance for a specific stage"""
        adjustments = []

        # Stage completed very quickly
        if (
            stage.status == ProgressStatus.COMPLETED
            and stage.time_spent_minutes < stage.estimated_hours * 30
        ):  # Less than 50% of estimated time
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.SKIP_REDUNDANT,
                    target_stage=stage.stage_name,
                    reason=f"{stage.stage_name}階段完成過快，可能已掌握相關技能",
                    recommended_actions=[
                        f"跳過{stage.stage_name}階段的部分重複內容",
                        "直接進入下一階段",
                        "增加挑戰性內容",
                    ],
                    priority=2,
                )
            )

        # Stage taking too long
        elif (
            stage.time_spent_minutes > stage.estimated_hours * 90
            and stage.completion_percentage < 50  # More than 150% of estimated time
        ):
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.ADD_FOUNDATION,
                    target_stage=stage.stage_name,
                    reason=f"{stage.stage_name}階段進度緩慢，可能缺乏前置知識",
                    recommended_actions=[
                        f"為{stage.stage_name}階段增加基礎內容",
                        "複習前置技能",
                        "調整學習方法",
                    ],
                    priority=4,
                )
            )

        # Stage nearly complete but stalled
        elif stage.completion_percentage > 80 and stage.status == ProgressStatus.IN_PROGRESS:
            adjustments.append(
                LearningAdjustment(
                    adjustment_type=AdjustmentType.EXTEND_PRACTICE,
                    target_stage=stage.stage_name,
                    reason=f"{stage.stage_name}階段接近完成，建議增加實戰練習",
                    recommended_actions=[
                        f"為{stage.stage_name}階段增加實戰項目",
                        "尋找相關案例研究",
                        "準備進入下一階段",
                    ],
                    priority=3,
                )
            )

        return adjustments

    def _calculate_adjusted_timeline(
        self, original_plan: Dict, adjustments: List[LearningAdjustment]
    ) -> Dict:
        """Calculate new timeline based on adjustments"""
        modified_timeline = original_plan.copy()

        if not modified_timeline.get("stages"):
            return modified_timeline

        # Apply time adjustments
        for adjustment in adjustments:
            if adjustment.adjustment_type == AdjustmentType.ACCELERATE:
                # Reduce time by 20%
                for stage in modified_timeline["stages"]:
                    stage["estimated_hours"] = int(stage["estimated_hours"] * 0.8)
            elif adjustment.adjustment_type == AdjustmentType.DECELERATE:
                # Increase time by 30%
                for stage in modified_timeline["stages"]:
                    stage["estimated_hours"] = int(stage["estimated_hours"] * 1.3)
            elif adjustment.adjustment_type == AdjustmentType.ADD_FOUNDATION:
                # Add 20% more time for foundation
                foundation_stages = [
                    s for s in modified_timeline["stages"] if s["name"] == "foundation"
                ]
                for stage in foundation_stages:
                    stage["estimated_hours"] = int(stage["estimated_hours"] * 1.2)

        # Recalculate total hours
        total_hours = sum(stage["estimated_hours"] for stage in modified_timeline["stages"])
        modified_timeline["total_hours"] = total_hours

        return modified_timeline

    async def _generate_next_actions(
        self, user_id: str, goal_id: str, adjustments: List[LearningAdjustment]
    ) -> List[str]:
        """Generate specific next actions based on adjustments"""
        actions = []

        # Sort adjustments by priority
        adjustments.sort(key=lambda x: x.priority, reverse=True)

        # Get current stage
        current_stage = await self.progress_tracker.get_current_stage(user_id, goal_id)

        for adjustment in adjustments[:3]:  # Top 3 priority adjustments
            if adjustment.adjustment_type == AdjustmentType.ACCELERATE:
                actions.append("🚀 建議加快學習進度，可以跳過部分基礎內容")
            elif adjustment.adjustment_type == AdjustmentType.DECELERATE:
                actions.append("⏰ 建議放慢學習節奏，確保充分理解每個概念")
            elif adjustment.adjustment_type == AdjustmentType.ADD_FOUNDATION:
                actions.append("📚 建議加強基礎知識，回顧前置技能")
            elif adjustment.adjustment_type == AdjustmentType.EXTEND_PRACTICE:
                actions.append("💪 建議增加實戰練習，鞏固所學技能")
            elif adjustment.adjustment_type == AdjustmentType.SKIP_REDUNDANT:
                actions.append("⏭️ 可以跳過部分重複內容，直接進入下一階段")

        # Add stage-specific actions
        if current_stage:
            actions.append(f"📍 當前建議專注於第{current_stage}階段的學習")

        return actions

    async def apply_adjustments(
        self, user_id: str, goal_id: str, adjustments: List[LearningAdjustment]
    ) -> bool:
        """Apply adjustments to user's learning plan"""
        try:
            # Update learning path with adjustments
            adjustment_data = {
                "adjustments_applied": [
                    {
                        "type": adj.adjustment_type.value,
                        "target": adj.target_stage,
                        "reason": adj.reason,
                        "applied_at": datetime.now().isoformat(),
                    }
                    for adj in adjustments
                ],
                "last_adjustment": datetime.now().isoformat(),
            }

            # Store adjustments in learning_paths table
            self.supabase.client.table("learning_paths").update(
                {
                    "path_data": {
                        **await self._get_original_plan(goal_id),
                        "dynamic_adjustments": adjustment_data,
                    }
                }
            ).eq("goal_id", goal_id).execute()

            return True

        except Exception as e:
            print(f"Failed to apply adjustments: {e}")
            return False

    async def get_adjustment_history(self, goal_id: str) -> List[Dict]:
        """Get history of adjustments made to a learning plan"""
        try:
            response = (
                self.supabase.client.table("learning_paths")
                .select("path_data")
                .eq("goal_id", goal_id)
                .single()
                .execute()
            )

            if response.data and "dynamic_adjustments" in response.data["path_data"]:
                return response.data["path_data"]["dynamic_adjustments"].get(
                    "adjustments_applied", []
                )

            return []

        except Exception:
            return []
