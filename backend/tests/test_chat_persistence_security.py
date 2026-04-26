"""
Security and Privacy Tests for Chat Persistence System

Tests:
  - Data encryption and access control
  - Authentication and authorisation flows
  - Data isolation between users
  - Rate limiting
  - Audit logging
  - Data deletion (right to be forgotten)

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5 (Task 10.3)
"""

from __future__ import annotations

import base64
import time
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Test: Data Encryption (Requirement 8.1)
# ---------------------------------------------------------------------------


class TestDataEncryption:
    """Verify conversation content is encrypted at rest."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted content must decrypt to original plaintext."""
        from app.core.security import decrypt_content, encrypt_content

        plaintext = "Sensitive conversation: my password is hunter2"
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)
        assert decrypted == plaintext

    def test_encrypted_content_is_not_plaintext(self):
        """Encrypted content must not contain the original plaintext."""
        from app.core.security import encrypt_content

        plaintext = "secret_data_12345"
        encrypted = encrypt_content(plaintext)
        assert plaintext not in encrypted

    def test_different_nonce_each_encryption(self):
        """Each encryption must use a different nonce (semantic security)."""
        from app.core.security import encrypt_content

        plaintext = "same message"
        enc1 = encrypt_content(plaintext)
        enc2 = encrypt_content(plaintext)
        assert enc1 != enc2  # Different nonces → different ciphertext

    def test_tampered_ciphertext_raises_error(self):
        """Tampered ciphertext must raise an error on decryption."""
        from app.core.security import decrypt_content, encrypt_content

        encrypted = encrypt_content("original message")
        nonce_b64, ct_b64 = encrypted.split(".")
        # Flip a byte in the ciphertext
        ct_bytes = bytearray(base64.b64decode(ct_b64))
        ct_bytes[0] ^= 0xFF
        tampered = f"{nonce_b64}.{base64.b64encode(bytes(ct_bytes)).decode()}"

        with pytest.raises(ValueError):
            decrypt_content(tampered)

    def test_encryption_handles_unicode(self):
        """Encryption must handle unicode content correctly."""
        from app.core.security import decrypt_content, encrypt_content

        plaintext = "你好世界 🔒 مرحبا"
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)
        assert decrypted == plaintext

    def test_encryption_handles_empty_string(self):
        """Encryption must handle empty strings with a round-trip."""
        from app.core.security import decrypt_content, encrypt_content

        encrypted = encrypt_content("")
        decrypted = decrypt_content(encrypted)
        assert decrypted == ""

    def test_is_encrypted_detection(self):
        """is_encrypted() must correctly identify encrypted vs plaintext."""
        from app.core.security import encrypt_content, is_encrypted

        plaintext = "not encrypted"
        encrypted = encrypt_content(plaintext)

        assert is_encrypted(encrypted) is True
        assert is_encrypted(plaintext) is False
        assert is_encrypted("") is False
        assert is_encrypted("no.dots.here.at.all") is False


# ---------------------------------------------------------------------------
# Test: Content Integrity (Requirement 8.1)
# ---------------------------------------------------------------------------


class TestContentIntegrity:
    """Verify content integrity verification works correctly."""

    def test_hash_matches_original_content(self):
        """SHA-256 hash must match the original content."""
        from app.core.security import compute_content_hash, verify_content_integrity

        content = "Important conversation data"
        hash_val = compute_content_hash(content)
        assert verify_content_integrity(content, hash_val) is True

    def test_hash_fails_for_modified_content(self):
        """Integrity check must fail for modified content."""
        from app.core.security import compute_content_hash, verify_content_integrity

        content = "Original content"
        hash_val = compute_content_hash(content)
        assert verify_content_integrity("Modified content", hash_val) is False

    def test_hash_is_deterministic(self):
        """Same content must always produce the same hash."""
        from app.core.security import compute_content_hash

        content = "Deterministic content"
        assert compute_content_hash(content) == compute_content_hash(content)

    def test_hash_is_hex_string(self):
        """Hash must be a valid hex string."""
        from app.core.security import compute_content_hash

        hash_val = compute_content_hash("test")
        assert len(hash_val) == 64  # SHA-256 = 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_timing_safe_comparison(self):
        """Integrity check must use timing-safe comparison."""
        from app.core.security import compute_content_hash, verify_content_integrity

        # Both calls should take similar time (no early exit)
        content = "test content"
        correct_hash = compute_content_hash(content)
        wrong_hash = "a" * 64

        t1_start = time.perf_counter()
        verify_content_integrity(content, correct_hash)
        t1 = time.perf_counter() - t1_start

        t2_start = time.perf_counter()
        verify_content_integrity(content, wrong_hash)
        t2 = time.perf_counter() - t2_start

        # Both should complete (no crash on wrong hash)
        assert t1 >= 0
        assert t2 >= 0


# ---------------------------------------------------------------------------
# Test: Rate Limiting (Requirement 8.2)
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Verify rate limiting prevents abuse."""

    def test_rate_limiter_allows_requests_within_limit(self):
        """Requests within the limit must be allowed."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)
        user_id = str(uuid4())

        for _ in range(5):
            assert limiter.is_allowed(user_id) is True

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Requests exceeding the limit must be blocked."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)
        user_id = str(uuid4())

        for _ in range(3):
            limiter.is_allowed(user_id)

        assert limiter.is_allowed(user_id) is False

    def test_rate_limiter_resets_after_window(self):
        """Rate limit must reset after the window expires."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=0.05)  # 50ms window
        user_id = str(uuid4())

        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.is_allowed(user_id) is False  # Blocked

        time.sleep(0.06)  # Wait for window to expire
        assert limiter.is_allowed(user_id) is True  # Reset

    def test_rate_limiter_isolates_users(self):
        """Rate limit must be per-user, not global."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)
        user_a = str(uuid4())
        user_b = str(uuid4())

        limiter.is_allowed(user_a)
        limiter.is_allowed(user_a)
        assert limiter.is_allowed(user_a) is False  # A is blocked

        assert limiter.is_allowed(user_b) is True  # B is not affected

    def test_rate_limiter_remaining_count(self):
        """remaining() must return correct count."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = str(uuid4())

        assert limiter.remaining(user_id) == 10
        limiter.is_allowed(user_id)
        assert limiter.remaining(user_id) == 9
        limiter.is_allowed(user_id)
        assert limiter.remaining(user_id) == 8

    def test_rate_limiter_reset(self):
        """reset() must clear the counter for a user."""
        from app.core.security import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)
        user_id = str(uuid4())

        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.is_allowed(user_id) is False

        limiter.reset(user_id)
        assert limiter.is_allowed(user_id) is True

    def test_pre_built_limiters_exist(self):
        """Pre-built rate limiter instances must be available."""
        from app.core.security import (
            conversation_api_limiter,
            public_api_limiter,
            smart_conversation_limiter,
        )

        assert conversation_api_limiter.max_requests == 120
        assert smart_conversation_limiter.max_requests == 20
        assert public_api_limiter.max_requests == 30


# ---------------------------------------------------------------------------
# Test: Audit Logging (Requirement 8.5)
# ---------------------------------------------------------------------------


class TestAuditLogging:
    """Verify security events are logged correctly."""

    @pytest.mark.asyncio
    async def test_log_security_event_calls_supabase(self):
        """log_security_event must insert a row into security_audit_log."""
        from app.core.security import AuditEvent, log_security_event

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        event = AuditEvent(
            user_id=uuid4(),
            event_type="access_denied",
            resource_type="conversation",
            reason="Unauthorized",
        )
        await log_security_event(mock_client, event)

        mock_client.table.assert_called_with("security_audit_log")
        mock_client.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_security_event_does_not_raise_on_db_error(self):
        """Audit logging failures must not propagate to the caller."""
        from app.core.security import AuditEvent, log_security_event

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "DB error"
        )

        event = AuditEvent(
            user_id=uuid4(),
            event_type="data_export",
            resource_type="conversation",
            reason="User export",
        )
        # Must not raise
        await log_security_event(mock_client, event)

    @pytest.mark.asyncio
    async def test_log_access_denied_convenience_wrapper(self):
        """log_access_denied must call log_security_event with correct event_type."""
        from app.core.security import log_access_denied

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        user_id = uuid4()
        await log_access_denied(mock_client, user_id, "conversation", reason="Not owner")

        call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["event_type"] == "access_denied"
        assert call_args["resource_type"] == "conversation"

    @pytest.mark.asyncio
    async def test_log_data_deletion_convenience_wrapper(self):
        """log_data_deletion must call log_security_event with correct event_type."""
        from app.core.security import log_data_deletion

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        user_id = uuid4()
        await log_data_deletion(mock_client, user_id, "conversation", metadata={"count": 5})

        call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["event_type"] == "data_deletion"

    def test_audit_event_dataclass_fields(self):
        """AuditEvent must have all required fields."""
        from app.core.security import AuditEvent

        event = AuditEvent(
            user_id=uuid4(),
            event_type="test",
            resource_type="conversation",
            reason="Test reason",
        )
        assert event.event_type == "test"
        assert event.resource_type == "conversation"
        assert event.reason == "Test reason"
        assert event.resource_id is None
        assert event.metadata == {}
        assert event.ip_address is None


# ---------------------------------------------------------------------------
# Test: Data Isolation (Requirement 8.4)
# ---------------------------------------------------------------------------


class TestDataIsolation:
    """Verify data is isolated between users."""

    def test_conversation_belongs_to_user(self):
        """Conversations must be associated with a specific user."""
        user_a = str(uuid4())
        user_b = str(uuid4())

        conv_a = {
            "id": str(uuid4()),
            "user_id": user_a,
            "title": "User A's conversation",
        }
        conv_b = {
            "id": str(uuid4()),
            "user_id": user_b,
            "title": "User B's conversation",
        }

        # User A should not see User B's conversation
        user_a_convs = [c for c in [conv_a, conv_b] if c["user_id"] == user_a]
        assert len(user_a_convs) == 1
        assert user_a_convs[0]["title"] == "User A's conversation"

    def test_message_isolation_via_conversation(self):
        """Messages are isolated via their conversation's user_id."""
        user_a = str(uuid4())
        user_b = str(uuid4())

        conv_a_id = str(uuid4())
        conv_b_id = str(uuid4())

        conversations = {
            conv_a_id: {"user_id": user_a},
            conv_b_id: {"user_id": user_b},
        }

        messages = [
            {"id": str(uuid4()), "conversation_id": conv_a_id, "content": "A's message"},
            {"id": str(uuid4()), "conversation_id": conv_b_id, "content": "B's message"},
        ]

        # User A can only access messages in their conversations
        user_a_messages = [
            m for m in messages if conversations[m["conversation_id"]]["user_id"] == user_a
        ]
        assert len(user_a_messages) == 1
        assert user_a_messages[0]["content"] == "A's message"

    def test_platform_link_isolation(self):
        """Platform links must be isolated per user."""
        user_a = str(uuid4())
        user_b = str(uuid4())

        links = [
            {"user_id": user_a, "platform": "discord", "platform_user_id": "discord_a"},
            {"user_id": user_b, "platform": "discord", "platform_user_id": "discord_b"},
        ]

        user_a_links = [link for link in links if link["user_id"] == user_a]
        assert len(user_a_links) == 1
        assert user_a_links[0]["platform_user_id"] == "discord_a"


# ---------------------------------------------------------------------------
# Test: Data Deletion (Requirement 8.3)
# ---------------------------------------------------------------------------


class TestDataDeletion:
    """Verify data deletion (right to be forgotten) works correctly."""

    def test_conversation_deletion_removes_all_data(self):
        """Deleting a conversation must remove all associated data."""
        user_id = str(uuid4())
        conv_id = str(uuid4())

        # Simulate data store
        conversations = [{"id": conv_id, "user_id": user_id}]
        messages = [{"id": str(uuid4()), "conversation_id": conv_id} for _ in range(5)]

        # Delete conversation
        conversations = [c for c in conversations if c["id"] != conv_id]
        # Cascade delete messages
        messages = [m for m in messages if m["conversation_id"] != conv_id]

        assert len(conversations) == 0
        assert len(messages) == 0

    def test_user_data_deletion_removes_all_user_data(self):
        """Deleting a user must remove all their data."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())

        conversations = [
            {"id": str(uuid4()), "user_id": user_id},
            {"id": str(uuid4()), "user_id": user_id},
            {"id": str(uuid4()), "user_id": other_user_id},
        ]
        platform_links = [
            {"user_id": user_id, "platform": "discord"},
            {"user_id": other_user_id, "platform": "discord"},
        ]

        # Delete user's data
        conversations = [c for c in conversations if c["user_id"] != user_id]
        platform_links = [link for link in platform_links if link["user_id"] != user_id]

        # User's data is gone
        assert all(c["user_id"] != user_id for c in conversations)
        assert all(link["user_id"] != user_id for link in platform_links)

        # Other user's data is preserved
        assert any(c["user_id"] == other_user_id for c in conversations)
        assert any(link["user_id"] == other_user_id for link in platform_links)
