"""Mixin extracted from user_identity.py."""
from __future__ import annotations

import string
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class VerificationMixin:
    async def verify_platform_identity(
        self,
        platform: str,
        platform_user_id: str,
        verification_data: dict[str, Any],
    ) -> bool:
        """Verify a platform identity using platform-specific verification data.

        Currently validates that the ``platform_user_id`` matches the value
        stored in ``verification_data["platform_user_id"]`` and that an
        active link exists.  Additional platform-specific checks (e.g. OAuth
        token validation) can be added here in the future.

        Args:
            platform: External platform name.
            platform_user_id: User's identifier on the external platform.
            verification_data: Platform-specific data used for verification.
                Expected key: ``"platform_user_id"`` (must match
                ``platform_user_id`` argument).

        Returns:
            ``True`` if the identity is verified, ``False`` otherwise.

        Validates: Requirements 5.5
        """
        self.logger.info(
            "Verifying platform identity",
            platform=platform,
            platform_user_id=platform_user_id,
        )

        # Basic structural check: verification_data must contain a matching id
        provided_id = verification_data.get("platform_user_id")
        if provided_id != platform_user_id:
            self.logger.warning(
                "Platform identity verification failed: id mismatch",
                platform=platform,
                platform_user_id=platform_user_id,
                provided_id=provided_id,
            )
            return False

        # Confirm an active link exists in the database
        try:
            owner = await self.get_user_by_platform_id(platform, platform_user_id)
        except DatabaseError:
            self.logger.error(
                "Database error during platform identity verification",
                platform=platform,
                platform_user_id=platform_user_id,
            )
            return False

        verified = owner is not None
        self.logger.info(
            "Platform identity verification result",
            platform=platform,
            platform_user_id=platform_user_id,
            verified=verified,
        )
        return verified

    # ------------------------------------------------------------------
    # Verification code helpers
    # ------------------------------------------------------------------

    def generate_verification_code(self, user_id: str) -> str:
        """Generate a 6-digit verification code for a user.

        Replaces any previously active code for the same user.  The code
        expires after :data:`_VERIFICATION_CODE_TTL_MINUTES` minutes.

        Args:
            user_id: System user identifier.

        Returns:
            A 6-digit numeric string.

        Validates: Requirements 5.5
        """
        code = "".join(random.choices(string.digits, k=_VERIFICATION_CODE_LENGTH))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_VERIFICATION_CODE_TTL_MINUTES)
        self._verification_codes[user_id] = _VerificationEntry(
            code=code,
            expires_at=expires_at,
        )
        self.logger.info(
            "Verification code generated",
            user_id=user_id,
            expires_at=expires_at.isoformat(),
        )
        return code

    def validate_verification_code(self, user_id: str, code: str) -> bool:
        """Validate a verification code for a user.

        A code is valid if it matches the stored code and has not expired.
        Valid codes are consumed (deleted) on first use to prevent replay.

        Args:
            user_id: System user identifier.
            code: The 6-digit code to validate.

        Returns:
            ``True`` if the code is valid and not expired, ``False`` otherwise.

        Validates: Requirements 5.5
        """
        entry = self._verification_codes.get(user_id)
        if entry is None:
            self.logger.debug(
                "No verification code found for user",
                user_id=user_id,
            )
            return False

        now = datetime.now(timezone.utc)
        if now > entry.expires_at:
            # Clean up expired entry
            del self._verification_codes[user_id]
            self.logger.debug(
                "Verification code expired",
                user_id=user_id,
            )
            return False

        if entry.code != code:
            self.logger.debug(
                "Verification code mismatch",
                user_id=user_id,
            )
            return False

        # Consume the code (one-time use)
        del self._verification_codes[user_id]
        self.logger.info(
            "Verification code validated and consumed",
            user_id=user_id,
        )
        return True

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def get_audit_log(self) -> list[_AuditEntry]:
        """Return a copy of the in-memory audit log.

        Returns:
            List of :class:`_AuditEntry` objects in chronological order.
        """
        return list(self._audit_log)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _record_audit(
        self,
        *,
        action: str,
        user_id: str,
        platform: str,
        platform_user_id: str,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an entry to the in-memory audit log.

        Args:
            action: Operation type (``"link"``, ``"unlink"``, ``"verify"``).
            user_id: System user identifier.
            platform: Platform involved.
            platform_user_id: Platform-side user identifier.
            success: Whether the operation succeeded.
            details: Optional extra context.
        """
        entry = _AuditEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            success=success,
            details=details or {},
        )
        self._audit_log.append(entry)
        self.logger.debug(
            "Audit entry recorded",
            action=action,
            user_id=user_id,
            platform=platform,
            success=success,
        )
