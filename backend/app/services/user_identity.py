"""
User Identity Manager Service

Manages user identity linking between the system and external platforms
(e.g. Discord).  Provides secure account binding, unbinding, verification
code generation/validation, and audit logging.

Key capabilities:
- Link / unlink a platform account to a system user
- Generate and validate 6-digit verification codes (10-minute expiry)
- Look up a system user by their platform identity
- List all active platform links for a user
- Verify platform identity via verification data
- Audit log for all binding operations

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.errors import DatabaseError, ErrorCode
from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLATFORM_WEB = "web"
PLATFORM_DISCORD = "discord"
SUPPORTED_PLATFORMS = {PLATFORM_WEB, PLATFORM_DISCORD}

_VERIFICATION_CODE_LENGTH = 6
_VERIFICATION_CODE_TTL_MINUTES = 10


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class LinkResult:
    """Result of a platform account linking operation.

    Attributes:
        success: Whether the link was created successfully.
        user_id: System user identifier.
        platform: Platform that was linked (e.g. ``"discord"``).
        platform_user_id: The user's identifier on the external platform.
        error: Human-readable error message when ``success`` is ``False``.
    """

    success: bool
    user_id: str
    platform: str
    platform_user_id: str
    error: Optional[str] = None


@dataclass
class PlatformLink:
    """Represents an active or historical platform link for a user.

    Attributes:
        user_id: System user identifier.
        platform: External platform name.
        platform_user_id: User's identifier on the external platform.
        platform_username: Optional display name on the external platform.
        linked_at: UTC timestamp when the link was created.
        is_active: Whether the link is currently active.
    """

    user_id: str
    platform: str
    platform_user_id: str
    platform_username: Optional[str]
    linked_at: datetime
    is_active: bool


@dataclass
class _VerificationEntry:
    """Internal storage for a pending verification code.

    Attributes:
        code: The 6-digit verification code.
        expires_at: UTC timestamp after which the code is invalid.
    """

    code: str
    expires_at: datetime


@dataclass
class _AuditEntry:
    """A single audit log entry for an identity binding operation.

    Attributes:
        timestamp: UTC timestamp of the operation.
        action: Operation type (``"link"``, ``"unlink"``, ``"verify"``).
        user_id: System user identifier.
        platform: Platform involved.
        platform_user_id: Platform-side user identifier.
        success: Whether the operation succeeded.
        details: Optional extra context.
    """

    timestamp: datetime
    action: str
    user_id: str
    platform: str
    platform_user_id: str
    success: bool
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


from app.services._ui_verification_mixin import VerificationMixin


class UserIdentityManager(VerificationMixin):
    """Service for managing cross-platform user identity linking.

    Stores platform links in the ``user_platform_links`` Supabase table and
    keeps verification codes in memory (one active code per user at a time).

    The Supabase client is injected at construction time so the service can
    be tested without a live database.

    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    """

    def __init__(self, supabase_client: Any) -> None:
        """Initialise the service.

        Args:
            supabase_client: An initialised Supabase ``Client`` instance used
                for all database operations.
        """
        self._client = supabase_client

        # user_id -> _VerificationEntry (one active code per user)
        self._verification_codes: dict[str, _VerificationEntry] = {}

        # Audit log (in-memory; can be persisted to a table in the future)
        self._audit_log: list[_AuditEntry] = []

        self.logger = get_logger(f"{__name__}.UserIdentityManager")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def link_platform_account(
        self,
        user_id: str,
        platform: str,
        platform_user_id: str,
        verification_token: str,
    ) -> LinkResult:
        """Link an external platform account to a system user.

        Validates the verification token before creating the link.  If the
        platform account is already linked to *another* user the operation
        fails.  Re-linking the same account (e.g. after an unlink) is
        supported by reactivating the existing row.

        Args:
            user_id: System user identifier.
            platform: External platform name (``"web"`` or ``"discord"``).
            platform_user_id: User's identifier on the external platform.
            verification_token: 6-digit code previously generated by
                :meth:`generate_verification_code`.

        Returns:
            A :class:`LinkResult` describing the outcome.

        Validates: Requirements 5.1, 5.2, 5.5
        """
        self.logger.info(
            "Linking platform account",
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )

        # --- Validate platform ---
        if platform not in SUPPORTED_PLATFORMS:
            error_msg = f"Unsupported platform: {platform}"
            self.logger.warning(error_msg, user_id=user_id, platform=platform)
            self._record_audit(
                action="link",
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                success=False,
                details={"error": error_msg},
            )
            return LinkResult(
                success=False,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                error=error_msg,
            )

        # --- Validate verification token ---
        if not self.validate_verification_code(user_id, verification_token):
            error_msg = "Invalid or expired verification code"
            self.logger.warning(
                error_msg,
                user_id=user_id,
                platform=platform,
            )
            self._record_audit(
                action="link",
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                success=False,
                details={"error": error_msg},
            )
            return LinkResult(
                success=False,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                error=error_msg,
            )

        # --- Check if platform_user_id is already linked to a *different* user ---
        try:
            existing_owner = await self.get_user_by_platform_id(platform, platform_user_id)
        except Exception as exc:
            self.logger.error(
                "Database error while checking existing platform link",
                error=str(exc),
                platform=platform,
                platform_user_id=platform_user_id,
            )
            raise DatabaseError(
                "Failed to check existing platform link",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            )

        if existing_owner is not None and existing_owner != user_id:
            error_msg = f"Platform account {platform_user_id!r} is already linked to another user"
            self.logger.warning(
                error_msg,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                existing_owner=existing_owner,
            )
            self._record_audit(
                action="link",
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                success=False,
                details={"error": error_msg, "existing_owner": existing_owner},
            )
            return LinkResult(
                success=False,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                error=error_msg,
            )

        # --- Upsert the link row ---
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            row = {
                "user_id": user_id,
                "platform": platform,
                "platform_user_id": platform_user_id,
                "linked_at": now_iso,
                "is_active": True,
            }
            (
                self._client.table("user_platform_links")
                .upsert(row, on_conflict="user_id,platform")
                .execute()
            )
        except Exception as exc:
            self.logger.error(
                "Database error while creating platform link",
                error=str(exc),
                user_id=user_id,
                platform=platform,
            )
            self._record_audit(
                action="link",
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                success=False,
                details={"error": str(exc)},
            )
            raise DatabaseError(
                "Failed to create platform link",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            )

        self.logger.info(
            "Platform account linked successfully",
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )
        self._record_audit(
            action="link",
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            success=True,
        )
        return LinkResult(
            success=True,
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )

    async def unlink_platform_account(
        self,
        user_id: str,
        platform: str,
    ) -> bool:
        """Deactivate the link between a user and a platform.

        Sets ``is_active = False`` on the link row rather than deleting it,
        so that historical data is preserved (Requirement 5.4).

        Args:
            user_id: System user identifier.
            platform: External platform name.

        Returns:
            ``True`` if the link was deactivated, ``False`` if no active link
            was found.

        Validates: Requirements 5.4
        """
        self.logger.info(
            "Unlinking platform account",
            user_id=user_id,
            platform=platform,
        )

        try:
            response = (
                self._client.table("user_platform_links")
                .update({"is_active": False})
                .eq("user_id", user_id)
                .eq("platform", platform)
                .eq("is_active", True)
                .execute()
            )
        except Exception as exc:
            self.logger.error(
                "Database error while unlinking platform account",
                error=str(exc),
                user_id=user_id,
                platform=platform,
            )
            raise DatabaseError(
                "Failed to unlink platform account",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            )

        rows_affected = len(response.data) if response.data else 0
        success = rows_affected > 0

        if success:
            self.logger.info(
                "Platform account unlinked",
                user_id=user_id,
                platform=platform,
            )
        else:
            self.logger.warning(
                "No active link found to unlink",
                user_id=user_id,
                platform=platform,
            )

        self._record_audit(
            action="unlink",
            user_id=user_id,
            platform=platform,
            platform_user_id="",
            success=success,
        )
        return success

    async def get_user_by_platform_id(
        self,
        platform: str,
        platform_user_id: str,
    ) -> Optional[str]:
        """Return the system ``user_id`` for a given platform identity.

        Args:
            platform: External platform name.
            platform_user_id: User's identifier on the external platform.

        Returns:
            The system ``user_id`` string, or ``None`` if no active link
            exists.

        Validates: Requirements 5.3
        """
        self.logger.debug(
            "Looking up user by platform identity",
            platform=platform,
            platform_user_id=platform_user_id,
        )

        try:
            response = (
                self._client.table("user_platform_links")
                .select("user_id")
                .eq("platform", platform)
                .eq("platform_user_id", platform_user_id)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            self.logger.error(
                "Database error while looking up user by platform id",
                error=str(exc),
                platform=platform,
                platform_user_id=platform_user_id,
            )
            raise DatabaseError(
                "Failed to look up user by platform identity",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            )

        if response.data:
            user_id: str = response.data[0]["user_id"]
            self.logger.debug(
                "Found user for platform identity",
                platform=platform,
                platform_user_id=platform_user_id,
                user_id=user_id,
            )
            return user_id

        self.logger.debug(
            "No user found for platform identity",
            platform=platform,
            platform_user_id=platform_user_id,
        )
        return None

    async def get_linked_platforms(
        self,
        user_id: str,
    ) -> list[PlatformLink]:
        """Return all active platform links for a user.

        Args:
            user_id: System user identifier.

        Returns:
            A list of :class:`PlatformLink` objects (may be empty).

        Validates: Requirements 5.3
        """
        self.logger.debug("Fetching linked platforms", user_id=user_id)

        try:
            response = (
                self._client.table("user_platform_links")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .execute()
            )
        except Exception as exc:
            self.logger.error(
                "Database error while fetching linked platforms",
                error=str(exc),
                user_id=user_id,
            )
            raise DatabaseError(
                "Failed to fetch linked platforms",
                error_code=ErrorCode.DB_QUERY_FAILED,
                original_error=exc,
            )

        links: list[PlatformLink] = []
        for row in response.data or []:
            linked_at_raw = row.get("linked_at")
            if isinstance(linked_at_raw, str):
                try:
                    linked_at = datetime.fromisoformat(linked_at_raw.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    linked_at = datetime.now(timezone.utc)
            elif isinstance(linked_at_raw, datetime):
                linked_at = linked_at_raw
            else:
                linked_at = datetime.now(timezone.utc)

            links.append(
                PlatformLink(
                    user_id=row["user_id"],
                    platform=row["platform"],
                    platform_user_id=row["platform_user_id"],
                    platform_username=row.get("platform_username"),
                    linked_at=linked_at,
                    is_active=row.get("is_active", True),
                )
            )

        self.logger.debug(
            "Fetched linked platforms",
            user_id=user_id,
            count=len(links),
        )
        return links
