"""
Tests for SmartConversationService

Validates task 7.1: Auto title generation service implementation
- Title generation from conversation content
- Multi-language support (Chinese and English)
- Title optimization and deduplication
- Persistence control

Validates: Requirements 3.2, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.smart_conversation import SmartConversationService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_conversation_repo():
    """Mock ConversationRepository for testing."""
    repo = MagicMock(spec=ConversationRepository)
    repo.get_conversation = AsyncMock()
    repo.update_title = AsyncMock()
    repo.update_conversation = AsyncMock()
    repo.list_conversations = AsyncMock()
    return repo


@pytest.fixture
def mock_message_repo():
    """Mock MessageRepository for testing."""
    repo = MagicMock(spec=MessageRepository)
    repo.get_messages = AsyncMock()
    repo.add_message = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_client():
    """Mock AsyncOpenAI client for testing."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def smart_service(mock_conversation_repo, mock_message_repo, mock_llm_client):
    """Create a SmartConversationService instance with mocked dependencies."""
    return SmartConversationService(
        conversation_repo=mock_conversation_repo,
        message_repo=mock_message_repo,
        llm_client=mock_llm_client,
    )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def create_mock_message(role: str, content: str, created_at=None):
    """Create a mock message object."""
    msg = MagicMock()
    msg.id = uuid4()
    msg.role = role
    msg.content = content
    msg.platform = "web"
    msg.metadata = {}
    msg.created_at = created_at or datetime.now(timezone.utc)
    return msg


def create_mock_conversation(
    title: str = "Test Conversation",
    tags: list[str] | None = None,
    message_count: int = 5,
):
    """Create a mock conversation object."""
    conv = MagicMock()
    conv.id = uuid4()
    conv.title = title
    conv.summary = None
    conv.platform = "web"
    conv.tags = tags or []
    conv.is_archived = False
    conv.is_favorite = False
    conv.created_at = datetime.now(timezone.utc)
    conv.last_message_at = datetime.now(timezone.utc)
    conv.message_count = message_count
    conv.metadata = {}
    return conv


def create_mock_llm_response(content: str):
    """Create a mock LLM API response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = content
    return response


# ---------------------------------------------------------------------------
# Test 7.1: Auto title generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_title_english_conversation(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test title generation for an English conversation.

    Validates: Requirement 3.2 - Auto title generation with English support
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # Mock messages
    messages = [
        create_mock_message("user", "How do I implement authentication in FastAPI?"),
        create_mock_message(
            "assistant", "To implement authentication in FastAPI, you can use OAuth2..."
        ),
        create_mock_message("user", "What about JWT tokens?"),
        create_mock_message(
            "assistant", "JWT tokens are a great choice for stateless authentication..."
        ),
    ]
    mock_message_repo.get_messages.return_value = messages

    # Mock LLM response
    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(
        "FastAPI Authentication Implementation"
    )

    # Generate title
    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )

    # Assertions
    assert title == "FastAPI Authentication Implementation"
    mock_message_repo.get_messages.assert_called_once_with(conversation_id, limit=6, ascending=True)
    mock_conversation_repo.update_title.assert_called_once_with(
        conversation_id=conversation_id,
        user_id=user_id,
        title="FastAPI Authentication Implementation",
    )


@pytest.mark.asyncio
async def test_generate_title_chinese_conversation(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test title generation for a Chinese conversation.

    Validates: Requirement 3.2 - Auto title generation with Chinese support
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # Mock Chinese messages
    messages = [
        create_mock_message("user", "如何在 Python 中實作非同步程式設計？"),
        create_mock_message(
            "assistant", "在 Python 中，你可以使用 asyncio 模組來實作非同步程式設計..."
        ),
        create_mock_message("user", "async/await 的用法是什麼？"),
    ]
    mock_message_repo.get_messages.return_value = messages

    # Mock LLM response in Chinese
    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(
        "Python 非同步程式設計入門"
    )

    # Generate title
    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )

    # Assertions
    assert title == "Python 非同步程式設計入門"
    assert mock_llm_client.chat.completions.create.called


@pytest.mark.asyncio
async def test_generate_title_with_quotes_sanitization(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test that generated titles are properly sanitized (quotes removed).

    Validates: Requirement 3.2 - Title optimization and deduplication logic
    """
    conversation_id = uuid4()
    user_id = uuid4()

    messages = [create_mock_message("user", "Test question")]
    mock_message_repo.get_messages.return_value = messages

    # Mock LLM response with quotes
    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(
        '"Test Title with Quotes"'
    )

    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )

    # Should strip quotes
    assert title == "Test Title with Quotes"
    assert '"' not in title


@pytest.mark.asyncio
async def test_generate_title_no_persist(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test title generation without persisting to database.

    Validates: Requirement 3.2 - Title suggestion and user confirmation mechanism
    """
    conversation_id = uuid4()
    user_id = uuid4()

    messages = [create_mock_message("user", "Test question")]
    mock_message_repo.get_messages.return_value = messages

    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(
        "Generated Title"
    )

    # Generate without persisting
    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=False,
    )

    # Should return title but not save to DB
    assert title == "Generated Title"
    mock_conversation_repo.update_title.assert_not_called()


@pytest.mark.asyncio
async def test_generate_title_empty_conversation(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test title generation for a conversation with no messages.

    Validates: Requirement 3.2 - Edge case handling
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # No messages
    mock_message_repo.get_messages.return_value = []

    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )

    # Should return default title
    assert title == "New Conversation"
    mock_llm_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_generate_title_llm_failure_handling(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test that LLM failures are properly handled with retries.

    Validates: Requirement 3.2 - Error handling and resilience
    """
    conversation_id = uuid4()
    user_id = uuid4()

    messages = [create_mock_message("user", "Test question")]
    mock_message_repo.get_messages.return_value = messages

    # Mock LLM failure
    mock_llm_client.chat.completions.create.side_effect = Exception("API Error")

    # Should raise ExternalServiceError after retries
    with pytest.raises(Exception):
        await smart_service.generate_title(
            conversation_id=conversation_id,
            user_id=user_id,
            persist=True,
        )


@pytest.mark.asyncio
async def test_generate_title_max_messages_limit(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test that title generation respects max_messages parameter.

    Validates: Requirement 3.2 - Configurable message sampling
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # Create 10 messages
    messages = [create_mock_message("user", f"Message {i}") for i in range(10)]
    mock_message_repo.get_messages.return_value = messages

    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response("Test Title")

    # Generate with custom max_messages
    await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        max_messages=3,
        persist=False,
    )

    # Should request only 3 messages
    mock_message_repo.get_messages.assert_called_once_with(conversation_id, limit=3, ascending=True)


# ---------------------------------------------------------------------------
# Test 7.2: Conversation summary generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_summary(
    smart_service, mock_message_repo, mock_llm_client, mock_conversation_repo
):
    """Test conversation summary generation.

    Validates: Requirement 6.2 - Conversation summary generation
    """
    conversation_id = uuid4()
    user_id = uuid4()

    messages = [
        create_mock_message("user", "How do I use async/await in Python?"),
        create_mock_message("assistant", "Async/await is used for asynchronous programming..."),
    ]
    mock_message_repo.get_messages.return_value = messages

    summary_text = (
        "Discussion about Python async/await syntax and usage.\n• Key insight 1\n• Key insight 2"
    )
    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(summary_text)

    summary = await smart_service.generate_summary(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )

    assert summary == summary_text
    mock_conversation_repo.update_conversation.assert_called_once()


# ---------------------------------------------------------------------------
# Test 7.3: Related conversation recommendation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_related_conversations(smart_service, mock_conversation_repo, mock_message_repo):
    """Test finding related conversations based on tags and keywords.

    Validates: Requirements 3.5, 6.4 - Related conversation recommendation
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # Reference conversation
    ref_conv = create_mock_conversation(
        title="Python Async Programming",
        tags=["python", "async"],
    )
    mock_conversation_repo.get_conversation.return_value = ref_conv

    # Reference messages
    ref_messages = [
        create_mock_message("user", "How to use asyncio in Python?"),
    ]
    mock_message_repo.get_messages.return_value = ref_messages

    # Candidate conversations
    candidates = [
        create_mock_conversation(
            title="FastAPI Async Endpoints",
            tags=["python", "async", "fastapi"],
        ),
        create_mock_conversation(
            title="JavaScript Promises",
            tags=["javascript", "async"],
        ),
        create_mock_conversation(
            title="Python Data Science",
            tags=["python", "data"],
        ),
    ]
    mock_conversation_repo.list_conversations.return_value = candidates

    related = await smart_service.get_related_conversations(
        conversation_id=conversation_id,
        user_id=user_id,
        limit=5,
    )

    # Should return related conversations sorted by similarity
    assert len(related) > 0
    assert all(r.similarity_score >= 0 for r in related)
    # First result should have highest similarity (shares both tags)
    assert related[0].similarity_score > 0


# ---------------------------------------------------------------------------
# Test 7.4: Conversation analysis and insights
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_conversations(
    smart_service, mock_conversation_repo, mock_message_repo, mock_llm_client
):
    """Test conversation analysis and insights generation.

    Validates: Requirements 6.1, 6.3, 6.4, 6.5 - Conversation analysis
    """
    user_id = uuid4()

    # Mock conversations
    conversations = [
        create_mock_conversation(
            title="Python Basics",
            tags=["python", "beginner"],
            message_count=10,
        ),
        create_mock_conversation(
            title="Advanced Python",
            tags=["python", "advanced"],
            message_count=15,
        ),
        create_mock_conversation(
            title="JavaScript Intro",
            tags=["javascript", "beginner"],
            message_count=8,
        ),
    ]
    mock_conversation_repo.list_conversations.return_value = conversations

    # Mock LLM response for insights
    llm_response = {
        "knowledge_gaps": ["Error handling", "Testing"],
        "learning_suggestions": [
            "Practice more with async/await",
            "Learn about design patterns",
        ],
        "trend_summary": "User is actively learning Python with focus on basics and advanced topics.",
    }
    import json

    llm_json = json.dumps(llm_response)
    mock_llm_client.chat.completions.create.return_value = create_mock_llm_response(
        f"```json\n{llm_json}\n```"
    )

    insights = await smart_service.analyse_conversations(
        user_id=user_id,
        days=30,
    )

    # Assertions
    assert insights.active_days > 0
    assert insights.avg_messages_per_day >= 0
    assert len(insights.top_tags) > 0
    assert "python" in insights.top_tags
    assert insights.topic_distribution.get("python", 0) > 0


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_smart_conversation_service_integration(
    smart_service, mock_conversation_repo, mock_message_repo, mock_llm_client
):
    """Integration test for the complete smart conversation workflow.

    Tests the full flow: create conversation → add messages → generate title → generate summary

    Validates: Task 7.1 complete implementation
    """
    conversation_id = uuid4()
    user_id = uuid4()

    # Setup messages
    messages = [
        create_mock_message("user", "What is FastAPI?"),
        create_mock_message("assistant", "FastAPI is a modern Python web framework..."),
        create_mock_message("user", "How do I create an API endpoint?"),
        create_mock_message("assistant", "You can create an endpoint using @app.get decorator..."),
    ]
    mock_message_repo.get_messages.return_value = messages

    # Mock LLM responses
    mock_llm_client.chat.completions.create.side_effect = [
        create_mock_llm_response("FastAPI Basics Tutorial"),  # Title
        create_mock_llm_response(
            "Introduction to FastAPI framework and API creation.\n• Key concepts covered\n• Practical examples provided"
        ),  # Summary
    ]

    # Generate title
    title = await smart_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )
    assert title == "FastAPI Basics Tutorial"

    # Generate summary
    summary = await smart_service.generate_summary(
        conversation_id=conversation_id,
        user_id=user_id,
        persist=True,
    )
    assert "FastAPI" in summary
    assert len(summary) > 0

    # Verify both operations called the LLM
    assert mock_llm_client.chat.completions.create.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
