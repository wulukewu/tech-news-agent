"""
Example usage of QA Agent data models.

This script demonstrates how to create and use the core data models
for the intelligent Q&A agent system.
"""

from datetime import datetime
from uuid import uuid4

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
    UserProfile,
)


def example_parsed_query():
    """Example of creating and using ParsedQuery."""
    print("=== ParsedQuery Example ===")

    # Create a parsed query
    query = ParsedQuery(
        original_query="What are the latest developments in artificial intelligence?",
        language=QueryLanguage.ENGLISH,
        intent=QueryIntent.SEARCH,
        keywords=["artificial intelligence", "developments", "latest", "AI"],
        filters={
            "time_range": {"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:59"},
            "categories": ["AI", "Technology"],
            "technical_depth": 3,
        },
        confidence=0.85,
    )

    print(f"Query: {query.original_query}")
    print(f"Language: {query.language}")
    print(f"Intent: {query.intent}")
    print(f"Keywords: {query.keywords}")
    print(f"Confidence: {query.confidence}")
    print(f"Is valid: {query.is_valid()}")
    print(f"Requires clarification: {query.requires_clarification()}")
    print()


def example_article_match():
    """Example of creating and using ArticleMatch."""
    print("=== ArticleMatch Example ===")

    # Create an article match
    article = ArticleMatch(
        article_id=uuid4(),
        title="Breakthrough in Large Language Models: GPT-4 and Beyond",
        content_preview="Recent advances in large language models have shown remarkable capabilities in natural language understanding and generation. This article explores the latest developments in GPT-4 and discusses future directions in AI research.",
        similarity_score=0.92,
        keyword_score=0.78,
        url="https://example.com/ai-breakthrough-2023",
        published_at=datetime(2023, 6, 15, 10, 30),
        feed_name="AI Research Today",
        category="Artificial Intelligence",
        metadata={
            "author": "Dr. Jane Smith",
            "reading_difficulty": "intermediate",
            "tags": ["GPT-4", "LLM", "NLP"],
        },
    )

    print(f"Title: {article.title}")
    print(f"Similarity Score: {article.similarity_score}")
    print(f"Keyword Score: {article.keyword_score}")
    print(f"Combined Score: {article.combined_score:.3f}")
    print(f"Is relevant: {article.is_relevant()}")
    print(f"Reading time estimate: {article.get_reading_time_estimate()} minutes")
    print()


def example_structured_response():
    """Example of creating and using StructuredResponse."""
    print("=== StructuredResponse Example ===")

    # Create article summaries
    articles = [
        ArticleSummary(
            article_id=uuid4(),
            title="GPT-4: Revolutionary Language Model",
            summary="GPT-4 represents a significant advancement in language model capabilities. It demonstrates improved reasoning and reduced hallucinations. The model shows promise for various applications including code generation and creative writing.",
            url="https://example.com/gpt4-review",
            relevance_score=0.95,
            reading_time=8,
            category="AI Research",
            key_insights=[
                "GPT-4 shows 40% improvement in factual accuracy",
                "Multimodal capabilities enable image understanding",
                "Better alignment with human preferences",
            ],
        ),
        ArticleSummary(
            article_id=uuid4(),
            title="The Future of AI: Trends and Predictions",
            summary="Industry experts predict significant changes in AI development over the next decade. Key trends include increased focus on AI safety and alignment. The integration of AI into everyday applications will accelerate.",
            url="https://example.com/ai-future-trends",
            relevance_score=0.87,
            reading_time=6,
            category="AI Trends",
            key_insights=[
                "AI safety becomes top priority",
                "Edge AI deployment increases",
                "Human-AI collaboration improves",
            ],
        ),
    ]

    # Create structured response
    response = StructuredResponse(
        query="What are the latest developments in artificial intelligence?",
        response_type=ResponseType.STRUCTURED,
        articles=articles,
        insights=[
            "AI development is accelerating with focus on safety and alignment",
            "Large language models are becoming more capable and reliable",
            "Multimodal AI systems are emerging as the next frontier",
        ],
        recommendations=[
            "Explore GPT-4's multimodal capabilities for your projects",
            "Stay updated on AI safety research and best practices",
            "Consider the ethical implications of AI deployment",
        ],
        conversation_id=uuid4(),
        response_time=2.3,
        confidence=0.91,
    )

    print(f"Query: {response.query}")
    print(f"Response Type: {response.response_type}")
    print(f"Number of articles: {response.get_article_count()}")
    print(f"Top article: {response.get_top_article().title}")
    print(f"Is successful: {response.is_successful()}")
    print(f"Response time: {response.response_time}s")
    print(f"Confidence: {response.confidence}")

    print("\nInsights:")
    for i, insight in enumerate(response.insights, 1):
        print(f"  {i}. {insight}")

    print("\nRecommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"  {i}. {rec}")
    print()


def example_conversation_context():
    """Example of creating and using ConversationContext."""
    print("=== ConversationContext Example ===")

    user_id = uuid4()

    # Create conversation context
    context = ConversationContext(user_id=user_id)
    context.current_topic = "artificial intelligence"

    print(f"Conversation ID: {context.conversation_id}")
    print(f"User ID: {context.user_id}")
    print(f"Status: {context.status}")
    print(f"Is active: {context.is_active()}")

    # Add conversation turns
    context.add_turn("What is artificial intelligence?")
    context.add_turn("How does machine learning work?")
    context.add_turn("What are neural networks?")

    print(f"\nConversation turns: {len(context.turns)}")
    print(f"Recent queries: {context.get_recent_queries(2)}")
    print(f"Summary: {context.get_conversation_summary()}")

    # Test context reset logic
    related_query = "Tell me about deep learning"
    unrelated_query = "How to cook pasta?"

    print(f"\nShould reset for '{related_query}': {context.should_reset_context(related_query)}")
    print(f"Should reset for '{unrelated_query}': {context.should_reset_context(unrelated_query)}")
    print()


def example_user_profile():
    """Example of creating and using UserProfile."""
    print("=== UserProfile Example ===")

    user_id = uuid4()

    # Create user profile
    profile = UserProfile(
        user_id=user_id,
        preferred_topics=["AI", "Machine Learning", "Data Science", "Python"],
        language_preference=QueryLanguage.ENGLISH,
    )

    # Simulate user interactions
    article_ids = [uuid4() for _ in range(5)]
    for article_id in article_ids:
        profile.add_read_article(article_id)

    # Add query history
    queries = [
        "What is machine learning?",
        "How to implement neural networks?",
        "Best practices for data science",
        "Python libraries for AI",
    ]
    for query in queries:
        profile.add_query(query)

    # Add satisfaction scores
    satisfaction_scores = [0.8, 0.9, 0.7, 0.85, 0.75]
    for score in satisfaction_scores:
        profile.add_satisfaction_score(score)

    print(f"User ID: {profile.user_id}")
    print(f"Language preference: {profile.language_preference}")
    print(f"Preferred topics: {profile.get_top_topics(3)}")
    print(f"Reading history size: {len(profile.reading_history)}")
    print(f"Query history size: {len(profile.query_history)}")
    print(f"Average satisfaction: {profile.get_average_satisfaction():.2f}")
    print(f"Has read article: {profile.has_read_article(article_ids[0])}")
    print()


def main():
    """Run all examples."""
    print("QA Agent Data Models - Example Usage\n")
    print("=" * 50)

    example_parsed_query()
    example_article_match()
    example_structured_response()
    example_conversation_context()
    example_user_profile()

    print("=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
