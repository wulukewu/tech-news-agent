# Docker Compose 使用指南

本專案提供兩種 Docker Compose 配置：

## 🔧 開發環境 (Development)

使用 `docker-compose.yml` 進行開發，支援 hot reloading。

### 啟動開發環境

```bash
docker-compose up -d
```

### 查看日誌

```bash
docker-compose logs -f
```

### 停止開發環境

```bash
docker-compose down
```

### 特點

- ✅ 前端 Next.js hot reloading (檔案變更自動重新載入)
- ✅ 後端 FastAPI hot reloading (程式碼變更自動重新載入)
- ✅ 本地程式碼透過 volume 掛載到容器
- ✅ 適合快速開發和測試

### Volume 掛載

- Backend: `./backend/app` → `/app/app` (程式碼同步)
- Frontend: `./frontend` → `/app` (整個專案同步，排除 node_modules 和 .next)

---

## 🚀 正式環境 (Production)

使用 `docker-compose.prod.yml` 進行部署，不包含 hot reloading。

### 啟動正式環境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 查看日誌

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 停止正式環境

```bash
docker-compose -f docker-compose.prod.yml down
```

### 特點

- ✅ 優化的生產環境建置
- ✅ 不包含開發工具和 hot reloading
- ✅ 更小的映像檔大小
- ✅ 更好的效能和安全性

---

## 📋 Dockerfile 說明

### 開發環境 Dockerfiles

- `backend/Dockerfile.dev` - FastAPI 開發版本 (含 --reload)
- `frontend/Dockerfile.dev` - Next.js 開發版本 (npm run dev)

### 正式環境 Dockerfiles

- `backend/Dockerfile` - FastAPI 生產版本
- `frontend/Dockerfile` - Next.js 生產版本 (多階段建置)

---

## 🔄 常用指令

### 重新建置映像檔

開發環境：

```bash
docker-compose build
```

正式環境：

```bash
docker-compose -f docker-compose.prod.yml build
```

### 重新建置並啟動

開發環境：

```bash
docker-compose up -d --build
```

正式環境：

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 查看運行中的容器

```bash
docker-compose ps
```

### 進入容器內部

Backend:

```bash
docker exec -it tech-news-agent-backend-dev bash  # 開發環境
docker exec -it tech-news-agent-backend bash      # 正式環境
```

Frontend:

```bash
docker exec -it tech-news-agent-frontend-dev sh   # 開發環境
docker exec -it tech-news-agent-frontend sh       # 正式環境
```

---

## ⚙️ 環境變數設定

確保以下檔案已正確設定：

- `backend/.env` - 後端環境變數
- `frontend/.env.local` - 前端環境變數

參考 `.env.example` 和 `frontend/.env.example` 進行設定。

---

## 🐛 疑難排解

### 前端 hot reloading 不工作

1. 確認 volume 掛載正確
2. 檢查 `next.config.js` 是否有 `watchOptions` 設定
3. 重新建置容器：`docker-compose up -d --build`

### 後端 hot reloading 不工作

1. 確認 `--reload` 參數存在於 CMD
2. 檢查 volume 掛載路徑
3. 查看容器日誌：`docker-compose logs backend`

### Port 衝突

如果 port 3000 或 8000 已被佔用：

1. 修改 `docker-compose.yml` 中的 ports 映射
2. 例如：`"3001:3000"` 或 `"8001:8000"`

---

## 📦 部署建議

### 開發流程

1. 使用 `docker-compose.yml` 進行本地開發
2. 程式碼變更會自動反映在容器中
3. 測試完成後提交程式碼

### 部署流程

1. 在伺服器上使用 `docker-compose.prod.yml`
2. 設定正確的環境變數
3. 使用 `--build` 確保使用最新程式碼
4. 考慮使用 CI/CD 自動化部署

### 安全性建議

- 不要在正式環境使用 `.env.local` 的開發設定
- 確保 `JWT_SECRET` 使用強密碼
- 設定 `COOKIE_SECURE=true` 在正式環境
- 使用 HTTPS 並設定正確的 `CORS_ORIGINS`
