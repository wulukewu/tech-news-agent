"""Auth package: JWT utilities, Discord OAuth, and auth endpoints.

All public symbols are re-exported here so existing imports like
    from app.api.auth import get_current_user, create_access_token, ...
continue to work without changes.
"""

from fastapi import APIRouter

from .endpoints import (
    get_current_user,
    get_current_user_info,
    get_user_stats,
    logout,
    refresh_token,
    set_cookie_endpoint,
)
from .endpoints import router as _endpoints_router
from .jwt import (
    TokenBlacklist,
    create_access_token,
    decode_token,
    get_token_blacklist,
    set_token_cookie,
)
from .oauth import router as _oauth_router

# Combined router (same as the original auth.router)
router = APIRouter()
router.include_router(_oauth_router)
router.include_router(_endpoints_router)

__all__ = [
    "router",
    # JWT utils
    "create_access_token",
    "decode_token",
    "set_token_cookie",
    "TokenBlacklist",
    "get_token_blacklist",
    # Auth dependency
    "get_current_user",
    # Endpoints (exported for tests that import them directly)
    "get_current_user_info",
    "get_user_stats",
    "refresh_token",
    "logout",
    "set_cookie_endpoint",
]
