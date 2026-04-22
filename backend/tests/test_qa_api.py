"""
End-to-End Integration Tests for QA API Endpoints

Tests the complete QA API flow including:
- Single query endpoint (POST /api/qa/query)
- Create conversation (POST /api/qa/conversations)
- Continue conversation (POST /api/qa/conversations/{id}/continue)
- Get conversation history (GET /api/qa/conversations/{id})
- Delete conversation (DELETE /api/qa/conversations/{id})
- Authentication (unauthenticated requests return 401)
- Response time (responses complete within 3 seconds)

Requirements: 6.1, 6.2
"""

import time
from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.main import app
from app.qa_agent.models import (
    ArticleSummary,
    ConversationContext,
    ConversationTurn,
    ResponseType,
    StructuredResponse,
)

# ============================================================================
# Constants
# ============================================================================

TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_DISCORD_ID = "123456789"
TEST_CONVERSATION_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
RESPONSE_TIME_LIMIT = 3.0  # seconds — Requirement 6.2


# ============================================================================
# Helpers
# ============================================================================


def _make_article_summary(
    article_id: Optional[UUID] = None,
    title: str = "Test Article",
    category: str = "Technology",
) -> ArticleSummary:
    """Create a minimal valid ArticleSummary."""
    return ArticleSummary(
        article_id=article_id or uuid4(),
        title=title,
        summary="This is the first sentence of the summary. This is the second sentence.",
        url="https://example.com/article",
        relevance_score=0.85,
        reading_time=3,
        key_insights=["Key insight one"],
        published_at=datetime(2024, 1, 15, 10, 0, 0),
        category=category,
    )


def _make_structured_response(
    query: str = "test query",
    conversation_id: Optional[UUID] = None,
    articles: Optional[List[ArticleSummary]] = None,
) -> StructuredResponse:
    """Create a minimal valid StructuredResponse."""
    return StructuredResponse(
        query=query,
        articles=articles or [_make_article_summary()],
        insights=["Insight about the topic"],
        recommendations=["Read more about related topics"],
        conversation_id=conversation_id or TEST_CONVERSATION_ID,
        response_time=0.5,
        response_type=ResponseType.STRUCTURED,
        confidence=0.8,
    )


def _make_conversation_context(
    conversation_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    turns: Optional[List[ConversationTurn]] = None,
) -> ConversationContext:
    """Create a minimal valid ConversationContext."""
    return ConversationContext(
        conversation_id=conversation_id or TEST_CONVERSATION_ID,
        user_id=user_id or TEST_USER_ID,
        turns=turns or [],
        current_topic="AI and machine learning",
        created_at=datetime(2024, 1, 15, 10, 0, 0),
    )


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def override_auth():
    """
    Override get_current_user dependency for all tests in this module.
    Restores the original after each test.
    """
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": TEST_USER_ID,
        "discord_id": TEST_DISCORD_ID,
    }
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client():
    """Synchronous TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_qa_controller():
    """
    Patch QAAgentController at the API layer so no real DB/LLM calls are made.
    Returns the mock instance.
    """
    with patch("app.api.qa.QAAgentController") as MockClass:
        instance = MagicMock()
        MockClass.return_value = instance

        # process_query echoes back the actual query text so assertions on
        # response["query"] work correctly.
        async def _process_query(user_id, query, conversation_id=None, **kwargs):
            return _make_structured_response(query=query, conversation_id=TEST_CONVERSATION_ID)

        instance.process_query = AsyncMock(side_effect=_process_query)
        instance.continue_conversation = AsyncMock(
            return_value=_make_structured_response(conversation_id=TEST_CONVERSATION_ID)
        )
        instance.get_conversation_history = AsyncMock(return_value=_make_conversation_context())
        instance.delete_conversation = AsyncMock(return_value=True)

        yield instance


# ── Supabase-backed conversation helper mocks ─────────────────────────────────

_MOCK_CONVERSATION_ROW = {
    "id": str(TEST_CONVERSATION_ID),
    "user_id": str(TEST_USER_ID),
    "context": {
        "conversation_id": str(TEST_CONVERSATION_ID),
        "user_id": str(TEST_USER_ID),
        "turns": [],
        "current_topic": "AI and machine learning",
    },
    "created_at": "2024-01-15T10:00:00",
    "last_updated": "2024-01-15T10:00:00",
    "expires_at": "2099-01-01T00:00:00",  # Far future — never expires in tests
}


@pytest.fixture
def mock_conversation_manager():
    """
    Patch the Supabase-backed conversation helpers in app.api.qa.
    Replaces the old ConversationManager fixture.
    """
    with (
        patch(
            "app.api.qa._create_conversation_in_db",
            new=AsyncMock(return_value=str(TEST_CONVERSATION_ID)),
        ),
        patch(
            "app.api.qa._get_conversation_from_db",
            new=AsyncMock(return_value=_MOCK_CONVERSATION_ROW),
        ),
        patch(
            "app.api.qa._append_turn_to_db",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.qa._delete_conversation_from_db",
            new=AsyncMock(return_value=True),
        ),
    ):
        yield


# ============================================================================
# 1. Single Query Endpoint — POST /api/qa/query
# ============================================================================


class TestQueryEndpoint:
    """Tests for POST /api/qa/query."""

    def test_query_returns_200_with_structured_response(self, client, mock_qa_controller):
        """
        Complete flow: authenticated user submits a query → receives structured response.

        Validates: Requirements 6.1, 6.2
        """
        response = client.post(
            "/api/qa/query",
            json={"query": "What are the latest AI developments?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        result = data["data"]
        assert result["query"] == "What are the latest AI developments?"
        assert "articles" in result
        assert "insights" in result
        assert "recommendations" in result
        assert "conversation_id" in result
        assert "response_time" in result

    def test_query_response_contains_article_fields(self, client, mock_qa_controller):
        """Verify article objects in the response have all required fields."""
        response = client.post(
            "/api/qa/query",
            json={"query": "Tell me about machine learning"},
        )

        assert response.status_code == 200
        articles = response.json()["data"]["articles"]
        assert len(articles) > 0

        article = articles[0]
        for field in ("article_id", "title", "summary", "url", "relevance_score", "reading_time"):
            assert field in article, f"Missing field: {field}"

    def test_query_with_conversation_id_continues_conversation(self, client, mock_qa_controller):
        """Passing an existing conversation_id should reuse that conversation."""
        response = client.post(
            "/api/qa/query",
            json={
                "query": "Tell me more",
                "conversation_id": str(TEST_CONVERSATION_ID),
            },
        )

        assert response.status_code == 200
        mock_qa_controller.process_query.assert_called_once()
        call_kwargs = mock_qa_controller.process_query.call_args.kwargs
        assert call_kwargs.get("conversation_id") == str(TEST_CONVERSATION_ID)

    def test_query_empty_string_returns_422(self, client, mock_qa_controller):
        """An empty query string should fail Pydantic validation (min_length=1)."""
        response = client.post("/api/qa/query", json={"query": ""})
        assert response.status_code == 422

    def test_query_too_long_returns_422(self, client, mock_qa_controller):
        """A query exceeding 2000 characters should fail validation."""
        response = client.post("/api/qa/query", json={"query": "x" * 2001})
        assert response.status_code == 422

    def test_query_controller_error_returns_500(self, client, mock_qa_controller):
        """When the controller raises an unexpected exception, the API returns 500."""
        mock_qa_controller.process_query = AsyncMock(side_effect=RuntimeError("DB down"))

        response = client.post("/api/qa/query", json={"query": "test"})
        assert response.status_code == 500

    def test_query_controller_returns_none_returns_500(self, client, mock_qa_controller):
        """When the controller returns None, the API returns 500."""
        mock_qa_controller.process_query = AsyncMock(return_value=None)

        response = client.post("/api/qa/query", json={"query": "test"})
        assert response.status_code == 500


# ============================================================================
# 2. Create Conversation — POST /api/qa/conversations
# ============================================================================


class TestCreateConversationEndpoint:
    """Tests for POST /api/qa/conversations."""

    def test_create_conversation_returns_200_with_id(
        self, client, mock_conversation_manager, mock_qa_controller
    ):
        """Creating a conversation without an initial query returns a conversation_id."""
        response = client.post("/api/qa/conversations", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "conversation_id" in data["data"]
        assert data["data"]["conversation_id"] == str(TEST_CONVERSATION_ID)

    def test_create_conversation_with_initial_query_returns_query_result(
        self, client, mock_conversation_manager, mock_qa_controller
    ):
        """Creating a conversation with an initial_query also returns a query result."""
        response = client.post(
            "/api/qa/conversations",
            json={"initial_query": "What is deep learning?"},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "conversation_id" in data
        assert data["query_result"] is not None
        assert data["query_result"]["query"] == "What is deep learning?"

    def test_create_conversation_without_initial_query_has_null_result(
        self, client, mock_conversation_manager, mock_qa_controller
    ):
        """Creating a conversation without initial_query should have null query_result."""
        response = client.post("/api/qa/conversations", json={})

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["query_result"] is None

    def test_create_conversation_initial_query_too_long_returns_422(
        self, client, mock_conversation_manager
    ):
        """initial_query exceeding 2000 characters should fail validation."""
        response = client.post(
            "/api/qa/conversations",
            json={"initial_query": "x" * 2001},
        )
        assert response.status_code == 422

    def test_create_conversation_manager_error_returns_500(self, client, mock_conversation_manager):
        """When _create_conversation_in_db raises, the API returns 500."""
        with patch(
            "app.api.qa._create_conversation_in_db",
            new=AsyncMock(side_effect=RuntimeError("DB error")),
        ):
            response = client.post("/api/qa/conversations", json={})
        assert response.status_code == 500


# ============================================================================
# 3. Continue Conversation — POST /api/qa/conversations/{id}/continue
# ============================================================================


class TestContinueConversationEndpoint:
    """Tests for POST /api/qa/conversations/{id}/continue."""

    def test_continue_conversation_returns_200(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """Continuing an existing conversation returns a structured response."""
        response = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "Tell me more about neural networks"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert "query" in result
        assert "conversation_id" in result

    def test_continue_conversation_preserves_conversation_id(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """The response conversation_id should match the path parameter."""
        response = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "Follow-up question"},
        )

        assert response.status_code == 200
        result = response.json()["data"]
        assert result["conversation_id"] == str(TEST_CONVERSATION_ID)

    def test_continue_conversation_not_found_returns_404(self, client, mock_qa_controller):
        """When conversation doesn't exist, the API returns 404."""
        with patch("app.api.qa._get_conversation_from_db", new=AsyncMock(return_value=None)):
            response = client.post(
                f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
                json={"query": "Follow-up"},
            )

        assert response.status_code == 404

    def test_continue_conversation_empty_query_returns_422(self, client, mock_qa_controller):
        """An empty follow-up query should fail validation."""
        response = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_continue_conversation_controller_error_returns_500(self, client, mock_qa_controller):
        """When continue_conversation raises, the API returns 500."""
        with patch(
            "app.api.qa._get_conversation_from_db",
            new=AsyncMock(
                return_value={
                    "id": str(TEST_CONVERSATION_ID),
                    "user_id": str(TEST_USER_ID),
                    "context": {"turns": []},
                    "created_at": "2024-01-15T10:00:00",
                    "last_updated": "2024-01-15T10:00:00",
                    "expires_at": "2099-01-01T00:00:00",
                }
            ),
        ):
            mock_qa_controller.continue_conversation = AsyncMock(
                side_effect=RuntimeError("LLM timeout")
            )
            response = client.post(
                f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
                json={"query": "Follow-up"},
            )
        assert response.status_code == 500

    def test_continue_conversation_controller_returns_none_returns_500(
        self, client, mock_qa_controller
    ):
        """When continue_conversation returns None, the API returns 500."""
        with patch(
            "app.api.qa._get_conversation_from_db",
            new=AsyncMock(
                return_value={
                    "id": str(TEST_CONVERSATION_ID),
                    "user_id": str(TEST_USER_ID),
                    "context": {"turns": []},
                    "created_at": "2024-01-15T10:00:00",
                    "last_updated": "2024-01-15T10:00:00",
                    "expires_at": "2099-01-01T00:00:00",
                }
            ),
        ):
            mock_qa_controller.continue_conversation = AsyncMock(return_value=None)
            response = client.post(
                f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
                json={"query": "Follow-up"},
            )
        assert response.status_code == 500


# ============================================================================
# 4. Get Conversation History — GET /api/qa/conversations/{id}
# ============================================================================


class TestGetConversationEndpoint:
    """Tests for GET /api/qa/conversations/{id}."""

    def test_get_conversation_returns_200_with_history(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """Retrieving an existing conversation returns its history."""
        response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        result = data["data"]
        assert result["conversation_id"] == str(TEST_CONVERSATION_ID)
        assert result["user_id"] == str(TEST_USER_ID)
        assert "turns" in result
        assert "created_at" in result
        assert "last_updated" in result

    def test_get_conversation_not_found_returns_404(self, client, mock_qa_controller):
        """When conversation doesn't exist, the API returns 404."""
        with patch("app.api.qa._get_conversation_from_db", new=AsyncMock(return_value=None)):
            response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 404

    def test_get_conversation_with_turns_returns_turn_data(self, client, mock_qa_controller):
        """Conversation with turns should include turn details in the response."""
        row_with_turns = {
            "id": str(TEST_CONVERSATION_ID),
            "user_id": str(TEST_USER_ID),
            "context": {
                "conversation_id": str(TEST_CONVERSATION_ID),
                "user_id": str(TEST_USER_ID),
                "turns": [
                    {
                        "turn_number": 1,
                        "query": "What is AI?",
                        "timestamp": "2024-01-15T10:05:00",
                    }
                ],
                "current_topic": "AI",
            },
            "created_at": "2024-01-15T10:00:00",
            "last_updated": "2024-01-15T10:05:00",
            "expires_at": "2099-01-01T00:00:00",
        }
        with patch(
            "app.api.qa._get_conversation_from_db", new=AsyncMock(return_value=row_with_turns)
        ):
            response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")

        assert response.status_code == 200
        turns = response.json()["data"]["turns"]
        assert len(turns) == 1
        assert turns[0]["turn_number"] == 1
        assert turns[0]["query"] == "What is AI?"

    def test_get_conversation_controller_error_returns_500(self, client, mock_qa_controller):
        """When _get_conversation_from_db raises, the API returns 500."""
        with patch(
            "app.api.qa._get_conversation_from_db",
            new=AsyncMock(side_effect=RuntimeError("DB error")),
        ):
            response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 500


# ============================================================================
# 5. Delete Conversation — DELETE /api/qa/conversations/{id}
# ============================================================================


class TestDeleteConversationEndpoint:
    """Tests for DELETE /api/qa/conversations/{id}."""

    def test_delete_conversation_returns_200(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """Deleting an existing conversation returns 200 with success message."""
        response = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data["data"]

    def test_delete_conversation_not_found_returns_404(self, client, mock_qa_controller):
        """When conversation doesn't exist, the API returns 404."""
        with patch("app.api.qa._delete_conversation_from_db", new=AsyncMock(return_value=False)):
            response = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 404

    def test_delete_conversation_controller_error_returns_500(self, client, mock_qa_controller):
        """When _delete_conversation_from_db raises, the API returns 500."""
        with patch(
            "app.api.qa._delete_conversation_from_db",
            new=AsyncMock(side_effect=RuntimeError("DB error")),
        ):
            response = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 500


# ============================================================================
# 6. Authentication — unauthenticated requests return 401
# ============================================================================


class TestAuthentication:
    """Verify that all QA endpoints require authentication."""

    @pytest.fixture(autouse=True)
    def remove_auth_override(self):
        """Remove the auth override so real auth is enforced."""
        app.dependency_overrides.pop(get_current_user, None)
        yield
        # Restore the override for other tests (autouse fixture in module scope handles this)
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": TEST_USER_ID,
            "discord_id": TEST_DISCORD_ID,
        }

    def test_query_without_auth_returns_401(self, client):
        """POST /api/qa/query without a token returns 401."""
        response = client.post("/api/qa/query", json={"query": "test"})
        assert response.status_code == 401

    def test_create_conversation_without_auth_returns_401(self, client):
        """POST /api/qa/conversations without a token returns 401."""
        response = client.post("/api/qa/conversations", json={})
        assert response.status_code == 401

    def test_continue_conversation_without_auth_returns_401(self, client):
        """POST /api/qa/conversations/{id}/continue without a token returns 401."""
        response = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "test"},
        )
        assert response.status_code == 401

    def test_get_conversation_without_auth_returns_401(self, client):
        """GET /api/qa/conversations/{id} without a token returns 401."""
        response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 401

    def test_delete_conversation_without_auth_returns_401(self, client):
        """DELETE /api/qa/conversations/{id} without a token returns 401."""
        response = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert response.status_code == 401


# ============================================================================
# 7. Response Time — responses complete within 3 seconds (Requirement 6.2)
# ============================================================================


class TestResponseTime:
    """Verify that API responses complete within the 3-second requirement."""

    def test_query_response_time_under_3_seconds(self, client, mock_qa_controller):
        """
        POST /api/qa/query must complete within 3 seconds.

        Validates: Requirement 6.2
        """
        start = time.monotonic()
        response = client.post(
            "/api/qa/query",
            json={"query": "What is machine learning?"},
        )
        elapsed = time.monotonic() - start

        assert response.status_code == 200
        assert (
            elapsed < RESPONSE_TIME_LIMIT
        ), f"Query response took {elapsed:.2f}s, exceeds {RESPONSE_TIME_LIMIT}s limit"

    def test_create_conversation_response_time_under_3_seconds(
        self, client, mock_conversation_manager, mock_qa_controller
    ):
        """
        POST /api/qa/conversations must complete within 3 seconds.

        Validates: Requirement 6.2
        """
        start = time.monotonic()
        response = client.post("/api/qa/conversations", json={})
        elapsed = time.monotonic() - start

        assert response.status_code == 200
        assert (
            elapsed < RESPONSE_TIME_LIMIT
        ), f"Create conversation took {elapsed:.2f}s, exceeds {RESPONSE_TIME_LIMIT}s limit"

    def test_continue_conversation_response_time_under_3_seconds(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """
        POST /api/qa/conversations/{id}/continue must complete within 3 seconds.

        Validates: Requirement 6.2
        """
        start = time.monotonic()
        response = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "Tell me more"},
        )
        elapsed = time.monotonic() - start

        assert response.status_code == 200
        assert (
            elapsed < RESPONSE_TIME_LIMIT
        ), f"Continue conversation took {elapsed:.2f}s, exceeds {RESPONSE_TIME_LIMIT}s limit"

    def test_get_conversation_response_time_under_3_seconds(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """
        GET /api/qa/conversations/{id} must complete within 3 seconds.

        Validates: Requirement 6.2
        """
        start = time.monotonic()
        response = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        elapsed = time.monotonic() - start

        assert response.status_code == 200
        assert (
            elapsed < RESPONSE_TIME_LIMIT
        ), f"Get conversation took {elapsed:.2f}s, exceeds {RESPONSE_TIME_LIMIT}s limit"

    def test_delete_conversation_response_time_under_3_seconds(
        self, client, mock_qa_controller, mock_conversation_manager
    ):
        """
        DELETE /api/qa/conversations/{id} must complete within 3 seconds.

        Validates: Requirement 6.2
        """
        start = time.monotonic()
        response = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        elapsed = time.monotonic() - start

        assert response.status_code == 200
        assert (
            elapsed < RESPONSE_TIME_LIMIT
        ), f"Delete conversation took {elapsed:.2f}s, exceeds {RESPONSE_TIME_LIMIT}s limit"


# ============================================================================
# 8. Multi-turn Conversation Flow
# ============================================================================


class TestMultiTurnConversationFlow:
    """
    End-to-end multi-turn conversation flow tests.

    Validates: Requirements 6.1, 6.2
    """

    def test_full_multi_turn_flow(self, client, mock_conversation_manager, mock_qa_controller):
        """
        Complete multi-turn flow:
        1. Create conversation
        2. Submit initial query
        3. Continue with follow-up
        4. Retrieve history
        5. Delete conversation
        """
        # Step 1: Create conversation
        create_resp = client.post("/api/qa/conversations", json={})
        assert create_resp.status_code == 200
        conversation_id = create_resp.json()["data"]["conversation_id"]

        # Step 2: Submit a query (using the conversation_id)
        query_resp = client.post(
            "/api/qa/query",
            json={"query": "What is AI?", "conversation_id": conversation_id},
        )
        assert query_resp.status_code == 200
        assert query_resp.json()["data"]["conversation_id"] == str(TEST_CONVERSATION_ID)

        # Step 3: Continue conversation
        continue_resp = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "Tell me more about neural networks"},
        )
        assert continue_resp.status_code == 200

        # Step 4: Retrieve history
        history_resp = client.get(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert history_resp.status_code == 200
        history = history_resp.json()["data"]
        assert history["conversation_id"] == str(TEST_CONVERSATION_ID)

        # Step 5: Delete conversation
        delete_resp = client.delete(f"/api/qa/conversations/{TEST_CONVERSATION_ID}")
        assert delete_resp.status_code == 200

    def test_multi_turn_conversation_with_initial_query(
        self, client, mock_conversation_manager, mock_qa_controller
    ):
        """
        Create conversation with initial query, then continue with follow-ups.
        """
        # Create with initial query
        create_resp = client.post(
            "/api/qa/conversations",
            json={"initial_query": "What is machine learning?"},
        )
        assert create_resp.status_code == 200
        data = create_resp.json()["data"]
        assert data["query_result"] is not None
        assert data["query_result"]["query"] == "What is machine learning?"

        # Continue conversation
        continue_resp = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "What are the main algorithms?"},
        )
        assert continue_resp.status_code == 200

        # Another follow-up
        continue_resp2 = client.post(
            f"/api/qa/conversations/{TEST_CONVERSATION_ID}/continue",
            json={"query": "Which one is best for classification?"},
        )
        assert continue_resp2.status_code == 200
