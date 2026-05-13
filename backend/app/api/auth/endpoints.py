"""Auth API endpoints: /me, /me/stats, /set-cookie, /refresh, /logout."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Response
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.services.supabase_service import SupabaseService

from .jwt import (
    create_access_token,
    decode_token,
    get_token_blacklist,
    set_token_cookie,
)

router = APIRouter()


async def get_current_user(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None),
) -> dict[str, Any]:
    """FastAPI dependency: validate JWT and return current user info."""
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if not token and access_token:
        token = access_token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    blacklist = get_token_blacklist()
    if await blacklist.is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        user_id_str = payload.get("sub")
        discord_id = payload.get("discord_id")
        if not user_id_str or not discord_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = UUID(user_id_str)
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "user_id": user_id,
        "discord_id": discord_id,
        "username": payload.get("username"),
        "avatar_url": payload.get("avatar_url"),
    }


@router.post("/set-cookie")
async def set_cookie_endpoint(token: str = Query(..., description="JWT token to set as cookie")):
    """Set a JWT token as an HttpOnly cookie (used after OAuth callback)."""
    try:
        decode_token(token)
        response = Response(
            content='{"success": true, "data": {"message": "Cookie set successfully"}, "metadata": null}',
            media_type="application/json",
            status_code=200,
        )
        set_token_cookie(response, token)
        return response
    except (JWTError, ExpiredSignatureError):
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to set cookie")


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Return current user info from JWT payload."""
    try:
        return {
            "id": str(current_user["user_id"]),
            "discord_id": current_user["discord_id"],
            "username": current_user.get("username"),
            "avatar": current_user.get("avatar_url"),
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve user information")


@router.get("/me/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Return user reading stats: reading list count, subscriptions, articles read."""
    try:
        supabase = SupabaseService()
        user_id = str(current_user["user_id"])
        discord_id = current_user["discord_id"]

        reading_list_resp = (
            supabase.client.table("reading_list")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        articles_read_resp = (
            supabase.client.table("reading_list")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "Read")
            .execute()
        )
        subscriptions = await supabase.get_user_subscriptions(discord_id)

        return {
            "reading_list_count": reading_list_resp.count or 0,
            "subscriptions_count": len(subscriptions),
            "articles_read_count": articles_read_resp.count or 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user stats: {e}")


@router.post("/refresh")
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    access_token: str | None = Cookie(None),
):
    """Issue a new JWT token and blacklist the old one."""
    try:
        new_token = create_access_token(
            user_id=current_user["user_id"],
            discord_id=current_user["discord_id"],
            username=current_user.get("username"),
            avatar_url=current_user.get("avatar_url"),
        )
        if access_token:
            await get_token_blacklist().add(access_token)

        response = Response(
            content='{"success": true, "data": {"access_token": "'
            + new_token
            + '", "token_type": "Bearer"}, "metadata": null}',
            media_type="application/json",
            status_code=200,
        )
        set_token_cookie(response, new_token)
        return response
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    access_token: str | None = Cookie(None),
):
    """Blacklist the current token and clear the auth cookie."""
    try:
        if access_token:
            await get_token_blacklist().add(access_token)

        response = Response(
            content='{"success": true, "data": {"message": "Logged out successfully"}, "metadata": null}',
            media_type="application/json",
            status_code=200,
        )
        response.set_cookie(
            key="access_token",
            value="",
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=0,
            path="/",
        )
        return response
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to logout")
