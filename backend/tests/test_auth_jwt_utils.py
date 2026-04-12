"""
測試 JWT 工具模組的功能

包含 create_access_token, decode_token, set_token_cookie 的單元測試
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import Response
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from app.api.auth import create_access_token, decode_token, set_token_cookie
from app.core.config import settings


@pytest.fixture(scope="module", autouse=True)
def setup_jwt_secret():
    """設置測試用的 JWT_SECRET"""
    # 保存原始值
    original_secret = settings.jwt_secret

    # 設置測試用的 secret
    test_secret = "test_jwt_secret_at_least_32_characters_long_for_testing"
    settings.jwt_secret = test_secret

    yield

    # 恢復原始值
    settings.jwt_secret = original_secret


class TestCreateAccessToken:
    """測試 JWT Token 生成功能"""

    def test_create_token_with_valid_data(self):
        """測試使用有效資料生成 Token"""
        user_id = uuid4()
        discord_id = "123456789"

        token = create_access_token(user_id, discord_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_payload_contains_correct_data(self):
        """測試生成的 Token payload 包含正確資料"""
        user_id = uuid4()
        discord_id = "987654321"

        token = create_access_token(user_id, discord_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["discord_id"] == discord_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_with_custom_expiration(self):
        """測試使用自訂過期時間生成 Token"""
        user_id = uuid4()
        discord_id = "111222333"
        expires_delta = timedelta(hours=1)

        token = create_access_token(user_id, discord_id, expires_delta)
        payload = decode_token(token)

        # 驗證過期時間大約是 1 小時後
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        time_diff = exp_time - iat_time

        # 允許幾秒的誤差
        assert abs(time_diff.total_seconds() - 3600) < 5

    def test_create_token_uses_default_expiration(self):
        """測試預設過期時間為配置的天數"""
        user_id = uuid4()
        discord_id = "444555666"

        token = create_access_token(user_id, discord_id)
        payload = decode_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        time_diff = exp_time - iat_time

        expected_seconds = settings.jwt_expiration_days * 24 * 60 * 60
        # 允許幾秒的誤差
        assert abs(time_diff.total_seconds() - expected_seconds) < 5


class TestDecodeToken:
    """測試 JWT Token 解碼功能"""

    def test_decode_valid_token(self):
        """測試解碼有效的 Token"""
        user_id = uuid4()
        discord_id = "777888999"

        token = create_access_token(user_id, discord_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["discord_id"] == discord_id

    def test_decode_expired_token_raises_error(self):
        """測試解碼過期 Token 會拋出 ExpiredSignatureError"""
        user_id = uuid4()
        discord_id = "000111222"
        # 建立已過期的 Token（過期時間為 -1 秒）
        expires_delta = timedelta(seconds=-1)

        token = create_access_token(user_id, discord_id, expires_delta)

        with pytest.raises(ExpiredSignatureError):
            decode_token(token)

    def test_decode_invalid_token_raises_error(self):
        """測試解碼無效 Token 會拋出 JWTError"""
        invalid_token = "invalid.token.string"

        with pytest.raises(JWTError):
            decode_token(invalid_token)

    def test_decode_token_with_wrong_signature(self):
        """測試解碼簽名錯誤的 Token 會拋出 JWTError"""
        user_id = uuid4()
        discord_id = "333444555"

        token = create_access_token(user_id, discord_id)
        # 修改 Token 的最後幾個字元來破壞簽名
        tampered_token = token[:-10] + "tampered00"

        with pytest.raises(JWTError):
            decode_token(tampered_token)


class TestSetTokenCookie:
    """測試 Cookie 設置功能"""

    def test_set_cookie_with_correct_attributes(self):
        """測試設置 Cookie 包含正確的屬性"""
        user_id = uuid4()
        discord_id = "666777888"
        token = create_access_token(user_id, discord_id)

        response = Response()
        set_token_cookie(response, token)

        # 檢查 Cookie 是否被設置
        assert "access_token" in response.headers.get("set-cookie", "")

        # 檢查 Cookie 屬性
        cookie_header = response.headers.get("set-cookie", "")
        assert "httponly" in cookie_header.lower()
        assert "samesite=lax" in cookie_header.lower()
        assert "path=/" in cookie_header.lower()

        # 檢查 secure 屬性（根據配置）
        if settings.cookie_secure:
            assert "secure" in cookie_header.lower()

    def test_set_cookie_max_age(self):
        """測試 Cookie 的 max_age 設置正確"""
        user_id = uuid4()
        discord_id = "999000111"
        token = create_access_token(user_id, discord_id)

        response = Response()
        set_token_cookie(response, token)

        cookie_header = response.headers.get("set-cookie", "")
        expected_max_age = settings.jwt_expiration_days * 24 * 60 * 60

        assert f"max-age={expected_max_age}" in cookie_header.lower()


class TestTokenRoundTrip:
    """測試 Token 的完整生命週期"""

    def test_create_and_decode_round_trip(self):
        """測試建立和解碼 Token 的完整流程"""
        user_id = uuid4()
        discord_id = "123123123"

        # 建立 Token
        token = create_access_token(user_id, discord_id)

        # 解碼 Token
        payload = decode_token(token)

        # 驗證資料一致性
        assert payload["sub"] == str(user_id)
        assert payload["discord_id"] == discord_id

    def test_multiple_tokens_are_unique(self):
        """測試多次生成的 Token 是唯一的（因為 iat 不同）"""
        import time

        user_id = uuid4()
        discord_id = "456456456"

        token1 = create_access_token(user_id, discord_id)
        # 等待一秒確保 iat 時間戳不同
        time.sleep(1)
        token2 = create_access_token(user_id, discord_id)

        # Token 應該不同（因為 iat 時間戳不同）
        assert token1 != token2

        # 但解碼後的 user_id 和 discord_id 應該相同
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)

        assert payload1["sub"] == payload2["sub"]
        assert payload1["discord_id"] == payload2["discord_id"]
