# Render 環境變數快速設定指南

## 必要環境變數清單

### 基礎配置

```bash
# 環境類型
APP_ENV=prod

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Discord Bot
DISCORD_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=your-channel-id  # 選填

# Discord OAuth2
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=https://your-api.render.com/api/auth/discord/callback

# LLM (Groq)
GROQ_API_KEY=your-groq-api-key

# JWT
JWT_SECRET=your-secure-random-secret-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# CORS
CORS_ORIGINS=https://your-frontend.netlify.app

# Security
COOKIE_SECURE=true

# Frontend URL (重要！用於 OAuth redirect)
FRONTEND_URL=https://your-frontend.netlify.app
```

## 設定步驟

### 1. 登入 Render

前往 https://dashboard.render.com/

### 2. 選擇服務

點擊你的後端 Web Service

### 3. 進入環境變數設定

點擊左側選單的 **Environment** 標籤

### 4. 批次新增變數

點擊 **Add Environment Variable**，逐一新增上述變數

### 5. 儲存並重新部署

點擊 **Save Changes**，Render 會自動觸發重新部署

## 驗證設定

### 檢查部署日誌

```bash
# 在 Render Dashboard 中查看 Logs
# 確認沒有 ConfigurationError
```

### 測試 API

```bash
# Health check
curl https://your-api.render.com/health

# 預期回應
{"status":"healthy"}
```

### 測試 OAuth

1. 前往前端網站
2. 點擊「使用 Discord 登入」
3. 完成授權
4. 確認重定向到正確網域（不是 localhost）

## 常見錯誤

### ConfigurationError: FRONTEND_URL is required

**原因**: 沒有設定 `FRONTEND_URL` 環境變數

**解決**: 在 Render 新增 `FRONTEND_URL=https://your-frontend.netlify.app`

### CORS Error

**原因**: `CORS_ORIGINS` 與前端網址不符

**解決**: 確保 `CORS_ORIGINS` 包含前端的完整網址（包含 https://）

### OAuth redirect 到 localhost

**原因**: `FRONTEND_URL` 設定錯誤或未設定

**解決**:

1. 確認 `FRONTEND_URL` 設定為正式網域
2. 重新部署後端服務
3. 清除瀏覽器快取

### Cookie not set

**原因**: `COOKIE_SECURE=true` 但使用 HTTP

**解決**: 確保使用 HTTPS，或在開發環境設定 `COOKIE_SECURE=false`

## 環境變數優先順序

Render 環境變數 > .env 檔案

**注意**: Render 上設定的環境變數會覆蓋 `.env` 檔案中的值

## 安全建議

1. **JWT_SECRET**: 使用 `openssl rand -hex 32` 生成強密鑰
2. **COOKIE_SECURE**: 正式環境必須設為 `true`
3. **CORS_ORIGINS**: 只允許信任的網域
4. **SUPABASE_KEY**: 使用 service_role key，不要使用 anon key
5. **環境變數**: 不要在程式碼中硬編碼敏感資訊

## 相關文件

- [Render 環境變數文件](https://render.com/docs/environment-variables)
- [OAuth Redirect 修復指南](./oauth-redirect-fix.md)
- [專案環境變數範例](../../.env.example)
