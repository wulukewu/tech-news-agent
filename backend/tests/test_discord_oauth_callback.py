"""
測試 Discord OAuth2 Callback 端點

驗證 OAuth2 callback 處理流程的正確性。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


@pytest.fixture
def mock_discord_responses():
    """模擬 Discord API 回應"""
    return {
        "token": {
            "access_token": "mock_access_token_12345",
            "token_type": "Bearer",
            "expires_in": 604800,
            "refresh_token": "mock_refresh_token",
            "scope": "identify"
        },
        "user": {
            "id": "123456789012345678",
            "username": "testuser",
            "discriminator": "0001",
            "avatar": "abc123"
        }
    }


class TestDiscordOAuthCallback:
    """測試 Discord OAuth2 Callback 端點"""
    
    def test_callback_with_error_parameter(self, client):
        """測試使用者拒絕授權的情況"""
        response = client.get(
            "/api/auth/discord/callback",
            params={
                "error": "access_denied",
                "error_description": "User denied authorization"
            }
        )
        
        assert response.status_code == 400
        assert "error" in response.json()["detail"]
        assert response.json()["detail"]["error"] == "access_denied"
    
    def test_callback_without_code(self, client):
        """測試缺少 authorization code 的情況"""
        response = client.get("/api/auth/discord/callback")
        
        assert response.status_code == 400
        assert "Authorization code missing" in response.json()["detail"]
    
    @patch('app.api.auth.settings')
    @patch('app.api.auth.httpx.AsyncClient')
    @patch('app.api.auth.SupabaseService')
    def test_callback_success(self, mock_supabase_cls, mock_httpx_cls, mock_settings, client, mock_discord_responses):
        """測試成功的 OAuth2 callback 流程"""
        # 模擬 settings
        mock_settings.discord_client_id = "test_client_id"
        mock_settings.discord_client_secret = "test_client_secret"
        mock_settings.discord_redirect_uri = "http://localhost:8000/callback"
        mock_settings.jwt_secret = "test_jwt_secret_at_least_32_characters_long_12345"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        mock_settings.cookie_secure = False
        
        # 模擬 httpx.AsyncClient
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__aenter__.return_value = mock_client
        mock_httpx_cls.return_value.__aexit__.return_value = AsyncMock(return_value=False)
        
        # 模擬 token 交換回應
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = mock_discord_responses["token"]
        
        # 模擬使用者資訊回應
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = mock_discord_responses["user"]
        
        # 設定 mock client 的行為
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_user_response)
        
        # 模擬 SupabaseService
        mock_supabase = mock_supabase_cls.return_value
        test_user_uuid = uuid4()
        mock_supabase.get_or_create_user = AsyncMock(return_value=test_user_uuid)
        
        # 執行請求
        response = client.get(
            "/api/auth/discord/callback",
            params={"code": "test_authorization_code"}
        )
        
        # 驗證回應
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "Bearer"
        
        # 驗證 Cookie 被設置
        assert "access_token" in response.cookies
        
        # 驗證 SupabaseService 被正確呼叫
        mock_supabase.get_or_create_user.assert_called_once_with(
            mock_discord_responses["user"]["id"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
