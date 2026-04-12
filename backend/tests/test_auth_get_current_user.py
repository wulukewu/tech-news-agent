"""
Unit tests for get_current_user() Dependency

Task 1.12

This module tests the get_current_user() dependency function that validates
JWT tokens and extracts user information from Authorization headers or cookies.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9**
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.auth import create_access_token, get_current_user, get_token_blacklist
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_jwt_secret(monkeypatch):
    """
    設置測試用的 JWT_SECRET

    這個 fixture 會自動應用到所有測試，確保 JWT_SECRET 已配置。
    """
    test_jwt_secret = "test_jwt_secret_at_least_32_characters_long_for_testing"
    monkeypatch.setattr(settings, "jwt_secret", test_jwt_secret)


class TestGetCurrentUser:
    """測試 get_current_user() Dependency"""

    @pytest.mark.asyncio
    async def test_extract_token_from_authorization_header(self):
        """
        測試從 Authorization Header 提取 Token

        **Validates: Requirement 5.2**
        """
        # 生成測試 Token
        user_id = uuid4()
        discord_id = "123456789"
        token = create_access_token(user_id, discord_id)

        # 模擬 Authorization Header
        authorization = f"Bearer {token}"

        # 呼叫 get_current_user
        result = await get_current_user(authorization=authorization, access_token=None)

        # 驗證結果
        assert result["user_id"] == user_id
        assert result["discord_id"] == discord_id

    @pytest.mark.asyncio
    async def test_extract_token_from_cookie(self):
        """
        測試從 Cookie 提取 Token

        **Validates: Requirement 5.3**
        """
        # 生成測試 Token
        user_id = uuid4()
        discord_id = "987654321"
        token = create_access_token(user_id, discord_id)

        # 呼叫 get_current_user (只提供 Cookie)
        result = await get_current_user(authorization=None, access_token=token)

        # 驗證結果
        assert result["user_id"] == user_id
        assert result["discord_id"] == discord_id

    @pytest.mark.asyncio
    async def test_authorization_header_takes_precedence_over_cookie(self):
        """
        測試 Authorization Header 優先於 Cookie

        **Validates: Requirement 5.2**
        """
        # 生成兩個不同的 Token
        user_id_1 = uuid4()
        discord_id_1 = "111111111"
        token_1 = create_access_token(user_id_1, discord_id_1)

        user_id_2 = uuid4()
        discord_id_2 = "222222222"
        token_2 = create_access_token(user_id_2, discord_id_2)

        # 同時提供 Header 和 Cookie
        authorization = f"Bearer {token_1}"

        # 呼叫 get_current_user
        result = await get_current_user(authorization=authorization, access_token=token_2)

        # 驗證使用 Header 中的 Token (user_id_1)
        assert result["user_id"] == user_id_1
        assert result["discord_id"] == discord_id_1

    @pytest.mark.asyncio
    async def test_missing_token_raises_401(self):
        """
        測試 Token 缺失時拋出 401

        **Validates: Requirement 5.4**
        """
        # 不提供任何 Token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None, access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """
        測試過期 Token 被拒絕

        **Validates: Requirement 5.6**
        """
        # 生成已過期的 Token
        user_id = uuid4()
        discord_id = "123456789"

        # 使用負數過期時間生成過期 Token
        expired_token = create_access_token(
            user_id, discord_id, expires_delta=timedelta(seconds=-1)
        )

        # 呼叫 get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {expired_token}", access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expired"

    @pytest.mark.asyncio
    async def test_invalid_signature_raises_401(self):
        """
        測試無效簽名的 Token 被拒絕

        **Validates: Requirement 5.7**
        """
        # 生成 Token 但使用錯誤的 secret 簽名
        user_id = uuid4()
        discord_id = "123456789"

        payload = {
            "sub": str(user_id),
            "discord_id": discord_id,
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
        }

        # 使用錯誤的 secret 簽名
        invalid_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        # 呼叫 get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {invalid_token}", access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_malformed_token_raises_401(self):
        """
        測試格式錯誤的 Token 被拒絕

        **Validates: Requirement 5.7**
        """
        # 使用格式錯誤的 Token
        malformed_token = "not.a.valid.jwt.token"

        # 呼叫 get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {malformed_token}", access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_401(self):
        """
        測試黑名單中的 Token 被拒絕

        **Validates: Requirement 5.9**
        """
        # 生成測試 Token
        user_id = uuid4()
        discord_id = "123456789"
        token = create_access_token(user_id, discord_id)

        # 將 Token 加入黑名單
        blacklist = get_token_blacklist()
        await blacklist.add(token)

        # 呼叫 get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {token}", access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has been revoked"

    @pytest.mark.asyncio
    async def test_token_without_bearer_prefix_ignored(self):
        """
        測試沒有 Bearer 前綴的 Authorization Header 被忽略

        **Validates: Requirement 5.2**
        """
        # 生成測試 Token
        user_id = uuid4()
        discord_id = "123456789"
        token = create_access_token(user_id, discord_id)

        # 不使用 Bearer 前綴
        authorization = token  # 缺少 "Bearer " 前綴

        # 呼叫 get_current_user (應該失敗，因為沒有 Bearer 前綴且沒有 Cookie)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=authorization, access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_extracts_correct_user_id_and_discord_id(self):
        """
        測試正確提取 user_id 和 discord_id

        **Validates: Requirements 5.8, 5.9**
        """
        # 生成測試 Token
        user_id = uuid4()
        discord_id = "999888777"
        token = create_access_token(user_id, discord_id)

        # 呼叫 get_current_user
        result = await get_current_user(authorization=f"Bearer {token}", access_token=None)

        # 驗證提取的資訊正確
        assert result["user_id"] == user_id
        assert result["discord_id"] == discord_id
        assert isinstance(result["user_id"], type(user_id))  # 確保是 UUID 類型
        assert isinstance(result["discord_id"], str)

    @pytest.mark.asyncio
    async def test_token_missing_required_claims_raises_401(self):
        """
        測試缺少必要欄位的 Token 被拒絕

        **Validates: Requirement 5.7**
        """
        # 生成缺少 discord_id 的 Token
        user_id = uuid4()

        payload = {
            "sub": str(user_id),
            # 缺少 discord_id
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
        }

        invalid_token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        # 呼叫 get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {invalid_token}", access_token=None)

        # 驗證錯誤
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
