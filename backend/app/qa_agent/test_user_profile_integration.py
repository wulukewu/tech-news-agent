"""
Integration Tests for UserProfileManager

Tests the complete user profile workflow including database operations.

Requirements: 8.1, 8.3, 8.5
"""

import asyncio
from uuid import uuid4

import pytest

from .user_profile_manager import get_user_profile_manager


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_user_profile_workflow():
    """
    Test complete user profile workflow from creation to learning.

    This integration test validates:
    - Profile creation
    - Reading history tracking
    - Preference learning
    - Satisfaction feedback
    - Profile updates

    Validates: Requirements 8.1, 8.3, 8.5
    """
    manager = get_user_profile_manager()
    user_id = uuid4()

    try:
        # Step 1: Create new user profile
        profile = await manager.get_or_create_profile(user_id)
        assert profile.user_id == user_id
        assert len(profile.reading_history) == 0

        # Step 2: Track article views
        article_ids = [uuid4() for _ in range(5)]

        for i, article_id in enumerate(article_ids):
            await manager.track_article_view(
                user_id=user_id,
                article_id=article_id,
                read_duration_seconds=300 + (i * 50),
                completion_rate=0.7 + (i * 0.05),
            )

        # Step 3: Verify reading history
        history = await manager.get_reading_history(user_id, limit=10)
        assert len(history) == 5

        # Step 4: Get reading statistics
        stats = await manager.get_reading_statistics(user_id)
        assert stats["total_articles_read"] == 5
        assert stats["avg_read_duration_seconds"] > 0
        assert stats["avg_completion_rate"] > 0.7

        # Step 5: Record satisfaction feedback
        for article_id in article_ids[:3]:
            await manager.record_satisfaction_feedback(
                user_id=user_id,
                article_id=article_id,
                satisfaction_score=0.8,
                feedback_type="explicit",
            )

        # Step 6: Learn preferences from queries
        queries = [
            "python best practices",
            "python tutorial",
            "machine learning basics",
            "machine learning algorithms",
            "python data structures",
            "web development python",
        ]

        learned_topics = await manager.learn_preferences_from_queries(user_id, queries)
        assert len(learned_topics) > 0
        assert "python" in learned_topics

        # Step 7: Update preferences
        learned_preferences = {
            "preferred_categories": ["programming", "data-science"],
            "preferred_technical_depth": "intermediate",
        }
        await manager.update_user_preferences(user_id, learned_preferences)

        # Step 8: Verify updated profile
        updated_profile = await manager.get_or_create_profile(user_id)
        assert len(updated_profile.preferred_topics) > 0

        # Step 9: Analyze satisfaction trends
        trends = await manager.analyze_satisfaction_trends(user_id, days_back=30)
        assert "trend" in trends
        assert "avg_satisfaction" in trends

        print("✓ Complete user profile workflow test passed")

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reading_history_persistence():
    """
    Test that reading history persists correctly across sessions.

    Validates: Requirement 8.1 - Track user reading history
    """
    manager = get_user_profile_manager()
    user_id = uuid4()
    article_id = uuid4()

    try:
        # Track article view
        await manager.track_article_view(
            user_id=user_id,
            article_id=article_id,
            read_duration_seconds=450,
            completion_rate=0.95,
        )

        # Retrieve and verify
        history = await manager.get_reading_history(user_id, limit=10)
        assert len(history) >= 1

        # Find our entry
        our_entry = next((entry for entry in history if entry.article_id == article_id), None)
        assert our_entry is not None
        assert our_entry.read_duration_seconds == 450
        assert our_entry.completion_rate == 0.95

        print("✓ Reading history persistence test passed")

    except Exception as e:
        pytest.fail(f"Reading history persistence test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_preference_learning_accuracy():
    """
    Test that preference learning accurately identifies user interests.

    Validates: Requirement 8.3 - Learn from user behavior patterns
    """
    manager = get_user_profile_manager()
    user_id = uuid4()

    try:
        # Simulate consistent query patterns
        queries = [
            "python machine learning tutorial",
            "python deep learning basics",
            "machine learning algorithms python",
            "python neural networks",
            "machine learning best practices",
            "python tensorflow tutorial",
            "deep learning python examples",
        ]

        learned_topics = await manager.learn_preferences_from_queries(user_id, queries)

        # Should identify python and machine learning as key topics
        assert "python" in learned_topics
        assert "machine" in learned_topics or "learning" in learned_topics

        # Should not include stop words
        assert "the" not in learned_topics
        assert "and" not in learned_topics

        print("✓ Preference learning accuracy test passed")

    except Exception as e:
        pytest.fail(f"Preference learning accuracy test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_satisfaction_feedback_tracking():
    """
    Test satisfaction feedback tracking and trend analysis.

    Validates: Requirement 8.5 - Track satisfaction feedback and optimize
    """
    manager = get_user_profile_manager()
    user_id = uuid4()

    try:
        # Create multiple reading sessions with varying satisfaction
        article_ids = [uuid4() for _ in range(10)]

        # Simulate improving satisfaction over time
        for i, article_id in enumerate(article_ids):
            await manager.track_article_view(
                user_id=user_id,
                article_id=article_id,
                read_duration_seconds=300,
                completion_rate=0.8,
            )

            # Satisfaction improves over time
            satisfaction = 0.5 + (i * 0.05)
            await manager.record_satisfaction_feedback(
                user_id=user_id,
                article_id=article_id,
                satisfaction_score=satisfaction,
                feedback_type="explicit",
            )

        # Analyze trends
        trends = await manager.analyze_satisfaction_trends(user_id, days_back=30)

        assert trends["avg_satisfaction"] > 0.5
        assert "trend" in trends
        assert "recommendations" in trends

        print("✓ Satisfaction feedback tracking test passed")

    except Exception as e:
        pytest.fail(f"Satisfaction feedback tracking test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_implicit_satisfaction_calculation():
    """
    Test implicit satisfaction calculation from reading behavior.

    Validates: Requirement 8.5 - Track satisfaction feedback
    """
    manager = get_user_profile_manager()

    # Test ideal reading behavior
    ideal_satisfaction = await manager.calculate_implicit_satisfaction(
        read_duration_seconds=300,
        completion_rate=0.9,
        expected_read_time=300,
    )
    assert ideal_satisfaction > 0.8

    # Test poor reading behavior (low completion)
    poor_satisfaction = await manager.calculate_implicit_satisfaction(
        read_duration_seconds=100,
        completion_rate=0.3,
        expected_read_time=300,
    )
    assert poor_satisfaction < 0.6

    # Test skimming behavior (too fast)
    skim_satisfaction = await manager.calculate_implicit_satisfaction(
        read_duration_seconds=100,
        completion_rate=0.9,
        expected_read_time=300,
    )
    assert 0.5 <= skim_satisfaction <= 0.8

    print("✓ Implicit satisfaction calculation test passed")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_profile_updates():
    """
    Test that concurrent profile updates are handled correctly.

    Validates: Requirements 8.1, 8.3, 8.5
    """
    manager = get_user_profile_manager()
    user_id = uuid4()

    try:
        # Create profile
        await manager.get_or_create_profile(user_id)

        # Simulate concurrent article views
        article_ids = [uuid4() for _ in range(5)]

        tasks = [
            manager.track_article_view(
                user_id=user_id,
                article_id=article_id,
                read_duration_seconds=300,
                completion_rate=0.8,
            )
            for article_id in article_ids
        ]

        # Execute concurrently
        await asyncio.gather(*tasks)

        # Verify all were tracked
        history = await manager.get_reading_history(user_id, limit=10)
        assert len(history) >= 5

        print("✓ Concurrent profile updates test passed")

    except Exception as e:
        pytest.fail(f"Concurrent profile updates test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_profile_personalization_over_time():
    """
    Test that profile personalization improves with more data.

    Validates: Requirements 8.1, 8.3, 8.5
    """
    manager = get_user_profile_manager()
    user_id = uuid4()

    try:
        # Initial profile (no data)
        initial_profile = await manager.get_or_create_profile(user_id)
        assert len(initial_profile.preferred_topics) == 0

        # Add some reading history
        for _ in range(10):
            await manager.track_article_view(
                user_id=user_id,
                article_id=uuid4(),
                read_duration_seconds=300,
                completion_rate=0.8,
            )

        # Learn from queries
        queries = [
            "python tutorial",
            "python best practices",
            "python advanced",
            "python frameworks",
            "python testing",
        ]
        learned_topics = await manager.learn_preferences_from_queries(user_id, queries)

        # Update preferences
        if learned_topics:
            await manager.update_user_preferences(
                user_id, {"preferred_categories": learned_topics[:5]}
            )

        # Verify profile has been enriched
        enriched_profile = await manager.get_or_create_profile(user_id)
        assert len(enriched_profile.reading_history) > 0
        assert len(enriched_profile.preferred_topics) > 0

        print("✓ Profile personalization over time test passed")

    except Exception as e:
        pytest.fail(f"Profile personalization over time test failed: {e}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
