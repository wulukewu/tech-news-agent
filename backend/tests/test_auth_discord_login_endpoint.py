"""
單元測試：Discord OAuth2 登入端點

測試 GET /api/auth/discord/login 端點的功能。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """建立 FastAPI 測試客戶端"""
    return TestClient(app)


def test_discord_login_redirects_to_discord(client):
    """
    測試 /api/auth/discord/login 重導向至 Discord
    
    驗證：
    1. 返回 302 狀態碼
    2. Location header 包含 Discord OAuth2 URL
    3. URL 包含正確的查詢參數
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    # 模擬環境變數已設定
    with patch.object(settings, 'discord_client_id', 'test_client_id'), \
         patch.object(settings, 'discord_redirect_uri', 'http://localhost:8000/api/auth/discord/callback'):
        
        # 發送請求
        response = client.get("/api/auth/discord/login", follow_redirects=False)
        
        # 驗證狀態碼
        assert response.status_code == 302, "應返回 302 重導向"
        
        # 驗證 Location header
        assert "Location" in response.headers, "應包含 Location header"
        location = response.headers["Location"]
        
        # 驗證 Discord OAuth2 URL
        assert location.startswith("https://discord.com/api/oauth2/authorize"), \
            "應重導向至 Discord OAuth2 授權頁面"
        
        # 解析 URL 和查詢參數
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        # 驗證必要的查詢參數
        assert "client_id" in query_params, "應包含 client_id 參數"
        assert query_params["client_id"][0] == "test_client_id", "client_id 應正確"
        
        assert "redirect_uri" in query_params, "應包含 redirect_uri 參數"
        assert query_params["redirect_uri"][0] == "http://localhost:8000/api/auth/discord/callback", \
            "redirect_uri 應正確"
        
        assert "response_type" in query_params, "應包含 response_type 參數"
        assert query_params["response_type"][0] == "code", "response_type 應為 code"
        
        assert "scope" in query_params, "應包含 scope 參數"
        assert query_params["scope"][0] == "identify", "scope 應為 identify"


def test_discord_login_missing_client_id(client):
    """
    測試缺少 DISCORD_CLIENT_ID 時返回 500 錯誤
    
    Validates: Requirements 1.7
    """
    with patch.object(settings, 'discord_client_id', None), \
         patch.object(settings, 'discord_redirect_uri', 'http://localhost:8000/callback'):
        
        response = client.get("/api/auth/discord/login")
        
        assert response.status_code == 500, "應返回 500 錯誤"
        assert "DISCORD_CLIENT_ID" in response.json()["detail"], \
            "錯誤訊息應提及 DISCORD_CLIENT_ID"


def test_discord_login_missing_redirect_uri(client):
    """
    測試缺少 DISCORD_REDIRECT_URI 時返回 500 錯誤
    
    Validates: Requirements 1.7
    """
    with patch.object(settings, 'discord_client_id', 'test_client_id'), \
         patch.object(settings, 'discord_redirect_uri', None):
        
        response = client.get("/api/auth/discord/login")
        
        assert response.status_code == 500, "應返回 500 錯誤"
        assert "DISCORD_REDIRECT_URI" in response.json()["detail"], \
            "錯誤訊息應提及 DISCORD_REDIRECT_URI"


def test_discord_login_url_encoding(client):
    """
    測試 URL 參數正確編碼
    
    驗證特殊字元在 URL 中被正確編碼
    """
    redirect_uri_with_special_chars = "http://localhost:8000/callback?state=test&foo=bar"
    
    with patch.object(settings, 'discord_client_id', 'test_client_id'), \
         patch.object(settings, 'discord_redirect_uri', redirect_uri_with_special_chars):
        
        response = client.get("/api/auth/discord/login", follow_redirects=False)
        
        assert response.status_code == 302
        location = response.headers["Location"]
        
        # 驗證 URL 可以正確解析
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        # redirect_uri 應該被正確編碼
        assert "redirect_uri" in query_params
        assert query_params["redirect_uri"][0] == redirect_uri_with_special_chars
