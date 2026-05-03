# 環境變數檔案結構說明

## 檔案位置

本專案採用**單一環境變數檔案**的架構：

```
project/
├── .env              # ✅ 唯一的環境變數檔案（本地開發用，不提交到 Git）
├── .env.example      # ✅ 環境變數範本（提交到 Git）
├── backend/          # ❌ 不再有 .env
└── frontend/         # ❌ 不再有 .env.local
```

## 為什麼這樣設計？

### 1. 統一管理

所有環境變數集中在一個檔案，避免散落在各個子目錄：

- ✅ 容易維護和更新
- ✅ 避免配置不一致
- ✅ 減少重複設定

### 2. Docker 友善

Docker Compose 從根目錄讀取 `.env`：

```yaml
services:
  backend:
    env_file: .env # 從根目錄讀取
  frontend:
    env_file: .env # 從根目錄讀取
```

### 3. 部署友善

正式部署時，環境變數直接在平台上設定：

- **Render**: Dashboard > Environment Variables
- **Netlify**: Site settings > Environment variables

不需要上傳 `.env` 檔案，更安全！

## 如何使用

### 本地開發

1. 複製範本：

   ```bash
   cp .env.example .env
   ```

2. 填入你的實際值：

   ```bash
   # 編輯 .env
   SUPABASE_URL=https://your-project.supabase.co
   DISCORD_TOKEN=your-token
   # ... 其他變數
   ```

3. 啟動服務：

   ```bash
   # Docker
   docker-compose up

   # 或分別啟動
   cd backend && uvicorn app.main:app --reload
   cd frontend && npm run dev
   ```

### 正式部署

**不要上傳 `.env` 檔案！**

在部署平台上設定環境變數：

#### Render (後端)

1. 前往 Dashboard > 選擇服務 > Environment
2. 新增所有後端需要的變數：
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `DISCORD_TOKEN`
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_REDIRECT_URI`
   - `GROQ_API_KEY`
   - `JWT_SECRET`
   - `CORS_ORIGINS`
   - `COOKIE_SECURE=true`
   - `FRONTEND_URL` ⭐ **重要！用於 OAuth redirect**
   - `APP_ENV=prod`

#### Netlify (前端)

1. 前往 Site settings > Environment variables
2. 新增前端需要的變數：
   - `NEXT_PUBLIC_API_BASE_URL`
   - `NEXT_PUBLIC_APP_NAME`
   - `NEXT_PUBLIC_APP_URL`

## 後端如何讀取環境變數

後端的 `config.py` 會從專案根目錄讀取 `.env`：

```python
# backend/app/core/config.py
model_config = SettingsConfigDict(
    env_file="../.env",  # 相對於 backend/ 目錄，指向根目錄
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False
)
```

在 Docker 或正式部署時，環境變數會從系統環境中讀取，不依賴檔案。

## 前端如何讀取環境變數

Next.js 會自動讀取根目錄的 `.env`：

- `NEXT_PUBLIC_*` 變數會在建置時注入到前端程式碼
- 其他變數只在伺服器端可用

## 環境變數優先順序

1. **系統環境變數** (最高優先)
   - Render/Netlify 上設定的變數
   - Docker Compose 的 `environment` 區塊

2. **`.env` 檔案**
   - 本地開發使用
   - 不提交到 Git

3. **程式碼預設值** (最低優先)
   - `config.py` 中的預設值

## 安全注意事項

### ✅ 應該做的

- 將 `.env` 加入 `.gitignore`
- 使用 `.env.example` 作為範本
- 在部署平台上設定環境變數
- 定期更新敏感資訊（JWT_SECRET、API Keys）

### ❌ 不應該做的

- 提交 `.env` 到 Git
- 在程式碼中硬編碼敏感資訊
- 在前端變數（`NEXT_PUBLIC_*`）中放敏感資訊
- 在多個地方重複設定相同的變數

## 常見問題

### Q: 為什麼不在 backend/ 和 frontend/ 各放一個 .env？

A:

1. 容易造成配置不一致
2. Docker Compose 需要從根目錄讀取
3. 維護成本高，容易遺漏更新

### Q: Docker 如何讀取根目錄的 .env？

A: Docker Compose 預設會讀取 `docker-compose.yml` 同層的 `.env` 檔案，並透過 `env_file: .env` 傳遞給容器。

### Q: 正式部署時需要 .env 檔案嗎？

A: 不需要！正式部署時，環境變數直接在平台上設定（Render/Netlify Dashboard），更安全且方便管理。

### Q: 如何確認環境變數有正確載入？

A:

```bash
# 後端：檢查 config
cd backend
python -c "from app.core.config import settings; print(settings.supabase_url)"

# 前端：檢查建置輸出
cd frontend
npm run build  # 會顯示載入的環境變數
```

## 相關文件

- [環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)
- [OAuth Redirect 修復](./deployment/oauth-redirect-fix.md)
- [Render 環境變數設定](./deployment/render-env-setup.md)
- [環境變數範本](../.env.example)
