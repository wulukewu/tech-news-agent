# 專案重構遷移指南

本指南說明如何將現有的 FastAPI 後端遷移到新的 `backend/` 目錄結構，以支援前後端分離的 Docker Compose 部署。

## 遷移步驟

### 1. 建立 backend 目錄並移動檔案

```bash
# 建立 backend 目錄
mkdir -p backend

# 移動後端相關檔案
mv app backend/
mv requirements.txt backend/
mv requirements-dev.txt backend/
mv pytest.ini backend/
mv tests backend/
mv scripts backend/
mv .env backend/

# 移動文件（可選）
cp -r docs backend/
cp README.md backend/
cp README_zh.md backend/
```

### 2. 更新 backend/.env 檔案

確保 `backend/.env` 包含 CORS 設定以允許前端訪問：

```env
# 新增或更新 CORS 設定
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. 驗證後端 Dockerfile

`backend/Dockerfile` 已經建立，內容與原本的 `Dockerfile` 相同。

### 4. 初始化前端專案

```bash
# 建立 frontend 目錄
mkdir -p frontend

# 進入 frontend 目錄
cd frontend

# 初始化 Next.js 專案
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# 安裝額外依賴
npm install @radix-ui/react-* class-variance-authority clsx tailwind-merge
npm install lucide-react date-fns
npm install -D @types/node
```

### 5. 配置前端環境變數

建立 `frontend/.env.local`：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Tech News Agent
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 6. 測試 Docker Compose

```bash
# 回到專案根目錄
cd ..

# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 測試後端
curl http://localhost:8000/health

# 測試前端
curl http://localhost:3000
```

### 7. 更新 Git 忽略檔案

確保 `.gitignore` 包含：

```gitignore
# Backend
backend/.env
backend/logs/
backend/__pycache__/
backend/venv/
backend/.pytest_cache/

# Frontend
frontend/.env.local
frontend/node_modules/
frontend/.next/
frontend/out/
frontend/build/
```

## 目錄結構對照

### 遷移前

```
tech-news-agent/
├── app/                    # FastAPI 應用
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── ...
```

### 遷移後

```
tech-news-agent/
├── backend/                # FastAPI 後端
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/               # Next.js 前端
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── Dockerfile
│   └── .env.local
└── docker-compose.yml      # 管理兩個服務
```

## 開發工作流程

### 本地開發（不使用 Docker）

**後端：**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

### 使用 Docker Compose

```bash
# 啟動所有服務
docker-compose up -d

# 重新建置
docker-compose up -d --build

# 停止服務
docker-compose down

# 查看日誌
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 常見問題

### Q: 後端無法連接到 Supabase

A: 確保 `backend/.env` 中的 Supabase 配置正確。

### Q: 前端無法連接到後端

A: 檢查以下項目：

1. `frontend/.env.local` 中的 `NEXT_PUBLIC_API_BASE_URL` 是否正確
2. `backend/.env` 中的 `CORS_ORIGINS` 是否包含前端 URL
3. 後端服務是否正在運行

### Q: Docker 容器無法啟動

A: 執行以下命令清理並重新建置：

```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

### Q: 需要保留舊的專案結構嗎？

A: 遷移完成並驗證無誤後，可以刪除根目錄的舊檔案：

- 舊的 `Dockerfile`（已移至 `backend/Dockerfile`）
- 根目錄的 `app/`（已移至 `backend/app/`）

但建議先備份或使用 Git 版本控制。

## 驗證清單

- [ ] 後端服務可以在 http://localhost:8000 訪問
- [ ] 前端服務可以在 http://localhost:3000 訪問
- [ ] 前端可以成功呼叫後端 API
- [ ] Discord OAuth2 登入流程正常
- [ ] CORS 配置正確，無跨域錯誤
- [ ] Docker Compose 可以同時啟動兩個服務
- [ ] 日誌正常輸出
- [ ] 環境變數正確載入

## 下一步

完成遷移後，可以開始實作 Phase 6 的前端功能：

1. 執行 Task 1: 專案初始化與基礎配置
2. 執行 Task 2: 型別定義與資料模型
3. 執行 Task 3: API 客戶端層實作
4. ...依照 tasks.md 順序執行

詳細實作計劃請參考 `.kiro/specs/web-dashboard-frontend/tasks.md`。
