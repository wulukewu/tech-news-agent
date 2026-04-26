"""
Platform Linking API Router

Provides REST endpoints for managing user platform account bindings.

Endpoints:
  POST   /api/user/platforms              - Link a platform account
  GET    /api/user/platforms              - Get user's platform links
  DELETE /api/user/platforms/{platform}   - Unlink a platform account
  POST   /api/conversations/{id}/sync     - Manually trigger conversation sync
  POST   /api/user/platforms/initiate     - Generate a verification code

Validates: Requirements 5.1, 5.2, 5.4, 2.1
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.core.errors import DatabaseError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.schemas.responses import SuccessResponse, success_response
from app.services.cross_platform_sync import CrossPlatformSyncService
from app.services.discord_auth import DiscordAuthService
from app.services.supabase_service import SupabaseService
from app.services.user_identity import UserIdentityManager

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_supabase() -> SupabaseService:
    return SupabaseService(validate_connection=False)


def _get_identity_manager(svc: SupabaseService = Depends(_get_supabase)) -> UserIdentityManager:
    return UserIdentityManager(supabase_client=svc.client)


def _get_discord_auth(
    identity_manager: UserIdentityManager = Depends(_get_identity_manager),
) -> DiscordAuthService:
    return DiscordAuthService(identity_manager=identity_manager)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class LinkPlatformRequest(BaseModel):
    platform: str = Field(..., description="Platform name: 'discord'")
    platform_user_id: str = Field(..., description="User ID on the external platform")
    verification_token: str = Field(..., description="6-digit verification code")
    platform_username: Optional[str] = Field(None, description="Display name on the platform")


class PlatformLinkOut(BaseModel):
    user_id: str
    platform: str
    platform_user_id: str
    platform_username: Optional[str] = None
    linked_at: str
    is_active: bool


class InitiateLinkResponse(BaseModel):
    verification_code: str
    expires_in_minutes: int = 10
    instructions: str


# ---------------------------------------------------------------------------
# POST /api/user/platforms/initiate
# ---------------------------------------------------------------------------


@router.post(
    "/initiate",
    response_model=SuccessResponse[InitiateLinkResponse],
    summary="Generate a verification code for platform linking",
)
async def initiate_platform_link(
    current_user: dict = Depends(get_current_user),
    discord_auth: DiscordAuthService = Depends(_get_discord_auth),
):
    """
    Generate a 6-digit verification code that the user can submit via the
    Discord /link command to bind their Discord account.
    """
    user_id = str(current_user["user_id"])
    code = discord_auth.initiate_discord_link(user_id)
    return success_response(
        InitiateLinkResponse(
            verification_code=code,
            expires_in_minutes=10,
            instructions=(
                f"Use the Discord command: /link {code}\n" "The code expires in 10 minutes."
            ),
        )
    )


# ---------------------------------------------------------------------------
# POST /api/user/platforms
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SuccessResponse[PlatformLinkOut],
    status_code=201,
    summary="Link a platform account",
)
async def link_platform(
    body: LinkPlatformRequest,
    current_user: dict = Depends(get_current_user),
    identity_manager: UserIdentityManager = Depends(_get_identity_manager),
):
    """Link an external platform account to the authenticated user."""
    user_id = str(current_user["user_id"])

    try:
        result = await identity_manager.link_platform_account(
            user_id=user_id,
            platform=body.platform,
            platform_user_id=body.platform_user_id,
            verification_token=body.verification_token,
        )
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error or "Linking failed")

        # Fetch the created link to return full details
        links = await identity_manager.get_linked_platforms(user_id)
        link = next((lnk for lnk in links if lnk.platform == body.platform), None)
        if link is None:
            raise HTTPException(status_code=500, detail="Link created but could not be retrieved")

        return success_response(
            PlatformLinkOut(
                user_id=str(link.user_id),
                platform=link.platform,
                platform_user_id=link.platform_user_id,
                platform_username=link.platform_username,
                linked_at=(
                    link.linked_at.isoformat()
                    if hasattr(link.linked_at, "isoformat")
                    else str(link.linked_at)
                ),
                is_active=link.is_active,
            )
        )
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error("Failed to link platform", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to link platform account")


# ---------------------------------------------------------------------------
# GET /api/user/platforms
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[list[PlatformLinkOut]],
    summary="Get platform links",
)
async def get_platform_links(
    current_user: dict = Depends(get_current_user),
    identity_manager: UserIdentityManager = Depends(_get_identity_manager),
):
    """Get all active platform links for the authenticated user."""
    user_id = str(current_user["user_id"])

    try:
        links = await identity_manager.get_linked_platforms(user_id)
        return success_response(
            [
                PlatformLinkOut(
                    user_id=str(lnk.user_id),
                    platform=lnk.platform,
                    platform_user_id=lnk.platform_user_id,
                    platform_username=lnk.platform_username,
                    linked_at=(
                        lnk.linked_at.isoformat()
                        if hasattr(lnk.linked_at, "isoformat")
                        else str(lnk.linked_at)
                    ),
                    is_active=lnk.is_active,
                )
                for lnk in links
            ]
        )
    except DatabaseError as e:
        logger.error("Failed to get platform links", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve platform links")


# ---------------------------------------------------------------------------
# DELETE /api/user/platforms/{platform}
# ---------------------------------------------------------------------------


@router.delete(
    "/{platform}",
    response_model=SuccessResponse[dict],
    summary="Unlink a platform account",
)
async def unlink_platform(
    platform: str,
    current_user: dict = Depends(get_current_user),
    identity_manager: UserIdentityManager = Depends(_get_identity_manager),
):
    """Deactivate the link between the authenticated user and the given platform."""
    user_id = str(current_user["user_id"])

    try:
        unlinked = await identity_manager.unlink_platform_account(
            user_id=user_id, platform=platform
        )
        if not unlinked:
            raise HTTPException(
                status_code=404, detail=f"No active {platform} link found for this user"
            )
        return success_response({"unlinked": True, "platform": platform})
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error("Failed to unlink platform", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to unlink platform account")


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/sync  (mounted separately in main.py)
# ---------------------------------------------------------------------------


class SyncConversationRequest(BaseModel):
    target_platforms: list[str] = Field(
        default_factory=lambda: ["discord"],
        description="Platforms to sync to",
    )
    state_update: dict[str, Any] = Field(
        default_factory=dict,
        description="State fields to sync (e.g. title, tags)",
    )


@router.post(
    "/conversations/{conversation_id}/sync",
    response_model=SuccessResponse[dict],
    summary="Manually trigger conversation sync",
    tags=["conversations"],
)
async def sync_conversation(
    conversation_id: str,
    body: SyncConversationRequest,
    current_user: dict = Depends(get_current_user),
    svc: SupabaseService = Depends(_get_supabase),
):
    """Manually trigger a cross-platform sync for a conversation."""
    user_id = current_user["user_id"]

    # Verify ownership
    conv_repo = ConversationRepository(svc.client)
    conv = await conv_repo.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    sync_svc = CrossPlatformSyncService()
    result = await sync_svc.sync_conversation_state(
        conversation_id=conversation_id,
        state_update=body.state_update or {"title": conv.title, "tags": conv.tags},
    )

    return success_response(
        {
            "success": result.success,
            "synced_platforms": result.synced_platforms,
            "failed_platforms": result.failed_platforms,
            "errors": result.errors,
            "sync_timestamp": result.sync_timestamp.isoformat(),
        }
    )
