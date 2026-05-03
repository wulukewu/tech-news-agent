"""
Unit Tests for UserProfileManager

Tests reading history tracking, preference learning, and satisfaction feedback.

Requirements: 8.1, 8.3, 8.5
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.qa_agent.models import QueryLanguage, UserProfile
from app.qa_agent.user_profile_manager import (
    ReadingHistoryEntry,
    UserProfileManager,
    UserProfileManagerError,
    get_user_profile_manager,
)


@pytest.fixture
def user_profile_manager():
    """Create a UserProfileManager instance for testing."""
    return UserProfileManager()


@pytest.fixture
def sample_user_id():
    """Create a sample user ID."""
    return uuid4()


@pytest.fixture
def sample_article_id():
    """Create a sample article ID."""
    return uuid4()


@pytest.fixture
def sample_user_profile(sample_user_id):
    """Create a sample user profile."""
    return UserProfile(
        user_id=sample_user_id,
        reading_history=[uuid4() for _ in range(10)],
        preferred_topics=["python", "machine-learning", "web-development"],
        language_preference=QueryLanguage.CHINESE,
        interaction_patterns={"technical_depth": "intermediate"},
        query_history=[
            "python best practices",
            "machine learning tutorial",
            "web development frameworks",
        ],
        satisfaction_scores=[0.8, 0.7, 0.9, 0.6, 0.8],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ------------------------------------------------------------------
# Reading History Tracking Tests (Requirement 8.1)
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_track_article_view_basic(user_profile_manager, sample_user_id, sample_article_id):
    """Test basic article view tracking."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        await user_profile_manager.track_article_view(
            user_id=sample_user_id,
            article_id=sample_article_id,
            read_duration_seconds=300,
            completion_rate=0.8,
        )

        # Verify database calls
        assert mock_connection.execute.call_count == 2  # Insert + Update


@pytest.mark.asyncio
async def test_track_article_view_without_metrics(
    user_profile_manager, sample_user_id, sample_article_id
):
    """Test article view tracking without optional metrics."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        await user_profile_manager.track_article_view(
            user_id=sample_user_id, article_id=sample_article_id
        )

        # Should still work with None values
        assert mock_connection.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_reading_history(user_profile_manager, sample_user_id):
    """Test retrieving reading history."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock database response
        mock_rows = [
            {
                "article_id": uuid4(),
                "read_at": datetime.utcnow(),
                "read_duration_seconds": 300,
                "completion_rate": 0.8,
                "satisfaction_score": 0.9,
            },
            {
                "article_id": uuid4(),
                "read_at": datetime.utcnow() - timedelta(days=1),
                "read_duration_seconds": 450,
                "completion_rate": 0.95,
                "satisfaction_score": 0.85,
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        history = await user_profile_manager.get_reading_history(user_id=sample_user_id, limit=10)

        assert len(history) == 2
        assert all(isinstance(entry, ReadingHistoryEntry) for entry in history)
        assert history[0].read_duration_seconds == 300
        assert history[1].completion_rate == 0.95


@pytest.mark.asyncio
async def test_get_reading_history_with_time_filter(user_profile_manager, sample_user_id):
    """Test retrieving reading history with time filtering."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = []

        history = await user_profile_manager.get_reading_history(
            user_id=sample_user_id, limit=50, days_back=30
        )

        # Verify query includes time filter
        call_args = mock_connection.fetch.call_args
        assert len(call_args[0]) > 1  # Should have additional parameter for date


@pytest.mark.asyncio
async def test_get_reading_statistics(user_profile_manager, sample_user_id):
    """Test retrieving reading statistics."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock statistics response
        mock_connection.fetchrow.return_value = {
            "total_articles_read": 50,
            "avg_read_duration": 350.5,
            "avg_completion_rate": 0.82,
            "avg_satisfaction": 0.78,
            "last_read_at": datetime.utcnow(),
            "reading_days": 25,
        }

        stats = await user_profile_manager.get_reading_statistics(user_id=sample_user_id)

        assert stats["total_articles_read"] == 50
        assert stats["avg_read_duration_seconds"] == 350.5
        assert stats["avg_completion_rate"] == 0.82
        assert stats["avg_satisfaction"] == 0.78
        assert stats["reading_days"] == 25


# ------------------------------------------------------------------
# Preference Learning Tests (Requirement 8.3)
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_learn_preferences_from_queries_sufficient_data(user_profile_manager, sample_user_id):
    """Test learning preferences from sufficient query data."""
    queries = [
        "python best practices",
        "python tutorial",
        "machine learning basics",
        "machine learning algorithms",
        "python data structures",
        "web development python",
    ]

    learned_topics = await user_profile_manager.learn_preferences_from_queries(
        user_id=sample_user_id, recent_queries=queries
    )

    # Should identify "python" and "machine" as frequent topics
    assert len(learned_topics) > 0
    assert "python" in learned_topics
    assert "machine" in learned_topics or "learning" in learned_topics


@pytest.mark.asyncio
async def test_learn_preferences_from_queries_insufficient_data(
    user_profile_manager, sample_user_id
):
    """Test learning preferences with insufficient query data."""
    queries = ["python", "javascript"]  # Too few queries

    learned_topics = await user_profile_manager.learn_preferences_from_queries(
        user_id=sample_user_id, recent_queries=queries
    )

    # Should return empty list due to insufficient data
    assert learned_topics == []


@pytest.mark.asyncio
async def test_learn_preferences_from_reading(user_profile_manager, sample_user_id):
    """Test learning preferences from reading history."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock reading history with metadata
        mock_rows = [
            {
                "article_id": uuid4(),
                "read_duration_seconds": 300,
                "completion_rate": 0.9,
                "satisfaction_score": 0.85,
                "metadata": {
                    "category": "programming",
                    "technical_level": "intermediate",
                    "topics": ["python", "algorithms"],
                },
            },
            {
                "article_id": uuid4(),
                "read_duration_seconds": 450,
                "completion_rate": 0.95,
                "satisfaction_score": 0.9,
                "metadata": {
                    "category": "programming",
                    "technical_level": "advanced",
                    "topics": ["python", "performance"],
                },
            },
            {
                "article_id": uuid4(),
                "read_duration_seconds": 200,
                "completion_rate": 0.75,
                "satisfaction_score": 0.7,
                "metadata": {
                    "category": "web-development",
                    "technical_level": "intermediate",
                    "topics": ["javascript", "react"],
                },
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        preferences = await user_profile_manager.learn_preferences_from_reading(
            user_id=sample_user_id
        )

        assert "preferred_categories" in preferences
        assert "programming" in preferences["preferred_categories"]
        assert "preferred_technical_depth" in preferences
        assert preferences["preferred_technical_depth"] == "intermediate"
        assert "high_engagement_topics" in preferences
        assert "python" in preferences["high_engagement_topics"]


@pytest.mark.asyncio
async def test_learn_preferences_from_reading_no_data(user_profile_manager, sample_user_id):
    """Test learning preferences with no reading history."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = []

        preferences = await user_profile_manager.learn_preferences_from_reading(
            user_id=sample_user_id
        )

        assert preferences["preferred_categories"] == []
        assert preferences["preferred_technical_depth"] == "intermediate"
        assert preferences["avg_reading_time_seconds"] == 0


@pytest.mark.asyncio
async def test_update_user_preferences(user_profile_manager, sample_user_id):
    """Test updating user preferences in database."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        learned_preferences = {
            "preferred_categories": ["programming", "data-science"],
            "preferred_technical_depth": "advanced",
        }

        await user_profile_manager.update_user_preferences(
            user_id=sample_user_id, learned_preferences=learned_preferences
        )

        # Verify database updates
        assert mock_connection.execute.call_count == 2  # Two update queries


# ------------------------------------------------------------------
# Satisfaction Feedback Tests (Requirement 8.5)
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_satisfaction_feedback_explicit(
    user_profile_manager, sample_user_id, sample_article_id
):
    """Test recording explicit satisfaction feedback."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        await user_profile_manager.record_satisfaction_feedback(
            user_id=sample_user_id,
            article_id=sample_article_id,
            satisfaction_score=0.9,
            feedback_type="explicit",
        )

        # Verify database calls
        assert mock_connection.execute.call_count == 2  # Update + Append


@pytest.mark.asyncio
async def test_record_satisfaction_feedback_invalid_score(
    user_profile_manager, sample_user_id, sample_article_id
):
    """Test recording satisfaction feedback with invalid score."""
    with pytest.raises(ValueError):
        await user_profile_manager.record_satisfaction_feedback(
            user_id=sample_user_id,
            article_id=sample_article_id,
            satisfaction_score=1.5,  # Invalid: > 1.0
        )

    with pytest.raises(ValueError):
        await user_profile_manager.record_satisfaction_feedback(
            user_id=sample_user_id,
            article_id=sample_article_id,
            satisfaction_score=-0.1,  # Invalid: < 0.0
        )


@pytest.mark.asyncio
async def test_calculate_implicit_satisfaction_ideal_reading(user_profile_manager):
    """Test calculating implicit satisfaction with ideal reading behavior."""
    # User read for expected time with high completion
    satisfaction = await user_profile_manager.calculate_implicit_satisfaction(
        read_duration_seconds=300,
        completion_rate=0.9,
        expected_read_time=300,
    )

    # Should be high satisfaction
    assert 0.8 <= satisfaction <= 1.0


@pytest.mark.asyncio
async def test_calculate_implicit_satisfaction_low_completion(user_profile_manager):
    """Test calculating implicit satisfaction with low completion rate."""
    satisfaction = await user_profile_manager.calculate_implicit_satisfaction(
        read_duration_seconds=100,
        completion_rate=0.3,  # Low completion
        expected_read_time=300,
    )

    # Should be lower satisfaction
    assert satisfaction < 0.6


@pytest.mark.asyncio
async def test_calculate_implicit_satisfaction_too_fast(user_profile_manager):
    """Test calculating implicit satisfaction when reading too fast (skimming)."""
    satisfaction = await user_profile_manager.calculate_implicit_satisfaction(
        read_duration_seconds=100,  # Too fast
        completion_rate=0.9,
        expected_read_time=300,
    )

    # Should be moderate satisfaction (might be skimming)
    assert 0.5 <= satisfaction <= 0.8


@pytest.mark.asyncio
async def test_analyze_satisfaction_trends_improving(user_profile_manager, sample_user_id):
    """Test analyzing satisfaction trends when improving."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock improving trend (recent scores higher)
        mock_rows = [
            {"read_date": datetime.utcnow().date(), "avg_satisfaction": 0.9, "article_count": 3},
            {
                "read_date": (datetime.utcnow() - timedelta(days=1)).date(),
                "avg_satisfaction": 0.85,
                "article_count": 2,
            },
            {
                "read_date": (datetime.utcnow() - timedelta(days=5)).date(),
                "avg_satisfaction": 0.7,
                "article_count": 4,
            },
            {
                "read_date": (datetime.utcnow() - timedelta(days=10)).date(),
                "avg_satisfaction": 0.6,
                "article_count": 2,
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        trends = await user_profile_manager.analyze_satisfaction_trends(
            user_id=sample_user_id, days_back=30
        )

        assert trends["trend"] == "improving"
        assert trends["satisfaction_improving"] is True
        assert trends["avg_satisfaction"] > 0.7


@pytest.mark.asyncio
async def test_analyze_satisfaction_trends_declining(user_profile_manager, sample_user_id):
    """Test analyzing satisfaction trends when declining."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock declining trend (recent scores lower)
        mock_rows = [
            {"read_date": datetime.utcnow().date(), "avg_satisfaction": 0.5, "article_count": 2},
            {
                "read_date": (datetime.utcnow() - timedelta(days=1)).date(),
                "avg_satisfaction": 0.6,
                "article_count": 3,
            },
            {
                "read_date": (datetime.utcnow() - timedelta(days=5)).date(),
                "avg_satisfaction": 0.75,
                "article_count": 2,
            },
            {
                "read_date": (datetime.utcnow() - timedelta(days=10)).date(),
                "avg_satisfaction": 0.85,
                "article_count": 4,
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        trends = await user_profile_manager.analyze_satisfaction_trends(
            user_id=sample_user_id, days_back=30
        )

        assert trends["trend"] == "declining"
        assert trends["satisfaction_improving"] is False
        assert len(trends["recommendations"]) > 0


@pytest.mark.asyncio
async def test_analyze_satisfaction_trends_insufficient_data(user_profile_manager, sample_user_id):
    """Test analyzing satisfaction trends with insufficient data."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = []

        trends = await user_profile_manager.analyze_satisfaction_trends(
            user_id=sample_user_id, days_back=30
        )

        assert trends["trend"] == "insufficient_data"
        assert trends["avg_satisfaction"] == 0.5


# ------------------------------------------------------------------
# Profile Management Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_profile_existing(
    user_profile_manager, sample_user_id, sample_user_profile
):
    """Test getting an existing user profile."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock existing profile
        mock_connection.fetchrow.return_value = {
            "user_id": sample_user_id,
            "reading_history": [str(aid) for aid in sample_user_profile.reading_history],
            "preferred_topics": sample_user_profile.preferred_topics,
            "language_preference": "zh",
            "interaction_patterns": sample_user_profile.interaction_patterns,
            "query_history": sample_user_profile.query_history,
            "satisfaction_scores": sample_user_profile.satisfaction_scores,
            "created_at": sample_user_profile.created_at,
            "updated_at": sample_user_profile.updated_at,
        }

        profile = await user_profile_manager.get_or_create_profile(user_id=sample_user_id)

        assert profile.user_id == sample_user_id
        assert len(profile.reading_history) == 10
        assert len(profile.preferred_topics) == 3
        assert profile.language_preference == QueryLanguage.CHINESE


@pytest.mark.asyncio
async def test_get_or_create_profile_new(user_profile_manager, sample_user_id):
    """Test creating a new user profile."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        # Mock no existing profile
        mock_connection.fetchrow.return_value = None

        profile = await user_profile_manager.get_or_create_profile(user_id=sample_user_id)

        assert profile.user_id == sample_user_id
        assert len(profile.reading_history) == 0
        assert len(profile.preferred_topics) == 0
        assert profile.language_preference == QueryLanguage.CHINESE
        # Verify insert was called
        assert mock_connection.execute.called


@pytest.mark.asyncio
async def test_update_profile(user_profile_manager, sample_user_profile):
    """Test updating a user profile."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection

        await user_profile_manager.update_profile(profile=sample_user_profile)

        # Verify update was called
        assert mock_connection.execute.called
        call_args = mock_connection.execute.call_args[0]
        assert "UPDATE user_profiles" in call_args[0]


# ------------------------------------------------------------------
# Helper Method Tests
# ------------------------------------------------------------------


def test_extract_query_keywords(user_profile_manager):
    """Test keyword extraction from queries."""
    query = "What are the best Python machine learning libraries?"
    keywords = user_profile_manager._extract_query_keywords(query)

    assert "python" in keywords
    assert "machine" in keywords
    assert "learning" in keywords
    assert "libraries" in keywords
    # Stop words should be filtered
    assert "the" not in keywords
    assert "are" not in keywords
    assert "what" not in keywords


def test_extract_query_keywords_chinese(user_profile_manager):
    """Test keyword extraction from Chinese queries."""
    query = "如何學習 Python 機器學習"
    keywords = user_profile_manager._extract_query_keywords(query)

    assert "python" in keywords
    assert len(keywords) > 0


def test_extract_query_keywords_mixed(user_profile_manager):
    """Test keyword extraction from mixed language queries."""
    query = "Python 最佳實踐 best practices"
    keywords = user_profile_manager._extract_query_keywords(query)

    assert "python" in keywords
    assert "practices" in keywords


# ------------------------------------------------------------------
# ReadingHistoryEntry Tests
# ------------------------------------------------------------------


def test_reading_history_entry_creation():
    """Test creating a ReadingHistoryEntry."""
    article_id = uuid4()
    read_at = datetime.utcnow()

    entry = ReadingHistoryEntry(
        article_id=article_id,
        read_at=read_at,
        read_duration_seconds=300,
        completion_rate=0.85,
        satisfaction_score=0.9,
    )

    assert entry.article_id == article_id
    assert entry.read_at == read_at
    assert entry.read_duration_seconds == 300
    assert entry.completion_rate == 0.85
    assert entry.satisfaction_score == 0.9


def test_reading_history_entry_to_dict():
    """Test converting ReadingHistoryEntry to dictionary."""
    article_id = uuid4()
    read_at = datetime.utcnow()

    entry = ReadingHistoryEntry(
        article_id=article_id,
        read_at=read_at,
        read_duration_seconds=300,
        completion_rate=0.85,
    )

    entry_dict = entry.to_dict()

    assert entry_dict["article_id"] == str(article_id)
    assert entry_dict["read_at"] == read_at.isoformat()
    assert entry_dict["read_duration_seconds"] == 300
    assert entry_dict["completion_rate"] == 0.85


def test_reading_history_entry_from_dict():
    """Test creating ReadingHistoryEntry from dictionary."""
    article_id = uuid4()
    read_at = datetime.utcnow()

    entry_dict = {
        "article_id": str(article_id),
        "read_at": read_at.isoformat(),
        "read_duration_seconds": 300,
        "completion_rate": 0.85,
        "satisfaction_score": 0.9,
    }

    entry = ReadingHistoryEntry.from_dict(entry_dict)

    assert entry.article_id == article_id
    assert entry.read_duration_seconds == 300
    assert entry.completion_rate == 0.85


# ------------------------------------------------------------------
# Singleton Tests
# ------------------------------------------------------------------


def test_get_user_profile_manager_singleton():
    """Test that get_user_profile_manager returns singleton instance."""
    manager1 = get_user_profile_manager()
    manager2 = get_user_profile_manager()

    assert manager1 is manager2


# ------------------------------------------------------------------
# Error Handling Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_track_article_view_database_error(
    user_profile_manager, sample_user_id, sample_article_id
):
    """Test handling database errors when tracking article views."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection
        mock_connection.execute.side_effect = Exception("Database error")

        with pytest.raises(UserProfileManagerError):
            await user_profile_manager.track_article_view(
                user_id=sample_user_id, article_id=sample_article_id
            )


@pytest.mark.asyncio
async def test_get_reading_history_database_error(user_profile_manager, sample_user_id):
    """Test handling database errors when retrieving reading history."""
    with patch("app.qa_agent.user_profile_manager.get_db_connection") as mock_conn:
        mock_connection = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.side_effect = Exception("Database error")

        with pytest.raises(UserProfileManagerError):
            await user_profile_manager.get_reading_history(user_id=sample_user_id)
