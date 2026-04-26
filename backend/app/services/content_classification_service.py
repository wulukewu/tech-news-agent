import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List

from ..schemas.article import ArticleSchema
from ..services.llm_service import LLMService
from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class ContentType(Enum):
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    NEWS = "news"
    REFERENCE = "reference"
    PROJECT = "project"
    OPINION = "opinion"


class DifficultyLevel(Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class EducationalFeatures:
    has_code_examples: bool
    has_step_by_step: bool
    has_practical_exercises: bool
    has_visual_aids: bool
    estimated_reading_time: int
    prerequisite_skills: List[str]


@dataclass
class ArticleClassification:
    article_id: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    learning_value_score: float
    educational_features: EducationalFeatures
    confidence_score: float
    classification_timestamp: datetime


class ContentClassificationService:
    """LLM-powered content classification for educational value assessment."""

    def __init__(self, llm_service: LLMService, supabase_service: SupabaseService):
        self.llm = llm_service
        self.supabase = supabase_service
        self.classification_cache: Dict[str, ArticleClassification] = {}

    async def classify_article(self, article: ArticleSchema) -> ArticleClassification:
        """Classify article for educational value and learning characteristics."""
        try:
            # Check cache first
            if article.id in self.classification_cache:
                return self.classification_cache[article.id]

            # Check database
            existing = (
                self.supabase.client.table("article_classifications")
                .select("*")
                .eq("article_id", article.id)
                .execute()
            )

            if existing.data:
                return self._parse_classification(existing.data[0])

            # Classify with LLM
            system_prompt = """You are an educational content analyst. Analyze the given article and classify it for learning value.

Classify the article on these dimensions:
1. Content Type: tutorial, guide, news, reference, project, opinion
2. Difficulty Level: beginner (1), intermediate (2), advanced (3), expert (4)
3. Learning Value Score: 0.0-1.0 based on educational utility
4. Educational Features: code examples, step-by-step instructions, practical exercises, visual aids
5. Estimated Reading Time: in minutes
6. Prerequisite Skills: required background knowledge

Return JSON format with confidence score (0.0-1.0)."""

            user_prompt = f"""
Title: {article.title}
Content: {article.content[:2000]}...
URL: {article.url}

Analyze this article and return JSON with:
{{
    "content_type": "tutorial|guide|news|reference|project|opinion",
    "difficulty_level": 1-4,
    "learning_value_score": 0.0-1.0,
    "confidence_score": 0.0-1.0,
    "educational_features": {{
        "has_code_examples": boolean,
        "has_step_by_step": boolean,
        "has_practical_exercises": boolean,
        "has_visual_aids": boolean,
        "estimated_reading_time": minutes,
        "prerequisite_skills": ["skill1", "skill2"]
    }}
}}"""

            response = await self.llm.generate_response(
                system_prompt=system_prompt, user_prompt=user_prompt, model="llama-3.1-8b-instant"
            )

            # Parse response
            try:
                classification_data = json.loads(response)
            except json.JSONDecodeError:
                # Fallback classification
                classification_data = self._fallback_classification(article)

            # Create classification object
            classification = ArticleClassification(
                article_id=article.id,
                content_type=ContentType(classification_data["content_type"]),
                difficulty_level=DifficultyLevel(classification_data["difficulty_level"]),
                learning_value_score=classification_data["learning_value_score"],
                educational_features=EducationalFeatures(
                    **classification_data["educational_features"]
                ),
                confidence_score=classification_data["confidence_score"],
                classification_timestamp=datetime.now(),
            )

            # Store in database
            await self._store_classification(classification)

            # Cache result
            self.classification_cache[article.id] = classification

            return classification

        except Exception as e:
            logger.error(f"Failed to classify article {article.id}: {e}")
            return self._fallback_classification(article)

    def _fallback_classification(self, article: ArticleSchema) -> ArticleClassification:
        """Fallback classification based on simple heuristics."""
        title_lower = article.title.lower()
        content_lower = article.content.lower()

        # Determine content type
        if any(word in title_lower for word in ["tutorial", "how to", "step by step"]):
            content_type = ContentType.TUTORIAL
            learning_value = 0.8
        elif any(word in title_lower for word in ["guide", "introduction", "getting started"]):
            content_type = ContentType.GUIDE
            learning_value = 0.7
        elif any(word in title_lower for word in ["reference", "documentation", "api"]):
            content_type = ContentType.REFERENCE
            learning_value = 0.6
        elif any(word in title_lower for word in ["project", "build", "create"]):
            content_type = ContentType.PROJECT
            learning_value = 0.9
        else:
            content_type = ContentType.NEWS
            learning_value = 0.3

        # Determine difficulty
        if any(word in title_lower for word in ["beginner", "intro", "basics"]):
            difficulty = DifficultyLevel.BEGINNER
        elif any(word in title_lower for word in ["advanced", "expert", "deep dive"]):
            difficulty = DifficultyLevel.ADVANCED
        else:
            difficulty = DifficultyLevel.INTERMEDIATE

        # Educational features
        features = EducationalFeatures(
            has_code_examples="code" in content_lower or "```" in article.content,
            has_step_by_step="step" in content_lower,
            has_practical_exercises="exercise" in content_lower or "practice" in content_lower,
            has_visual_aids=False,  # Can't detect from text
            estimated_reading_time=max(5, len(article.content.split()) // 200),
            prerequisite_skills=[],
        )

        return ArticleClassification(
            article_id=article.id,
            content_type=content_type,
            difficulty_level=difficulty,
            learning_value_score=learning_value,
            educational_features=features,
            confidence_score=0.6,  # Lower confidence for fallback
            classification_timestamp=datetime.now(),
        )

    async def _store_classification(self, classification: ArticleClassification):
        """Store classification in database."""
        try:
            data = {
                "article_id": classification.article_id,
                "content_type": classification.content_type.value,
                "difficulty_level": classification.difficulty_level.value,
                "learning_value_score": classification.learning_value_score,
                "confidence_score": classification.confidence_score,
                "educational_features": {
                    "has_code_examples": classification.educational_features.has_code_examples,
                    "has_step_by_step": classification.educational_features.has_step_by_step,
                    "has_practical_exercises": classification.educational_features.has_practical_exercises,
                    "has_visual_aids": classification.educational_features.has_visual_aids,
                    "estimated_reading_time": classification.educational_features.estimated_reading_time,
                    "prerequisite_skills": classification.educational_features.prerequisite_skills,
                },
                "estimated_reading_time": classification.educational_features.estimated_reading_time,
                "prerequisite_skills": classification.educational_features.prerequisite_skills,
            }

            self.supabase.client.table("article_classifications").insert(data).execute()

        except Exception as e:
            logger.error(f"Failed to store classification for {classification.article_id}: {e}")

    def _parse_classification(self, data: Dict) -> ArticleClassification:
        """Parse classification from database."""
        features = EducationalFeatures(
            has_code_examples=data["educational_features"]["has_code_examples"],
            has_step_by_step=data["educational_features"]["has_step_by_step"],
            has_practical_exercises=data["educational_features"]["has_practical_exercises"],
            has_visual_aids=data["educational_features"]["has_visual_aids"],
            estimated_reading_time=data["educational_features"]["estimated_reading_time"],
            prerequisite_skills=data["educational_features"]["prerequisite_skills"],
        )

        return ArticleClassification(
            article_id=data["article_id"],
            content_type=ContentType(data["content_type"]),
            difficulty_level=DifficultyLevel(data["difficulty_level"]),
            learning_value_score=data["learning_value_score"],
            educational_features=features,
            confidence_score=data["confidence_score"],
            classification_timestamp=data["classified_at"],
        )

    async def get_educational_articles(
        self,
        content_types: List[ContentType] = None,
        min_learning_value: float = 0.6,
        limit: int = 50,
    ) -> List[Dict]:
        """Get articles classified as educational content."""
        try:
            query = (
                self.supabase.client.table("article_classifications")
                .select("*, articles(id, title, url, published_at, feed_id)")
                .gte("learning_value_score", min_learning_value)
            )

            if content_types:
                query = query.in_("content_type", [ct.value for ct in content_types])

            result = query.order("learning_value_score", desc=True).limit(limit).execute()

            return result.data

        except Exception as e:
            logger.error(f"Failed to get educational articles: {e}")
            return []
