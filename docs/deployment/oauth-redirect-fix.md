# OAuth Redirect 修復指南

## 問題描述

部署到 Netlify 和 Render 後，Discord OAuth 登入完成後會重定向到 `http://localhost:3000/auth/callback` 而不是正式網域。

## 根本原因

後端在生成 OAuth redirect URL 時，使用了錯誤的環境變數來取得前端 URL：

```python
# ❌ 錯誤做法 (之前)
frontend_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
```

`NEXT_PUBLIC_APP_URL` 是前端的環境變數，在後端環境中不存在，所以總是使用預設值 `http://localhost:3000`。

## 解決方案

### 1. 程式碼修改 (已完成)

- 在 `backend/app/core/config.py` 新增 `frontend_url` 配置
- 更新 `backend/app/api/auth.py` 使用 `settings.frontend_url`
- 更新 `.env.example` 加入 `FRONTEND_URL` 說明
- **統一環境變數管理**: 所有環境變數統一放在專案根目錄的 `.env` 檔案

### 2. 環境變數檔案結構

```
project/
├── .env              # ✅ 唯一的環境變數檔案（本地開發用）
├── .env.example      # ✅ 環境變數範本
├── backend/          # ❌ 不再有 .env
└── frontend/         # ❌ 不再有 .env.local
```

**重要**:

- Docker 會從根目錄的 `.env` 讀取環境變數
- 正式部署時，在 Render/Netlify 上直接設定環境變數，不使用 `.env` 檔案

### 3. Render 環境變數設定 (必須執行)

前往 Render Dashboard 設定後端服務的環境變數：

#### 開發環境

```bash
FRONTEND_URL=http://localhost:3000
```

#### 正式環境 (Render + Netlify)

```bash
FRONTEND_URL=https://your-frontend-domain.netlify.app
```

**設定步驟：**

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 選擇你的後端服務 (Web Service)
3. 點擊 **Environment** 標籤
4. 點擊 **Add Environment Variable**
5. 新增：
   - Key: `FRONTEND_URL`
   - Value: `https://your-frontend-domain.netlify.app`
6. 點擊 **Save Changes**
7. Render 會自動重新部署服務

### 3. 驗證設定

部署完成後，測試 Discord OAuth 登入流程：

1. 前往前端網站
2. 點擊「使用 Discord 登入」
3. 完成 Discord 授權
4. 確認重定向到正確的網域（不是 localhost）

## 環境變數清單

確保以下環境變數都已正確設定：

### 後端 (Render)

| 變數名稱               | 說明                           | 範例值                                                  |
| ---------------------- | ------------------------------ | ------------------------------------------------------- |
| `FRONTEND_URL`         | 前端網址 (用於 OAuth redirect) | `https://your-app.netlify.app`                          |
| `CORS_ORIGINS`         | 允許的 CORS 來源               | `https://your-app.netlify.app`                          |
| `DISCORD_REDIRECT_URI` | Discord OAuth callback URL     | `https://your-api.render.com/api/auth/discord/callback` |
| `COOKIE_SECURE`        | 是否使用 HTTPS Cookie          | `true`                                                  |
| `APP_ENV`              | 環境類型                       | `prod`                                                  |

### 前端 (Netlify)

| 變數名稱                   | 說明         | 範例值                         |
| -------------------------- | ------------ | ------------------------------ |
| `NEXT_PUBLIC_API_BASE_URL` | 後端 API URL | `https://your-api.render.com`  |
| `NEXT_PUBLIC_APP_URL`      | 前端網址     | `https://your-app.netlify.app` |

## Discord Developer Portal 設定

確保 Discord OAuth2 Redirects 包含正式環境的 callback URL：

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇你的應用程式
3. 點擊 **OAuth2** > **General**
4. 在 **Redirects** 中新增：
   ```
   https://your-api.render.com/api/auth/discord/callback
   ```
5. 點擊 **Save Changes**

## 常見問題

### Q: 為什麼不直接使用 `NEXT_PUBLIC_APP_URL`？

A: `NEXT_PUBLIC_*` 前綴的環境變數是 Next.js 專用的，只會在前端建置時注入。後端無法存取這些變數，所以需要獨立的 `FRONTEND_URL` 配置。

### Q: 本地開發時需要設定嗎？

A: 本地開發時，`FRONTEND_URL` 預設為 `http://localhost:3000`，通常不需要額外設定。但如果你使用不同的 port，需要在 `backend/.env` 中設定。

### Q: 如何測試是否設定成功？

A: 檢查後端日誌，在 OAuth callback 時應該會看到正確的 redirect URL。或者直接測試登入流程，確認不會跳轉到 localhost。

## 相關文件

- [Discord OAuth2 文件](https://discord.com/developers/docs/topics/oauth2)
- [Render 環境變數設定](https://render.com/docs/environment-variables)
- [Netlify 環境變數設定](https://docs.netlify.com/environment-variables/overview/)
