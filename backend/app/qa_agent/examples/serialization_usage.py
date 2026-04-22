"""
Example usage of model serialization/deserialization methods.

This demonstrates how to use the JSON serialization and deserialization
methods for UserProfile, Article, and ArticleSummary models.

Requirements: 8.1, 8.2, 3.2
"""

from datetime import datetime
from uuid import uuid4

from app.qa_agent.article_models import Article, ArticleMetadata
from app.qa_agent.models import ArticleSummary, QueryLanguage, UserProfile


def example_user_profile_serialization():
    """Example: UserProfile serialization and deserialization."""
    print("=" * 60)
    print("UserProfile Serialization Example")
    print("=" * 60)

    # Create a UserProfile instance
    user_id = uuid4()
    profile = UserProfile(
        user_id=user_id,
        reading_history=[uuid4(), uuid4()],
        preferred_topics=["AI", "Machine Learning", "Python"],
        language_preference=QueryLanguage.ENGLISH,
        interaction_patterns={"search_frequency": "high", "avg_session_time": 300},
        query_history=["What is AI?", "Machine learning basics"],
        satisfaction_scores=[0.8, 0.9, 0.85],
    )

    print("\nOriginal UserProfile:")
    print(f"  User ID: {profile.user_id}")
    print(f"  Preferred Topics: {profile.preferred_topics}")
    print(f"  Language: {profile.language_preference}")
    print(f"  Reading History: {len(profile.reading_history)} articles")

    # Serialize to JSON
    json_str = profile.to_json()
    print("\nSerialized to JSON (first 200 chars):")
    print(f"  {json_str[:200]}...")

    # Deserialize from JSON
    restored_profile = UserProfile.from_json(json_str)
    print("\nRestored UserProfile:")
    print(f"  User ID: {restored_profile.user_id}")
    print(f"  Preferred Topics: {restored_profile.preferred_topics}")
    print(f"  Match: {restored_profile.user_id == profile.user_id}")

    # Also demonstrate dict serialization
    profile_dict = profile.to_dict()
    print("\nAs Dictionary (keys):")
    print(f"  {list(profile_dict.keys())}")

    print("\n✓ UserProfile serialization complete!\n")


def example_article_summary_serialization():
    """Example: ArticleSummary serialization and deserialization."""
    print("=" * 60)
    print("ArticleSummary Serialization Example")
    print("=" * 60)

    # Create an ArticleSummary instance
    article_id = uuid4()
    summary = ArticleSummary(
        article_id=article_id,
        title="Introduction to Machine Learning",
        summary="This article covers the basics of machine learning. It explains key concepts and algorithms. Perfect for beginners.",
        url="https://example.com/ml-intro",
        relevance_score=0.92,
        reading_time=8,
        key_insights=[
            "Machine learning enables computers to learn from data",
            "Supervised and unsupervised learning are two main types",
            "Neural networks are inspired by biological neurons",
        ],
        published_at=datetime.utcnow(),
        category="Technology",
    )

    print("\nOriginal ArticleSummary:")
    print(f"  Title: {summary.title}")
    print(f"  Relevance Score: {summary.relevance_score}")
    print(f"  Reading Time: {summary.reading_time} minutes")
    print(f"  Key Insights: {len(summary.key_insights)} insights")

    # Serialize to JSON
    json_str = summary.to_json()
    print("\nSerialized to JSON (first 200 chars):")
    print(f"  {json_str[:200]}...")

    # Deserialize from JSON
    restored_summary = ArticleSummary.from_json(json_str)
    print("\nRestored ArticleSummary:")
    print(f"  Title: {restored_summary.title}")
    print(f"  Relevance Score: {restored_summary.relevance_score}")
    print(f"  Match: {restored_summary.article_id == summary.article_id}")

    print("\n✓ ArticleSummary serialization complete!\n")


def example_article_serialization():
    """Example: Article serialization and deserialization."""
    print("=" * 60)
    print("Article Serialization Example")
    print("=" * 60)

    # Create an Article instance with metadata
    article_id = uuid4()
    feed_id = uuid4()

    article = Article(
        id=article_id,
        title="Deep Learning Fundamentals",
        content="Deep learning is a subset of machine learning that uses neural networks with multiple layers. These networks can learn hierarchical representations of data...",
        url="https://example.com/deep-learning",
        feed_id=feed_id,
        feed_name="AI Research Blog",
        category="Artificial Intelligence",
        published_at=datetime.utcnow(),
        metadata=ArticleMetadata(
            author="Dr. Jane Smith",
            source="AI Research Institute",
            tags=["deep-learning", "neural-networks", "ai"],
            reading_difficulty="intermediate",
            technical_depth=4,
            word_count=2500,
            language="en",
            content_type="tutorial",
            code_snippets=True,
        ),
    )

    print("\nOriginal Article:")
    print(f"  Title: {article.title}")
    print(f"  Category: {article.category}")
    print(f"  Author: {article.metadata.author}")
    print(f"  Tags: {article.metadata.tags}")
    print(f"  Technical Depth: {article.metadata.technical_depth}/5")

    # Serialize to JSON
    json_str = article.to_json()
    print("\nSerialized to JSON (first 200 chars):")
    print(f"  {json_str[:200]}...")

    # Deserialize from JSON
    restored_article = Article.from_json(json_str)
    print("\nRestored Article:")
    print(f"  Title: {restored_article.title}")
    print(f"  Category: {restored_article.category}")
    print(f"  Author: {restored_article.metadata.author}")
    print(f"  Match: {restored_article.id == article.id}")

    # Demonstrate dict serialization
    article_dict = article.to_dict()
    print("\nAs Dictionary (top-level keys):")
    print(f"  {list(article_dict.keys())[:10]}...")

    print("\n✓ Article serialization complete!\n")


def example_storage_workflow():
    """Example: Complete workflow for storing and retrieving models."""
    print("=" * 60)
    print("Storage Workflow Example")
    print("=" * 60)

    # Simulate storing a user profile to a file
    user_id = uuid4()
    profile = UserProfile(
        user_id=user_id,
        preferred_topics=["Python", "Data Science"],
        language_preference=QueryLanguage.CHINESE,
    )

    print("\n1. Creating UserProfile...")
    print(f"   User ID: {profile.user_id}")

    # Serialize to JSON string (ready for storage)
    json_data = profile.to_json()
    print(f"\n2. Serialized to JSON ({len(json_data)} bytes)")

    # Simulate storage (in real app, this would be written to file/database)
    print("\n3. [Simulated] Writing to storage...")
    stored_data = json_data  # In real app: write to file or database

    # Simulate retrieval
    print("\n4. [Simulated] Reading from storage...")
    retrieved_data = stored_data  # In real app: read from file or database

    # Deserialize from JSON
    restored_profile = UserProfile.from_json(retrieved_data)
    print("\n5. Deserialized UserProfile:")
    print(f"   User ID: {restored_profile.user_id}")
    print(f"   Preferred Topics: {restored_profile.preferred_topics}")

    # Verify data integrity
    print("\n6. Data Integrity Check:")
    print(f"   User ID matches: {restored_profile.user_id == profile.user_id}")
    print(f"   Topics match: {restored_profile.preferred_topics == profile.preferred_topics}")

    print("\n✓ Storage workflow complete!\n")


def example_unicode_support():
    """Example: Unicode (Chinese) content serialization."""
    print("=" * 60)
    print("Unicode Support Example (Chinese Content)")
    print("=" * 60)

    # Create profile with Chinese content
    user_id = uuid4()
    profile = UserProfile(
        user_id=user_id,
        preferred_topics=["人工智能", "機器學習", "深度學習"],
        query_history=["什麼是人工智能？", "機器學習的基礎知識", "深度學習應用"],
        language_preference=QueryLanguage.CHINESE,
    )

    print("\nOriginal UserProfile (Chinese):")
    print(f"  Preferred Topics: {profile.preferred_topics}")
    print(f"  Query History: {profile.query_history}")

    # Serialize (ensure_ascii=False preserves Unicode)
    json_str = profile.to_json()
    print("\nSerialized JSON (contains actual Chinese characters):")
    print(f"  {json_str[:300]}...")

    # Verify Chinese characters are preserved
    print("\nUnicode Preservation Check:")
    print(f"  Contains '人工智能': {'人工智能' in json_str}")
    print(f"  Contains '機器學習': {'機器學習' in json_str}")

    # Deserialize and verify
    restored_profile = UserProfile.from_json(json_str)
    print("\nRestored UserProfile:")
    print(f"  Preferred Topics: {restored_profile.preferred_topics}")
    print(f"  Match: {restored_profile.preferred_topics == profile.preferred_topics}")

    print("\n✓ Unicode support verified!\n")


if __name__ == "__main__":
    """Run all examples."""
    print("\n" + "=" * 60)
    print("QA Agent Model Serialization Examples")
    print("=" * 60 + "\n")

    # Run all examples
    example_user_profile_serialization()
    example_article_summary_serialization()
    example_article_serialization()
    example_storage_workflow()
    example_unicode_support()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60 + "\n")
