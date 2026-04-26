import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.auth import get_current_user

from ..services.content_classification_service import ContentClassificationService
from ..services.educational_rss_manager import EducationalRSSManager, FeedType
from ..services.enhanced_recommendation_engine import EnhancedRecommendationEngine
from ..services.llm_service import LLMService
from ..services.quality_assurance_system import ContentFeedback, QualityAssuranceSystem
from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning-content", tags=["Learning Content Enhancement"])


# Pydantic models
class FeedCategoryRequest(BaseModel):
    feed_type: str
    content_focus: str
    target_audience: str = "developers"
    primary_topics: List[str] = []


class ContentFeedbackRequest(BaseModel):
    article_id: str
    educational_value_rating: Optional[int] = None
    difficulty_accuracy: Optional[bool] = None
    content_type_accuracy: Optional[bool] = None
    completion_status: str = "partial"
    time_spent_minutes: int = 0
    feedback_text: Optional[str] = None


class UserPreferencesRequest(BaseModel):
    preferred_content_types: List[str] = ["tutorial", "guide"]
    preferred_difficulty_progression: float = 0.7
    learning_style: str = "balanced"
    time_availability_minutes: int = 30
    completion_rate_threshold: float = 0.8


# Dependency injection
def get_educational_rss_manager() -> EducationalRSSManager:
    supabase_service = SupabaseService()
    return EducationalRSSManager(supabase_service)


def get_content_classifier() -> ContentClassificationService:
    llm_service = LLMService()
    supabase_service = SupabaseService()
    return ContentClassificationService(llm_service, supabase_service)


def get_enhanced_recommender() -> EnhancedRecommendationEngine:
    supabase_service = SupabaseService()
    classifier = get_content_classifier()
    return EnhancedRecommendationEngine(supabase_service, classifier)


def get_quality_system() -> QualityAssuranceSystem:
    supabase_service = SupabaseService()
    return QualityAssuranceSystem(supabase_service)


# Feed Management Endpoints
@router.get("/feeds/categories")
async def get_feed_categories(
    feed_type: Optional[str] = None,
    rss_manager: EducationalRSSManager = Depends(get_educational_rss_manager),
):
    """Get all feed categories, optionally filtered by type."""
    try:
        if feed_type:
            feeds = await rss_manager.get_feeds_by_type(FeedType(feed_type))
            return {"feeds": feeds}
        else:
            educational_feeds = await rss_manager.get_educational_feeds()
            return {"feeds": educational_feeds}
    except Exception as e:
        logger.error(f"Failed to get feed categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feed categories")


@router.post("/feeds/{feed_id}/categorize")
async def categorize_feed(
    feed_id: str,
    category_data: FeedCategoryRequest,
    current_user: dict = Depends(get_current_user),
    rss_manager: EducationalRSSManager = Depends(get_educational_rss_manager),
):
    """Categorize an existing feed as educational content."""
    try:
        # This would update an existing feed's category
        # Implementation would depend on specific requirements
        return {"message": "Feed categorized successfully", "feed_id": feed_id}
    except Exception as e:
        logger.error(f"Failed to categorize feed {feed_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to categorize feed")


# Content Classification Endpoints
@router.get("/articles/{article_id}/classification")
async def get_article_classification(
    article_id: str, classifier: ContentClassificationService = Depends(get_content_classifier)
):
    """Get classification for a specific article."""
    try:
        # Get article first
        supabase = SupabaseService()
        article_result = (
            supabase.client.table("articles").select("*").eq("id", article_id).execute()
        )

        if not article_result.data:
            raise HTTPException(status_code=404, detail="Article not found")

        # Get or create classification
        from ..schemas.article import ArticleSchema

        article = ArticleSchema(**article_result.data[0])
        classification = await classifier.classify_article(article)

        return {
            "article_id": article_id,
            "classification": {
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
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get classification for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get article classification")


@router.get("/articles/educational")
async def get_educational_articles(
    content_types: List[str] = Query(default=["tutorial", "guide"]),
    min_learning_value: float = Query(default=0.6, ge=0.0, le=1.0),
    limit: int = Query(default=20, le=100),
    classifier: ContentClassificationService = Depends(get_content_classifier),
):
    """Get articles classified as educational content."""
    try:
        from .content_classification_service import ContentType

        content_type_enums = [ContentType(ct) for ct in content_types]

        articles = await classifier.get_educational_articles(
            content_types=content_type_enums, min_learning_value=min_learning_value, limit=limit
        )

        return {"articles": articles, "count": len(articles)}
    except Exception as e:
        logger.error(f"Failed to get educational articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get educational articles")


# Enhanced Recommendations Endpoints
@router.get("/recommendations/enhanced")
async def get_enhanced_recommendations(
    goal_id: Optional[str] = None,
    stage: int = Query(default=1, ge=1),
    content_types: List[str] = Query(default=["tutorial", "guide"]),
    limit: int = Query(default=10, le=50),
    current_user: dict = Depends(get_current_user),
    recommender: EnhancedRecommendationEngine = Depends(get_enhanced_recommender),
):
    """Get enhanced learning recommendations prioritizing educational content."""
    try:
        user_id = str(current_user["user_id"])

        recommendations = await recommender.get_learning_recommendations(
            user_id=user_id, goal_id=goal_id, stage=stage, content_types=content_types, limit=limit
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "user_id": user_id,
            "parameters": {
                "goal_id": goal_id,
                "stage": stage,
                "content_types": content_types,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get enhanced recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


# User Feedback Endpoints
@router.post("/feedback")
async def submit_content_feedback(
    feedback: ContentFeedbackRequest,
    current_user: dict = Depends(get_current_user),
    quality_system: QualityAssuranceSystem = Depends(get_quality_system),
):
    """Submit feedback on content quality and educational value."""
    try:
        user_id = str(current_user["user_id"])

        feedback_obj = ContentFeedback(
            user_id=user_id,
            article_id=feedback.article_id,
            educational_value_rating=feedback.educational_value_rating,
            difficulty_accuracy=feedback.difficulty_accuracy,
            content_type_accuracy=feedback.content_type_accuracy,
            completion_status=feedback.completion_status,
            time_spent_minutes=feedback.time_spent_minutes,
            feedback_text=feedback.feedback_text,
        )

        success = await quality_system.collect_user_feedback(feedback_obj)

        if success:
            return {"message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/feedback/{article_id}/summary")
async def get_feedback_summary(
    article_id: str, quality_system: QualityAssuranceSystem = Depends(get_quality_system)
):
    """Get feedback summary for a specific article."""
    try:
        quality_score = await quality_system.calculate_content_quality_score(article_id)

        return {
            "article_id": article_id,
            "quality_score": quality_score,
            "quality_rating": "high"
            if quality_score > 0.8
            else "medium"
            if quality_score > 0.6
            else "low",
        }
    except Exception as e:
        logger.error(f"Failed to get feedback summary for {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback summary")


# User Preferences Endpoints
@router.get("/preferences")
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    recommender: EnhancedRecommendationEngine = Depends(get_enhanced_recommender),
):
    """Get user learning preferences."""
    try:
        user_id = str(current_user["user_id"])
        preferences = await recommender._get_user_preferences(user_id)

        return {
            "user_id": user_id,
            "preferences": {
                "preferred_content_types": [ct.value for ct in preferences.preferred_content_types],
                "preferred_difficulty_progression": preferences.preferred_difficulty_progression,
                "learning_style": preferences.learning_style,
                "time_availability_minutes": preferences.time_availability,
                "completion_rate_threshold": preferences.completion_rate_threshold,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user preferences")


@router.put("/preferences")
async def update_user_preferences(
    preferences: UserPreferencesRequest,
    current_user: dict = Depends(get_current_user),
    recommender: EnhancedRecommendationEngine = Depends(get_enhanced_recommender),
):
    """Update user learning preferences."""
    try:
        user_id = str(current_user["user_id"])

        success = await recommender.update_user_preferences(
            user_id=user_id, preferences=preferences.dict()
        )

        if success:
            return {"message": "Preferences updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


# Quality Metrics Endpoints
@router.get("/quality/overview")
async def get_quality_overview(
    current_user: dict = Depends(get_current_user),
    quality_system: QualityAssuranceSystem = Depends(get_quality_system),
):
    """Get overall system quality metrics."""
    try:
        overview = await quality_system.get_quality_overview()
        return overview
    except Exception as e:
        logger.error(f"Failed to get quality overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality overview")


@router.get("/quality/sources/low-performing")
async def get_low_performing_sources(
    threshold: float = Query(default=0.6, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_user),
    quality_system: QualityAssuranceSystem = Depends(get_quality_system),
):
    """Get RSS sources with low quality scores."""
    try:
        low_quality_sources = await quality_system.identify_low_quality_sources(threshold)
        return {"sources": low_quality_sources, "threshold": threshold}
    except Exception as e:
        logger.error(f"Failed to get low performing sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get low performing sources")
