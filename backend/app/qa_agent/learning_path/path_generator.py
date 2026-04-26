"""
Learning Path Generator

Generates structured multi-stage learning paths based on skill tree.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from app.qa_agent.learning_path.skill_tree import SkillNode, SkillTree
from app.services.supabase_service import SupabaseService


@dataclass
class LearningStage:
    """Represents a single stage in the learning path"""

    stage_name: str
    stage_order: int
    description: str
    skills: List[SkillNode]
    estimated_hours: int
    prerequisites: List[str]


@dataclass
class LearningPath:
    """Complete learning path with multiple stages"""

    id: str
    goal_id: str
    stages: List[LearningStage]
    total_stages: int
    total_estimated_hours: int
    created_at: datetime


class LearningPathGenerator:
    """
    Generates structured learning paths based on skill tree dependencies.
    Creates foundation → intermediate → advanced progression.
    """

    def __init__(self, supabase_service: SupabaseService, skill_tree: SkillTree):
        self.supabase = supabase_service
        self.skill_tree = skill_tree

    async def generate_path(self, goal_id: str, target_skill: str) -> LearningPath:
        """
        Generate a complete learning path for a target skill.

        Args:
            goal_id: ID of the learning goal
            target_skill: Target skill name

        Returns:
            LearningPath with structured stages
        """
        # Get skill progression from skill tree
        skill_stages = await self.skill_tree.get_learning_path(target_skill)

        if not skill_stages or all(len(stage) == 0 for stage in skill_stages):
            raise ValueError(f"Cannot generate learning path for skill: {target_skill}")

        # Create learning stages
        stages = []
        stage_names = ["foundation", "intermediate", "advanced"]
        stage_descriptions = ["建立基礎概念和核心技能", "深入理解和實際應用", "進階技巧和專業實戰"]

        for i, (skills, name, desc) in enumerate(
            zip(skill_stages, stage_names, stage_descriptions)
        ):
            if skills:  # Only create stage if it has skills
                stage = LearningStage(
                    stage_name=name,
                    stage_order=i + 1,
                    description=desc,
                    skills=skills,
                    estimated_hours=self.skill_tree.estimate_total_hours(skills),
                    prerequisites=self._get_stage_prerequisites(skills),
                )
                stages.append(stage)

        # Calculate total hours
        total_hours = sum(stage.estimated_hours for stage in stages)

        # Create learning path
        path = LearningPath(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            stages=stages,
            total_stages=len(stages),
            total_estimated_hours=total_hours,
            created_at=datetime.now(),
        )

        # Save to database
        await self._save_path_to_database(path)

        return path

    def _get_stage_prerequisites(self, skills: List[SkillNode]) -> List[str]:
        """Extract unique prerequisites for a stage"""
        prerequisites = set()
        for skill in skills:
            prerequisites.update(skill.prerequisites)
        return list(prerequisites)

    async def _save_path_to_database(self, path: LearningPath) -> None:
        """Save learning path and stages to database"""
        try:
            # Prepare path data for JSON storage
            path_data = {
                "target_skill": path.stages[-1].skills[-1].name if path.stages else "",
                "total_hours": path.total_estimated_hours,
                "stages": [
                    {
                        "name": stage.stage_name,
                        "order": stage.stage_order,
                        "description": stage.description,
                        "skills": [skill.name for skill in stage.skills],
                        "estimated_hours": stage.estimated_hours,
                        "prerequisites": stage.prerequisites,
                    }
                    for stage in path.stages
                ],
            }

            # Insert learning path
            self.supabase.client.table("learning_paths").insert(
                {
                    "id": path.id,
                    "goal_id": path.goal_id,
                    "path_data": path_data,
                    "total_stages": path.total_stages,
                }
            ).execute()

            # Insert individual stages
            for stage in path.stages:
                self.supabase.client.table("learning_stages").insert(
                    {
                        "id": str(uuid.uuid4()),
                        "path_id": path.id,
                        "stage_order": stage.stage_order,
                        "stage_name": stage.stage_name,
                        "stage_description": stage.description,
                        "estimated_hours": stage.estimated_hours,
                        "prerequisites": stage.prerequisites,
                    }
                ).execute()

        except Exception as e:
            raise Exception(f"Failed to save learning path: {e}")

    async def get_path_by_goal_id(self, goal_id: str) -> Optional[LearningPath]:
        """Retrieve learning path by goal ID"""
        try:
            response = (
                self.supabase.client.table("learning_paths")
                .select("*")
                .eq("goal_id", goal_id)
                .single()
                .execute()
            )

            if not response.data:
                return None

            path_record = response.data

            # Get stages
            stages_response = (
                self.supabase.client.table("learning_stages")
                .select("*")
                .eq("path_id", path_record["id"])
                .order("stage_order")
                .execute()
            )

            stages = []
            for stage_record in stages_response.data:
                # Reconstruct skills from path_data
                path_data = path_record["path_data"]
                stage_data = next(
                    (s for s in path_data["stages"] if s["order"] == stage_record["stage_order"]),
                    None,
                )

                if stage_data:
                    skills = []
                    for skill_name in stage_data["skills"]:
                        skill = await self.skill_tree.get_skill(skill_name)
                        if skill:
                            skills.append(skill)

                    stage = LearningStage(
                        stage_name=stage_record["stage_name"],
                        stage_order=stage_record["stage_order"],
                        description=stage_record["stage_description"],
                        skills=skills,
                        estimated_hours=stage_record["estimated_hours"],
                        prerequisites=stage_record["prerequisites"] or [],
                    )
                    stages.append(stage)

            return LearningPath(
                id=path_record["id"],
                goal_id=path_record["goal_id"],
                stages=stages,
                total_stages=path_record["total_stages"],
                total_estimated_hours=path_data["total_hours"],
                created_at=datetime.fromisoformat(path_record["created_at"].replace("Z", "+00:00")),
            )

        except Exception as e:
            raise Exception(f"Failed to retrieve learning path: {e}")

    async def update_path_progress(
        self, path_id: str, stage_order: int, completion_percentage: int
    ) -> None:
        """Update progress for a specific stage"""
        try:
            # This would typically update learning_progress table
            # Implementation depends on how progress tracking is structured
            pass
        except Exception as e:
            raise Exception(f"Failed to update path progress: {e}")

    def estimate_completion_date(self, path: LearningPath, hours_per_week: int = 10) -> datetime:
        """Estimate completion date based on weekly study hours"""
        weeks_needed = path.total_estimated_hours / hours_per_week
        return datetime.now() + timedelta(weeks=weeks_needed)
