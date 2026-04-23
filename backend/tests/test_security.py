"""
Unit tests for security module

Tests encryption, audit logging, rate limiting, and integrity verification.

Validates: Requirements 8.1, 8.2, 8.5
"""

import base64
import time
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.security import (
    AuditEvent,
    RateLimiter,
    compute_content_hash,
    conversation_api_limiter,
    decrypt_content,
    encrypt_content,
    is_encrypted,
    log_access_denied,
    log_data_deletion,
    log_security_event,
    public_api_limiter,
    smart_conversation_limiter,
    verify_content_integrity,
)

# ============================================================================
# Encryption Tests
# ============================================================================


class TestEncryption:
    """Test AES-256-GCM encryption and decryption"""

    def test_encrypt_content_returns_base64_format(self):
        """Test that encrypted content is in base64 format with nonce.ciphertext structure"""
        plaintext = "Hello, World!"
        encrypted = encrypt_content(plaintext)

        # Should contain exactly one dot separator
        assert encrypted.count(".") == 1

        # Both parts should be valid base64
        nonce_b64, ct_b64 = encrypted.split(".")
        try:
            base64.b64decode(nonce_b64)
            base64.b64decode(ct_b64)
        except Exception as e:
            pytest.fail(f"Encrypted content is not valid base64: {e}")

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverse operations"""
        plaintext = "Sensitive conversation data 🔒"
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)

        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Test that encrypting the same plaintext produces different ciphertext (due to random nonce)"""
        plaintext = "Same message"
        encrypted1 = encrypt_content(plaintext)
        encrypted2 = encrypt_content(plaintext)

        # Different ciphertext due to random nonce
        assert encrypted1 != encrypted2

        # But both decrypt to the same plaintext
        assert decrypt_content(encrypted1) == plaintext
        assert decrypt_content(encrypted2) == plaintext

    def test_encrypt_empty_string(self):
        """Test encryption of empty string"""
        plaintext = ""
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)

        assert decrypted == plaintext

    def test_encrypt_unicode_content(self):
        """Test encryption of unicode content"""
        plaintext = "你好世界 🌍 مرحبا بالعالم"
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_content(self):
        """Test encryption of long content"""
        plaintext = "A" * 10000  # 10KB of data
        encrypted = encrypt_content(plaintext)
        decrypted = decrypt_content(encrypted)

        assert decrypted == plaintext

    def test_decrypt_invalid_format_raises_error(self):
        """Test that decrypting invalid format raises ValueError"""
        with pytest.raises(ValueError, match="Malformed encrypted content"):
            decrypt_content("invalid-format-no-dot")

    def test_decrypt_invalid_base64_raises_error(self):
        """Test that decrypting invalid base64 raises ValueError"""
        with pytest.raises(ValueError, match="Malformed encrypted content"):
            decrypt_content("not-base64.also-not-base64")

    def test_decrypt_tampered_ciphertext_raises_error(self):
        """Test that decrypting tampered ciphertext raises ValueError"""
        plaintext = "Original message"
        encrypted = encrypt_content(plaintext)

        # Tamper with the ciphertext
        nonce_b64, ct_b64 = encrypted.split(".")
        tampered_ct = base64.b64encode(b"tampered" + base64.b64decode(ct_b64)).decode()
        tampered = f"{nonce_b64}.{tampered_ct}"

        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_content(tampered)

    def test_is_encrypted_detects_encrypted_content(self):
        """Test that is_encrypted correctly identifies encrypted content"""
        plaintext = "Test message"
        encrypted = encrypt_content(plaintext)

        assert is_encrypted(encrypted) is True

    def test_is_encrypted_rejects_plaintext(self):
        """Test that is_encrypted correctly rejects plaintext"""
        plaintext = "Not encrypted"

        assert is_encrypted(plaintext) is False

    def test_is_encrypted_rejects_invalid_format(self):
        """Test that is_encrypted rejects invalid formats"""
        assert is_encrypted("no-dot-separator") is False
        assert is_encrypted("too.many.dots") is False
        assert is_encrypted("not-base64.also-not") is False


# ============================================================================
# Audit Logging Tests
# ============================================================================


class TestAuditLogging:
    """Test security audit logging functionality"""

    @pytest.mark.asyncio
    async def test_log_security_event_success(self):
        """Test successful security event logging"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        user_id = uuid4()
        event = AuditEvent(
            user_id=user_id,
            event_type="access_denied",
            resource_type="conversation",
            resource_id=uuid4(),
            reason="Unauthorized access attempt",
            metadata={"ip": "192.168.1.1"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        await log_security_event(mock_client, event)

        # Verify table was called
        mock_client.table.assert_called_once_with("security_audit_log")

        # Verify insert was called with correct data
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["user_id"] == str(user_id)
        assert insert_call_args["event_type"] == "access_denied"
        assert insert_call_args["resource_type"] == "conversation"
        assert insert_call_args["reason"] == "Unauthorized access attempt"
        assert insert_call_args["ip_address"] == "192.168.1.1"
        assert insert_call_args["user_agent"] == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_log_security_event_handles_failure_gracefully(self):
        """Test that audit logging failures don't propagate exceptions"""
        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("Database error")

        user_id = uuid4()
        event = AuditEvent(
            user_id=user_id,
            event_type="data_deletion",
            resource_type="conversation",
            reason="User requested deletion",
        )

        # Should not raise exception
        await log_security_event(mock_client, event)

    @pytest.mark.asyncio
    async def test_log_access_denied_convenience_wrapper(self):
        """Test log_access_denied convenience function"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        user_id = uuid4()
        resource_id = uuid4()

        await log_access_denied(
            mock_client,
            user_id=user_id,
            resource_type="conversation",
            resource_id=resource_id,
            reason="Insufficient permissions",
            ip_address="10.0.0.1",
        )

        # Verify correct event type was logged
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["event_type"] == "access_denied"
        assert insert_call_args["user_id"] == str(user_id)
        assert insert_call_args["resource_id"] == str(resource_id)

    @pytest.mark.asyncio
    async def test_log_data_deletion_convenience_wrapper(self):
        """Test log_data_deletion convenience function"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        user_id = uuid4()
        resource_id = uuid4()

        await log_data_deletion(
            mock_client,
            user_id=user_id,
            resource_type="conversation",
            resource_id=resource_id,
            metadata={"message_count": 42},
        )

        # Verify correct event type was logged
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["event_type"] == "data_deletion"
        assert insert_call_args["metadata"]["message_count"] == 42


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within the limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        key = "user-123"

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed(key) is True

    def test_rate_limiter_blocks_requests_exceeding_limit(self):
        """Test that rate limiter blocks requests exceeding the limit"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        key = "user-456"

        # First 3 requests allowed
        for i in range(3):
            assert limiter.is_allowed(key) is True

        # 4th request should be blocked
        assert limiter.is_allowed(key) is False

    def test_rate_limiter_resets_after_window_expires(self):
        """Test that rate limiter resets after the time window expires"""
        limiter = RateLimiter(max_requests=2, window_seconds=0.1)  # 100ms window
        key = "user-789"

        # Use up the limit
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is False

        # Wait for window to expire
        time.sleep(0.15)

        # Should be allowed again
        assert limiter.is_allowed(key) is True

    def test_rate_limiter_tracks_different_keys_independently(self):
        """Test that rate limiter tracks different keys independently"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        key1 = "user-1"
        key2 = "user-2"

        # Use up limit for key1
        assert limiter.is_allowed(key1) is True
        assert limiter.is_allowed(key1) is True
        assert limiter.is_allowed(key1) is False

        # key2 should still be allowed
        assert limiter.is_allowed(key2) is True
        assert limiter.is_allowed(key2) is True

    def test_rate_limiter_remaining_count(self):
        """Test that remaining() returns correct count"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        key = "user-remaining"

        assert limiter.remaining(key) == 5

        limiter.is_allowed(key)
        assert limiter.remaining(key) == 4

        limiter.is_allowed(key)
        limiter.is_allowed(key)
        assert limiter.remaining(key) == 2

    def test_rate_limiter_reset(self):
        """Test that reset() clears the counter for a key"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        key = "user-reset"

        # Use up the limit
        limiter.is_allowed(key)
        limiter.is_allowed(key)
        assert limiter.is_allowed(key) is False

        # Reset the counter
        limiter.reset(key)

        # Should be allowed again
        assert limiter.is_allowed(key) is True

    def test_pre_built_limiters_exist(self):
        """Test that pre-built limiter instances are configured correctly"""
        # Conversation API limiter
        assert conversation_api_limiter.max_requests == 120
        assert conversation_api_limiter.window_seconds == 60

        # Smart conversation limiter (stricter)
        assert smart_conversation_limiter.max_requests == 20
        assert smart_conversation_limiter.window_seconds == 60

        # Public API limiter (most restrictive)
        assert public_api_limiter.max_requests == 30
        assert public_api_limiter.window_seconds == 60


# ============================================================================
# Content Integrity Tests
# ============================================================================


class TestContentIntegrity:
    """Test content integrity verification"""

    def test_compute_content_hash_produces_consistent_hash(self):
        """Test that computing hash of same content produces same result"""
        content = "Test content for hashing"

        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert hash1 == hash2

    def test_compute_content_hash_produces_different_hash_for_different_content(self):
        """Test that different content produces different hashes"""
        content1 = "Content A"
        content2 = "Content B"

        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)

        assert hash1 != hash2

    def test_compute_content_hash_returns_hex_string(self):
        """Test that hash is returned as lowercase hex string"""
        content = "Test"
        hash_value = compute_content_hash(content)

        # Should be 64 characters (SHA-256 hex)
        assert len(hash_value) == 64

        # Should be lowercase hex
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_verify_content_integrity_accepts_valid_hash(self):
        """Test that verification succeeds for valid hash"""
        content = "Original content"
        expected_hash = compute_content_hash(content)

        assert verify_content_integrity(content, expected_hash) is True

    def test_verify_content_integrity_rejects_invalid_hash(self):
        """Test that verification fails for invalid hash"""
        content = "Original content"
        wrong_hash = compute_content_hash("Different content")

        assert verify_content_integrity(content, wrong_hash) is False

    def test_verify_content_integrity_rejects_tampered_content(self):
        """Test that verification detects content tampering"""
        original_content = "Original message"
        expected_hash = compute_content_hash(original_content)

        tampered_content = "Tampered message"

        assert verify_content_integrity(tampered_content, expected_hash) is False

    def test_verify_content_integrity_handles_unicode(self):
        """Test that integrity verification works with unicode content"""
        content = "Unicode: 你好 🌍 مرحبا"
        expected_hash = compute_content_hash(content)

        assert verify_content_integrity(content, expected_hash) is True


# ============================================================================
# Integration Tests
# ============================================================================


class TestSecurityIntegration:
    """Integration tests for security features"""

    def test_encrypt_and_verify_integrity(self):
        """Test combining encryption with integrity verification"""
        plaintext = "Sensitive data"

        # Encrypt the content
        encrypted = encrypt_content(plaintext)

        # Compute hash of encrypted content
        encrypted_hash = compute_content_hash(encrypted)

        # Verify integrity
        assert verify_content_integrity(encrypted, encrypted_hash) is True

        # Decrypt
        decrypted = decrypt_content(encrypted)
        assert decrypted == plaintext

    @pytest.mark.asyncio
    async def test_rate_limiting_with_audit_logging(self):
        """Test rate limiting combined with audit logging"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        user_id = uuid4()
        key = str(user_id)

        # First 2 requests allowed
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is True

        # 3rd request blocked - log it
        if not limiter.is_allowed(key):
            await log_access_denied(
                mock_client,
                user_id=user_id,
                resource_type="api_endpoint",
                reason="Rate limit exceeded",
            )

        # Verify audit log was called
        mock_client.table.assert_called_once_with("security_audit_log")

    def test_multiple_encryption_operations_are_independent(self):
        """Test that multiple encryption operations don't interfere with each other"""
        messages = [
            "Message 1",
            "Message 2",
            "Message 3",
        ]

        # Encrypt all messages
        encrypted_messages = [encrypt_content(msg) for msg in messages]

        # All encrypted messages should be different
        assert len(set(encrypted_messages)) == len(encrypted_messages)

        # All should decrypt correctly
        decrypted_messages = [decrypt_content(enc) for enc in encrypted_messages]
        assert decrypted_messages == messages


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestSecurityEdgeCases:
    """Test edge cases and error handling"""

    def test_encrypt_special_characters(self):
        """Test encryption of special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        encrypted = encrypt_content(special_chars)
        decrypted = decrypt_content(encrypted)

        assert decrypted == special_chars

    def test_encrypt_newlines_and_tabs(self):
        """Test encryption of content with newlines and tabs"""
        content = "Line 1\nLine 2\tTabbed\r\nWindows newline"
        encrypted = encrypt_content(content)
        decrypted = decrypt_content(encrypted)

        assert decrypted == content

    def test_rate_limiter_with_zero_requests(self):
        """Test rate limiter with max_requests=0"""
        limiter = RateLimiter(max_requests=0, window_seconds=60)
        key = "user-zero"

        # Should immediately block
        assert limiter.is_allowed(key) is False

    def test_rate_limiter_remaining_for_unknown_key(self):
        """Test remaining() for a key that hasn't been used"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        key = "unknown-key"

        # Should return max_requests
        assert limiter.remaining(key) == 10

    def test_audit_event_with_minimal_fields(self):
        """Test creating audit event with only required fields"""
        user_id = uuid4()
        event = AuditEvent(
            user_id=user_id,
            event_type="test_event",
            resource_type="test_resource",
            reason="Test reason",
        )

        assert event.user_id == user_id
        assert event.event_type == "test_event"
        assert event.resource_id is None
        assert event.metadata == {}

    def test_compute_hash_of_empty_string(self):
        """Test computing hash of empty string"""
        hash_value = compute_content_hash("")

        # Should still produce a valid hash
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)
