"""JWT utility functions: token creation, decoding, cookie management, and blacklist."""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Response
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings

__all__ = [
    "create_access_token",
    "decode_token",
    "set_token_cookie",
    "TokenBlacklist",
    "get_token_blacklist",
]

# Global token blacklist instance
_token_blacklist = None


def create_access_token(
    user_id: UUID,
    discord_id: str,
    username: str = None,
    avatar_url: str = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a JWT access token."""
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")

    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_expiration_days)

    now = datetime.utcnow()
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "discord_id": discord_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError or ExpiredSignatureError on failure."""
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def set_token_cookie(response: Response, token: str) -> None:
    """Set the JWT token as an HttpOnly cookie on the response."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expiration_days * 24 * 60 * 60,
        path="/",
        domain=None,
    )


class TokenBlacklist:
    """In-memory token blacklist. Can be extended to Redis for distributed deployments."""

    def __init__(self) -> None:
        self._blacklist: set[str] = set()
        self._lock = asyncio.Lock()

    async def add(self, token: str) -> None:
        async with self._lock:
            self._blacklist.add(token)

    async def is_blacklisted(self, token: str) -> bool:
        async with self._lock:
            return token in self._blacklist

    async def cleanup_expired(self) -> None:
        """Remove expired/invalid tokens to prevent unbounded memory growth."""
        async with self._lock:
            to_remove = []
            for token in self._blacklist:
                try:
                    decode_token(token)
                except (ExpiredSignatureError, JWTError):
                    to_remove.append(token)
            for token in to_remove:
                self._blacklist.discard(token)


def get_token_blacklist() -> TokenBlacklist:
    """Return the global TokenBlacklist singleton."""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist
