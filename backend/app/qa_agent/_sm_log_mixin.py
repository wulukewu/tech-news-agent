"""Mixin from app/qa_agent/security_manager.py."""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.qa_agent.database import get_db_connection

logger = logging.getLogger(__name__)


class SecurityLogMixin:
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
