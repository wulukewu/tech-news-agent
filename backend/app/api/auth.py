"""
JWT 認證工具模組

提供 JWT Token 的生成、驗證和 Cookie 設置功能。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote, urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.services.supabase_service import SupabaseService

# 建立 FastAPI Router
router = APIRouter()

# 全域 Token 黑名單實例
token_blacklist = None


def create_access_token(
    user_id: UUID,
    discord_id: str,
    username: str = None,
    avatar_url: str = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    生成 JWT Access Token

    Args:
        user_id: 使用者 UUID
        discord_id: Discord 使用者 ID
        expires_delta: 過期時間（預設從配置讀取）

    Returns:
        JWT Token 字串

    Raises:
        ValueError: 當 JWT_SECRET 未設定時
    """
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")

    # 設定過期時間
    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_expiration_days)

    # 構建 payload
    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),  # Subject: user UUID
        "discord_id": discord_id,
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
    }

    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    # 生成 JWT Token
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return token


def decode_token(token: str) -> dict[str, Any]:
    """
    解碼並驗證 JWT Token

    Args:
        token: JWT Token 字串

    Returns:
        Dict: Token payload，包含 sub, discord_id, exp, iat

    Raises:
        JWTError: 當 Token 簽名無效或格式錯誤時
        ExpiredSignatureError: 當 Token 已過期時
    """
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except ExpiredSignatureError:
        # 重新拋出過期錯誤，讓呼叫者處理
        raise
    except JWTError:
        # 重新拋出 JWT 錯誤，讓呼叫者處理
        raise


def set_token_cookie(response: Response, token: str) -> None:
    """
    設置 JWT Token 為 HttpOnly Cookie

    Args:
        response: FastAPI Response 物件
        token: JWT Token 字串
    """
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # 防止 JavaScript 存取
        secure=settings.cookie_secure,  # 生產環境要求 HTTPS
        samesite="lax",  # CSRF 防護
        max_age=settings.jwt_expiration_days * 24 * 60 * 60,  # 轉換為秒
        path="/",  # 全站可用
        domain=None,  # 不設置 domain，讓瀏覽器自動處理
    )


class TokenBlacklist:
    """
    Token 黑名單管理（記憶體實作）

    使用 set 儲存已撤銷的 Token。
    未來可擴展為 Redis 實作以支援分散式部署。
    """

    def __init__(self):
        """初始化黑名單"""
        self._blacklist: set[str] = set()
        self._lock = asyncio.Lock()

    async def add(self, token: str) -> None:
        """
        將 Token 加入黑名單

        Args:
            token: JWT Token 字串
        """
        async with self._lock:
            self._blacklist.add(token)

    async def is_blacklisted(self, token: str) -> bool:
        """
        檢查 Token 是否在黑名單中

        Args:
            token: JWT Token 字串

        Returns:
            bool: True 表示 Token 在黑名單中，False 表示不在
        """
        async with self._lock:
            return token in self._blacklist

    async def cleanup_expired(self) -> None:
        """
        清理過期的 Token（定期執行）

        解碼所有 Token，移除已過期的，避免記憶體無限增長。
        """
        async with self._lock:
            expired_tokens = []
            for token in self._blacklist:
                try:
                    # 嘗試解碼 Token 以檢查是否過期
                    decode_token(token)
                except ExpiredSignatureError:
                    # Token 已過期，標記為待移除
                    expired_tokens.append(token)
                except JWTError:
                    # Token 無效，也移除
                    expired_tokens.append(token)

            # 移除過期的 Token
            for token in expired_tokens:
                self._blacklist.discard(token)


def get_token_blacklist() -> TokenBlacklist:
    """
    取得全域 Token 黑名單實例

    Returns:
        TokenBlacklist: 黑名單實例
    """
    global token_blacklist
    if token_blacklist is None:
        token_blacklist = TokenBlacklist()
    return token_blacklist


# ============================================================================
# OAuth2 端點
# ============================================================================


@router.get("/discord/login")
async def discord_login():
    """
    重導向至 Discord OAuth2 授權頁面

    構建 Discord OAuth2 授權 URL 並重導向使用者至 Discord 進行授權。

    Returns:
        Response: 302 重導向至 Discord 授權頁面

    Raises:
        HTTPException: 500 當必要的環境變數缺失時
    """
    # 驗證必要的環境變數
    if not settings.discord_client_id:
        raise HTTPException(status_code=500, detail="DISCORD_CLIENT_ID is not configured")

    if not settings.discord_redirect_uri:
        raise HTTPException(status_code=500, detail="DISCORD_REDIRECT_URI is not configured")

    # 構建 Discord OAuth2 授權 URL
    discord_auth_base_url = "https://discord.com/api/oauth2/authorize"

    # 構建查詢參數
    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": settings.discord_redirect_uri,
        "response_type": "code",
        "scope": "identify",
    }

    # 組合完整的授權 URL
    auth_url = f"{discord_auth_base_url}?{urlencode(params)}"

    # 返回 302 重導向
    return Response(status_code=302, headers={"Location": auth_url})


@router.get("/discord/callback")
async def discord_callback(
    code: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):
    """
    處理 Discord OAuth2 授權回調

    接收 Discord 的授權回調，交換 authorization code 取得 Access Token，
    並使用 Access Token 取得使用者資訊，最後生成 JWT Token。

    Args:
        code: 授權碼（使用者同意授權時）
        error: 錯誤代碼（使用者拒絕授權時）
        error_description: 錯誤描述

    Returns:
        RedirectResponse: 成功時重定向到前端 callback 頁面（帶 token），
                          失敗時重定向到前端 callback 頁面（帶 error）
    """
    frontend_url = settings.frontend_url

    def redirect_error(msg: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?error={quote(msg, safe='')}",
            status_code=302,
        )

    # 1. 使用者拒絕授權或 Discord 回傳錯誤
    if error:
        return redirect_error(error_description or error)

    # 2. 驗證 authorization code 存在
    if not code:
        return redirect_error("Authorization code missing")

    # 3. 驗證必要的環境變數
    if not settings.discord_client_id or not settings.discord_client_secret:
        return redirect_error("Discord OAuth2 configuration is incomplete")

    if not settings.discord_redirect_uri:
        return redirect_error("DISCORD_REDIRECT_URI is not configured")

    # 4. 使用 httpx.AsyncClient 交換 authorization code 取得 Access Token
    token_url = "https://discord.com/api/oauth2/token"
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
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )

            if token_response.status_code != 200:
                return redirect_error("Failed to authenticate with Discord")

            token_json = token_response.json()
            access_token = token_json.get("access_token")

            if not access_token:
                return redirect_error("Failed to authenticate with Discord")

            # 5. 使用 Access Token 呼叫 Discord /users/@me API
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

            avatar_url = None
            if avatar_hash:
                avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"

            if not discord_id:
                return redirect_error("Failed to retrieve user information")

    except httpx.RequestError:
        return redirect_error("Failed to communicate with Discord API")
    except Exception:
        return redirect_error("An unexpected error occurred during authentication")

    # 6. 呼叫 supabase_service.get_or_create_user(discord_id) 註冊使用者
    try:
        supabase_service = SupabaseService(validate_connection=False)
        user_uuid = await supabase_service.get_or_create_user(discord_id)
    except Exception:
        return redirect_error("Failed to register user")

    # 7. 生成 JWT Token
    try:
        jwt_token = create_access_token(
            user_id=user_uuid, discord_id=discord_id, username=username, avatar_url=avatar_url
        )
    except Exception:
        return redirect_error("Failed to generate authentication token")

    # 8. 重定向到前端並帶上 token
    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?token={quote(jwt_token, safe='')}",
        status_code=302,
    )


# ============================================================================
# 認證 Dependency
# ============================================================================


async def get_current_user(
    authorization: str | None = Header(None), access_token: str | None = Cookie(None)
) -> dict[str, Any]:
    """
    驗證 JWT Token 並返回當前使用者資訊

    這是一個 FastAPI Dependency，用於保護需要認證的 API 端點。
    支援從 Authorization Header 或 Cookie 中提取 Token。

    Args:
        authorization: Authorization Header (格式: "Bearer {token}")
        access_token: Cookie 中的 Token

    Returns:
        Dict: {"user_id": UUID, "discord_id": str}

    Raises:
        HTTPException: 401 當 Token 缺失時
        HTTPException: 401 當 Token 過期時
        HTTPException: 401 當 Token 無效時
        HTTPException: 401 當 Token 已撤銷時

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9**
    """
    # 1. Token 提取：優先從 Authorization Header 提取
    token = None

    if authorization:
        # 從 Authorization Header 提取 (格式: "Bearer {token}")
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # 若 Header 不存在，從 Cookie 提取
    if not token and access_token:
        token = access_token

    # 若兩者都不存在，拋出 401
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 2. Token 驗證：解碼並驗證簽名
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        # Token 已過期
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        # Token 簽名無效或格式錯誤
        raise HTTPException(status_code=401, detail="Invalid token")

    # 3. 黑名單檢查：檢查 Token 是否已被撤銷
    blacklist = get_token_blacklist()
    if await blacklist.is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    # 4. 提取使用者資訊：從 Payload 提取 user_id 和 discord_id
    try:
        user_id_str = payload.get("sub")
        discord_id = payload.get("discord_id")

        if not user_id_str or not discord_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 轉換 user_id 為 UUID 物件
        user_id = UUID(user_id_str)

    except (ValueError, KeyError):
        # UUID 格式錯誤或必要欄位缺失
        raise HTTPException(status_code=401, detail="Invalid token")

    # 5. 返回使用者資訊
    return {
        "user_id": user_id,
        "discord_id": discord_id,
        "username": payload.get("username"),
        "avatar_url": payload.get("avatar_url"),
    }


@router.post("/set-cookie")
async def set_cookie_endpoint(token: str = Query(..., description="JWT token to set as cookie")):
    """
    設置 JWT Token 為 Cookie

    這個端點允許前端在收到 token 後設置為 HttpOnly Cookie。
    用於 OAuth callback 流程。

    Args:
        token: JWT Token 字串

    Returns:
        Response: 成功訊息並設置 Cookie
    """
    try:
        # 驗證 token 是否有效
        decode_token(token)

        # 設置 Cookie
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


# ============================================================================
# 使用者資訊端點
# ============================================================================


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    取得當前使用者資訊

    驗證 JWT Token 並返回使用者的基本資訊。
    由於 users 表只存儲 discord_id，我們直接從 JWT payload 返回資訊。

    Args:
        current_user: 當前使用者資訊（從 Dependency 注入）

    Returns:
        Dict: 使用者資訊，包含 user_id, discord_id

    Raises:
        HTTPException: 401 當 Token 無效時
    """
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
    """Get user profile statistics: reading list count, subscriptions, articles read."""
    try:
        supabase = SupabaseService()
        user_id = str(current_user["user_id"])
        discord_id = current_user["discord_id"]

        # Reading list count
        reading_list_resp = (
            supabase.client.table("reading_list")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        reading_list_count = reading_list_resp.count or 0

        # Articles read (status = 'Read')
        articles_read_resp = (
            supabase.client.table("reading_list")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "Read")
            .execute()
        )
        articles_read_count = articles_read_resp.count or 0

        # Subscriptions count
        subscriptions = await supabase.get_user_subscriptions(discord_id)
        subscriptions_count = len(subscriptions)

        return {
            "reading_list_count": reading_list_count,
            "subscriptions_count": subscriptions_count,
            "articles_read_count": articles_read_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user stats: {e}")


# ============================================================================
# Token 管理端點
# ============================================================================


@router.post("/refresh")
async def refresh_token(
    current_user: dict = Depends(get_current_user), access_token: str | None = Cookie(None)
):
    """
    刷新 JWT Token

    驗證當前 Token 後生成新的 Token，並將舊 Token 加入黑名單。

    Args:
        current_user: 當前使用者資訊（從 Dependency 注入）
        access_token: 當前 Token（用於加入黑名單）

    Returns:
        Response: 新的 access_token 和 Set-Cookie header

    **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7**
    """
    try:
        # 1. 生成新的 JWT Token（使用相同的 user_id 和 discord_id）
        new_token = create_access_token(
            user_id=current_user["user_id"],
            discord_id=current_user["discord_id"],
            username=current_user.get("username"),
            avatar_url=current_user.get("avatar_url"),
        )

        # 2. 將舊 Token 加入黑名單
        if access_token:
            blacklist = get_token_blacklist()
            await blacklist.add(access_token)

        # 3. 設定新 Token 為 Cookie 並返回 JSON
        response_data = {"access_token": new_token, "token_type": "Bearer"}

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
    current_user: dict = Depends(get_current_user), access_token: str | None = Cookie(None)
):
    """
    登出並撤銷 Token

    將當前 Token 加入黑名單並清除 Cookie。

    Args:
        current_user: 當前使用者資訊（從 Dependency 注入）
        access_token: 當前 Token（用於加入黑名單）

    Returns:
        Response: 成功訊息

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6**
    """
    try:
        # 1. 將 Token 加入黑名單
        if access_token:
            blacklist = get_token_blacklist()
            await blacklist.add(access_token)

        # 2. 清除 Cookie（設定 max_age=0）
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
            max_age=0,  # 立即過期
            path="/",
        )

        return response

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to logout")
