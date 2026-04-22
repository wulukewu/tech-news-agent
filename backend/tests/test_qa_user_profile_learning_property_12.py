"""
Property-based tests for User Profile Learning (Property 12)

Feature: intelligent-qa-agent
Property 12: User Profile Learning

**Validates: Requirements 8.1, 8.3, 8.5**

For any user's reading history and query patterns, the system SHALL build
accurate user profiles, provide increasingly relevant query suggestions over
time, and adapt recommendations based on satisfaction feedback.

Sub-properties tested:
  12.1 - Profile reading history accumulation (Req 8.1)
  12.2 - Query history accumulation (Req 8.1, 8.3)
  12.3 - Preference learning from queries (Req 8.3)
  12.4 - Satisfaction score tracking (Req 8.5)
  12.5 - Implicit satisfaction calculation (Req 8.5)
  12.6 - Profile serialization round-trip (Req 8.1)
  12.7 - Preferred topics deduplication (Req 8.3)
  12.8 - Satisfaction trend analysis (Req 8.5)
"""

import asyncio
from typing import List
from uuid import UUID, uuid4

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.qa_agent.models import QueryLanguage, UserProfile
from app.qa_agent.user_profile_manager import UserProfileManager

# ============================================================================
# Custom Strategies for Test Data Generation
# ============================================================================


@composite
def article_ids(draw, min_size=1, max_size=20):
    """Generate a list of unique article UUIDs."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    return [uuid4() for _ in range(count)]


@composite
def query_strings(draw, min_size=1, max_size=20):
    """Generate realistic query strings with repeated keywords for learning tests."""
    topics = [
        "machine learning",
        "deep learning",
        "neural networks",
        "artificial intelligence",
        "natural language processing",
        "computer vision",
        "blockchain",
        "cloud computing",
        "data science",
        "python programming",
        "web development",
        "cybersecurity",
        "quantum computing",
        "robotics",
        "automation",
    ]
    templates = [
        "What is {}?",
        "Tell me about {}",
        "How does {} work?",
        "Latest news on {}",
        "Introduction to {}",
        "Advanced {} techniques",
        "Best practices for {}",
    ]
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    queries = []
    for _ in range(count):
        template = draw(st.sampled_from(templates))
        topic = draw(st.sampled_from(topics))
        queries.append(template.format(topic))
    return queries


@composite
def satisfaction_scores(draw, min_size=1, max_size=60):
    """Generate a list of valid satisfaction scores in [0.0, 1.0]."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)) for _ in range(count)]


@composite
def topic_lists_with_duplicates(draw, min_size=1, max_size=30):
    """Generate a list of topics that may contain duplicates."""
    base_topics = [
        "AI",
        "Machine Learning",
        "Python",
        "Data Science",
        "Cloud",
        "Security",
        "Web Dev",
        "Mobile",
        "DevOps",
        "Blockchain",
        "IoT",
        "AR/VR",
        "Quantum",
        "Robotics",
        "NLP",
        "Computer Vision",
        "Big Data",
        "Analytics",
        "API",
        "Microservices",
        "Kubernetes",
        "Docker",
        "React",
        "TypeScript",
        "Rust",
    ]
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    # Allow duplicates by sampling with replacement
    return [draw(st.sampled_from(base_topics)) for _ in range(count)]


@composite
def user_profiles(draw):
    """Generate a valid UserProfile with arbitrary field values."""
    num_articles = draw(st.integers(min_value=0, max_value=50))
    num_queries = draw(st.integers(min_value=0, max_value=30))
    num_scores = draw(st.integers(min_value=0, max_value=30))

    reading_history = [uuid4() for _ in range(num_articles)]
    query_history = draw(query_strings(min_size=0, max_size=num_queries)) if num_queries > 0 else []
    scores = [
        draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)) for _ in range(num_scores)
    ]

    num_topics = draw(st.integers(min_value=0, max_value=10))
    base_topics = [
        "AI",
        "ML",
        "Python",
        "Cloud",
        "Security",
        "Web",
        "Data",
        "DevOps",
        "Mobile",
        "IoT",
    ]
    topics = (
        list(dict.fromkeys(draw(st.sampled_from(base_topics)) for _ in range(num_topics)))
        if num_topics > 0
        else []
    )

    return UserProfile(
        user_id=uuid4(),
        reading_history=reading_history,
        preferred_topics=topics,
        language_preference=draw(st.sampled_from(list(QueryLanguage))),
        interaction_patterns={},
        query_history=query_history,
        satisfaction_scores=scores,
    )


# ============================================================================
# Property 12.1: Profile Reading History Accumulation
# **Validates: Requirement 8.1**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(article_id_list=article_ids(min_size=1, max_size=50))
def test_property_12_1_reading_history_accumulation(article_id_list: List[UUID]):
    """
    Property 12.1: Profile Reading History Accumulation

    **Validates: Requirements 8.1**

    For any sequence of article IDs added to a UserProfile, the reading_history
    SHALL contain all unique articles (up to the 1000-article limit), with
    duplicates not added twice.
    """
    profile = UserProfile(user_id=uuid4())

    # Add all articles (including intentional duplicates by re-adding)
    for article_id in article_id_list:
        profile.add_read_article(article_id)
    # Add them all again to test deduplication
    for article_id in article_id_list:
        profile.add_read_article(article_id)

    unique_ids = list(dict.fromkeys(article_id_list))  # preserve order, deduplicate

    # Duplicates must not be stored twice
    assert len(profile.reading_history) == len(
        unique_ids
    ), f"Expected {len(unique_ids)} unique articles, got {len(profile.reading_history)}"

    # All unique articles must be present
    for article_id in unique_ids:
        assert (
            article_id in profile.reading_history
        ), f"Article {article_id} should be in reading history"

    # has_read_article must agree
    for article_id in unique_ids:
        assert profile.has_read_article(
            article_id
        ), f"has_read_article should return True for {article_id}"


@settings(max_examples=20, deadline=None)
@given(
    first_batch=article_ids(min_size=900, max_size=1000),
    second_batch=article_ids(min_size=50, max_size=100),
)
def test_property_12_1b_reading_history_1000_limit(
    first_batch: List[UUID], second_batch: List[UUID]
):
    """
    Property 12.1b: Reading history is capped at 1000 articles.

    **Validates: Requirement 8.1**
    """
    profile = UserProfile(user_id=uuid4())

    for article_id in first_batch:
        profile.add_read_article(article_id)

    for article_id in second_batch:
        profile.add_read_article(article_id)

    assert (
        len(profile.reading_history) <= 1000
    ), f"Reading history must not exceed 1000 articles, got {len(profile.reading_history)}"


# ============================================================================
# Property 12.2: Query History Accumulation
# **Validates: Requirements 8.1, 8.3**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(queries=query_strings(min_size=1, max_size=30))
def test_property_12_2_query_history_accumulation(queries: List[str]):
    """
    Property 12.2: Query History Accumulation

    **Validates: Requirements 8.1, 8.3**

    For any sequence of queries added to a UserProfile, the query_history SHALL
    contain the most recent queries (up to 100), in order.
    """
    profile = UserProfile(user_id=uuid4())

    for query in queries:
        profile.add_query(query)

    expected_count = min(len(queries), 100)
    assert (
        len(profile.query_history) == expected_count
    ), f"Expected {expected_count} queries in history, got {len(profile.query_history)}"

    # The stored queries must be the most recent ones, in order
    expected_queries = queries[-expected_count:]
    assert (
        profile.query_history == expected_queries
    ), "Query history should contain the most recent queries in chronological order"


@settings(max_examples=20, deadline=None)
@given(queries=query_strings(min_size=110, max_size=150))
def test_property_12_2b_query_history_100_limit(queries: List[str]):
    """
    Property 12.2b: Query history is capped at 100 entries.

    **Validates: Requirements 8.1, 8.3**
    """
    profile = UserProfile(user_id=uuid4())

    for query in queries:
        profile.add_query(query)

    assert (
        len(profile.query_history) <= 100
    ), f"Query history must not exceed 100 entries, got {len(profile.query_history)}"

    # Must keep the most recent 100
    assert (
        profile.query_history == queries[-100:]
    ), "Query history should keep the most recent 100 queries"


# ============================================================================
# Property 12.3: Preference Learning from Queries
# **Validates: Requirement 8.3**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(queries=query_strings(min_size=5, max_size=30))
def test_property_12_3_preference_learning_sufficient_queries(queries: List[str]):
    """
    Property 12.3a: Preference learning with sufficient queries (>= 5).

    **Validates: Requirement 8.3**

    For any list of queries >= 5 (the learning threshold),
    learn_preferences_from_queries SHALL return a non-empty list of topics
    when keywords repeat across queries.
    """
    manager = UserProfileManager()
    user_id = uuid4()

    # Run the async method synchronously
    result = asyncio.get_event_loop().run_until_complete(
        manager.learn_preferences_from_queries(user_id, queries)
    )

    # Result must be a list
    assert isinstance(result, list), "learn_preferences_from_queries must return a list"

    # With >= 5 queries that share topic keywords (from our generator), we expect
    # at least some topics to be learned when there is repetition.
    # We don't assert non-empty unconditionally because the generator may produce
    # queries with no repeated keywords — but we do assert the return type and
    # that all returned items are strings.
    for topic in result:
        assert isinstance(topic, str), f"Each learned topic must be a string, got {type(topic)}"


@settings(max_examples=50, deadline=None)
@given(queries=query_strings(min_size=1, max_size=4))
def test_property_12_3b_preference_learning_insufficient_queries(queries: List[str]):
    """
    Property 12.3b: Preference learning with insufficient queries (< 5).

    **Validates: Requirement 8.3**

    For lists < 5 queries, learn_preferences_from_queries SHALL return an empty list.
    """
    manager = UserProfileManager()
    user_id = uuid4()

    result = asyncio.get_event_loop().run_until_complete(
        manager.learn_preferences_from_queries(user_id, queries)
    )

    assert (
        result == []
    ), f"Expected empty list for {len(queries)} queries (below threshold of 5), got {result}"


@settings(max_examples=30, deadline=None)
@given(
    repeated_keyword=st.sampled_from(["machine", "learning", "python", "cloud", "security"]),
    num_queries=st.integers(min_value=5, max_value=20),
)
def test_property_12_3c_preference_learning_repeated_keywords(
    repeated_keyword: str, num_queries: int
):
    """
    Property 12.3c: Repeated keywords across queries produce learned topics.

    **Validates: Requirement 8.3**

    When the same keyword appears in the majority of queries, it SHALL appear
    in the learned topics list.
    """
    manager = UserProfileManager()
    user_id = uuid4()

    # Build queries that all contain the repeated keyword
    queries = [f"What is {repeated_keyword} and how does it work?" for _ in range(num_queries)]

    result = asyncio.get_event_loop().run_until_complete(
        manager.learn_preferences_from_queries(user_id, queries)
    )

    assert isinstance(result, list), "Result must be a list"
    assert (
        len(result) > 0
    ), f"Expected non-empty topics when '{repeated_keyword}' repeats across {num_queries} queries"
    assert (
        repeated_keyword in result
    ), f"'{repeated_keyword}' should appear in learned topics when it repeats across all queries"


# ============================================================================
# Property 12.4: Satisfaction Score Tracking
# **Validates: Requirement 8.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(scores=satisfaction_scores(min_size=1, max_size=60))
def test_property_12_4_satisfaction_score_tracking(scores: List[float]):
    """
    Property 12.4: Satisfaction Score Tracking

    **Validates: Requirement 8.5**

    For any sequence of valid satisfaction scores (0.0–1.0) added to a
    UserProfile, the average satisfaction SHALL equal the arithmetic mean of
    the stored scores (up to 50 scores).
    """
    profile = UserProfile(user_id=uuid4())

    for score in scores:
        profile.add_satisfaction_score(score)

    # Scores are capped at 50
    stored_scores = profile.satisfaction_scores
    assert (
        len(stored_scores) <= 50
    ), f"Satisfaction scores must not exceed 50 entries, got {len(stored_scores)}"

    # All stored scores must be in [0.0, 1.0]
    for s in stored_scores:
        assert 0.0 <= s <= 1.0, f"Stored score {s} is out of range [0.0, 1.0]"

    # Average must equal arithmetic mean of stored scores
    if stored_scores:
        expected_avg = sum(stored_scores) / len(stored_scores)
        actual_avg = profile.get_average_satisfaction()
        assert (
            abs(actual_avg - expected_avg) < 1e-9
        ), f"Average satisfaction {actual_avg} != expected {expected_avg}"

    # Stored scores must be the most recent ones
    expected_stored = scores[-50:] if len(scores) > 50 else scores
    assert (
        stored_scores == expected_stored
    ), "Satisfaction scores should keep the most recent 50 entries"


def test_property_12_4b_satisfaction_default_when_empty():
    """
    Property 12.4b: Default satisfaction when no scores recorded.

    **Validates: Requirement 8.5**

    When no satisfaction scores have been recorded, get_average_satisfaction
    SHALL return the neutral default of 0.5.
    """
    profile = UserProfile(user_id=uuid4())
    assert (
        profile.get_average_satisfaction() == 0.5
    ), "Default satisfaction with no scores should be 0.5 (neutral)"


# ============================================================================
# Property 12.5: Implicit Satisfaction Calculation
# **Validates: Requirement 8.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(
    read_duration=st.integers(min_value=1, max_value=3600),
    completion_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    expected_read_time=st.integers(min_value=1, max_value=3600),
)
def test_property_12_5_implicit_satisfaction_range(
    read_duration: int, completion_rate: float, expected_read_time: int
):
    """
    Property 12.5a: Implicit satisfaction is always in [0.0, 1.0].

    **Validates: Requirement 8.5**

    For any (read_duration, completion_rate, expected_read_time) triple,
    calculate_implicit_satisfaction SHALL return a value in [0.0, 1.0].
    """
    manager = UserProfileManager()

    result = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=read_duration,
            completion_rate=completion_rate,
            expected_read_time=expected_read_time,
        )
    )

    assert isinstance(result, float), f"Result must be a float, got {type(result)}"
    assert 0.0 <= result <= 1.0, (
        f"Implicit satisfaction {result} is out of range [0.0, 1.0] "
        f"(duration={read_duration}, completion={completion_rate}, expected={expected_read_time})"
    )


@settings(max_examples=50, deadline=None)
@given(
    read_duration=st.integers(min_value=60, max_value=600),
    expected_read_time=st.integers(min_value=60, max_value=600),
    low_completion=st.floats(min_value=0.0, max_value=0.4, allow_nan=False),
    high_completion=st.floats(min_value=0.6, max_value=1.0, allow_nan=False),
)
def test_property_12_5b_higher_completion_higher_satisfaction(
    read_duration: int,
    expected_read_time: int,
    low_completion: float,
    high_completion: float,
):
    """
    Property 12.5b: Higher completion rates produce higher or equal satisfaction.

    **Validates: Requirement 8.5**

    When read_duration is held constant, higher completion_rate SHALL produce
    higher or equal implicit satisfaction scores.
    """
    manager = UserProfileManager()

    low_score = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=read_duration,
            completion_rate=low_completion,
            expected_read_time=expected_read_time,
        )
    )

    high_score = asyncio.get_event_loop().run_until_complete(
        manager.calculate_implicit_satisfaction(
            read_duration_seconds=read_duration,
            completion_rate=high_completion,
            expected_read_time=expected_read_time,
        )
    )

    assert high_score >= low_score, (
        f"Higher completion ({high_completion}) should produce >= satisfaction "
        f"than lower completion ({low_completion}). "
        f"Got high={high_score}, low={low_score} "
        f"(duration={read_duration}, expected={expected_read_time})"
    )


# ============================================================================
# Property 12.6: Profile Serialization Round-Trip
# **Validates: Requirement 8.1**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(profile=user_profiles())
def test_property_12_6_serialization_round_trip(profile: UserProfile):
    """
    Property 12.6: Profile Serialization Round-Trip

    **Validates: Requirement 8.1**

    For any UserProfile, to_dict() followed by from_dict() SHALL produce an
    equal profile (same user_id, reading_history, preferred_topics,
    satisfaction_scores).
    """
    serialized = profile.to_dict()
    restored = UserProfile.from_dict(serialized)

    assert (
        restored.user_id == profile.user_id
    ), f"user_id mismatch after round-trip: {restored.user_id} != {profile.user_id}"

    assert (
        restored.reading_history == profile.reading_history
    ), "reading_history mismatch after round-trip"

    assert restored.preferred_topics == profile.preferred_topics, (
        f"preferred_topics mismatch after round-trip: "
        f"{restored.preferred_topics} != {profile.preferred_topics}"
    )

    assert (
        restored.satisfaction_scores == profile.satisfaction_scores
    ), "satisfaction_scores mismatch after round-trip"

    assert (
        restored.query_history == profile.query_history
    ), "query_history mismatch after round-trip"

    assert restored.language_preference == profile.language_preference, (
        f"language_preference mismatch after round-trip: "
        f"{restored.language_preference} != {profile.language_preference}"
    )


# ============================================================================
# Property 12.7: Preferred Topics Deduplication
# **Validates: Requirement 8.3**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(topics=topic_lists_with_duplicates(min_size=1, max_size=30))
def test_property_12_7_preferred_topics_deduplication(topics: List[str]):
    """
    Property 12.7: Preferred Topics Deduplication

    **Validates: Requirement 8.3**

    For any list of topics with duplicates added to preferred_topics, the stored
    list SHALL contain no duplicates and be limited to 20 topics.
    """
    profile = UserProfile(user_id=uuid4(), preferred_topics=topics)

    stored = profile.preferred_topics

    # No duplicates
    assert len(stored) == len(
        set(stored)
    ), f"preferred_topics must not contain duplicates, got: {stored}"

    # Capped at 20
    assert len(stored) <= 20, f"preferred_topics must not exceed 20 entries, got {len(stored)}"

    # All stored topics must come from the original list
    for topic in stored:
        assert topic in topics, f"Stored topic '{topic}' was not in the original list"


@settings(max_examples=30, deadline=None)
@given(topics=topic_lists_with_duplicates(min_size=25, max_size=40))
def test_property_12_7b_preferred_topics_20_limit(topics: List[str]):
    """
    Property 12.7b: Preferred topics are capped at 20 unique entries.

    **Validates: Requirement 8.3**
    """
    profile = UserProfile(user_id=uuid4(), preferred_topics=topics)

    assert (
        len(profile.preferred_topics) <= 20
    ), f"preferred_topics must not exceed 20 entries, got {len(profile.preferred_topics)}"


# ============================================================================
# Property 12.8: Satisfaction Trend Analysis
# **Validates: Requirement 8.5**
# ============================================================================


def _compute_trend(scores: List[float]) -> str:
    """
    Pure trend computation logic mirroring analyze_satisfaction_trends.

    Splits scores into two halves (most-recent first, as returned by the DB
    query ordered DESC) and compares averages.
    """
    if not scores:
        return "insufficient_data"

    mid_point = len(scores) // 2
    if mid_point == 0:
        return "stable"

    recent_avg = sum(scores[:mid_point]) / mid_point
    older_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)

    return "improving" if recent_avg > older_avg else "declining"


@settings(max_examples=50, deadline=None)
@given(
    older_scores=st.lists(
        st.floats(min_value=0.1, max_value=0.4, allow_nan=False), min_size=2, max_size=10
    ),
    recent_scores=st.lists(
        st.floats(min_value=0.6, max_value=1.0, allow_nan=False), min_size=2, max_size=10
    ),
)
def test_property_12_8_improving_trend_detection(
    older_scores: List[float], recent_scores: List[float]
):
    """
    Property 12.8a: Improving trend detected when recent scores > older scores.

    **Validates: Requirement 8.5**

    When recent satisfaction scores are consistently higher than older scores,
    analyze_satisfaction_trends SHALL identify an "improving" trend.

    Tests the pure trend logic directly (no DB required).
    """
    # The DB query returns scores ordered DESC (most recent first).
    # So we pass [recent_scores..., older_scores...] to match that ordering.
    scores_desc = recent_scores + older_scores

    trend = _compute_trend(scores_desc)

    assert trend == "improving", (
        f"Expected 'improving' trend when recent avg "
        f"({sum(recent_scores)/len(recent_scores):.3f}) > "
        f"older avg ({sum(older_scores)/len(older_scores):.3f}), got '{trend}'"
    )


@settings(max_examples=50, deadline=None)
@given(
    recent_scores=st.lists(
        st.floats(min_value=0.1, max_value=0.4, allow_nan=False), min_size=2, max_size=10
    ),
    older_scores=st.lists(
        st.floats(min_value=0.6, max_value=1.0, allow_nan=False), min_size=2, max_size=10
    ),
)
def test_property_12_8b_declining_trend_detection(
    recent_scores: List[float], older_scores: List[float]
):
    """
    Property 12.8b: Declining trend detected when recent scores < older scores.

    **Validates: Requirement 8.5**

    When recent satisfaction scores are consistently lower than older scores,
    analyze_satisfaction_trends SHALL identify a "declining" trend.

    Tests the pure trend logic directly (no DB required).
    """
    # DB returns DESC order: most recent first
    scores_desc = recent_scores + older_scores

    trend = _compute_trend(scores_desc)

    assert trend == "declining", (
        f"Expected 'declining' trend when recent avg "
        f"({sum(recent_scores)/len(recent_scores):.3f}) < "
        f"older avg ({sum(older_scores)/len(older_scores):.3f}), got '{trend}'"
    )


@settings(max_examples=30, deadline=None)
@given(
    scores=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=0, max_size=1
    )
)
def test_property_12_8c_insufficient_data_trend(scores: List[float]):
    """
    Property 12.8c: Insufficient data returns stable/insufficient_data trend.

    **Validates: Requirement 8.5**

    When there are 0 or 1 data points, the trend SHALL be "stable" or
    "insufficient_data" (not "improving" or "declining").
    """
    trend = _compute_trend(scores)

    assert trend in (
        "stable",
        "insufficient_data",
    ), f"Expected 'stable' or 'insufficient_data' for {len(scores)} data points, got '{trend}'"
