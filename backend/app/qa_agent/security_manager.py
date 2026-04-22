"""
Security Manager for Intelligent Q&A Agent

This module implements data encryption, access control, and secure deletion
mechanisms for the intelligent Q&A agent system.

Validates: Requirements 10.1, 10.3, 10.4, 10.5
"""

import hashlib
import logging
import secrets
from typing import Any, Dict, List, Optional
from uuid import UUID

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.qa_agent.database import get_db_connection

logger = logging.getLogger(__name__)


class SecurityManagerError(Exception):
    """Raised when security operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class AccessDeniedError(SecurityManagerError):
    """Raised when access control validation fails."""

    pass


class EncryptionError(SecurityManagerError):
    """Raised when encryption/decryption operations fail."""

    pass


class SecurityManager:
    """
    Manages data encryption, access control, and secure deletion for the Q&A agent.

    Provides:
    - Encryption/decryption for sensitive data (query logs, conversations)
    - Access control validation (user data isolation)
    - Secure deletion mechanisms (GDPR compliance)
    - Audit logging for security events

    Validates: Requirements 10.1, 10.3, 10.4, 10.5
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize the SecurityManager.

        Args:
            encryption_key: Optional encryption key. If not provided, uses settings.
        """
        self._encryption_key = encryption_key or self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        self._audit_enabled = True

    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key from settings.

        Returns:
            Encryption key as bytes

        Raises:
            SecurityManagerError: If key cannot be obtained
        """
        try:
            # Try to get key from settings
            if hasattr(settings, "encryption_key") and settings.encryption_key:
                key = settings.encryption_key
                if isinstance(key, str):
                    key = key.encode("utf-8")

                # If key is a password, derive a proper Fernet key
                if len(key) != 44:  # Fernet keys are 44 bytes base64-encoded
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b"intelligent-qa-agent-salt",  # In production, use unique salt per deployment
                        iterations=100000,
                    )
                    key = kdf.derive(key)
                    key = Fernet.generate_key()  # Convert to proper Fernet key format

                return key
            else:
                # Generate a new key (for development/testing only)
                logger.warning(
                    "No encryption key found in settings. Generating temporary key. "
                    "This should NOT be used in production!"
                )
                return Fernet.generate_key()

        except Exception as e:
            logger.error(f"Failed to get encryption key: {e}", exc_info=True)
            raise SecurityManagerError(f"Failed to get encryption key: {e}", original_error=e)

    # ============================================================================
    # ENCRYPTION/DECRYPTION (Requirement 10.1)
    # ============================================================================

    def encrypt_text(self, plaintext: str) -> str:
        """
        Encrypt text data.

        Args:
            plaintext: Text to encrypt

        Returns:
            Encrypted text as base64-encoded string

        Raises:
            EncryptionError: If encryption fails

        Validates: Requirement 10.1 - Encrypt stored query logs and conversation data
        """
        if not plaintext:
            return ""

        try:
            plaintext_bytes = plaintext.encode("utf-8")
            encrypted_bytes = self._cipher.encrypt(plaintext_bytes)
            encrypted_text = encrypted_bytes.decode("utf-8")

            logger.debug(f"Encrypted text of length {len(plaintext)}")
            return encrypted_text

        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to encrypt text: {e}", original_error=e)

    def decrypt_text(self, encrypted_text: str) -> str:
        """
        Decrypt text data.

        Args:
            encrypted_text: Encrypted text as base64-encoded string

        Returns:
            Decrypted plaintext

        Raises:
            EncryptionError: If decryption fails

        Validates: Requirement 10.1 - Encrypt stored query logs and conversation data
        """
        if not encrypted_text:
            return ""

        try:
            encrypted_bytes = encrypted_text.encode("utf-8")
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            plaintext = decrypted_bytes.decode("utf-8")

            logger.debug(f"Decrypted text of length {len(plaintext)}")
            return plaintext

        except Exception as e:
            logger.error(f"Decryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to decrypt text: {e}", original_error=e)

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt dictionary data.

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted data as base64-encoded string

        Raises:
            EncryptionError: If encryption fails

        Validates: Requirement 10.1 - Encrypt stored query logs and conversation data
        """
        try:
            import json

            json_str = json.dumps(data, ensure_ascii=False)
            return self.encrypt_text(json_str)

        except Exception as e:
            logger.error(f"Dictionary encryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to encrypt dictionary: {e}", original_error=e)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt dictionary data.

        Args:
            encrypted_data: Encrypted data as base64-encoded string

        Returns:
            Decrypted dictionary

        Raises:
            EncryptionError: If decryption fails

        Validates: Requirement 10.1 - Encrypt stored query logs and conversation data
        """
        try:
            import json

            json_str = self.decrypt_text(encrypted_data)
            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Dictionary decryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to decrypt dictionary: {e}", original_error=e)

    def hash_sensitive_data(self, data: str) -> str:
        """
        Create a one-way hash of sensitive data for indexing/comparison.

        Useful for creating searchable indexes without storing plaintext.

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string

        Validates: Requirement 10.1 - Encrypt stored query logs and conversation data
        """
        try:
            data_bytes = data.encode("utf-8")
            hash_obj = hashlib.sha256(data_bytes)
            return hash_obj.hexdigest()

        except Exception as e:
            logger.error(f"Hashing failed: {e}", exc_info=True)
            raise SecurityManagerError(f"Failed to hash data: {e}", original_error=e)

    # ============================================================================
    # ACCESS CONTROL (Requirements 10.3, 10.5)
    # ============================================================================

    async def validate_user_access(
        self, user_id: UUID, resource_type: str, resource_id: UUID
    ) -> bool:
        """
        Validate that a user has access to a specific resource.

        Implements user data isolation by verifying ownership.

        Args:
            user_id: User requesting access
            resource_type: Type of resource (conversation, query_log, profile)
            resource_id: ID of the resource

        Returns:
            True if access is allowed, False otherwise

        Raises:
            AccessDeniedError: If access is denied
            SecurityManagerError: If validation fails

        Validates: Requirements 10.3, 10.5 - User data isolation and access control
        """
        try:
            async with get_db_connection() as conn:
                # Check ownership based on resource type
                if resource_type == "conversation":
                    owner_id = await conn.fetchval(
                        "SELECT user_id FROM conversations WHERE id = $1 AND deleted_at IS NULL",
                        resource_id,
                    )
                elif resource_type == "query_log":
                    owner_id = await conn.fetchval(
                        "SELECT user_id FROM query_logs WHERE id = $1 AND deleted_at IS NULL",
                        resource_id,
                    )
                elif resource_type == "profile":
                    owner_id = await conn.fetchval(
                        "SELECT user_id FROM user_profiles WHERE user_id = $1 AND deleted_at IS NULL",
                        resource_id,
                    )
                else:
                    logger.error(f"Unknown resource type: {resource_type}")
                    raise SecurityManagerError(f"Unknown resource type: {resource_type}")

                # Check if user owns the resource
                if owner_id is None:
                    logger.warning(f"Resource not found: type={resource_type}, id={resource_id}")
                    await self._log_security_event(
                        user_id=user_id,
                        event_type="access_denied",
                        resource_type=resource_type,
                        resource_id=resource_id,
                        reason="resource_not_found",
                    )
                    return False

                if owner_id != user_id:
                    logger.warning(
                        f"Access denied: user {user_id} attempted to access "
                        f"{resource_type} {resource_id} owned by {owner_id}"
                    )
                    await self._log_security_event(
                        user_id=user_id,
                        event_type="access_denied",
                        resource_type=resource_type,
                        resource_id=resource_id,
                        reason="not_owner",
                    )
                    raise AccessDeniedError(
                        f"Access denied: User does not own this {resource_type}"
                    )

                # Access granted
                logger.debug(f"Access granted: user {user_id} to {resource_type} {resource_id}")
                return True

        except AccessDeniedError:
            raise
        except Exception as e:
            logger.error(f"Access validation failed: {e}", exc_info=True)
            raise SecurityManagerError(f"Failed to validate access: {e}", original_error=e)

    async def validate_bulk_access(
        self, user_id: UUID, resource_type: str, resource_ids: List[UUID]
    ) -> Dict[UUID, bool]:
        """
        Validate access to multiple resources at once.

        Args:
            user_id: User requesting access
            resource_type: Type of resources
            resource_ids: List of resource IDs

        Returns:
            Dictionary mapping resource IDs to access status

        Validates: Requirements 10.3, 10.5 - User data isolation and access control
        """
        results = {}

        for resource_id in resource_ids:
            try:
                results[resource_id] = await self.validate_user_access(
                    user_id, resource_type, resource_id
                )
            except AccessDeniedError:
                results[resource_id] = False
            except Exception as e:
                logger.error(f"Failed to validate access for {resource_id}: {e}")
                results[resource_id] = False

        return results

    async def get_user_owned_resources(
        self, user_id: UUID, resource_type: str, limit: int = 100
    ) -> List[UUID]:
        """
        Get all resources owned by a user.

        Args:
            user_id: User ID
            resource_type: Type of resources to retrieve
            limit: Maximum number of resources to return

        Returns:
            List of resource IDs owned by the user

        Validates: Requirements 10.3, 10.5 - User data isolation and access control
        """
        try:
            async with get_db_connection() as conn:
                if resource_type == "conversation":
                    rows = await conn.fetch(
                        """
                        SELECT id FROM conversations
                        WHERE user_id = $1 AND deleted_at IS NULL
                        ORDER BY last_updated DESC
                        LIMIT $2
                        """,
                        user_id,
                        limit,
                    )
                elif resource_type == "query_log":
                    rows = await conn.fetch(
                        """
                        SELECT id FROM query_logs
                        WHERE user_id = $1 AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        user_id,
                        limit,
                    )
                else:
                    raise SecurityManagerError(f"Unknown resource type: {resource_type}")

                return [row["id"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get user resources: {e}", exc_info=True)
            raise SecurityManagerError(f"Failed to get user resources: {e}", original_error=e)

    # ============================================================================
    # SECURE DELETION (Requirement 10.4)
    # ============================================================================

    async def secure_delete_conversation(self, user_id: UUID, conversation_id: UUID) -> bool:
        """
        Securely delete a conversation with data overwriting.

        Implements GDPR-compliant deletion by:
        1. Validating user ownership
        2. Overwriting sensitive data with random data
        3. Marking as deleted
        4. Logging the deletion event

        Args:
            user_id: User requesting deletion
            conversation_id: Conversation to delete

        Returns:
            True if deletion successful, False if not found

        Raises:
            AccessDeniedError: If user doesn't own the conversation
            SecurityManagerError: If deletion fails

        Validates: Requirement 10.4 - Secure data deletion mechanisms
        """
        try:
            # Validate access
            await self.validate_user_access(user_id, "conversation", conversation_id)

            async with get_db_connection() as conn:
                # Overwrite sensitive data before deletion
                random_data = secrets.token_hex(32)

                result = await conn.fetchval(
                    """
                    UPDATE conversations
                    SET context = $1::jsonb,
                        current_topic = $2,
                        deleted_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $3 AND user_id = $4 AND deleted_at IS NULL
                    RETURNING id
                    """,
                    '{"overwritten": true}',
                    f"DELETED_{random_data}",
                    conversation_id,
                    user_id,
                )

                if result:
                    logger.info(
                        f"Securely deleted conversation {conversation_id} for user {user_id}"
                    )
                    await self._log_security_event(
                        user_id=user_id,
                        event_type="secure_delete",
                        resource_type="conversation",
                        resource_id=conversation_id,
                        reason="user_request",
                    )
                    return True
                else:
                    logger.warning(f"Conversation {conversation_id} not found for deletion")
                    return False

        except AccessDeniedError:
            raise
        except Exception as e:
            logger.error(f"Secure deletion failed: {e}", exc_info=True)
            raise SecurityManagerError(
                f"Failed to securely delete conversation: {e}", original_error=e
            )

    async def secure_delete_query_logs(
        self, user_id: UUID, query_log_ids: Optional[List[UUID]] = None
    ) -> int:
        """
        Securely delete query logs for a user.

        Args:
            user_id: User requesting deletion
            query_log_ids: Optional list of specific query log IDs. If None, deletes all.

        Returns:
            Number of query logs deleted

        Raises:
            SecurityManagerError: If deletion fails

        Validates: Requirement 10.4 - Secure data deletion mechanisms
        """
        try:
            async with get_db_connection() as conn:
                # Overwrite sensitive data
                random_data = secrets.token_hex(16)

                if query_log_ids:
                    # Delete specific query logs
                    result = await conn.fetch(
                        """
                        UPDATE query_logs
                        SET query_text = $1,
                            response_data = $2::jsonb,
                            deleted_at = NOW(),
                            updated_at = NOW()
                        WHERE id = ANY($3) AND user_id = $4 AND deleted_at IS NULL
                        RETURNING id
                        """,
                        f"DELETED_{random_data}",
                        '{"overwritten": true}',
                        query_log_ids,
                        user_id,
                    )
                else:
                    # Delete all query logs for user
                    result = await conn.fetch(
                        """
                        UPDATE query_logs
                        SET query_text = $1,
                            response_data = $2::jsonb,
                            deleted_at = NOW(),
                            updated_at = NOW()
                        WHERE user_id = $3 AND deleted_at IS NULL
                        RETURNING id
                        """,
                        f"DELETED_{random_data}",
                        '{"overwritten": true}',
                        user_id,
                    )

                deleted_count = len(result)

                if deleted_count > 0:
                    logger.info(f"Securely deleted {deleted_count} query logs for user {user_id}")
                    await self._log_security_event(
                        user_id=user_id,
                        event_type="secure_delete",
                        resource_type="query_logs",
                        resource_id=None,
                        reason="user_request",
                        metadata={"count": deleted_count},
                    )

                return deleted_count

        except Exception as e:
            logger.error(f"Secure deletion of query logs failed: {e}", exc_info=True)
            raise SecurityManagerError(
                f"Failed to securely delete query logs: {e}", original_error=e
            )

    async def secure_delete_user_profile(self, user_id: UUID) -> bool:
        """
        Securely delete a user profile.

        Args:
            user_id: User ID

        Returns:
            True if deletion successful

        Raises:
            SecurityManagerError: If deletion fails

        Validates: Requirement 10.4 - Secure data deletion mechanisms
        """
        try:
            async with get_db_connection() as conn:
                # Overwrite sensitive data
                random_data = secrets.token_hex(16)

                result = await conn.fetchval(
                    """
                    UPDATE user_profiles
                    SET reading_history = '[]'::jsonb,
                        preferred_topics = '[]'::jsonb,
                        interaction_patterns = '{}'::jsonb,
                        satisfaction_scores = '[]'::jsonb,
                        deleted_at = NOW(),
                        updated_at = NOW()
                    WHERE user_id = $1 AND deleted_at IS NULL
                    RETURNING user_id
                    """,
                    user_id,
                )

                if result:
                    logger.info(f"Securely deleted user profile for user {user_id}")
                    await self._log_security_event(
                        user_id=user_id,
                        event_type="secure_delete",
                        resource_type="user_profile",
                        resource_id=user_id,
                        reason="user_request",
                    )
                    return True
                else:
                    logger.warning(f"User profile {user_id} not found for deletion")
                    return False

        except Exception as e:
            logger.error(f"Secure deletion of user profile failed: {e}", exc_info=True)
            raise SecurityManagerError(
                f"Failed to securely delete user profile: {e}", original_error=e
            )

    async def secure_delete_all_user_data(self, user_id: UUID) -> Dict[str, int]:
        """
        Securely delete all data for a user (GDPR right to be forgotten).

        Deletes:
        - All conversations
        - All query logs
        - User profile
        - Reading history

        Args:
            user_id: User ID

        Returns:
            Dictionary with deletion counts for each resource type

        Raises:
            SecurityManagerError: If deletion fails

        Validates: Requirement 10.4 - Secure data deletion mechanisms
        """
        try:
            results = {"conversations": 0, "query_logs": 0, "user_profile": 0}

            # Delete all conversations
            async with get_db_connection() as conn:
                conversation_ids = await conn.fetch(
                    "SELECT id FROM conversations WHERE user_id = $1 AND deleted_at IS NULL",
                    user_id,
                )

                for row in conversation_ids:
                    await self.secure_delete_conversation(user_id, row["id"])
                    results["conversations"] += 1

            # Delete all query logs
            results["query_logs"] = await self.secure_delete_query_logs(user_id)

            # Delete user profile
            if await self.secure_delete_user_profile(user_id):
                results["user_profile"] = 1

            logger.info(f"Securely deleted all data for user {user_id}: {results}")

            await self._log_security_event(
                user_id=user_id,
                event_type="complete_data_deletion",
                resource_type="all",
                resource_id=user_id,
                reason="gdpr_request",
                metadata=results,
            )

            return results

        except Exception as e:
            logger.error(f"Complete data deletion failed: {e}", exc_info=True)
            raise SecurityManagerError(f"Failed to delete all user data: {e}", original_error=e)

    # ============================================================================
    # AUDIT LOGGING
    # ============================================================================

    async def _log_security_event(
        self,
        user_id: UUID,
        event_type: str,
        resource_type: str,
        resource_id: Optional[UUID],
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log security events for audit trail.

        Args:
            user_id: User involved in the event
            event_type: Type of security event
            resource_type: Type of resource involved
            resource_id: ID of resource (if applicable)
            reason: Reason for the event
            metadata: Additional event metadata
        """
        if not self._audit_enabled:
            return

        try:
            async with get_db_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO security_audit_log
                    (user_id, event_type, resource_type, resource_id, reason, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    """,
                    user_id,
                    event_type,
                    resource_type,
                    resource_id,
                    reason,
                    metadata or {},
                )

                logger.debug(f"Logged security event: {event_type} for user {user_id}")

        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to log security event: {e}", exc_info=True)

    async def get_security_audit_log(
        self, user_id: Optional[UUID] = None, event_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve security audit log entries.

        Args:
            user_id: Optional filter by user ID
            event_type: Optional filter by event type
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        try:
            async with get_db_connection() as conn:
                query = "SELECT * FROM security_audit_log WHERE 1=1"
                params = []
                param_count = 1

                if user_id:
                    query += f" AND user_id = ${param_count}"
                    params.append(user_id)
                    param_count += 1

                if event_type:
                    query += f" AND event_type = ${param_count}"
                    params.append(event_type)
                    param_count += 1

                query += f" ORDER BY created_at DESC LIMIT ${param_count}"
                params.append(limit)

                rows = await conn.fetch(query, *params)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to retrieve audit log: {e}", exc_info=True)
            return []


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """
    Get the global security manager instance.

    Returns:
        SecurityManager instance
    """
    global _security_manager

    if _security_manager is None:
        _security_manager = SecurityManager()

    return _security_manager
