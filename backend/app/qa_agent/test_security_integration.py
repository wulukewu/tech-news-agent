"""
Integration Tests for SecurityManager

Tests encryption, access control, and secure deletion with actual database.

Validates: Requirements 10.1, 10.3, 10.4, 10.5
"""

from uuid import uuid4

import pytest

from app.qa_agent.database import get_db_connection
from app.qa_agent.security_manager import AccessDeniedError, SecurityManager


@pytest.fixture
async def setup_database():
    """Set up test database with required tables."""
    async with get_db_connection() as conn:
        # Ensure security_audit_log table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                resource_type VARCHAR(50) NOT NULL,
                resource_id UUID,
                reason VARCHAR(100) NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Ensure users table exists (simplified for testing)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Ensure conversations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                context JSONB NOT NULL DEFAULT '{}',
                current_topic TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_updated TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        # Ensure query_logs table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                conversation_id UUID,
                query_text TEXT NOT NULL,
                response_data JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        # Ensure user_profiles table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id UUID PRIMARY KEY,
                reading_history JSONB DEFAULT '[]',
                preferred_topics JSONB DEFAULT '[]',
                interaction_patterns JSONB DEFAULT '{}',
                satisfaction_scores JSONB DEFAULT '[]',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

    yield

    # Cleanup after tests
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM security_audit_log")
        await conn.execute("DELETE FROM query_logs")
        await conn.execute("DELETE FROM conversations")
        await conn.execute("DELETE FROM user_profiles")
        await conn.execute("DELETE FROM users WHERE email LIKE 'test_%'")


@pytest.mark.asyncio
async def test_access_control_conversation_owner(setup_database):
    """Test that conversation owner can access their conversation."""
    security_manager = SecurityManager()

    # Create test user
    user_id = uuid4()
    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        # Create conversation owned by user
        conversation_id = uuid4()
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context)
            VALUES ($1, $2, $3)
            """,
            conversation_id,
            user_id,
            '{"test": true}',
        )

    # Validate access - should succeed
    result = await security_manager.validate_user_access(user_id, "conversation", conversation_id)
    assert result is True


@pytest.mark.asyncio
async def test_access_control_conversation_non_owner(setup_database):
    """Test that non-owner cannot access conversation."""
    security_manager = SecurityManager()

    # Create two test users
    owner_id = uuid4()
    other_user_id = uuid4()

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2), ($3, $4)",
            owner_id,
            f"test_{owner_id}@example.com",
            other_user_id,
            f"test_{other_user_id}@example.com",
        )

        # Create conversation owned by owner_id
        conversation_id = uuid4()
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context)
            VALUES ($1, $2, $3)
            """,
            conversation_id,
            owner_id,
            '{"test": true}',
        )

    # Validate access by non-owner - should raise AccessDeniedError
    with pytest.raises(AccessDeniedError):
        await security_manager.validate_user_access(other_user_id, "conversation", conversation_id)


@pytest.mark.asyncio
async def test_access_control_query_log_owner(setup_database):
    """Test that query log owner can access their logs."""
    security_manager = SecurityManager()

    # Create test user
    user_id = uuid4()
    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        # Create query log owned by user
        query_log_id = uuid4()
        await conn.execute(
            """
            INSERT INTO query_logs (id, user_id, query_text)
            VALUES ($1, $2, $3)
            """,
            query_log_id,
            user_id,
            "test query",
        )

    # Validate access - should succeed
    result = await security_manager.validate_user_access(user_id, "query_log", query_log_id)
    assert result is True


@pytest.mark.asyncio
async def test_secure_delete_conversation(setup_database):
    """Test secure deletion of conversation with data overwriting."""
    security_manager = SecurityManager()

    # Create test user and conversation
    user_id = uuid4()
    conversation_id = uuid4()
    original_context = {"query": "sensitive data", "topic": "AI"}
    original_topic = "Artificial Intelligence"

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context, current_topic)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id,
            user_id,
            original_context,
            original_topic,
        )

    # Securely delete conversation
    result = await security_manager.secure_delete_conversation(user_id, conversation_id)
    assert result is True

    # Verify data was overwritten
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT context, current_topic, deleted_at FROM conversations WHERE id = $1",
            conversation_id,
        )

        assert row is not None
        assert row["deleted_at"] is not None
        assert row["context"] == {"overwritten": True}
        assert "DELETED_" in row["current_topic"]
        assert original_topic not in row["current_topic"]


@pytest.mark.asyncio
async def test_secure_delete_query_logs(setup_database):
    """Test secure deletion of query logs."""
    security_manager = SecurityManager()

    # Create test user and query logs
    user_id = uuid4()
    query_log_ids = [uuid4(), uuid4(), uuid4()]

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        for query_log_id in query_log_ids:
            await conn.execute(
                """
                INSERT INTO query_logs (id, user_id, query_text, response_data)
                VALUES ($1, $2, $3, $4)
                """,
                query_log_id,
                user_id,
                "sensitive query text",
                '{"result": "sensitive data"}',
            )

    # Securely delete specific query logs
    deleted_count = await security_manager.secure_delete_query_logs(user_id, query_log_ids[:2])
    assert deleted_count == 2

    # Verify data was overwritten for deleted logs
    async with get_db_connection() as conn:
        for query_log_id in query_log_ids[:2]:
            row = await conn.fetchrow(
                "SELECT query_text, response_data, deleted_at FROM query_logs WHERE id = $1",
                query_log_id,
            )

            assert row is not None
            assert row["deleted_at"] is not None
            assert "DELETED_" in row["query_text"]
            assert row["response_data"] == {"overwritten": True}

        # Verify third log was not deleted
        row = await conn.fetchrow(
            "SELECT deleted_at FROM query_logs WHERE id = $1", query_log_ids[2]
        )
        assert row["deleted_at"] is None


@pytest.mark.asyncio
async def test_secure_delete_user_profile(setup_database):
    """Test secure deletion of user profile."""
    security_manager = SecurityManager()

    # Create test user and profile
    user_id = uuid4()

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        await conn.execute(
            """
            INSERT INTO user_profiles (user_id, reading_history, preferred_topics, interaction_patterns)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            '["article1", "article2"]',
            '["AI", "ML"]',
            '{"preference": "technical"}',
        )

    # Securely delete profile
    result = await security_manager.secure_delete_user_profile(user_id)
    assert result is True

    # Verify data was overwritten
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT reading_history, preferred_topics, interaction_patterns, deleted_at
            FROM user_profiles WHERE user_id = $1
            """,
            user_id,
        )

        assert row is not None
        assert row["deleted_at"] is not None
        assert row["reading_history"] == []
        assert row["preferred_topics"] == []
        assert row["interaction_patterns"] == {}


@pytest.mark.asyncio
async def test_secure_delete_all_user_data(setup_database):
    """Test complete user data deletion (GDPR compliance)."""
    security_manager = SecurityManager()

    # Create test user with all data types
    user_id = uuid4()

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

        # Create conversations
        for i in range(3):
            await conn.execute(
                """
                INSERT INTO conversations (id, user_id, context)
                VALUES ($1, $2, $3)
                """,
                uuid4(),
                user_id,
                f'{{"test": {i}}}',
            )

        # Create query logs
        for i in range(5):
            await conn.execute(
                """
                INSERT INTO query_logs (id, user_id, query_text)
                VALUES ($1, $2, $3)
                """,
                uuid4(),
                user_id,
                f"query {i}",
            )

        # Create user profile
        await conn.execute(
            """
            INSERT INTO user_profiles (user_id, reading_history)
            VALUES ($1, $2)
            """,
            user_id,
            '["article1"]',
        )

    # Delete all user data
    results = await security_manager.secure_delete_all_user_data(user_id)

    assert results["conversations"] == 3
    assert results["query_logs"] == 5
    assert results["user_profile"] == 1

    # Verify all data is marked as deleted
    async with get_db_connection() as conn:
        # Check conversations
        conv_count = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE user_id = $1 AND deleted_at IS NULL", user_id
        )
        assert conv_count == 0

        # Check query logs
        log_count = await conn.fetchval(
            "SELECT COUNT(*) FROM query_logs WHERE user_id = $1 AND deleted_at IS NULL", user_id
        )
        assert log_count == 0

        # Check user profile
        profile = await conn.fetchrow(
            "SELECT deleted_at FROM user_profiles WHERE user_id = $1", user_id
        )
        assert profile["deleted_at"] is not None


@pytest.mark.asyncio
async def test_audit_logging(setup_database):
    """Test security audit logging."""
    security_manager = SecurityManager()

    # Create test user
    user_id = uuid4()
    resource_id = uuid4()

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)", user_id, f"test_{user_id}@example.com"
        )

    # Log a security event
    await security_manager._log_security_event(
        user_id=user_id,
        event_type="test_event",
        resource_type="test_resource",
        resource_id=resource_id,
        reason="testing",
        metadata={"test": True},
    )

    # Retrieve audit log
    logs = await security_manager.get_security_audit_log(user_id=user_id, event_type="test_event")

    assert len(logs) > 0
    assert logs[0]["user_id"] == user_id
    assert logs[0]["event_type"] == "test_event"
    assert logs[0]["resource_type"] == "test_resource"
    assert logs[0]["resource_id"] == resource_id
    assert logs[0]["reason"] == "testing"
    assert logs[0]["metadata"]["test"] is True


@pytest.mark.asyncio
async def test_get_user_owned_resources(setup_database):
    """Test retrieving user-owned resources."""
    security_manager = SecurityManager()

    # Create test user
    user_id = uuid4()
    other_user_id = uuid4()

    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2), ($3, $4)",
            user_id,
            f"test_{user_id}@example.com",
            other_user_id,
            f"test_{other_user_id}@example.com",
        )

        # Create conversations for user
        user_conv_ids = []
        for i in range(3):
            conv_id = uuid4()
            user_conv_ids.append(conv_id)
            await conn.execute(
                """
                INSERT INTO conversations (id, user_id, context)
                VALUES ($1, $2, $3)
                """,
                conv_id,
                user_id,
                f'{{"test": {i}}}',
            )

        # Create conversation for other user
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context)
            VALUES ($1, $2, $3)
            """,
            uuid4(),
            other_user_id,
            '{"other": true}',
        )

    # Get user's conversations
    owned_resources = await security_manager.get_user_owned_resources(user_id, "conversation")

    assert len(owned_resources) == 3
    assert all(conv_id in owned_resources for conv_id in user_conv_ids)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
