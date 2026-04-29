"""Mixin from app/qa_agent/security_manager.py."""
import logging
import secrets
from typing import Dict, List, Optional
from uuid import UUID

from app.qa_agent.database import get_db_connection

logger = logging.getLogger(__name__)


class SecureDeleteMixin:
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
