# Learning Content Enhancement System - Technical Design

## Architecture Overview

The Learning Content Enhancement System transforms the existing news-focused RSS aggregation into an education-focused learning platform. The system maintains backward compatibility while adding intelligent content classification and educational content prioritization.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Learning Content Enhancement                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐ │
│  │   RSS Sources   │───▶│  Content         │───▶│  Enhanced Learning      │ │
│  │                 │    │  Classifier      │    │  Recommendation Engine  │ │
│  │ • Educational   │    │                  │    │                         │ │
│  │ • News         │    │ • LLM Analysis   │    │ • Educational Priority │ │
│  │ • Official     │    │ • Type Detection │    │ • Quality Filtering     │ │
│  │ • Community    │    │ • Value Scoring  │    │ • Personalization      │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────────────┘ │
│           │                       │                         │               │
│           ▼                       ▼                         ▼               │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐ │
│  │ Feed Management │    │ Classification   │    │ User Feedback &         │ │
│  │ Service         │    │ Storage          │    │ Quality Assurance       │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Existing Learning Path System                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Skill Tree • Goal Parser • Path Generator • Progress Tracker • Evaluator  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Educational RSS Source Manager

```python
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass

class FeedType(Enum):
    EDUCATIONAL = "educational"
    NEWS = "news"
    OFFICIAL = "official"
    COMMUNITY = "community"

class ContentFocus(Enum):
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    REFERENCE = "reference"
    NEWS = "news"
    PROJECT = "project"

@dataclass
class FeedMetadata:
    feed_id: str
    feed_type: FeedType
    content_focus: ContentFocus
    quality_score: float
    update_frequency: int  # hours
    target_audience: str
    primary_topics: List[str]

class EducationalRSSManager:
    """Manages educational RSS feeds with quality scoring and categorization."""

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.feed_cache: Dict[str, FeedMetadata] = {}

    async def add_educational_feed(
        self,
        url: str,
        feed_type: FeedType,
        content_focus: ContentFocus,
        metadata: Dict
    ) -> str:
        """Add a new educational RSS feed with categorization."""

    async def get_feeds_by_type(self, feed_type: FeedType) -> List[FeedMetadata]:
        """Get all feeds of a specific type."""

    async def calculate_feed_quality_score(self, feed_id: str) -> float:
        """Calculate quality score based on user feedback and engagement."""

    async def get_feed_health_status(self, feed_id: str) -> Dict:
        """Get feed health metrics (uptime, update frequency, error rate)."""
```

### 2. Content Classification Service

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

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

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.classification_cache: Dict[str, ArticleClassification] = {}

    async def classify_article(self, article: ArticleSchema) -> ArticleClassification:
        """Classify article for educational value and learning characteristics."""

        system_prompt = """
        You are an educational content analyst. Analyze the given article and classify it for learning value.

        Classify the article on these dimensions:
        1. Content Type: tutorial, guide, news, reference, project, opinion
        2. Difficulty Level: beginner (1), intermediate (2), advanced (3), expert (4)
        3. Learning Value Score: 0.0-1.0 based on educational utility
        4. Educational Features: code examples, step-by-step instructions, practical exercises, visual aids
        5. Estimated Reading Time: in minutes
        6. Prerequisite Skills: required background knowledge

        Return JSON format with confidence score.
        """

        # Implementation details...

    async def calculate_learning_value_score(
        self,
        title: str,
        content: str,
        features: EducationalFeatures
    ) -> float:
        """Calculate learning value score based on multiple factors."""

        score_factors = {
            'tutorial_keywords': 0.25,
            'code_examples': 0.20,
            'step_by_step': 0.20,
            'practical_focus': 0.15,
            'beginner_friendly': 0.10,
            'comprehensive_coverage': 0.10
        }

        # Implementation details...

    async def extract_educational_features(self, content: str) -> EducationalFeatures:
        """Extract educational features from article content."""

        # Implementation details...
```

### 3. Enhanced Recommendation Engine

```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class LearningPreferences:
    preferred_content_types: List[ContentType]
    preferred_difficulty_progression: float  # 0.0-1.0
    learning_style: str  # visual, hands-on, theoretical
    time_availability: int  # minutes per session
    completion_rate_threshold: float

@dataclass
class RecommendationContext:
    user_id: str
    current_learning_stage: int
    target_skills: List[str]
    completed_articles: List[str]
    learning_preferences: LearningPreferences
    session_context: Dict

class EnhancedRecommendationEngine:
    """Enhanced recommendation engine prioritizing educational content."""

    def __init__(
        self,
        supabase_service: SupabaseService,
        classification_service: ContentClassificationService
    ):
        self.supabase = supabase_service
        self.classifier = classification_service

    async def get_learning_recommendations(
        self,
        context: RecommendationContext,
        limit: int = 10
    ) -> List[RecommendedArticle]:
        """Get personalized learning recommendations with educational priority."""

        # 1. Get candidate articles for current learning stage
        candidates = await self._get_stage_candidates(context)

        # 2. Apply educational content filters
        educational_articles = await self._filter_educational_content(candidates)

        # 3. Apply quality and relevance scoring
        scored_articles = await self._score_articles(educational_articles, context)

        # 4. Apply diversity and personalization
        final_recommendations = await self._apply_personalization(scored_articles, context)

        return final_recommendations[:limit]

    async def _filter_educational_content(
        self,
        articles: List[ArticleSchema]
    ) -> List[ArticleSchema]:
        """Filter articles to prioritize educational content."""

        educational_priority = {
            ContentType.TUTORIAL: 1.0,
            ContentType.GUIDE: 0.9,
            ContentType.PROJECT: 0.8,
            ContentType.REFERENCE: 0.6,
            ContentType.NEWS: 0.3,
            ContentType.OPINION: 0.2
        }

        # Implementation details...

    async def _score_articles(
        self,
        articles: List[ArticleSchema],
        context: RecommendationContext
    ) -> List[ScoredArticle]:
        """Score articles based on learning value and user context."""

        scoring_weights = {
            'learning_value': 0.30,
            'difficulty_match': 0.25,
            'skill_relevance': 0.20,
            'user_preferences': 0.15,
            'content_freshness': 0.10
        }

        # Implementation details...

    async def _apply_personalization(
        self,
        scored_articles: List[ScoredArticle],
        context: RecommendationContext
    ) -> List[RecommendedArticle]:
        """Apply personalization based on user learning patterns."""

        # Implementation details...
```

### 4. Quality Assurance System

```python
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ContentFeedback:
    user_id: str
    article_id: str
    educational_value_rating: int  # 1-5
    difficulty_accuracy: bool
    content_type_accuracy: bool
    completion_status: str
    time_spent_minutes: int
    feedback_text: Optional[str]

@dataclass
class QualityMetrics:
    average_rating: float
    completion_rate: float
    user_engagement_score: float
    classification_accuracy: float
    recommendation_relevance: float

class QualityAssuranceSystem:
    """System for monitoring and improving content quality."""

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    async def collect_user_feedback(self, feedback: ContentFeedback) -> None:
        """Collect and store user feedback on content quality."""

    async def calculate_content_quality_score(self, article_id: str) -> float:
        """Calculate overall quality score for an article."""

    async def get_source_quality_metrics(self, feed_id: str) -> QualityMetrics:
        """Get quality metrics for a specific RSS source."""

    async def identify_low_quality_sources(self) -> List[str]:
        """Identify RSS sources with consistently low quality scores."""

    async def update_recommendation_weights(self) -> None:
        """Update recommendation algorithm weights based on feedback."""
```

## Database Schema Design

### New Tables

```sql
-- Feed categorization and metadata
CREATE TABLE feed_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    feed_type VARCHAR(20) NOT NULL CHECK (feed_type IN ('educational', 'news', 'official', 'community')),
    content_focus VARCHAR(20) NOT NULL CHECK (content_focus IN ('tutorial', 'guide', 'reference', 'news', 'project')),
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    update_frequency_hours INTEGER DEFAULT 24,
    target_audience VARCHAR(50),
    primary_topics TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Article classification results
CREATE TABLE article_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('tutorial', 'guide', 'news', 'reference', 'project', 'opinion')),
    difficulty_level INTEGER NOT NULL CHECK (difficulty_level BETWEEN 1 AND 4),
    learning_value_score FLOAT NOT NULL CHECK (learning_value_score >= 0.0 AND learning_value_score <= 1.0),
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    educational_features JSONB NOT NULL,
    estimated_reading_time INTEGER,
    prerequisite_skills TEXT[],
    classified_at TIMESTAMPTZ DEFAULT NOW(),
    classifier_version VARCHAR(10) DEFAULT '1.0'
);

-- User feedback on content quality
CREATE TABLE content_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    educational_value_rating INTEGER CHECK (educational_value_rating BETWEEN 1 AND 5),
    difficulty_accuracy BOOLEAN,
    content_type_accuracy BOOLEAN,
    completion_status VARCHAR(20) CHECK (completion_status IN ('completed', 'partial', 'abandoned')),
    time_spent_minutes INTEGER DEFAULT 0,
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning preferences per user
CREATE TABLE user_learning_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_content_types TEXT[] DEFAULT ARRAY['tutorial', 'guide'],
    preferred_difficulty_progression FLOAT DEFAULT 0.7 CHECK (preferred_difficulty_progression >= 0.0 AND preferred_difficulty_progression <= 1.0),
    learning_style VARCHAR(20) DEFAULT 'balanced' CHECK (learning_style IN ('visual', 'hands-on', 'theoretical', 'balanced')),
    time_availability_minutes INTEGER DEFAULT 30,
    completion_rate_threshold FLOAT DEFAULT 0.8,
    preferences_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content quality metrics cache
CREATE TABLE content_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    average_rating FLOAT DEFAULT 0.0,
    completion_rate FLOAT DEFAULT 0.0,
    user_engagement_score FLOAT DEFAULT 0.0,
    recommendation_success_rate FLOAT DEFAULT 0.0,
    total_feedback_count INTEGER DEFAULT 0,
    last_calculated TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_feed_categories_type ON feed_categories(feed_type);
CREATE INDEX idx_feed_categories_focus ON feed_categories(content_focus);
CREATE INDEX idx_feed_categories_quality ON feed_categories(quality_score DESC);

CREATE INDEX idx_article_classifications_type ON article_classifications(content_type);
CREATE INDEX idx_article_classifications_difficulty ON article_classifications(difficulty_level);
CREATE INDEX idx_article_classifications_value ON article_classifications(learning_value_score DESC);
CREATE INDEX idx_article_classifications_article ON article_classifications(article_id);

CREATE INDEX idx_content_feedback_user ON content_feedback(user_id);
CREATE INDEX idx_content_feedback_article ON content_feedback(article_id);
CREATE INDEX idx_content_feedback_rating ON content_feedback(educational_value_rating);

CREATE INDEX idx_user_learning_preferences_user ON user_learning_preferences(user_id);

CREATE INDEX idx_content_quality_metrics_article ON content_quality_metrics(article_id);
CREATE INDEX idx_content_quality_metrics_feed ON content_quality_metrics(feed_id);
```

## API Design

### New Endpoints

```python
# Feed Management API
@router.get("/feeds/categories")
async def get_feed_categories() -> List[FeedCategoryResponse]

@router.post("/feeds/{feed_id}/categorize")
async def categorize_feed(feed_id: str, category_data: FeedCategoryRequest) -> FeedCategoryResponse

@router.get("/feeds/quality-metrics")
async def get_feed_quality_metrics() -> List[FeedQualityMetrics]

# Content Classification API
@router.get("/articles/{article_id}/classification")
async def get_article_classification(article_id: str) -> ArticleClassificationResponse

@router.post("/articles/classify-batch")
async def classify_articles_batch(article_ids: List[str]) -> List[ArticleClassificationResponse]

# Enhanced Recommendations API
@router.get("/learning-path/goals/{goal_id}/recommendations/enhanced")
async def get_enhanced_recommendations(
    goal_id: str,
    stage: int = 1,
    content_types: List[str] = Query(default=["tutorial", "guide"]),
    limit: int = 10
) -> EnhancedRecommendationResponse

# User Feedback API
@router.post("/content/feedback")
async def submit_content_feedback(feedback: ContentFeedbackRequest) -> ContentFeedbackResponse

@router.get("/content/{article_id}/feedback-summary")
async def get_content_feedback_summary(article_id: str) -> FeedbackSummaryResponse

# User Preferences API
@router.get("/users/learning-preferences")
async def get_user_learning_preferences() -> UserLearningPreferencesResponse

@router.put("/users/learning-preferences")
async def update_user_learning_preferences(
    preferences: UserLearningPreferencesRequest
) -> UserLearningPreferencesResponse

# Quality Metrics API
@router.get("/quality/metrics/overview")
async def get_quality_metrics_overview() -> QualityMetricsOverview

@router.get("/quality/sources/low-performing")
async def get_low_performing_sources() -> List[LowPerformingSourceResponse]
```

## Integration Points

### 1. RSS Processing Pipeline Integration

```python
class EnhancedRSSProcessor:
    """Enhanced RSS processor with content classification."""

    async def process_article(self, article: ArticleSchema) -> ArticleSchema:
        # 1. Existing processing
        processed_article = await super().process_article(article)

        # 2. Content classification
        classification = await self.classifier.classify_article(processed_article)
        await self.store_classification(classification)

        # 3. Quality scoring
        quality_score = await self.quality_system.calculate_quality_score(processed_article)

        return processed_article
```

### 2. Learning Path Integration

```python
class EnhancedLearningPathGenerator:
    """Learning path generator with educational content awareness."""

    async def generate_path(self, goal_id: str, target_skill: str) -> LearningPath:
        # 1. Generate base learning path
        base_path = await super().generate_path(goal_id, target_skill)

        # 2. Enhance with educational content recommendations
        for stage in base_path.stages:
            educational_content = await self.get_educational_content_for_stage(stage)
            stage.recommended_articles = educational_content

        return base_path
```

## Performance Considerations

### 1. Caching Strategy

```python
# Classification results caching
CLASSIFICATION_CACHE_TTL = 7 * 24 * 3600  # 7 days
QUALITY_METRICS_CACHE_TTL = 24 * 3600     # 24 hours
RECOMMENDATION_CACHE_TTL = 6 * 3600       # 6 hours

# Redis cache keys
CLASSIFICATION_KEY = "classification:{article_id}"
QUALITY_METRICS_KEY = "quality:{feed_id}"
RECOMMENDATIONS_KEY = "recommendations:{user_id}:{goal_id}:{stage}"
```

### 2. Background Processing

```python
# Async classification processing
@celery.task
async def classify_article_async(article_id: str):
    """Background task for article classification."""

@celery.task
async def update_quality_metrics_async(feed_id: str):
    """Background task for quality metrics calculation."""

@celery.task
async def refresh_recommendations_async(user_id: str):
    """Background task for recommendation refresh."""
```

### 3. Database Optimization

- Proper indexing on classification and feedback tables
- Partitioning for large feedback tables
- Read replicas for recommendation queries
- Connection pooling and query optimization

## Monitoring and Observability

### 1. Key Metrics

```python
METRICS_TO_TRACK = {
    'classification_accuracy': 'Percentage of accurate classifications',
    'recommendation_relevance': 'User satisfaction with recommendations',
    'educational_content_ratio': 'Percentage of educational vs news content',
    'user_engagement': 'Time spent and completion rates',
    'system_performance': 'Response times and error rates'
}
```

### 2. Alerting

```python
ALERT_THRESHOLDS = {
    'classification_accuracy': 0.80,  # Alert if below 80%
    'recommendation_relevance': 3.5,  # Alert if below 3.5/5
    'educational_content_ratio': 0.50,  # Alert if below 50%
    'system_error_rate': 0.05  # Alert if above 5%
}
```

This technical design provides a comprehensive foundation for implementing the Learning Content Enhancement System while maintaining system reliability and performance.
