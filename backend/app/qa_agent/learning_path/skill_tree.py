"""
Skill Tree Model

Defines skill nodes and prerequisite dependencies for learning path generation.
Supports multi-level skill structure (foundation → intermediate → advanced).
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from app.services.supabase_service import SupabaseService


class DifficultyLevel(Enum):
    """Skill difficulty levels"""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5


@dataclass
class SkillNode:
    """Represents a single skill in the skill tree"""

    name: str
    display_name: str
    description: str
    category: str
    difficulty_level: DifficultyLevel
    estimated_hours: int
    prerequisites: List[str]
    tags: List[str]
    is_active: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            "skill_name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "difficulty_level": self.difficulty_level.value,
            "estimated_hours": self.estimated_hours,
            "prerequisites": self.prerequisites,
            "tags": self.tags,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SkillNode":
        """Create SkillNode from database record"""
        return cls(
            name=data["skill_name"],
            display_name=data["display_name"],
            description=data["description"],
            category=data["category"],
            difficulty_level=DifficultyLevel(data["difficulty_level"]),
            estimated_hours=data["estimated_hours"],
            prerequisites=data["prerequisites"] or [],
            tags=data["tags"] or [],
            is_active=data["is_active"],
        )


class SkillTree:
    """
    Skill tree and dependency relationship model.
    Manages skill nodes, validates dependencies, and generates learning paths.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self._skills: Dict[str, SkillNode] = {}
        self._loaded = False

    async def load_skills(self) -> None:
        """Load all skills from database"""
        try:
            response = (
                self.supabase.client.table("skill_tree").select("*").eq("is_active", True).execute()
            )

            self._skills = {}
            for record in response.data:
                skill = SkillNode.from_dict(record)
                self._skills[skill.name] = skill

            self._loaded = True
        except Exception as e:
            raise Exception(f"Failed to load skill tree: {e}")

    async def get_skill(self, skill_name: str) -> Optional[SkillNode]:
        """Get a specific skill by name"""
        if not self._loaded:
            await self.load_skills()

        return self._skills.get(skill_name)

    async def get_skills_by_category(self, category: str) -> List[SkillNode]:
        """Get all skills in a specific category"""
        if not self._loaded:
            await self.load_skills()

        return [skill for skill in self._skills.values() if skill.category == category]

    async def get_prerequisites(self, skill_name: str) -> List[SkillNode]:
        """Get all prerequisite skills for a given skill"""
        skill = await self.get_skill(skill_name)
        if not skill:
            return []

        prerequisites = []
        for prereq_name in skill.prerequisites:
            prereq_skill = await self.get_skill(prereq_name)
            if prereq_skill:
                prerequisites.append(prereq_skill)

        return prerequisites

    async def get_learning_path(self, target_skill: str) -> List[List[SkillNode]]:
        """
        Generate a structured learning path for a target skill.
        Returns skills organized by difficulty levels (foundation → intermediate → advanced).
        """
        if not self._loaded:
            await self.load_skills()

        target = await self.get_skill(target_skill)
        if not target:
            raise ValueError(f"Skill '{target_skill}' not found in skill tree")

        # Collect all required skills using DFS
        required_skills = []
        visited = set()

        async def collect_dependencies(skill_name: str):
            if skill_name in visited:
                return
            visited.add(skill_name)

            skill = await self.get_skill(skill_name)
            if skill:
                required_skills.append(skill)
                for prereq in skill.prerequisites:
                    await collect_dependencies(prereq)

        await collect_dependencies(target_skill)

        # Organize by difficulty levels
        foundation = [
            s for s in required_skills if s.difficulty_level in [DifficultyLevel.BEGINNER]
        ]
        intermediate = [
            s for s in required_skills if s.difficulty_level in [DifficultyLevel.INTERMEDIATE]
        ]
        advanced = [
            s
            for s in required_skills
            if s.difficulty_level
            in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT, DifficultyLevel.MASTER]
        ]

        # Sort within each level by estimated hours (easier first)
        foundation.sort(key=lambda x: x.estimated_hours)
        intermediate.sort(key=lambda x: x.estimated_hours)
        advanced.sort(key=lambda x: x.estimated_hours)

        return [foundation, intermediate, advanced]

    async def validate_dependencies(self, skill_name: str) -> bool:
        """Validate that all dependencies for a skill exist and form no cycles"""
        if not self._loaded:
            await self.load_skills()

        visited = set()
        rec_stack = set()

        async def has_cycle(current_skill: str) -> bool:
            if current_skill in rec_stack:
                return True
            if current_skill in visited:
                return False

            visited.add(current_skill)
            rec_stack.add(current_skill)

            skill = await self.get_skill(current_skill)
            if skill:
                for prereq in skill.prerequisites:
                    if await has_cycle(prereq):
                        return True

            rec_stack.remove(current_skill)
            return False

        return not await has_cycle(skill_name)

    async def add_skill(self, skill: SkillNode) -> bool:
        """Add a new skill to the tree"""
        try:
            # Validate dependencies
            if not await self.validate_dependencies(skill.name):
                raise ValueError(f"Adding skill '{skill.name}' would create a dependency cycle")

            # Insert into database
            self.supabase.client.table("skill_tree").insert(skill.to_dict()).execute()

            # Update local cache
            self._skills[skill.name] = skill
            return True
        except Exception as e:
            raise Exception(f"Failed to add skill '{skill.name}': {e}")

    async def get_categories(self) -> List[str]:
        """Get all available skill categories"""
        if not self._loaded:
            await self.load_skills()

        categories = set(skill.category for skill in self._skills.values())
        return sorted(list(categories))

    def estimate_total_hours(self, skills: List[SkillNode]) -> int:
        """Calculate total estimated learning hours for a list of skills"""
        return sum(skill.estimated_hours for skill in skills)


# Predefined skill tree data for common tech skills
PREDEFINED_SKILLS = [
    # Frontend Skills
    SkillNode(
        "html",
        "HTML",
        "HyperText Markup Language basics",
        "frontend",
        DifficultyLevel.BEGINNER,
        20,
        [],
        ["web", "markup"],
    ),
    SkillNode(
        "css",
        "CSS",
        "Cascading Style Sheets for styling",
        "frontend",
        DifficultyLevel.BEGINNER,
        30,
        ["html"],
        ["web", "styling"],
    ),
    SkillNode(
        "javascript",
        "JavaScript",
        "Programming language for web interactivity",
        "frontend",
        DifficultyLevel.INTERMEDIATE,
        60,
        ["html", "css"],
        ["web", "programming"],
    ),
    SkillNode(
        "react",
        "React",
        "JavaScript library for building user interfaces",
        "frontend",
        DifficultyLevel.INTERMEDIATE,
        40,
        ["javascript"],
        ["web", "framework", "ui"],
    ),
    SkillNode(
        "nextjs",
        "Next.js",
        "React framework for production",
        "frontend",
        DifficultyLevel.ADVANCED,
        35,
        ["react"],
        ["web", "framework", "ssr"],
    ),
    # Backend Skills
    SkillNode(
        "python",
        "Python",
        "General-purpose programming language",
        "backend",
        DifficultyLevel.BEGINNER,
        50,
        [],
        ["programming", "scripting"],
    ),
    SkillNode(
        "fastapi",
        "FastAPI",
        "Modern Python web framework",
        "backend",
        DifficultyLevel.INTERMEDIATE,
        30,
        ["python"],
        ["web", "api", "framework"],
    ),
    SkillNode(
        "postgresql",
        "PostgreSQL",
        "Advanced open source database",
        "backend",
        DifficultyLevel.INTERMEDIATE,
        40,
        [],
        ["database", "sql"],
    ),
    SkillNode(
        "redis",
        "Redis",
        "In-memory data structure store",
        "backend",
        DifficultyLevel.INTERMEDIATE,
        25,
        [],
        ["database", "cache"],
    ),
    # DevOps Skills
    SkillNode(
        "docker",
        "Docker",
        "Containerization platform",
        "devops",
        DifficultyLevel.INTERMEDIATE,
        35,
        [],
        ["containers", "deployment"],
    ),
    SkillNode(
        "kubernetes",
        "Kubernetes",
        "Container orchestration system",
        "devops",
        DifficultyLevel.ADVANCED,
        80,
        ["docker"],
        ["containers", "orchestration"],
    ),
    SkillNode(
        "aws",
        "AWS",
        "Amazon Web Services cloud platform",
        "devops",
        DifficultyLevel.ADVANCED,
        100,
        [],
        ["cloud", "infrastructure"],
    ),
    # Data Skills
    SkillNode(
        "sql",
        "SQL",
        "Structured Query Language",
        "data",
        DifficultyLevel.BEGINNER,
        30,
        [],
        ["database", "query"],
    ),
    SkillNode(
        "pandas",
        "Pandas",
        "Python data manipulation library",
        "data",
        DifficultyLevel.INTERMEDIATE,
        40,
        ["python"],
        ["data-analysis", "python"],
    ),
    SkillNode(
        "machine-learning",
        "Machine Learning",
        "AI and ML fundamentals",
        "data",
        DifficultyLevel.ADVANCED,
        120,
        ["python", "pandas"],
        ["ai", "ml", "data-science"],
    ),
]


async def initialize_skill_tree(supabase_service: SupabaseService) -> SkillTree:
    """Initialize skill tree with predefined skills"""
    skill_tree = SkillTree(supabase_service)

    try:
        # Check if skills already exist
        response = (
            supabase_service.client.table("skill_tree").select("skill_name").limit(1).execute()
        )

        if not response.data:
            # Insert predefined skills
            for skill in PREDEFINED_SKILLS:
                await skill_tree.add_skill(skill)

        await skill_tree.load_skills()
        return skill_tree
    except Exception as e:
        raise Exception(f"Failed to initialize skill tree: {e}")
