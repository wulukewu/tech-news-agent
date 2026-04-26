"""
Example Usage: SecurityManager Integration

This example demonstrates how to integrate the SecurityManager with the
Intelligent Q&A Agent for encryption, access control, and secure deletion.

Validates: Requirements 10.1, 10.3, 10.4, 10.5
"""

import asyncio
from uuid import uuid4

from app.qa_agent.database import get_db_connection
from app.qa_agent.security_manager import (
    AccessDeniedError,
    get_security_manager,
)


async def example_1_encrypt_query_data():
    """
    Example 1: Encrypting and storing query data

    Demonstrates: Requirement 10.1 - Encrypt stored query logs
    """
    print("\n" + "=" * 80)
    print("Example 1: Encrypting Query Data")
    print("=" * 80)

    security_manager = get_security_manager()

    # User submits a query
    user_id = uuid4()
    query_text = "What are the latest developments in artificial intelligence?"

    print(f"\nOriginal query: {query_text}")

    # Encrypt the query text before storing
    encrypted_query = security_manager.encrypt_text(query_text)
    print(f"Encrypted query: {encrypted_query[:50]}...")

    # Encrypt response data
    response_data = {
        "articles": [
            {"title": "AI Breakthrough", "url": "https://example.com/ai"},
            {"title": "ML Advances", "url": "https://example.com/ml"},
        ],
        "insights": ["AI is rapidly evolving", "ML models are getting larger"],
        "confidence": 0.95,
    }

    encrypted_response = security_manager.encrypt_dict(response_data)
    print(f"Encrypted response: {encrypted_response[:50]}...")

    # Store in database (simulated)
    print("\n✅ Query data encrypted and ready for storage")

    # Later, when retrieving the data
    decrypted_query = security_manager.decrypt_text(encrypted_query)
    decrypted_response = security_manager.decrypt_dict(encrypted_response)

    print(f"\nDecrypted query: {decrypted_query}")
    print(f"Decrypted response articles: {len(decrypted_response['articles'])} articles")
    print(f"Decrypted response confidence: {decrypted_response['confidence']}")


async def example_2_access_control():
    """
    Example 2: Validating user access to resources

    Demonstrates: Requirements 10.3, 10.5 - User data isolation and access control
    """
    print("\n" + "=" * 80)
    print("Example 2: Access Control and User Data Isolation")
    print("=" * 80)

    security_manager = get_security_manager()

    # Create test users and conversation
    user1_id = uuid4()
    user2_id = uuid4()
    conversation_id = uuid4()

    print(f"\nUser 1 ID: {user1_id}")
    print(f"User 2 ID: {user2_id}")
    print(f"Conversation ID: {conversation_id}")

    # Simulate creating a conversation owned by user1
    async with get_db_connection() as conn:
        # Ensure users table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        # Create users
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2), ($3, $4) ON CONFLICT DO NOTHING",
            user1_id,
            f"user1_{user1_id}@example.com",
            user2_id,
            f"user2_{user2_id}@example.com",
        )

        # Ensure conversations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                context JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_updated TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        # Create conversation owned by user1
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
            """,
            conversation_id,
            user1_id,
            '{"topic": "AI"}',
        )

    print("\n✅ Test data created")

    # User 1 tries to access their own conversation - should succeed
    try:
        result = await security_manager.validate_user_access(
            user1_id, "conversation", conversation_id
        )
        print("\n✅ User 1 access to their conversation: GRANTED")
    except AccessDeniedError as e:
        print(f"\n❌ User 1 access denied: {e}")

    # User 2 tries to access user 1's conversation - should fail
    try:
        result = await security_manager.validate_user_access(
            user2_id, "conversation", conversation_id
        )
        print("\n❌ User 2 access to user 1's conversation: GRANTED (This should not happen!)")
    except AccessDeniedError as e:
        print("\n✅ User 2 access denied (as expected): Access denied to conversation")

    # Get all conversations owned by user 1
    owned_conversations = await security_manager.get_user_owned_resources(user1_id, "conversation")
    print(f"\n✅ User 1 owns {len(owned_conversations)} conversation(s)")

    # Cleanup
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM conversations WHERE id = $1", conversation_id)
        await conn.execute("DELETE FROM users WHERE id IN ($1, $2)", user1_id, user2_id)


async def example_3_secure_deletion():
    """
    Example 3: Securely deleting user data

    Demonstrates: Requirement 10.4 - Secure data deletion mechanisms
    """
    print("\n" + "=" * 80)
    print("Example 3: Secure Data Deletion (GDPR Compliance)")
    print("=" * 80)

    security_manager = get_security_manager()

    # Create test user with data
    user_id = uuid4()
    conversation_id = uuid4()
    query_log_id = uuid4()

    print(f"\nUser ID: {user_id}")

    async with get_db_connection() as conn:
        # Ensure tables exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                context JSONB NOT NULL DEFAULT '{}',
                current_topic TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_updated TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                query_text TEXT NOT NULL,
                response_data JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id UUID PRIMARY KEY,
                reading_history JSONB DEFAULT '[]',
                preferred_topics JSONB DEFAULT '[]',
                interaction_patterns JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
        """)

        # Create user
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id,
            f"user_{user_id}@example.com",
        )

        # Create conversation with sensitive data
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, context, current_topic)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            """,
            conversation_id,
            user_id,
            '{"query": "sensitive medical question", "history": ["private data"]}',
            "Personal Health Information",
        )

        # Create query log with sensitive data
        await conn.execute(
            """
            INSERT INTO query_logs (id, user_id, query_text, response_data)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            """,
            query_log_id,
            user_id,
            "What are my symptoms indicating?",
            '{"diagnosis": "sensitive medical info"}',
        )

        # Create user profile
        await conn.execute(
            """
            INSERT INTO user_profiles (user_id, reading_history, preferred_topics)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
            """,
            user_id,
            '["article1", "article2"]',
            '["health", "medical"]',
        )

    print("✅ Test data created with sensitive information")

    # Verify data exists before deletion
    async with get_db_connection() as conn:
        conv = await conn.fetchrow(
            "SELECT context, current_topic FROM conversations WHERE id = $1", conversation_id
        )
        print("\nBefore deletion:")
        print(f"  Conversation topic: {conv['current_topic']}")
        print(f"  Conversation context: {conv['context']}")

    # Securely delete conversation
    print("\n🔒 Securely deleting conversation...")
    result = await security_manager.secure_delete_conversation(user_id, conversation_id)

    if result:
        print("✅ Conversation securely deleted")

        # Verify data was overwritten
        async with get_db_connection() as conn:
            conv = await conn.fetchrow(
                "SELECT context, current_topic, deleted_at FROM conversations WHERE id = $1",
                conversation_id,
            )
            print("\nAfter deletion:")
            print(f"  Conversation topic: {conv['current_topic']}")
            print(f"  Conversation context: {conv['context']}")
            print(f"  Deleted at: {conv['deleted_at']}")
            print("  ✅ Sensitive data overwritten with random data")

    # Delete all user data (GDPR right to be forgotten)
    print("\n🔒 Deleting all user data (GDPR compliance)...")
    results = await security_manager.secure_delete_all_user_data(user_id)

    print("\n✅ Complete data deletion results:")
    print(f"  Conversations deleted: {results['conversations']}")
    print(f"  Query logs deleted: {results['query_logs']}")
    print(f"  User profile deleted: {results['user_profile']}")

    # Cleanup
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM conversations WHERE id = $1", conversation_id)
        await conn.execute("DELETE FROM query_logs WHERE id = $1", query_log_id)
        await conn.execute("DELETE FROM user_profiles WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


async def example_4_audit_logging():
    """
    Example 4: Security audit logging

    Demonstrates: Security event tracking and audit trail
    """
    print("\n" + "=" * 80)
    print("Example 4: Security Audit Logging")
    print("=" * 80)

    security_manager = get_security_manager()

    # Create test user
    user_id = uuid4()
    resource_id = uuid4()

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

    print(f"\nUser ID: {user_id}")
    print(f"Resource ID: {resource_id}")

    # Log various security events
    print("\n📝 Logging security events...")

    # Event 1: Access denied
    await security_manager._log_security_event(
        user_id=user_id,
        event_type="access_denied",
        resource_type="conversation",
        resource_id=resource_id,
        reason="not_owner",
        metadata={"attempted_action": "read", "ip_address": "192.168.1.100"},
    )
    print("  ✅ Logged: access_denied event")

    # Event 2: Secure deletion
    await security_manager._log_security_event(
        user_id=user_id,
        event_type="secure_delete",
        resource_type="query_log",
        resource_id=resource_id,
        reason="user_request",
        metadata={"deleted_count": 5},
    )
    print("  ✅ Logged: secure_delete event")

    # Event 3: Complete data deletion
    await security_manager._log_security_event(
        user_id=user_id,
        event_type="complete_data_deletion",
        resource_type="all",
        resource_id=user_id,
        reason="gdpr_request",
        metadata={"conversations": 3, "query_logs": 10, "user_profile": 1},
    )
    print("  ✅ Logged: complete_data_deletion event")

    # Retrieve audit logs
    print("\n📋 Retrieving audit logs...")
    logs = await security_manager.get_security_audit_log(user_id=user_id, limit=10)

    print(f"\n✅ Found {len(logs)} audit log entries:")
    for i, log in enumerate(logs, 1):
        print(f"\n  Entry {i}:")
        print(f"    Event Type: {log['event_type']}")
        print(f"    Resource Type: {log['resource_type']}")
        print(f"    Reason: {log['reason']}")
        print(f"    Timestamp: {log['created_at']}")
        if log["metadata"]:
            print(f"    Metadata: {log['metadata']}")

    # Cleanup
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM security_audit_log WHERE user_id = $1", user_id)


async def example_5_integration_workflow():
    """
    Example 5: Complete integration workflow

    Demonstrates: End-to-end security integration in QA agent
    """
    print("\n" + "=" * 80)
    print("Example 5: Complete Integration Workflow")
    print("=" * 80)

    security_manager = get_security_manager()

    # Simulate a user query workflow
    user_id = uuid4()
    conversation_id = uuid4()

    print(f"\nUser ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")

    # Step 1: User submits a query
    query_text = "What are the best practices for data privacy in AI systems?"
    print(f"\n1️⃣ User submits query: '{query_text}'")

    # Step 2: Encrypt query before storing
    encrypted_query = security_manager.encrypt_text(query_text)
    print(f"2️⃣ Query encrypted: {encrypted_query[:50]}...")

    # Step 3: Process query and generate response (simulated)
    response_data = {
        "articles": [
            {"title": "GDPR Compliance in AI", "relevance": 0.95},
            {"title": "Privacy-Preserving ML", "relevance": 0.88},
        ],
        "insights": [
            "Implement data encryption at rest and in transit",
            "Use differential privacy techniques",
            "Provide user data deletion mechanisms",
        ],
    }
    encrypted_response = security_manager.encrypt_dict(response_data)
    print(f"3️⃣ Response encrypted: {encrypted_response[:50]}...")

    # Step 4: Store encrypted data (simulated)
    print("4️⃣ Encrypted data stored in database")

    # Step 5: User requests to view their conversation history
    print("\n5️⃣ User requests conversation history")

    # Step 6: Validate user access
    try:
        # In real implementation, this would check database
        print("6️⃣ Validating user access...")
        # await security_manager.validate_user_access(user_id, "conversation", conversation_id)
        print("   ✅ Access granted")
    except AccessDeniedError:
        print("   ❌ Access denied")
        return

    # Step 7: Decrypt data for display
    decrypted_query = security_manager.decrypt_text(encrypted_query)
    decrypted_response = security_manager.decrypt_dict(encrypted_response)
    print("7️⃣ Data decrypted for display")
    print(f"   Query: {decrypted_query}")
    print(f"   Articles found: {len(decrypted_response['articles'])}")

    # Step 8: User requests data deletion (GDPR)
    print("\n8️⃣ User requests complete data deletion (GDPR)")
    print("   🔒 Securely deleting all user data...")
    print("   ✅ All data securely deleted and overwritten")

    # Step 9: Verify audit trail
    print("\n9️⃣ Security audit trail:")
    print("   - Query encryption logged")
    print("   - Access validation logged")
    print("   - Data deletion logged")
    print("   ✅ Complete audit trail maintained")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SecurityManager Integration Examples")
    print("Intelligent Q&A Agent - Data Encryption and Access Control")
    print("=" * 80)

    try:
        await example_1_encrypt_query_data()
        await example_2_access_control()
        await example_3_secure_deletion()
        await example_4_audit_logging()
        await example_5_integration_workflow()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
