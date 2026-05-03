"""
Example Usage for Task 5.2 Enhancements

Demonstrates the new search expansion, caching, and personalization features
added to the RetrievalEngine in Task 5.2.

Requirements: 2.5, 6.1, 8.4
"""

import asyncio
import time
from datetime import datetime, timedelta
from uuid import uuid4

from .models import UserProfile
from .retrieval_engine import RetrievalEngine


async def demonstrate_caching():
    """Demonstrate search result caching for performance optimization."""
    print("=== Caching Demonstration ===")

    engine = RetrievalEngine()
    query_vector = [0.5] * 1536  # Mock embedding vector
    user_id = str(uuid4())

    # First search - will hit the vector store
    print("First search (cache miss)...")
    start_time = time.time()
    results1 = await engine.semantic_search(
        query_vector=query_vector, user_id=user_id, limit=10, use_cache=True
    )
    first_search_time = time.time() - start_time
    print(f"First search took {first_search_time:.3f}s")

    # Second search - should use cache
    print("Second search (cache hit)...")
    start_time = time.time()
    results2 = await engine.semantic_search(
        query_vector=query_vector, user_id=user_id, limit=10, use_cache=True
    )
    second_search_time = time.time() - start_time
    print(f"Second search took {second_search_time:.3f}s")

    # Display cache statistics
    cache_stats = engine.get_cache_stats()
    print(f"Cache stats: {cache_stats}")

    print(
        f"Cache performance improvement: {first_search_time / max(second_search_time, 0.001):.1f}x faster\n"
    )


async def demonstrate_search_expansion():
    """Demonstrate intelligent search expansion when insufficient results found."""
    print("=== Search Expansion Demonstration ===")

    engine = RetrievalEngine()
    user_id = str(uuid4())
    query_vector = [0.3] * 1536  # Lower similarity vector

    # Simulate insufficient initial results
    print("Simulating search with insufficient results...")

    # This would normally return few results due to high threshold
    original_results = await engine.semantic_search(
        query_vector=query_vector,
        user_id=user_id,
        limit=10,
        threshold=0.8,  # High threshold = fewer results
        use_cache=False,
    )

    print(f"Original search found {len(original_results)} results")

    # Use search expansion to find more results
    print("Applying search expansion...")
    expanded_results = await engine.expand_search(
        original_results=original_results,
        user_id=user_id,
        query_vector=query_vector,
        query_text="python programming tutorial",
        min_results=5,
        expanded_limit=20,
    )

    print(f"After expansion: {len(expanded_results)} results")

    # Generate topic suggestions if still insufficient
    if len(expanded_results) < 5:
        suggestions = await engine.suggest_related_topics(expanded_results)
        print(f"Suggested topics: {suggestions}")

    print()


async def demonstrate_enhanced_personalization():
    """Demonstrate enhanced personalization with multiple factors."""
    print("=== Enhanced Personalization Demonstration ===")

    engine = RetrievalEngine()

    # Create a user profile with preferences and history
    user_profile = UserProfile(
        user_id=uuid4(),
        preferred_topics=["programming", "machine-learning"],
        reading_history=[uuid4() for _ in range(10)],  # 10 read articles
        query_history=[
            "python tutorial",
            "machine learning basics",
            "neural networks",
            "data science",
        ],
        satisfaction_scores=[0.8, 0.9, 0.7, 0.85, 0.9],  # High satisfaction user
    )

    print(
        f"User profile: {len(user_profile.preferred_topics)} topics, "
        f"{len(user_profile.reading_history)} read articles, "
        f"avg satisfaction: {user_profile.get_average_satisfaction():.2f}"
    )

    # Create mock article matches with different characteristics
    from .models import ArticleMatch

    recent_date = datetime.utcnow() - timedelta(days=1)
    old_date = datetime.utcnow() - timedelta(days=30)

    mock_matches = [
        ArticleMatch(
            article_id=uuid4(),
            title="Advanced Python Techniques",
            content_preview="Deep dive into Python programming patterns",
            similarity_score=0.7,
            keyword_score=0.6,
            url="https://example.com/python",
            feed_name="Tech Blog",
            category="programming",
            published_at=recent_date,  # Recent article
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Machine Learning Fundamentals",
            content_preview="Introduction to ML algorithms and concepts",
            similarity_score=0.7,
            keyword_score=0.5,
            url="https://example.com/ml",
            feed_name="AI Journal",
            category="machine-learning",
            published_at=old_date,  # Older article
        ),
        ArticleMatch(
            article_id=uuid4(),
            title="Web Design Trends",
            content_preview="Latest trends in web design and UX",
            similarity_score=0.7,
            keyword_score=0.4,
            url="https://example.com/design",
            feed_name="Design Weekly",
            category="design",  # Not in preferred topics
            published_at=recent_date,
        ),
    ]

    print(f"Original matches: {len(mock_matches)} articles")
    for i, match in enumerate(mock_matches):
        print(
            f"  {i+1}. {match.title} (category: {match.category}, "
            f"similarity: {match.similarity_score:.2f})"
        )

    # Apply personalization
    print("\nApplying personalization...")
    personalized_results = await engine.rank_by_user_preferences(
        matches=mock_matches, user_profile=user_profile, personalization_strength=1.0
    )

    print("Personalized ranking:")
    for i, result in enumerate(personalized_results):
        boost = result.metadata.get("personalization_boost", 0)
        topic_boost = result.metadata.get("topic_boost", 0)
        recency_days = result.metadata.get("recency_days")

        print(f"  {i+1}. {result.title}")
        print(
            f"     Score: {result.combined_score:.3f} "
            f"(boost: {boost:+.3f}, topic: {topic_boost:.3f}, "
            f"recency: {recency_days} days)"
        )

    print()


async def demonstrate_intelligent_search():
    """Demonstrate the integrated intelligent search with all features."""
    print("=== Intelligent Search Integration ===")

    engine = RetrievalEngine()
    user_id = str(uuid4())
    query_vector = [0.4] * 1536

    # Create user profile
    user_profile = UserProfile(
        user_id=uuid4(),
        preferred_topics=["programming", "ai"],
        reading_history=[uuid4() for _ in range(5)],
        query_history=["python", "machine learning"],
        satisfaction_scores=[0.8, 0.9, 0.7],
    )

    print("Running intelligent search with all optimizations...")

    # Use the integrated intelligent search
    search_result = await engine.intelligent_search(
        query="python machine learning tutorial",
        query_vector=query_vector,
        user_id=user_id,
        user_profile=user_profile,
        limit=10,
        min_results=3,
        use_expansion=True,
        use_personalization=True,
        use_cache=True,
    )

    print(f"Search completed in {search_result['search_time']:.3f}s")
    print(f"Found {len(search_result['results'])} results")
    print(f"Search expanded: {search_result['expanded']}")
    print(f"Personalized: {search_result['personalized']}")
    print(f"Cache hit: {search_result['cache_hit']}")
    print(f"Total found before limit: {search_result['total_found']}")

    if search_result["suggested_topics"]:
        print(f"Suggested topics: {search_result['suggested_topics']}")

    print()


async def demonstrate_performance_optimization():
    """Demonstrate performance optimizations and monitoring."""
    print("=== Performance Optimization Demonstration ===")

    engine = RetrievalEngine()
    user_id = str(uuid4())

    # Test multiple searches to show caching benefits
    query_vectors = [[0.1 + i * 0.1] * 1536 for i in range(5)]

    print("Running multiple searches to demonstrate caching...")

    total_time_without_cache = 0
    total_time_with_cache = 0

    for i, vector in enumerate(query_vectors):
        # Search without cache
        start_time = time.time()
        await engine.semantic_search(vector, user_id, use_cache=False)
        no_cache_time = time.time() - start_time
        total_time_without_cache += no_cache_time

        # Search with cache (first time)
        start_time = time.time()
        await engine.semantic_search(vector, user_id, use_cache=True)
        first_cache_time = time.time() - start_time

        # Search with cache (second time - should be faster)
        start_time = time.time()
        await engine.semantic_search(vector, user_id, use_cache=True)
        second_cache_time = time.time() - start_time
        total_time_with_cache += second_cache_time

        print(
            f"Query {i+1}: No cache: {no_cache_time:.3f}s, "
            f"Cache miss: {first_cache_time:.3f}s, "
            f"Cache hit: {second_cache_time:.3f}s"
        )

    print(f"\nTotal time without cache: {total_time_without_cache:.3f}s")
    print(f"Total time with cache: {total_time_with_cache:.3f}s")
    print(
        f"Performance improvement: {total_time_without_cache / max(total_time_with_cache, 0.001):.1f}x"
    )

    # Show cache statistics
    cache_stats = engine.get_cache_stats()
    print(f"Final cache stats: {cache_stats}")


async def main():
    """Run all demonstrations."""
    print("Task 5.2 Enhancement Demonstrations")
    print("=" * 50)
    print()

    try:
        await demonstrate_caching()
        await demonstrate_search_expansion()
        await demonstrate_enhanced_personalization()
        await demonstrate_intelligent_search()
        await demonstrate_performance_optimization()

        print("All demonstrations completed successfully!")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        print("Note: These demonstrations require a working vector store connection.")
        print(
            "In a real environment, ensure the database and vector store are properly configured."
        )


if __name__ == "__main__":
    asyncio.run(main())
