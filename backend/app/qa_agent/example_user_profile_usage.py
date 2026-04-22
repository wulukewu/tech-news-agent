"""
Example Usage: UserProfileManager

Demonstrates how to use the UserProfileManager for tracking user behavior,
learning preferences, and optimizing recommendations.

Requirements: 8.1, 8.3, 8.5
"""

import asyncio
from uuid import uuid4

from .user_profile_manager import get_user_profile_manager


async def example_basic_tracking():
    """
    Example 1: Basic reading history tracking

    Demonstrates tracking article views with engagement metrics.
    """
    print("\n=== Example 1: Basic Reading History Tracking ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()
    article_id = uuid4()

    # Track an article view
    await manager.track_article_view(
        user_id=user_id,
        article_id=article_id,
        read_duration_seconds=450,  # User spent 7.5 minutes reading
        completion_rate=0.85,  # User read 85% of the article
    )

    print(f"✓ Tracked article view for user {user_id}")
    print(f"  Article: {article_id}")
    print("  Duration: 450 seconds")
    print("  Completion: 85%")

    # Retrieve reading history
    history = await manager.get_reading_history(user_id, limit=10)
    print(f"\n✓ Retrieved {len(history)} reading history entries")

    if history:
        entry = history[0]
        print(f"  Most recent: {entry.article_id}")
        print(f"  Read at: {entry.read_at}")
        print(f"  Duration: {entry.read_duration_seconds}s")
        print(f"  Completion: {entry.completion_rate * 100:.1f}%")


async def example_reading_statistics():
    """
    Example 2: Getting comprehensive reading statistics

    Demonstrates retrieving aggregated reading metrics.
    """
    print("\n=== Example 2: Reading Statistics ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()

    # Simulate multiple reading sessions
    for i in range(5):
        await manager.track_article_view(
            user_id=user_id,
            article_id=uuid4(),
            read_duration_seconds=300 + (i * 50),
            completion_rate=0.7 + (i * 0.05),
        )

    # Get statistics
    stats = await manager.get_reading_statistics(user_id)

    print(f"✓ Reading Statistics for user {user_id}:")
    print(f"  Total articles read: {stats['total_articles_read']}")
    print(f"  Average read duration: {stats['avg_read_duration_seconds']:.1f}s")
    print(f"  Average completion rate: {stats['avg_completion_rate'] * 100:.1f}%")
    print(f"  Average satisfaction: {stats['avg_satisfaction']:.2f}")
    print(f"  Reading days: {stats['reading_days']}")


async def example_preference_learning():
    """
    Example 3: Learning user preferences from query patterns

    Demonstrates automatic preference learning from user behavior.
    """
    print("\n=== Example 3: Preference Learning ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()

    # Simulate user queries over time
    queries = [
        "python best practices",
        "python tutorial for beginners",
        "machine learning with python",
        "python data structures",
        "machine learning algorithms",
        "python web development",
        "deep learning python",
    ]

    print(f"User queries ({len(queries)}):")
    for query in queries:
        print(f"  - {query}")

    # Learn preferences from queries
    learned_topics = await manager.learn_preferences_from_queries(user_id, queries)

    print(f"\n✓ Learned {len(learned_topics)} topics from query patterns:")
    for topic in learned_topics:
        print(f"  - {topic}")

    # Update user profile with learned preferences
    if learned_topics:
        await manager.update_user_preferences(user_id, {"preferred_categories": learned_topics[:5]})
        print("\n✓ Updated user profile with top 5 learned topics")


async def example_satisfaction_feedback():
    """
    Example 4: Recording and analyzing satisfaction feedback

    Demonstrates explicit and implicit satisfaction tracking.
    """
    print("\n=== Example 4: Satisfaction Feedback ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()
    article_id = uuid4()

    # Track article view
    await manager.track_article_view(
        user_id=user_id,
        article_id=article_id,
        read_duration_seconds=400,
        completion_rate=0.9,
    )

    # Record explicit satisfaction feedback
    await manager.record_satisfaction_feedback(
        user_id=user_id,
        article_id=article_id,
        satisfaction_score=0.85,
        feedback_type="explicit",
    )

    print("✓ Recorded explicit satisfaction feedback:")
    print(f"  User: {user_id}")
    print(f"  Article: {article_id}")
    print("  Score: 0.85 (85% satisfied)")

    # Calculate implicit satisfaction from behavior
    implicit_score = await manager.calculate_implicit_satisfaction(
        read_duration_seconds=400,
        completion_rate=0.9,
        expected_read_time=420,
    )

    print("\n✓ Calculated implicit satisfaction from behavior:")
    print("  Read duration: 400s (expected: 420s)")
    print("  Completion rate: 90%")
    print(f"  Implicit satisfaction: {implicit_score:.2f}")


async def example_satisfaction_trends():
    """
    Example 5: Analyzing satisfaction trends for optimization

    Demonstrates trend analysis and recommendation generation.
    """
    print("\n=== Example 5: Satisfaction Trend Analysis ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()

    # Simulate reading sessions with varying satisfaction
    print("Simulating 10 reading sessions with improving satisfaction...")

    for i in range(10):
        article_id = uuid4()

        await manager.track_article_view(
            user_id=user_id,
            article_id=article_id,
            read_duration_seconds=300 + (i * 20),
            completion_rate=0.6 + (i * 0.03),
        )

        # Satisfaction improves over time
        satisfaction = 0.5 + (i * 0.05)
        await manager.record_satisfaction_feedback(
            user_id=user_id,
            article_id=article_id,
            satisfaction_score=satisfaction,
            feedback_type="implicit",
        )

    # Analyze trends
    trends = await manager.analyze_satisfaction_trends(user_id, days_back=30)

    print("\n✓ Satisfaction Trend Analysis:")
    print(f"  Trend: {trends['trend']}")
    print(f"  Average satisfaction: {trends['avg_satisfaction']:.2f}")
    print(f"  Improving: {trends['satisfaction_improving']}")
    print(f"  Data points: {trends['data_points']}")

    if trends["recommendations"]:
        print("\n  Recommendations:")
        for rec in trends["recommendations"]:
            print(f"    - {rec}")


async def example_complete_workflow():
    """
    Example 6: Complete user profile workflow

    Demonstrates end-to-end profile management from creation to optimization.
    """
    print("\n=== Example 6: Complete User Profile Workflow ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()

    # Step 1: Create or get user profile
    print("Step 1: Creating user profile...")
    profile = await manager.get_or_create_profile(user_id)
    print(f"✓ Profile created for user {user_id}")
    print(f"  Initial topics: {len(profile.preferred_topics)}")
    print(f"  Initial history: {len(profile.reading_history)} articles")

    # Step 2: Track reading activity
    print("\nStep 2: Tracking reading activity...")
    article_ids = []
    for i in range(5):
        article_id = uuid4()
        article_ids.append(article_id)

        await manager.track_article_view(
            user_id=user_id,
            article_id=article_id,
            read_duration_seconds=300 + (i * 50),
            completion_rate=0.75 + (i * 0.04),
        )

    print(f"✓ Tracked {len(article_ids)} article views")

    # Step 3: Record satisfaction feedback
    print("\nStep 3: Recording satisfaction feedback...")
    for article_id in article_ids:
        await manager.record_satisfaction_feedback(
            user_id=user_id,
            article_id=article_id,
            satisfaction_score=0.8,
            feedback_type="explicit",
        )

    print(f"✓ Recorded satisfaction for {len(article_ids)} articles")

    # Step 4: Learn preferences from queries
    print("\nStep 4: Learning preferences from queries...")
    queries = [
        "python machine learning",
        "python deep learning",
        "machine learning algorithms",
        "python neural networks",
        "deep learning tutorial",
        "python tensorflow",
    ]

    learned_topics = await manager.learn_preferences_from_queries(user_id, queries)
    print(f"✓ Learned {len(learned_topics)} topics: {', '.join(learned_topics[:5])}")

    # Step 5: Update profile with learned preferences
    print("\nStep 5: Updating user profile...")
    if learned_topics:
        await manager.update_user_preferences(
            user_id,
            {
                "preferred_categories": learned_topics[:5],
                "preferred_technical_depth": "intermediate",
            },
        )
        print("✓ Profile updated with learned preferences")

    # Step 6: Get updated profile
    print("\nStep 6: Retrieving updated profile...")
    updated_profile = await manager.get_or_create_profile(user_id)
    print("✓ Updated profile retrieved:")
    print(f"  Preferred topics: {len(updated_profile.preferred_topics)}")
    print(f"  Reading history: {len(updated_profile.reading_history)} articles")
    print(f"  Satisfaction scores: {len(updated_profile.satisfaction_scores)}")
    print(f"  Average satisfaction: {updated_profile.get_average_satisfaction():.2f}")

    # Step 7: Analyze trends for optimization
    print("\nStep 7: Analyzing satisfaction trends...")
    trends = await manager.analyze_satisfaction_trends(user_id, days_back=30)
    print("✓ Trend analysis complete:")
    print(f"  Trend: {trends['trend']}")
    print(f"  Average satisfaction: {trends['avg_satisfaction']:.2f}")

    print("\n✓ Complete workflow finished successfully!")


async def example_personalization_impact():
    """
    Example 7: Demonstrating personalization impact

    Shows how user profiles improve recommendations over time.
    """
    print("\n=== Example 7: Personalization Impact ===\n")

    manager = get_user_profile_manager()
    user_id = uuid4()

    # Create profile
    profile = await manager.get_or_create_profile(user_id)

    print("Initial state (no personalization):")
    print(f"  Preferred topics: {profile.preferred_topics}")
    print(f"  Average satisfaction: {profile.get_average_satisfaction():.2f}")

    # Simulate consistent reading behavior
    print("\nSimulating consistent reading in 'python' and 'machine-learning'...")

    for i in range(15):
        await manager.track_article_view(
            user_id=user_id,
            article_id=uuid4(),
            read_duration_seconds=350,
            completion_rate=0.85,
        )

    # Learn from queries
    queries = [
        "python tutorial",
        "python best practices",
        "machine learning basics",
        "python machine learning",
        "machine learning algorithms",
    ] * 2  # Repeat to show consistency

    learned_topics = await manager.learn_preferences_from_queries(user_id, queries)

    if learned_topics:
        await manager.update_user_preferences(user_id, {"preferred_categories": learned_topics[:5]})

    # Get updated profile
    updated_profile = await manager.get_or_create_profile(user_id)

    print("\nAfter learning (with personalization):")
    print(f"  Preferred topics: {updated_profile.preferred_topics}")
    print(f"  Reading history: {len(updated_profile.reading_history)} articles")
    print(f"  Query patterns learned: {len(learned_topics)} topics")

    print("\n✓ Personalization enables:")
    print("  - Better article recommendations")
    print("  - Improved search result ranking")
    print("  - Tailored insights and suggestions")
    print("  - Optimized content discovery")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("UserProfileManager - Example Usage")
    print("=" * 70)

    try:
        await example_basic_tracking()
        await example_reading_statistics()
        await example_preference_learning()
        await example_satisfaction_feedback()
        await example_satisfaction_trends()
        await example_complete_workflow()
        await example_personalization_impact()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
