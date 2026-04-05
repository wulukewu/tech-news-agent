# 快速開始指南

## 🚀 快速啟動

### 方法 1: 使用 Makefile (推薦)

```bash
# 開發環境
make dev          # 啟動
make logs-dev     # 查看日誌
make down-dev     # 停止

# 正式環境
make prod         # 啟動
make logs-prod    # 查看日誌
make down-prod    # 停止
```

### 方法 2: 使用 Docker Compose

```bash
# 開發環境
docker-compose up -d
docker-compose logs -f
docker-compose down

# 正式環境
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
```

---

## 📝 首次設定

1. 複製環境變數範例檔案：

```bash
cp .env.example .env
```

2. 編輯環境變數檔案，填入必要的設定值：

```bash
nano .env
```

詳細的環境變數說明請參考 [ENV_SETUP_GUIDE.md](./setup/ENV_SETUP_GUIDE.md)

3. 啟動開發環境：

```bash
make dev
# 或
docker-compose up -d
```

4. 訪問應用程式：
   - 前端: http://localhost:3000
   - 後端 API: http://localhost:8000
   - API 文件: http://localhost:8000/docs

---

## 🔄 開發流程

### 前端開發

1. 修改 `frontend/` 目錄下的檔案
2. 儲存後瀏覽器會自動重新載入 (hot reload)
3. 無需重啟容器

### 後端開發

1. 修改 `backend/app/` 目錄下的檔案
2. 儲存後 FastAPI 會自動重新載入 (hot reload)
3. 無需重啟容器

### 安裝新的套件

**前端 (Node.js):**

```bash
# 進入容器
docker exec -it tech-news-agent-frontend-dev sh

# 安裝套件
npm install <package-name>

# 退出容器
exit

# 重新建置 (如果需要)
make build-dev
```

**後端 (Python):**

```bash
# 進入容器
docker exec -it tech-news-agent-backend-dev bash

# 安裝套件
pip install <package-name>

# 更新 requirements.txt
pip freeze > requirements.txt

# 退出容器
exit

# 重新建置
make build-dev
```

---

## 🐛 常見問題

### Q: Hot reload 不工作？

A: 嘗試重新建置容器：

```bash
make up-dev
# 或
docker-compose up -d --build
```

### Q: Port 已被佔用？

A: 修改 `docker-compose.yml` 中的 port 映射：

```yaml
ports:
  - '3001:3000' # 改用 3001
```

### Q: 容器無法啟動？

A: 檢查日誌找出問題：

```bash
make logs-dev
# 或
docker-compose logs
```

### Q: 如何清理所有容器和映像檔？

A: 使用清理指令：

```bash
make clean
```

---

## 📊 查看 Makefile 所有指令

```bash
make help
```

輸出範例：

```
可用指令：
  dev             啟動開發環境 (hot reloading)
  build-dev       重新建置開發環境映像檔
  up-dev          重新建置並啟動開發環境
  down-dev        停止開發環境
  logs-dev        查看開發環境日誌
  prod            啟動正式環境
  build-prod      重新建置正式環境映像檔
  up-prod         重新建置並啟動正式環境
  down-prod       停止正式環境
  logs-prod       查看正式環境日誌
  clean           清理所有容器、映像檔和 volumes
  restart-dev     重啟開發環境
  restart-prod    重啟正式環境
  ps              查看運行中的容器
```

---

## 🎯 部署到正式環境

1. 確保環境變數已正確設定（特別是安全性相關設定）

2. 使用正式環境配置啟動：

```bash
make prod
# 或
docker-compose -f docker-compose.prod.yml up -d --build
```

3. 檢查服務狀態：

```bash
make logs-prod
```

4. 訪問應用程式（使用您的網域或 IP）

---

## 📚 更多資訊

詳細說明請參考 [DOCKER_GUIDE.md](./docker/DOCKER_GUIDE.md)
