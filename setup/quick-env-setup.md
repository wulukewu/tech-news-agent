# 環境變數快速設定指南

## 🚀 本地開發（5 分鐘設定）

### 1. 複製環境變數範本

```bash
cp .env.example .env
```

### 2. 填入必要的值

編輯 `.env` 檔案，填入以下必填項目：

```bash
# Supabase (必填)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Discord Bot (必填)
DISCORD_TOKEN=your-discord-bot-token
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret

# Groq API (必填)
GROQ_API_KEY=your-groq-api-key

# JWT (必填 - 使用以下指令生成)
JWT_SECRET=$(openssl rand -hex 32)
```

### 3. 啟動服務

```bash
# 使用 Docker (推薦)
docker-compose up

# 或手動啟動
# 後端
cd backend && uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev
```

## 🌐 正式部署（Render + Netlify）

### Render 後端環境變數

在 Render Dashboard > Environment 設定：

```bash
# 基礎配置
APP_ENV=prod
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Discord
DISCORD_TOKEN=your-token
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=https://your-api.render.com/api/auth/discord/callback

# LLM
GROQ_API_KEY=your-key

# 安全性
JWT_SECRET=your-secure-random-secret-32-chars-minimum
COOKIE_SECURE=true

# CORS & Frontend
CORS_ORIGINS=https://your-frontend.netlify.app
FRONTEND_URL=https://your-frontend.netlify.app  # ⭐ 重要！
```

### Netlify 前端環境變數

在 Netlify Site settings > Environment variables 設定：

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api.render.com
NEXT_PUBLIC_APP_NAME=Tech News Agent
NEXT_PUBLIC_APP_URL=https://your-frontend.netlify.app
```

## ⚠️ 重要提醒

### ✅ 應該做的

- 將 `.env` 加入 `.gitignore`（已設定）
- 使用強隨機的 `JWT_SECRET`
- 正式環境設定 `COOKIE_SECURE=true`
- 定期更新 API Keys

### ❌ 不應該做的

- 提交 `.env` 到 Git
- 在前端變數（`NEXT_PUBLIC_*`）中放敏感資訊
- 在 `backend/` 或 `frontend/` 子目錄中創建 `.env` 檔案

## 📁 檔案結構

```
project/
├── .env              # ✅ 唯一的環境變數檔案（本地開發）
├── .env.example      # ✅ 範本（提交到 Git）
├── backend/          # ❌ 不要在這裡放 .env
└── frontend/         # ❌ 不要在這裡放 .env.local
```

## 🔍 驗證設定

### 檢查後端配置

```bash
cd backend
python3 -c "from app.core.config import settings; print(f'✅ Frontend URL: {settings.frontend_url}')"
```

### 檢查前端配置

```bash
cd frontend
npm run build  # 會顯示載入的環境變數
```

## 🐛 常見問題

### OAuth redirect 到 localhost

**原因**: Render 上沒有設定 `FRONTEND_URL`

**解決**: 在 Render 新增環境變數 `FRONTEND_URL=https://your-frontend.netlify.app`

### CORS 錯誤

**原因**: `CORS_ORIGINS` 與前端網址不符

**解決**: 確保 `CORS_ORIGINS` 包含前端的完整網址（含 https://）

### Config 載入失敗

**原因**: `.env` 檔案不存在或格式錯誤

**解決**:

```bash
# 重新複製範本
cp .env.example .env
# 檢查格式（不要有多餘的引號或空格）
```

## 📚 詳細文件

- [環境變數檔案結構說明](./docs/ENV_FILE_STRUCTURE.md)
- [OAuth Redirect 修復指南](./docs/deployment/oauth-redirect-fix.md)
- [Render 環境變數設定](./docs/deployment/render-env-setup.md)
- [完整環境變數參考](./docs/setup/ENV_SETUP_GUIDE.md)
