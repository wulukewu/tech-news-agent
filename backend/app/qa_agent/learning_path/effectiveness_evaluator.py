"""
Learning Effectiveness Evaluator

Calculates learning efficiency metrics and generates performance reports.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Tuple

from app.qa_agent.learning_path.progress_tracker import LearningProgressReport, ProgressTracker
from app.services.supabase_service import SupabaseService


class PerformanceLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    NEEDS_IMPROVEMENT = "needs_improvement"


@dataclass
class EfficiencyMetrics:
    """Learning efficiency metrics"""

    time_efficiency: float  # actual vs estimated time ratio
    completion_rate: float  # percentage of planned content completed
    retention_score: float  # estimated knowledge retention
    consistency_score: float  # learning consistency over time
    difficulty_progression: float  # ability to handle increasing difficulty


@dataclass
class StrengthWeaknessAnalysis:
    """Analysis of learning strengths and weaknesses"""

    strengths: List[str]
    weaknesses: List[str]
    skill_proficiency: Dict[str, float]  # skill -> proficiency score (0-1)
    learning_style_indicators: Dict[str, float]


@dataclass
class StagePerformanceReport:
    """Performance report for a single learning stage"""

    stage_name: str
    performance_level: PerformanceLevel
    efficiency_metrics: EfficiencyMetrics
    time_actual_vs_estimated: Tuple[int, int]  # (actual_minutes, estimated_minutes)
    key_achievements: List[str]
    improvement_areas: List[str]


@dataclass
class ComprehensiveEvaluationReport:
    """Complete learning effectiveness evaluation"""

    goal_id: str
    user_id: str
    evaluation_date: datetime
    overall_performance: PerformanceLevel
    efficiency_metrics: EfficiencyMetrics
    stage_reports: List[StagePerformanceReport]
    strength_weakness_analysis: StrengthWeaknessAnalysis
    learning_trajectory: List[Tuple[datetime, float]]  # (date, performance_score)
    recommendations: List[str]
    next_steps: List[str]


class LearningEffectivenessEvaluator:
    """
    Evaluates learning effectiveness and generates comprehensive performance reports.
    Analyzes efficiency, identifies strengths/weaknesses, and provides optimization suggestions.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.progress_tracker = ProgressTracker(supabase_service)

    async def generate_evaluation_report(
        self, user_id: str, goal_id: str
    ) -> ComprehensiveEvaluationReport:
        """
        Generate comprehensive learning effectiveness evaluation.

        Args:
            user_id: User ID
            goal_id: Learning goal ID

        Returns:
            Complete evaluation report with metrics and recommendations
        """
        # Get progress report
        progress_report = await self.progress_tracker.get_progress_report(user_id, goal_id)

        # Calculate efficiency metrics
        efficiency_metrics = await self._calculate_efficiency_metrics(
            user_id, goal_id, progress_report
        )

        # Analyze stage performance
        stage_reports = await self._analyze_stage_performance(user_id, goal_id, progress_report)

        # Perform strength/weakness analysis
        strength_weakness = await self._analyze_strengths_weaknesses(
            user_id, goal_id, stage_reports
        )

        # Calculate learning trajectory
        trajectory = await self._calculate_learning_trajectory(user_id, goal_id)

        # Determine overall performance level
        overall_performance = self._determine_overall_performance(efficiency_metrics, stage_reports)

        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            efficiency_metrics, strength_weakness
        )
        next_steps = self._generate_next_steps(stage_reports, overall_performance)

        return ComprehensiveEvaluationReport(
            goal_id=goal_id,
            user_id=user_id,
            evaluation_date=datetime.now(),
            overall_performance=overall_performance,
            efficiency_metrics=efficiency_metrics,
            stage_reports=stage_reports,
            strength_weakness_analysis=strength_weakness,
            learning_trajectory=trajectory,
            recommendations=recommendations,
            next_steps=next_steps,
        )

    async def _calculate_efficiency_metrics(
        self, user_id: str, goal_id: str, progress_report: LearningProgressReport
    ) -> EfficiencyMetrics:
        """Calculate learning efficiency metrics"""

        # Time efficiency: actual vs estimated time
        actual_hours = progress_report.total_time_spent_hours
        estimated_hours = progress_report.estimated_total_hours
        time_efficiency = estimated_hours / actual_hours if actual_hours > 0 else 0

        # Completion rate
        completion_rate = progress_report.overall_completion / 100

        # Retention score (estimated based on review patterns)
        retention_score = await self._estimate_retention_score(user_id, goal_id)

        # Consistency score (based on learning frequency)
        consistency_score = await self._calculate_consistency_score(user_id, goal_id)

        # Difficulty progression (ability to handle increasing complexity)
        difficulty_progression = await self._calculate_difficulty_progression(user_id, goal_id)

        return EfficiencyMetrics(
            time_efficiency=min(time_efficiency, 2.0),  # Cap at 2x efficiency
            completion_rate=completion_rate,
            retention_score=retention_score,
            consistency_score=consistency_score,
            difficulty_progression=difficulty_progression,
        )

    async def _estimate_retention_score(self, user_id: str, goal_id: str) -> float:
        """Estimate knowledge retention based on review patterns"""
        try:
            # Get articles completed more than 2 weeks ago
            two_weeks_ago = datetime.now() - timedelta(weeks=2)

            old_articles_response = (
                self.supabase.client.table("learning_progress")
                .select("article_id")
                .eq("user_id", user_id)
                .eq("goal_id", goal_id)
                .eq("status", "completed")
                .lt("completed_at", two_weeks_ago.isoformat())
                .execute()
            )

            if not old_articles_response.data:
                return 0.8  # Default score for new learners

            # Check how many were revisited (simplified heuristic)
            old_article_ids = [record["article_id"] for record in old_articles_response.data]

            # In a real implementation, would check for re-reading or related article engagement
            # For now, use a simplified calculation based on completion consistency
            return min(0.9, 0.5 + (len(old_article_ids) * 0.05))

        except Exception:
            return 0.7  # Default retention score

    async def _calculate_consistency_score(self, user_id: str, goal_id: str) -> float:
        """Calculate learning consistency over time"""
        try:
            # Get completion dates for last 4 weeks
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

            if not response.data:
                return 0.0

            # Group by week and calculate consistency
            weekly_counts = [0, 0, 0, 0]  # Last 4 weeks

            for record in response.data:
                completed_date = datetime.fromisoformat(
                    record["completed_at"].replace("Z", "+00:00")
                )
                weeks_ago = (datetime.now() - completed_date).days // 7
                if 0 <= weeks_ago < 4:
                    weekly_counts[weeks_ago] += 1

            # Calculate consistency (lower variance = higher consistency)
            if sum(weekly_counts) == 0:
                return 0.0

            avg_weekly = sum(weekly_counts) / 4
            variance = sum((count - avg_weekly) ** 2 for count in weekly_counts) / 4
            consistency = max(0, 1 - (variance / (avg_weekly + 1)))

            return consistency

        except Exception:
            return 0.5

    async def _calculate_difficulty_progression(self, user_id: str, goal_id: str) -> float:
        """Calculate ability to handle increasing difficulty"""
        try:
            # Get completed articles with their difficulty levels
            response = (
                self.supabase.client.table("learning_progress")
                .select("article_id, completed_at")
                .eq("user_id", user_id)
                .eq("goal_id", goal_id)
                .eq("status", "completed")
                .order("completed_at")
                .execute()
            )

            if len(response.data) < 3:
                return 0.5  # Not enough data

            # In a real implementation, would get actual article difficulty levels
            # For now, simulate progression analysis
            progression_score = min(1.0, len(response.data) * 0.1)
            return progression_score

        except Exception:
            return 0.5

    async def _analyze_stage_performance(
        self, user_id: str, goal_id: str, progress_report: LearningProgressReport
    ) -> List[StagePerformanceReport]:
        """Analyze performance for each learning stage"""
        stage_reports = []

        for stage in progress_report.stages:
            # Calculate stage efficiency
            actual_minutes = stage.time_spent_minutes
            estimated_minutes = stage.estimated_hours * 60

            stage_efficiency = EfficiencyMetrics(
                time_efficiency=estimated_minutes / actual_minutes if actual_minutes > 0 else 0,
                completion_rate=stage.completion_percentage / 100,
                retention_score=0.8,  # Simplified
                consistency_score=0.7,  # Simplified
                difficulty_progression=0.6,  # Simplified
            )

            # Determine performance level
            performance_level = self._determine_stage_performance_level(
                stage_efficiency, stage.completion_percentage
            )

            # Generate achievements and improvement areas
            achievements = self._identify_stage_achievements(stage)
            improvements = self._identify_stage_improvements(stage)

            stage_report = StagePerformanceReport(
                stage_name=stage.stage_name,
                performance_level=performance_level,
                efficiency_metrics=stage_efficiency,
                time_actual_vs_estimated=(actual_minutes, estimated_minutes),
                key_achievements=achievements,
                improvement_areas=improvements,
            )

            stage_reports.append(stage_report)

        return stage_reports

    def _determine_stage_performance_level(
        self, efficiency: EfficiencyMetrics, completion: int
    ) -> PerformanceLevel:
        """Determine performance level for a stage"""
        if completion >= 90 and efficiency.time_efficiency >= 1.2:
            return PerformanceLevel.EXCELLENT
        elif completion >= 80 and efficiency.time_efficiency >= 1.0:
            return PerformanceLevel.GOOD
        elif completion >= 60 and efficiency.time_efficiency >= 0.8:
            return PerformanceLevel.AVERAGE
        elif completion >= 40:
            return PerformanceLevel.BELOW_AVERAGE
        else:
            return PerformanceLevel.NEEDS_IMPROVEMENT

    def _identify_stage_achievements(self, stage) -> List[str]:
        """Identify key achievements for a stage"""
        achievements = []

        if stage.completion_percentage >= 90:
            achievements.append(f"優秀完成{stage.stage_name}階段")
        elif stage.completion_percentage >= 70:
            achievements.append(f"良好完成{stage.stage_name}階段大部分內容")

        if stage.time_spent_minutes < stage.estimated_hours * 45:  # Less than 75% of estimated time
            achievements.append("學習效率優異")

        return achievements

    def _identify_stage_improvements(self, stage) -> List[str]:
        """Identify improvement areas for a stage"""
        improvements = []

        if stage.completion_percentage < 50:
            improvements.append(f"需要加強{stage.stage_name}階段的學習")

        if (
            stage.time_spent_minutes > stage.estimated_hours * 90
        ):  # More than 150% of estimated time
            improvements.append("可以提升學習效率")

        if stage.bottlenecks:
            improvements.extend([f"需要解決：{bottleneck}" for bottleneck in stage.bottlenecks])

        return improvements

    async def _analyze_strengths_weaknesses(
        self, user_id: str, goal_id: str, stage_reports: List[StagePerformanceReport]
    ) -> StrengthWeaknessAnalysis:
        """Analyze learning strengths and weaknesses"""
        strengths = []
        weaknesses = []
        skill_proficiency = {}
        learning_style = {}

        # Analyze across stages
        excellent_stages = [
            s for s in stage_reports if s.performance_level == PerformanceLevel.EXCELLENT
        ]
        weak_stages = [
            s
            for s in stage_reports
            if s.performance_level
            in [PerformanceLevel.BELOW_AVERAGE, PerformanceLevel.NEEDS_IMPROVEMENT]
        ]

        if excellent_stages:
            strengths.append(f"在{', '.join([s.stage_name for s in excellent_stages])}階段表現優異")

        if weak_stages:
            weaknesses.append(f"在{', '.join([s.stage_name for s in weak_stages])}階段需要改進")

        # Analyze time efficiency patterns
        efficient_stages = [s for s in stage_reports if s.efficiency_metrics.time_efficiency > 1.2]
        if efficient_stages:
            strengths.append("學習效率高，能快速掌握新概念")

        slow_stages = [s for s in stage_reports if s.efficiency_metrics.time_efficiency < 0.8]
        if slow_stages:
            weaknesses.append("學習節奏較慢，需要更多時間消化內容")

        # Simplified skill proficiency (would be more sophisticated in real implementation)
        for stage in stage_reports:
            skill_proficiency[stage.stage_name] = stage.efficiency_metrics.completion_rate

        # Learning style indicators (simplified)
        learning_style = {
            "visual_learner": 0.7,  # Would be calculated based on article types preferred
            "hands_on_learner": 0.8,  # Based on practical content engagement
            "theoretical_learner": 0.6,  # Based on conceptual content performance
        }

        return StrengthWeaknessAnalysis(
            strengths=strengths,
            weaknesses=weaknesses,
            skill_proficiency=skill_proficiency,
            learning_style_indicators=learning_style,
        )

    async def _calculate_learning_trajectory(
        self, user_id: str, goal_id: str
    ) -> List[Tuple[datetime, float]]:
        """Calculate learning performance trajectory over time"""
        try:
            # Get completion history
            response = (
                self.supabase.client.table("learning_progress")
                .select("completed_at")
                .eq("user_id", user_id)
                .eq("goal_id", goal_id)
                .eq("status", "completed")
                .order("completed_at")
                .execute()
            )

            trajectory = []
            cumulative_score = 0

            for i, record in enumerate(response.data):
                completed_date = datetime.fromisoformat(
                    record["completed_at"].replace("Z", "+00:00")
                )
                # Simplified performance score calculation
                cumulative_score = min(1.0, (i + 1) * 0.1)
                trajectory.append((completed_date, cumulative_score))

            return trajectory

        except Exception:
            return []

    def _determine_overall_performance(
        self, efficiency: EfficiencyMetrics, stage_reports: List[StagePerformanceReport]
    ) -> PerformanceLevel:
        """Determine overall performance level"""
        if not stage_reports:
            return PerformanceLevel.AVERAGE

        # Calculate average performance across stages
        performance_scores = {
            PerformanceLevel.EXCELLENT: 5,
            PerformanceLevel.GOOD: 4,
            PerformanceLevel.AVERAGE: 3,
            PerformanceLevel.BELOW_AVERAGE: 2,
            PerformanceLevel.NEEDS_IMPROVEMENT: 1,
        }

        avg_score = sum(
            performance_scores[stage.performance_level] for stage in stage_reports
        ) / len(stage_reports)

        if avg_score >= 4.5:
            return PerformanceLevel.EXCELLENT
        elif avg_score >= 3.5:
            return PerformanceLevel.GOOD
        elif avg_score >= 2.5:
            return PerformanceLevel.AVERAGE
        elif avg_score >= 1.5:
            return PerformanceLevel.BELOW_AVERAGE
        else:
            return PerformanceLevel.NEEDS_IMPROVEMENT

    def _generate_optimization_recommendations(
        self, efficiency: EfficiencyMetrics, strength_weakness: StrengthWeaknessAnalysis
    ) -> List[str]:
        """Generate learning optimization recommendations"""
        recommendations = []

        # Time efficiency recommendations
        if efficiency.time_efficiency < 0.8:
            recommendations.append("建議優化學習方法，提高時間效率")
        elif efficiency.time_efficiency > 1.5:
            recommendations.append("學習效率很高，可以挑戰更高難度的內容")

        # Consistency recommendations
        if efficiency.consistency_score < 0.6:
            recommendations.append("建議建立更規律的學習習慣")

        # Retention recommendations
        if efficiency.retention_score < 0.7:
            recommendations.append("建議增加複習和實踐，提高知識保持率")

        # Strength-based recommendations
        if "效率高" in " ".join(strength_weakness.strengths):
            recommendations.append("發揮學習效率優勢，可以擴展學習範圍")

        return recommendations

    def _generate_next_steps(
        self, stage_reports: List[StagePerformanceReport], overall_performance: PerformanceLevel
    ) -> List[str]:
        """Generate specific next steps"""
        next_steps = []

        # Find current stage
        incomplete_stages = [s for s in stage_reports if s.efficiency_metrics.completion_rate < 1.0]

        if incomplete_stages:
            current_stage = incomplete_stages[0]
            next_steps.append(f"專注完成{current_stage.stage_name}階段的剩餘內容")

            if current_stage.improvement_areas:
                next_steps.extend([f"改進：{area}" for area in current_stage.improvement_areas[:2]])
        else:
            next_steps.append("所有階段已完成，可以考慮進階學習或新的學習目標")

        # Performance-based next steps
        if overall_performance == PerformanceLevel.EXCELLENT:
            next_steps.append("表現優異！可以考慮成為導師或分享學習經驗")
        elif overall_performance == PerformanceLevel.NEEDS_IMPROVEMENT:
            next_steps.append("建議尋求額外支援或調整學習策略")

        return next_steps
