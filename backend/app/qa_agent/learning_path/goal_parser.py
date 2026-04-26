"""
Goal Parser

Uses LLM to parse natural language learning goals and validate their feasibility.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from app.qa_agent.learning_path.skill_tree import SkillTree
from app.services.llm_service import LLMService


@dataclass
class ParsedGoal:
    """Parsed learning goal with extracted information"""

    target_skill: str
    display_title: str
    description: str
    difficulty_level: int
    estimated_hours: int
    is_valid: bool
    clarification_needed: Optional[str] = None


class GoalParser:
    """
    Parses natural language learning goals using LLM.
    Validates goals against skill tree and estimates learning time.
    """

    def __init__(self, llm_service: LLMService, skill_tree: SkillTree):
        self.llm = llm_service
        self.skill_tree = skill_tree

    async def parse_goal(self, user_input: str) -> ParsedGoal:
        """
        Parse natural language learning goal.

        Args:
            user_input: Natural language goal like "我想學習 Kubernetes"

        Returns:
            ParsedGoal with extracted information
        """
        # Get available skills for context
        await self.skill_tree.load_skills()
        categories = await self.skill_tree.get_categories()

        system_prompt = f"""你是學習路徑規劃助手。請分析用戶的學習目標並提取關鍵資訊。

可用的技能類別：{', '.join(categories)}

請以 JSON 格式回應，包含：
- target_skill: 目標技能名稱（英文，小寫，用連字號）
- display_title: 顯示標題（繁體中文）
- description: 學習目標描述
- difficulty_level: 難度等級 (1-5)
- estimated_hours: 預估學習時數
- is_valid: 是否為有效的學習目標
- clarification_needed: 如果目標模糊，需要澄清的問題

範例回應：
{{"target_skill": "kubernetes", "display_title": "學習 Kubernetes", "description": "學習容器編排系統 Kubernetes 的基礎概念和實際應用", "difficulty_level": 4, "estimated_hours": 80, "is_valid": true}}"""

        user_prompt = f"用戶學習目標：{user_input}"

        try:
            response = await self.llm.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return self._create_invalid_goal("無法解析學習目標格式")

            import json

            parsed_data = json.loads(json_match.group())

            # Validate required fields
            required_fields = [
                "target_skill",
                "display_title",
                "description",
                "difficulty_level",
                "estimated_hours",
                "is_valid",
            ]
            if not all(field in parsed_data for field in required_fields):
                return self._create_invalid_goal("解析結果缺少必要欄位")

            # Check if target skill exists in skill tree
            skill_exists = await self.skill_tree.get_skill(parsed_data["target_skill"])
            if not skill_exists and parsed_data["is_valid"]:
                parsed_data["is_valid"] = False
                parsed_data["clarification_needed"] = (
                    f"技能 '{parsed_data['target_skill']}' 不在我們的技能樹中。請選擇其他技能或提供更具體的描述。"
                )

            return ParsedGoal(**parsed_data)

        except Exception as e:
            return self._create_invalid_goal(f"解析過程發生錯誤：{str(e)}")

    def _create_invalid_goal(self, reason: str) -> ParsedGoal:
        """Create an invalid goal with clarification needed"""
        return ParsedGoal(
            target_skill="",
            display_title="",
            description="",
            difficulty_level=1,
            estimated_hours=0,
            is_valid=False,
            clarification_needed=reason,
        )

    async def validate_goal_feasibility(self, target_skill: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a learning goal is feasible based on skill tree.

        Returns:
            (is_feasible, reason_if_not)
        """
        skill = await self.skill_tree.get_skill(target_skill)
        if not skill:
            return False, f"技能 '{target_skill}' 不存在於技能樹中"

        # Check if dependencies form valid path
        try:
            learning_path = await self.skill_tree.get_learning_path(target_skill)
            if not learning_path or all(len(stage) == 0 for stage in learning_path):
                return False, f"無法為 '{target_skill}' 生成有效的學習路徑"

            return True, None
        except Exception as e:
            return False, f"學習路徑生成失敗：{str(e)}"

    async def estimate_total_learning_time(self, target_skill: str) -> int:
        """Estimate total learning time including prerequisites"""
        try:
            learning_path = await self.skill_tree.get_learning_path(target_skill)
            total_hours = 0

            for stage in learning_path:
                total_hours += self.skill_tree.estimate_total_hours(stage)

            return total_hours
        except Exception:
            return 0
