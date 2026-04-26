-- Learning Content Enhancement System Database Schema
-- Migration 018: Content Enhancement Tables

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

-- Unique constraints
ALTER TABLE feed_categories ADD CONSTRAINT unique_feed_category UNIQUE (feed_id);
ALTER TABLE user_learning_preferences ADD CONSTRAINT unique_user_preferences UNIQUE (user_id);
