# Docker Compose 部署指南

本專案已重構為前後端分離架構，支援使用 Docker Compose 一鍵啟動完整服務。

## 專案結構

```
tech-news-agent/
├── backend/                 # FastAPI 後端
│   ├── app/                # 應用程式碼
│   ├── requirements.txt    # Python 依賴
│   ├── Dockerfile          # 後端 Docker 配置
│   └── .env                # 後端環境變數
├── frontend/               # Next.js 前端
│   ├── app/                # Next.js App Router
│   ├── components/         # React 元件
│   ├── lib/                # 工具函式和 API 客戶端
│   ├── package.json        # Node.js 依賴
│   ├── Dockerfile          # 前端 Docker 配置
│   └── .env.local          # 前端環境變數
└── docker-compose.yml      # Docker Compose 配置
```

## 快速開始

### 1. 準備環境變數

#### 後端環境變數 (backend/.env)

複製現有的 `.env` 檔案到 `backend/` 目錄：

```bash
cp .env backend/.env
```

確保包含以下必要變數：

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback

# JWT Configuration
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### 前端環境變數 (frontend/.env.local)

建立 `frontend/.env.local` 檔案：

```bash
cp frontend/.env.example frontend/.env.local
```

內容：

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=Tech News Agent
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 2. 啟動服務

使用 Docker Compose 啟動所有服務：

```bash
docker-compose up -d
```

這將啟動：

- **Backend (FastAPI)**: http://localhost:8000
- **Frontend (Next.js)**: http://localhost:3000

### 3. 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 只查看後端日誌
docker-compose logs -f backend

# 只查看前端日誌
docker-compose logs -f frontend
```

### 4. 停止服務

```bash
docker-compose down
```

## 開發模式

如果你想在本地開發而不使用 Docker：

### 後端開發

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端開發

```bash
cd frontend
npm install
npm run dev
```

## API 文件

後端 API 文件可在以下位置訪問：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 健康檢查

- Backend Health: http://localhost:8000/health
- Frontend: http://localhost:3000

## 故障排除

### 後端無法連接到 Supabase

確保 `backend/.env` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 正確。

### 前端無法連接到後端

1. 確認後端服務正在運行：`docker-compose ps`
2. 檢查 `frontend/.env.local` 中的 `NEXT_PUBLIC_API_BASE_URL` 是否正確
3. 確認 `backend/.env` 中的 `CORS_ORIGINS` 包含 `http://localhost:3000`

### 重新建置映像

如果修改了 Dockerfile 或依賴項：

```bash
docker-compose up -d --build
```

### 清理所有容器和映像

```bash
docker-compose down -v
docker system prune -a
```

## 生產部署

生產環境部署時，請注意：

1. 使用 HTTPS 並更新所有 URL
2. 設置強密碼和安全的 JWT_SECRET
3. 配置適當的 CORS_ORIGINS
4. 使用環境變數管理工具（如 AWS Secrets Manager）
5. 配置反向代理（如 Nginx）
6. 啟用日誌收集和監控

## 更多資訊

- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [Next.js 文件](https://nextjs.org/docs)
- [Docker Compose 文件](https://docs.docker.com/compose/)
