"""
Security Utilities for Chat Persistence System

Provides:
  - AES-256-GCM symmetric encryption / decryption for conversation content
  - Access-log helpers that write to the ``security_audit_log`` table
  - API rate-limit helpers (in-process sliding-window counter)
  - Convenience wrappers used by the conversation API layer

The encryption key is derived from ``settings.jwt_secret`` using HKDF-SHA256
so no additional secret needs to be configured.  In production you can set a
dedicated ``ENCRYPTION_KEY`` environment variable (32 raw bytes, base64-encoded)
to use an independent key.

Validates: Requirements 8.1, 8.2, 8.5
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Encryption helpers (AES-256-GCM via cryptography library)
# ---------------------------------------------------------------------------

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False
    logger.warning(
        "cryptography package not installed — content encryption disabled. "
        "Install with: pip install cryptography"
    )


def _derive_encryption_key() -> bytes:
    """Derive a 32-byte AES-256 key from the application secret.

    Priority:
    1. ``ENCRYPTION_KEY`` env var (base64-encoded 32 bytes)
    2. HKDF-SHA256 derived from ``settings.jwt_secret``

    Returns:
        32-byte key suitable for AES-256-GCM.
    """
    raw_env = os.environ.get("ENCRYPTION_KEY", "")
    if raw_env:
        try:
            key = base64.b64decode(raw_env)
            if len(key) == 32:
                return key
        except Exception:
            pass
        logger.warning("ENCRYPTION_KEY env var is set but invalid — falling back to derived key")

    # Derive from jwt_secret via HKDF
    from app.core.config import settings

    if not _CRYPTO_AVAILABLE:
        # Fallback: SHA-256 of the secret (not as secure, but functional)
        return hashlib.sha256(settings.jwt_secret.encode()).digest()

    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=b"chat-persistence-v1",
        info=b"aes256-gcm-content-encryption",
    )
    return hkdf.derive(settings.jwt_secret.encode())


# Lazy-initialised key — derived once on first use
_encryption_key: Optional[bytes] = None


def _get_key() -> bytes:
    global _encryption_key
    if _encryption_key is None:
        _encryption_key = _derive_encryption_key()
    return _encryption_key


def encrypt_content(plaintext: str) -> str:
    """Encrypt a string using AES-256-GCM.

    The output is a base64-encoded string in the format::

        <base64(nonce)>.<base64(ciphertext+tag)>

    Args:
        plaintext: UTF-8 string to encrypt.

    Returns:
        Encrypted string (base64 encoded, dot-separated nonce + ciphertext).
        Returns the original plaintext unchanged if the ``cryptography``
        package is not installed.
    """
    if not _CRYPTO_AVAILABLE:
        return plaintext  # Graceful degradation

    key = _get_key()
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    encoded = base64.b64encode(nonce).decode() + "." + base64.b64encode(ciphertext).decode()
    return encoded


def decrypt_content(encrypted: str) -> str:
    """Decrypt a string previously encrypted with :func:`encrypt_content`.

    Args:
        encrypted: Encrypted string in ``<nonce>.<ciphertext>`` format.

    Returns:
        Decrypted UTF-8 string.

    Raises:
        ValueError: If the encrypted string is malformed or decryption fails.
    """
    if not _CRYPTO_AVAILABLE:
        return encrypted  # Graceful degradation

    try:
        nonce_b64, ct_b64 = encrypted.split(".", 1)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ct_b64)
    except (ValueError, Exception) as exc:
        raise ValueError(f"Malformed encrypted content: {exc}") from exc

    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode("utf-8")
    except Exception as exc:
        raise ValueError(f"Decryption failed: {exc}") from exc


def is_encrypted(value: str) -> bool:
    """Return ``True`` if *value* looks like output from :func:`encrypt_content`.

    Uses a simple heuristic: the string contains exactly one ``.`` and both
    parts are valid base64.

    Args:
        value: String to test.

    Returns:
        ``True`` if the value appears to be encrypted.
    """
    if not _CRYPTO_AVAILABLE or "." not in value:
        return False
    parts = value.split(".", 1)
    if len(parts) != 2:
        return False
    try:
        base64.b64decode(parts[0])
        base64.b64decode(parts[1])
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Access / audit logging
# ---------------------------------------------------------------------------


@dataclass
class AuditEvent:
    """A single security audit event to be persisted.

    Attributes:
        user_id: UUID of the user who triggered the event.
        event_type: Short label, e.g. ``"access_denied"``, ``"data_export"``.
        resource_type: Type of resource, e.g. ``"conversation"``.
        resource_id: Optional UUID of the specific resource.
        reason: Human-readable reason for the event.
        metadata: Arbitrary extra context.
        ip_address: Optional client IP address.
        user_agent: Optional client user-agent string.
    """

    user_id: UUID
    event_type: str
    resource_type: str
    reason: str
    resource_id: Optional[UUID] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


async def log_security_event(client: Any, event: AuditEvent) -> None:
    """Persist a security audit event to the ``security_audit_log`` table.

    Failures are logged but never propagated — audit logging must not break
    the primary request flow.

    Args:
        client: Initialised Supabase ``Client`` instance.
        event: :class:`AuditEvent` to persist.
    """
    try:
        row: dict[str, Any] = {
            "user_id": str(event.user_id),
            "event_type": event.event_type,
            "resource_type": event.resource_type,
            "reason": event.reason,
            "metadata": event.metadata,
        }
        if event.resource_id is not None:
            row["resource_id"] = str(event.resource_id)
        if event.ip_address:
            row["ip_address"] = event.ip_address
        if event.user_agent:
            row["user_agent"] = event.user_agent

        client.table("security_audit_log").insert(row).execute()

        logger.info(
            "Security event logged",
            event_type=event.event_type,
            resource_type=event.resource_type,
            user_id=str(event.user_id),
        )
    except Exception as exc:
        logger.warning(
            "Failed to persist security audit event (non-fatal)",
            event_type=event.event_type,
            error=str(exc),
        )


async def log_access_denied(
    client: Any,
    user_id: UUID,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    reason: str = "Unauthorized access attempt",
    ip_address: Optional[str] = None,
) -> None:
    """Convenience wrapper for logging access-denied events.

    Args:
        client: Supabase client.
        user_id: UUID of the requesting user.
        resource_type: Type of resource that was denied.
        resource_id: Optional specific resource UUID.
        reason: Reason for denial.
        ip_address: Optional client IP.
    """
    await log_security_event(
        client,
        AuditEvent(
            user_id=user_id,
            event_type="access_denied",
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            ip_address=ip_address,
        ),
    )


async def log_data_deletion(
    client: Any,
    user_id: UUID,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Convenience wrapper for logging data-deletion events.

    Args:
        client: Supabase client.
        user_id: UUID of the user requesting deletion.
        resource_type: Type of resource deleted.
        resource_id: Optional specific resource UUID.
        metadata: Optional extra context (e.g. record counts).
    """
    await log_security_event(
        client,
        AuditEvent(
            user_id=user_id,
            event_type="data_deletion",
            resource_type=resource_type,
            resource_id=resource_id,
            reason="User-requested data deletion",
            metadata=metadata or {},
        ),
    )


# ---------------------------------------------------------------------------
# In-process rate limiter (sliding-window counter)
# ---------------------------------------------------------------------------


@dataclass
class _WindowEntry:
    """Internal state for one rate-limit window."""

    count: int = 0
    window_start: float = field(default_factory=time.monotonic)


class RateLimiter:
    """Simple in-process sliding-window rate limiter.

    Suitable for single-process deployments.  For multi-process / distributed
    deployments replace with a Redis-backed implementation.

    Args:
        max_requests: Maximum requests allowed per window.
        window_seconds: Duration of the sliding window in seconds.

    Example::

        limiter = RateLimiter(max_requests=60, window_seconds=60)
        if not limiter.is_allowed("user-uuid"):
            raise RateLimitError("Too many requests")
    """

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, _WindowEntry] = defaultdict(_WindowEntry)

    def is_allowed(self, key: str) -> bool:
        """Check whether *key* is within the rate limit and increment counter.

        Args:
            key: Unique identifier for the rate-limit subject (e.g. user ID,
                IP address).

        Returns:
            ``True`` if the request is allowed, ``False`` if the limit is
            exceeded.
        """
        now = time.monotonic()
        entry = self._windows[key]

        # Reset window if expired
        if now - entry.window_start >= self.window_seconds:
            entry.count = 0
            entry.window_start = now

        if entry.count >= self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                key=key,
                count=entry.count,
                max_requests=self.max_requests,
                window_seconds=self.window_seconds,
            )
            return False

        entry.count += 1
        return True

    def remaining(self, key: str) -> int:
        """Return the number of remaining requests in the current window.

        Args:
            key: Rate-limit subject identifier.

        Returns:
            Remaining request count (0 if limit exceeded).
        """
        now = time.monotonic()
        entry = self._windows.get(key)
        if entry is None:
            return self.max_requests
        if now - entry.window_start >= self.window_seconds:
            return self.max_requests
        return max(0, self.max_requests - entry.count)

    def reset(self, key: str) -> None:
        """Reset the rate-limit counter for *key*.

        Args:
            key: Rate-limit subject identifier.
        """
        self._windows.pop(key, None)


# ---------------------------------------------------------------------------
# Pre-built rate limiter instances
# ---------------------------------------------------------------------------

#: Default limiter for authenticated conversation API endpoints.
conversation_api_limiter = RateLimiter(max_requests=120, window_seconds=60)

#: Stricter limiter for LLM-backed smart-conversation endpoints.
smart_conversation_limiter = RateLimiter(max_requests=20, window_seconds=60)

#: Limiter for unauthenticated / public endpoints.
public_api_limiter = RateLimiter(max_requests=30, window_seconds=60)


# ---------------------------------------------------------------------------
# Integrity helpers
# ---------------------------------------------------------------------------


def compute_content_hash(content: str) -> str:
    """Compute a SHA-256 hex digest of *content* for integrity verification.

    Args:
        content: String to hash.

    Returns:
        Lowercase hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_content_integrity(content: str, expected_hash: str) -> bool:
    """Verify that *content* matches *expected_hash*.

    Uses ``hmac.compare_digest`` to prevent timing attacks.

    Args:
        content: String to verify.
        expected_hash: Previously computed SHA-256 hex digest.

    Returns:
        ``True`` if the content matches the hash.
    """
    actual = compute_content_hash(content)
    return hmac.compare_digest(actual, expected_hash)
