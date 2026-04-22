"""
Property-Based Tests for User Profile Learning

This module implements property-based tests for the User Profile Learning
functionality, validating Property 12 of the Intelligent Q&A Agent.

Feature: intelligent-qa-agent
Property tested:
- Property 12: User Profile Learning

Requirements validated: 8.1, 8.3, 8.5

Property 12 states:
    For any user's reading history and query patterns, the system SHALL build
    accurate user profiles, provide increasingly relevant query suggestions over
    time, and adapt recommendations based on satisfaction feedback.
"""

from typing import List
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.qa_agent.models import QueryLanguage, UserProfile
from app.qa_agent.user_profile_manager import UserProfileManager

# ============================================================================
# Custom Strategies
# ============================================================================


def article_id_strategy() -> st.SearchStrategy:
    """Generate valid article UUIDs."""
    return st.builds(uuid4)


def user_id_strategy() -> st.SearchStrategy:
    """Generate valid user UUIDs."""
    return st.builds(uuid4)


def satisfaction_score_strategy() -> st.SearchStrategy:
    """Generate valid satisfaction scores in [0.0, 1.0]."""
    return st.floats(
        min_value=0.0,
        max_value=1.0,
        allow_nan=False,
        allow_infinity=False,
    )


def topic_strategy() -> st.SearchStrategy:
    """Generate realistic topic strings."""
    return st.sampled_from(
        [
            "python",
            "machine learning",
            "deep learning",
            "javascript",
            "security",
            "cloud computing",
            "database",
            "API design",
            "DevOps",
            "data science",
            "web development",
            "mobile development",
            "blockchain",
            "performance optimization",
            "testing",
            "architecture",
            "microservices",
            "neural networks",
            "natural language processing",
            "computer vision",
        ]
    )


def query_strategy() -> st.SearchStrategy:
    """Generate realistic query strings with meaningful words."""
    return st.sampled_from(
        [
            "python best practices",
            "machine learning tutorial",
            "deep learning algorithms",
            "web development frameworks",
            "database optimization",
            "cloud computing services",
            "security vulnerabilities",
            "API design patterns",
            "DevOps automation",
            "data science tools",
            "neural network training",
            "natural language processing",
            "computer vision models",
            "microservices architecture",
            "performance testing",
            "python data structures",
            "machine learning python",
            "deep learning python",
            "python tensorflow",
            "python neural networks",
        ]
    )


@st.composite
def user_profile_strategy(draw) -> UserProfile:
    """Generate diverse UserProfile instances."""
    reading_history = draw(st.lists(article_id_strategy(), min_size=0, max_size=50, unique=True))
    preferred_topics = draw(st.lists(topic_strategy(), min_size=0, max_size=10, unique=True))
    satisfaction_scores = draw(st.lists(satisfaction_score_strategy(), min_size=0, max_size=20))
    query_history = draw(st.lists(query_strategy(), min_size=0, max_size=20))
    language = draw(st.sampled_from([QueryLanguage.CHINESE, QueryLanguage.ENGLISH]))

    return UserProfile(
        user_id=draw(user_id_strategy()),
        reading_history=reading_history,
        preferred_topics=preferred_topics,
        language_preference=language,
        interaction_patterns={},
        query_history=query_history,
        satisfaction_scores=satisfaction_scores,
    )


# ============================================================================
# Property 12: User Profile Learning — Requirement 8.1
# Reading history tracking: profile accurately records articles read
# ============================================================================


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    new_articles=st.lists(article_id_strategy(), min_size=1, max_size=20, unique=True),
)
def test_property_12_reading_history_grows_monotonically(
    profile: UserProfile,
    new_articles: List[UUID],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.1**

    For any user profile, adding articles to reading history SHALL grow the
    history monotonically — each new unique article increases the count by
    exactly one, and already-read articles are not duplicated.
    """
    initial_count = len(profile.reading_history)
    initial_set = set(profile.reading_history)

    # Only add articles not already in history to count expected additions
    truly_new = [a for a in new_articles if a not in initial_set]

    for article_id in new_articles:
        profile.add_read_article(article_id)

    final_count = len(profile.reading_history)
    final_set = set(profile.reading_history)

    # History should have grown by exactly the number of truly new articles
    assert final_count == initial_count + len(truly_new), (
        f"Expected history to grow by {len(truly_new)}, "
        f"but grew by {final_count - initial_count}"
    )

    # All new articles should now be in history
    for article_id in new_articles:
        assert (
            article_id in final_set
        ), f"Article {article_id} should be in reading history after add_read_article"

    # No duplicates should exist
    assert len(profile.reading_history) == len(
        set(profile.reading_history)
    ), "Reading history must not contain duplicate article IDs"


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    article=article_id_strategy(),
)
def test_property_12_has_read_article_consistent_with_history(
    profile: UserProfile,
    article: UUID,
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.1**

    For any article, has_read_article SHALL return True if and only if the
    article is present in reading_history — the membership check must be
    consistent with the stored history.
    """
    # Before adding: membership check must match actual history
    before_add = profile.has_read_article(article)
    assert before_add == (
        article in profile.reading_history
    ), "has_read_article must be consistent with reading_history membership"

    # After adding: must always return True
    profile.add_read_article(article)
    assert profile.has_read_article(
        article
    ), "has_read_article must return True after add_read_article"

    # Adding again must not change the result
    profile.add_read_article(article)
    assert profile.has_read_article(
        article
    ), "has_read_article must remain True after duplicate add"


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    articles=st.lists(article_id_strategy(), min_size=1001, max_size=1100, unique=True),
)
def test_property_12_reading_history_capped_at_1000(articles: List[UUID]):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.1**

    For any sequence of article additions, the reading history SHALL never
    exceed 1000 entries — the profile retains only the most recent 1000 articles.
    """
    profile = UserProfile(user_id=uuid4())

    for article_id in articles:
        profile.add_read_article(article_id)

    assert (
        len(profile.reading_history) <= 1000
    ), f"Reading history must not exceed 1000 entries, got {len(profile.reading_history)}"

    # The most recently added articles should be retained
    last_articles = articles[-1000:]
    for article_id in last_articles:
        assert (
            article_id in profile.reading_history
        ), f"Most recent article {article_id} should be in capped history"


# ============================================================================
# Property 12: User Profile Learning — Requirement 8.3
# Query pattern learning: preferences extracted from repeated query terms
# ============================================================================


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    repeated_topic=st.sampled_from(
        [
            "python",
            "machine",
            "learning",
            "security",
            "database",
            "cloud",
            "testing",
            "architecture",
            "performance",
            "neural",
        ]
    ),
    repeat_count=st.integers(min_value=5, max_value=15),
    noise_queries=st.lists(
        st.sampled_from(
            [
                "random topic one",
                "unrelated subject here",
                "something else entirely",
            ]
        ),
        min_size=0,
        max_size=3,
    ),
)
def test_property_12_frequent_query_terms_become_learned_topics(
    repeated_topic: str,
    repeat_count: int,
    noise_queries: List[str],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any set of queries where a topic appears frequently, the system SHALL
    learn that topic as a preference — terms appearing in >= 20% of queries
    must appear in the learned topics list.
    """
    import asyncio

    manager = UserProfileManager()
    user_id = uuid4()

    # Build queries where the repeated_topic appears in most of them
    queries = [f"{repeated_topic} tutorial {i}" for i in range(repeat_count)]
    queries += noise_queries

    # Need at least the threshold (5) queries to trigger learning
    assume(len(queries) >= manager._preference_learning_threshold)

    learned = asyncio.get_event_loop().run_until_complete(
        manager.learn_preferences_from_queries(user_id, queries)
    )

    # The repeated topic should appear in learned preferences
    assert repeated_topic in learned, (
        f"Topic '{repeated_topic}' appeared in {repeat_count}/{len(queries)} queries "
        f"but was not learned. Learned: {learned}"
    )


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    queries=st.lists(query_strategy(), min_size=0, max_size=4),
)
def test_property_12_insufficient_queries_return_empty_preferences(
    queries: List[str],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any set of queries below the learning threshold (5), the system SHALL
    return an empty list — no preferences are learned from insufficient data.
    """
    import asyncio

    manager = UserProfileManager()
    user_id = uuid4()

    # Ensure we are below the threshold
    assume(len(queries) < manager._preference_learning_threshold)

    learned = asyncio.get_event_loop().run_until_complete(
        manager.learn_preferences_from_queries(user_id, queries)
    )

    assert learned == [], (
        f"With only {len(queries)} queries (threshold={manager._preference_learning_threshold}), "
        f"no preferences should be learned, but got: {learned}"
    )


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    new_queries=st.lists(query_strategy(), min_size=1, max_size=10),
)
def test_property_12_query_history_grows_and_is_bounded(
    profile: UserProfile,
    new_queries: List[str],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any sequence of query additions, the query history SHALL grow by
    exactly the number of added queries (duplicates allowed) and never
    exceed 100 entries.
    """
    initial_count = len(profile.query_history)

    for query in new_queries:
        profile.add_query(query)

    final_count = len(profile.query_history)

    # History should have grown by exactly the number of new queries
    # (capped at 100 total)
    expected_count = min(initial_count + len(new_queries), 100)
    assert (
        final_count == expected_count
    ), f"Expected query history size {expected_count}, got {final_count}"

    # Must never exceed 100
    assert final_count <= 100, f"Query history must not exceed 100 entries, got {final_count}"


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    topics=st.lists(topic_strategy(), min_size=1, max_size=10, unique=True),
)
def test_property_12_preferred_topics_are_deduplicated(
    profile: UserProfile,
    topics: List[str],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any set of preferred topics, the profile SHALL store them without
    duplicates — the preferred_topics list must contain unique entries only.
    """
    # Set topics including duplicates
    duplicated = topics + topics  # intentionally duplicate
    profile_with_dupes = UserProfile(
        user_id=uuid4(),
        preferred_topics=duplicated,
    )

    # No duplicates should be stored
    assert len(profile_with_dupes.preferred_topics) == len(
        set(profile_with_dupes.preferred_topics)
    ), "preferred_topics must not contain duplicates"

    # All original topics should be present
    for topic in topics:
        assert (
            topic in profile_with_dupes.preferred_topics
        ), f"Topic '{topic}' should be in preferred_topics after deduplication"


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    topics=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=15,
        ),
        min_size=21,
        max_size=40,
        unique=True,
    ),
)
def test_property_12_preferred_topics_capped_at_20(topics: List[str]):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any list of preferred topics, the profile SHALL retain at most 20
    unique topics — excess topics are discarded.
    """
    profile = UserProfile(user_id=uuid4(), preferred_topics=topics)

    assert (
        len(profile.preferred_topics) <= 20
    ), f"preferred_topics must not exceed 20 entries, got {len(profile.preferred_topics)}"


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    limit=st.integers(min_value=1, max_value=10),
)
def test_property_12_get_top_topics_respects_limit(
    profile: UserProfile,
    limit: int,
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.3**

    For any user profile and limit, get_top_topics SHALL return at most
    `limit` topics, and the returned topics SHALL be a prefix of preferred_topics.
    """
    top = profile.get_top_topics(limit)

    # Must not exceed the requested limit
    assert (
        len(top) <= limit
    ), f"get_top_topics({limit}) returned {len(top)} topics, expected <= {limit}"

    # Must not exceed the actual number of preferred topics
    assert len(top) <= len(
        profile.preferred_topics
    ), "get_top_topics must not return more topics than exist in preferred_topics"

    # Returned topics must be a prefix of preferred_topics
    assert (
        top == profile.preferred_topics[:limit]
    ), "get_top_topics must return the first `limit` entries of preferred_topics"


# ============================================================================
# Property 12: User Profile Learning — Requirement 8.5
# Satisfaction feedback: scores tracked and averaged correctly
# ============================================================================


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    new_scores=st.lists(satisfaction_score_strategy(), min_size=1, max_size=10),
)
def test_property_12_satisfaction_scores_tracked_accurately(
    profile: UserProfile,
    new_scores: List[float],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For any sequence of satisfaction scores, the profile SHALL record each
    valid score (0.0–1.0) and the running average SHALL equal the arithmetic
    mean of all stored scores.
    """
    for score in new_scores:
        profile.add_satisfaction_score(score)

    stored = profile.satisfaction_scores

    # All stored scores must be in valid range
    for s in stored:
        assert 0.0 <= s <= 1.0, f"Stored satisfaction score {s} is outside valid range [0.0, 1.0]"

    # Average must equal arithmetic mean of stored scores
    if stored:
        expected_avg = sum(stored) / len(stored)
        actual_avg = profile.get_average_satisfaction()
        assert abs(actual_avg - expected_avg) < 1e-9, (
            f"get_average_satisfaction() returned {actual_avg}, " f"expected {expected_avg}"
        )


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
)
def test_property_12_empty_satisfaction_returns_neutral_default(
    profile: UserProfile,
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For a user profile with no satisfaction scores, get_average_satisfaction
    SHALL return the neutral default value of 0.5.
    """
    empty_profile = UserProfile(
        user_id=profile.user_id,
        reading_history=profile.reading_history,
        preferred_topics=profile.preferred_topics,
        language_preference=profile.language_preference,
        interaction_patterns=profile.interaction_patterns,
        query_history=profile.query_history,
        satisfaction_scores=[],  # explicitly empty
    )

    avg = empty_profile.get_average_satisfaction()
    assert avg == 0.5, f"Empty satisfaction scores should return neutral default 0.5, got {avg}"


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    scores=st.lists(satisfaction_score_strategy(), min_size=51, max_size=100),
)
def test_property_12_satisfaction_scores_capped_at_50(scores: List[float]):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For any sequence of satisfaction scores, the profile SHALL retain at most
    50 scores — only the most recent 50 are kept.
    """
    profile = UserProfile(user_id=uuid4())

    for score in scores:
        profile.add_satisfaction_score(score)

    assert (
        len(profile.satisfaction_scores) <= 50
    ), f"satisfaction_scores must not exceed 50 entries, got {len(profile.satisfaction_scores)}"

    # The most recently added scores should be retained
    last_50 = scores[-50:]
    for score in last_50:
        assert (
            score in profile.satisfaction_scores
        ), f"Most recent score {score} should be in capped satisfaction_scores"


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    profile=user_profile_strategy(),
    invalid_scores=st.lists(
        st.one_of(
            st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False),
            st.floats(min_value=1.001, allow_nan=False, allow_infinity=False),
        ),
        min_size=1,
        max_size=5,
    ),
)
def test_property_12_invalid_satisfaction_scores_rejected(
    profile: UserProfile,
    invalid_scores: List[float],
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For any satisfaction score outside [0.0, 1.0], the profile SHALL reject
    it — invalid scores must not be stored in satisfaction_scores.
    """
    initial_scores = list(profile.satisfaction_scores)

    for score in invalid_scores:
        profile.add_satisfaction_score(score)

    # Scores list should be unchanged (invalid scores silently dropped)
    assert profile.satisfaction_scores == initial_scores, (
        f"Invalid scores {invalid_scores} should not be added to satisfaction_scores. "
        f"Before: {initial_scores}, After: {profile.satisfaction_scores}"
    )


# ============================================================================
# Property 12: User Profile Learning — Implicit Satisfaction Calculation
# ============================================================================


@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    completion_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    read_duration=st.integers(min_value=1, max_value=3600),
    expected_read_time=st.integers(min_value=1, max_value=3600),
)
def test_property_12_implicit_satisfaction_always_in_valid_range(
    completion_rate: float,
    read_duration: int,
    expected_read_time: int,
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For any combination of reading behavior metrics, the implicit satisfaction
    score SHALL always be in the valid range [0.0, 1.0].
    """
    import asyncio

    manager = UserProfileManager()

    score = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=read_duration,
            completion_rate=completion_rate,
            expected_read_time=expected_read_time,
        )
    )

    assert 0.0 <= score <= 1.0, (
        f"Implicit satisfaction score {score} is outside valid range [0.0, 1.0] "
        f"for completion_rate={completion_rate}, read_duration={read_duration}, "
        f"expected_read_time={expected_read_time}"
    )


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(
    completion_rate=st.floats(min_value=0.8, max_value=1.0, allow_nan=False, allow_infinity=False),
    expected_read_time=st.integers(min_value=60, max_value=600),
)
def test_property_12_high_completion_yields_higher_satisfaction(
    completion_rate: float,
    expected_read_time: int,
):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.5**

    For high completion rates (>= 0.8) with on-pace reading, the implicit
    satisfaction score SHALL be higher than for low completion rates (< 0.4)
    under the same reading conditions.
    """
    import asyncio

    manager = UserProfileManager()

    # On-pace reading: actual time close to expected
    on_pace_duration = int(expected_read_time * 1.0)

    high_score = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=on_pace_duration,
            completion_rate=completion_rate,
            expected_read_time=expected_read_time,
        )
    )

    low_score = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=on_pace_duration,
            completion_rate=0.2,  # low completion
            expected_read_time=expected_read_time,
        )
    )

    assert high_score > low_score, (
        f"High completion ({completion_rate}) should yield higher satisfaction "
        f"({high_score}) than low completion (0.2) ({low_score})"
    )


# ============================================================================
# Property 12: User Profile Learning — Profile Serialization Round-trip
# ============================================================================


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
@given(profile=user_profile_strategy())
def test_property_12_profile_serialization_round_trip(profile: UserProfile):
    """
    Feature: intelligent-qa-agent, Property 12: User Profile Learning

    **Validates: Requirements 8.1, 8.3, 8.5**

    For any user profile, serializing to dict/JSON and deserializing back
    SHALL produce an equivalent profile — all learned data is preserved
    through the storage round-trip.
    """
    # Serialize to dict and back
    profile_dict = profile.to_dict()
    restored = UserProfile.from_dict(profile_dict)

    # Core identity must be preserved
    assert str(restored.user_id) == str(
        profile.user_id
    ), "user_id must survive serialization round-trip"

    # Reading history must be preserved
    assert [str(a) for a in restored.reading_history] == [
        str(a) for a in profile.reading_history
    ], "reading_history must survive serialization round-trip"

    # Preferred topics must be preserved
    assert (
        restored.preferred_topics == profile.preferred_topics
    ), "preferred_topics must survive serialization round-trip"

    # Language preference must be preserved
    assert (
        restored.language_preference == profile.language_preference
    ), "language_preference must survive serialization round-trip"

    # Satisfaction scores must be preserved
    assert (
        restored.satisfaction_scores == profile.satisfaction_scores
    ), "satisfaction_scores must survive serialization round-trip"

    # Query history must be preserved
    assert (
        restored.query_history == profile.query_history
    ), "query_history must survive serialization round-trip"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
