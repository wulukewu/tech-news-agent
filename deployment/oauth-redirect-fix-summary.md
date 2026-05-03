# OAuth Redirect 修復總結

## 🎯 問題

Discord OAuth 登入後重定向到 `http://localhost:3000/auth/callback` 而不是正式網域。

## ✅ 已完成的修復

### 1. 程式碼修改

#### backend/app/core/config.py

- ✅ 新增 `frontend_url` 配置欄位
- ✅ 新增 `frontend_url` validator
- ✅ 更新 `model_config` 從根目錄讀取 `.env` (`env_file="../.env"`)
- ✅ 更新 `get_env_file()` 函數指向根目錄
- ✅ 新增正式環境驗證規則

#### backend/app/api/auth.py

- ✅ 移除 `os.getenv("NEXT_PUBLIC_APP_URL")` 的錯誤用法
- ✅ 改用 `settings.frontend_url`

### 2. 環境變數結構重組

#### 統一環境變數管理

- ✅ 刪除 `backend/.env`
- ✅ 刪除 `frontend/.env.local`
- ✅ 統一使用根目錄的 `.env`
- ✅ 更新 `.env.example` 加入 `FRONTEND_URL` 說明

#### 檔案結構

```
project/
├── .env              # ✅ 唯一的環境變數檔案
├── .env.example      # ✅ 更新的範本
├── backend/          # ❌ 已刪除 .env
└── frontend/         # ❌ 已刪除 .env.local
```

### 3. 文件更新

#### 新增文件

- ✅ `docs/deployment/oauth-redirect-fix.md` - 詳細修復指南
- ✅ `docs/deployment/render-env-setup.md` - Render 環境變數設定
- ✅ `docs/ENV_FILE_STRUCTURE.md` - 環境變數檔案結構說明
- ✅ `QUICK_ENV_SETUP.md` - 快速設定指南

#### 更新文件

- ✅ `docs/README.md` - 加入新文件索引
- ✅ `README.md` - 加入快速設定連結
- ✅ `README_zh.md` - 加入快速設定連結
- ✅ `.env.example` - 加入 `FRONTEND_URL` 說明

## 📋 部署檢查清單

### Render 後端環境變數

在 Render Dashboard > Environment 新增：

```bash
# ⭐ 新增的關鍵變數
FRONTEND_URL=https://your-frontend.netlify.app

# 其他必要變數
APP_ENV=prod
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
DISCORD_TOKEN=your-token
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=https://your-api.render.com/api/auth/discord/callback
GROQ_API_KEY=your-key
JWT_SECRET=your-secure-secret-32-chars-min
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7
CORS_ORIGINS=https://your-frontend.netlify.app
COOKIE_SECURE=true
RATE_LIMIT_PER_MINUTE_UNAUTH=100
RATE_LIMIT_PER_MINUTE_AUTH=300
```

### Discord Developer Portal

確保 OAuth2 Redirects 包含：

```
https://your-api.render.com/api/auth/discord/callback
```

## 🧪 驗證步驟

### 1. 本地測試

```bash
# 測試配置載入
cd backend
python3 -c "from app.core.config import settings; print(f'Frontend URL: {settings.frontend_url}')"

# 預期輸出
Frontend URL: http://localhost:3000
```

### 2. 部署後測試

1. 前往前端網站
2. 點擊「使用 Discord 登入」
3. 完成 Discord 授權
4. ✅ 確認重定向到 `https://your-frontend.netlify.app/auth/callback?token=...`
5. ❌ 不應該重定向到 `http://localhost:3000/auth/callback`

## 🔧 技術細節

### 為什麼之前會失敗？

```python
# ❌ 錯誤做法
frontend_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
```

問題：

1. `NEXT_PUBLIC_APP_URL` 是前端環境變數
2. 後端環境中不存在這個變數
3. 總是使用預設值 `http://localhost:3000`

### 正確做法

```python
# ✅ 正確做法
from app.core.config import settings

frontend_url = settings.frontend_url  # 從配置讀取
```

優點：

1. 統一配置管理
2. 型別安全（Pydantic 驗證）
3. 環境特定驗證（正式環境必須 HTTPS）
4. 清晰的錯誤訊息

## 📚 相關資源

### 文件

- [OAuth Redirect 修復指南](./oauth-redirect-fix.md)
- [Render 環境變數設定](./render-env-setup.md)
- [環境變數檔案結構](../ENV_FILE_STRUCTURE.md)
- [快速設定指南](../../QUICK_ENV_SETUP.md)

### 外部連結

- [Discord OAuth2 文件](https://discord.com/developers/docs/topics/oauth2)
- [Render 環境變數](https://render.com/docs/environment-variables)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

## 🎉 預期結果

修復完成後：

1. ✅ 本地開發：OAuth 重定向到 `http://localhost:3000/auth/callback`
2. ✅ 正式環境：OAuth 重定向到 `https://your-frontend.netlify.app/auth/callback`
3. ✅ 環境變數統一管理在根目錄 `.env`
4. ✅ Docker 和部署平台都能正確讀取配置
5. ✅ 完整的文件和驗證流程

---

**修復日期**: 2026-04-17
**影響範圍**: Discord OAuth 登入流程
**向後相容**: 是（只需新增 `FRONTEND_URL` 環境變數）
