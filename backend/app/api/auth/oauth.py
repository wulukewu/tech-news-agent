"""Discord OAuth2 endpoints: /discord/login and /discord/callback."""

from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, Response

from app.core.config import settings
from app.services.supabase_service import SupabaseService

from .jwt import create_access_token

router = APIRouter()


@router.get("/discord/login")
async def discord_login():
    """Redirect to Discord OAuth2 authorization page."""
    if not settings.discord_client_id:
        raise HTTPException(status_code=500, detail="DISCORD_CLIENT_ID is not configured")
    if not settings.discord_redirect_uri:
        raise HTTPException(status_code=500, detail="DISCORD_REDIRECT_URI is not configured")

    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": settings.discord_redirect_uri,
        "response_type": "code",
        "scope": "identify guilds.join",
    }
    auth_url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    return Response(status_code=302, headers={"Location": auth_url})


@router.get("/discord/callback")
async def discord_callback(
    code: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):
    """Handle Discord OAuth2 callback: exchange code for token, create/fetch user, issue JWT."""
    frontend_url = settings.frontend_url

    def redirect_error(msg: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?error={quote(msg, safe='')}",
            status_code=302,
        )

    if error:
        return redirect_error(error_description or error)
    if not code:
        return redirect_error("Authorization code missing")
    if not settings.discord_client_id or not settings.discord_client_secret:
        return redirect_error("Discord OAuth2 configuration is incomplete")
    if not settings.discord_redirect_uri:
        return redirect_error("DISCORD_REDIRECT_URI is not configured")

    token_data = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
    }

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://discord.com/api/oauth2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            if token_response.status_code != 200:
                return redirect_error("Failed to authenticate with Discord")

            access_token = token_response.json().get("access_token")
            if not access_token:
                return redirect_error("Failed to authenticate with Discord")

            user_response = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0,
            )
            if user_response.status_code != 200:
                return redirect_error("Failed to retrieve user information")

            user_data = user_response.json()
            discord_id = user_data.get("id")
            username = user_data.get("username")
            avatar_hash = user_data.get("avatar")
            avatar_url = (
                f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
                if avatar_hash
                else None
            )

            if not discord_id:
                return redirect_error("Failed to retrieve user information")

            if settings.discord_guild_id and settings.discord_token:
                try:
                    await client.put(
                        f"https://discord.com/api/v10/guilds/{settings.discord_guild_id}/members/{discord_id}",
                        headers={"Authorization": f"Bot {settings.discord_token}"},
                        json={"access_token": access_token},
                        timeout=30.0,
                    )
                except Exception:
                    pass

    except httpx.RequestError:
        return redirect_error("Failed to communicate with Discord API")
    except Exception:
        return redirect_error("An unexpected error occurred during authentication")

    try:
        supabase_service = SupabaseService(validate_connection=False)
        user_uuid = await supabase_service.get_or_create_user(discord_id)
    except Exception:
        return redirect_error("Failed to register user")

    try:
        jwt_token = create_access_token(
            user_id=user_uuid, discord_id=discord_id, username=username, avatar_url=avatar_url
        )
    except Exception:
        return redirect_error("Failed to generate authentication token")

    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?token={quote(jwt_token, safe='')}",
        status_code=302,
    )
