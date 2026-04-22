# Docker 開發環境 vs 正式環境比較

## 📊 快速比較表

| 特性                    | 開發環境             | 正式環境                  |
| ----------------------- | -------------------- | ------------------------- |
| **配置檔案**            | `docker-compose.yml` | `docker-compose.prod.yml` |
| **Backend Dockerfile**  | `Dockerfile.dev`     | `Dockerfile`              |
| **Frontend Dockerfile** | `Dockerfile.dev`     | `Dockerfile`              |
| **Hot Reloading**       | ✅ 啟用              | ❌ 停用                   |
| **Volume 掛載**         | ✅ 完整程式碼        | ⚠️ 僅日誌                 |
| **建置時間**            | 快速                 | 較慢 (多階段建置)         |
| **映像檔大小**          | 較大                 | 較小 (優化)               |
| **啟動指令**            | `make dev`           | `make prod`               |
| **適用場景**            | 本地開發、測試       | 部署、生產環境            |

---

## 🔧 Backend 差異

### 開發環境 (Dockerfile.dev)

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- 使用 `--reload` 參數
- 監控檔案變更
- 自動重新載入

### 正式環境 (Dockerfile)

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- 無 `--reload` 參數
- 穩定運行
- 更好的效能

### Volume 掛載

**開發環境:**

```yaml
volumes:
  - ./backend/app:/app/app # 程式碼同步
  - ./backend/logs:/app/logs # 日誌持久化
```

**正式環境:**

```yaml
volumes:
  - ./backend/logs:/app/logs # 僅日誌持久化
```

---

## 🎨 Frontend 差異

### 開發環境 (Dockerfile.dev)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

- 單階段建置
- 使用 `npm run dev`
- 包含開發依賴

### 正式環境 (Dockerfile)

```dockerfile
FROM node:20-alpine AS base
# ... 多階段建置 ...
FROM base AS deps
# ... 安裝依賴 ...
FROM base AS builder
# ... 建置應用 ...
FROM base AS runner
# ... 運行應用 ...
CMD ["node", "server.js"]
```

- 多階段建置
- 使用 Next.js standalone 輸出
- 僅包含生產依賴
- 更小的最終映像檔

### Volume 掛載

**開發環境:**

```yaml
volumes:
  - ./frontend:/app # 整個專案同步
  - /app/node_modules # 排除 node_modules
  - /app/.next # 排除 .next
```

**正式環境:**

```yaml
# 無 volume 掛載
# 使用建置後的檔案
```

---

## 🌐 環境變數差異

### 開發環境

```yaml
environment:
  - NODE_ENV=development
  - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 正式環境

```yaml
environment:
  - NODE_ENV=production
  - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 # 應改為正式網域
```

---

## 🚀 啟動指令比較

### 開發環境

```bash
# 使用 Makefile
make dev
make logs-dev
make down-dev

# 使用 Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### 正式環境

```bash
# 使用 Makefile
make prod
make logs-prod
make down-prod

# 使用 Docker Compose
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
```

---

## 📦 容器命名差異

### 開發環境

- `tech-news-agent-backend-dev`
- `tech-news-agent-frontend-dev`

### 正式環境

- `tech-news-agent-backend`
- `tech-news-agent-frontend`

---

## 🔄 Hot Reloading 機制

### Backend (FastAPI)

**開發環境:**

- Uvicorn 的 `--reload` 參數
- 監控 Python 檔案變更
- 自動重新載入模組
- Volume 掛載 `./backend/app:/app/app`

**正式環境:**

- 無 hot reloading
- 程式碼打包進映像檔
- 需重新建置才能更新

### Frontend (Next.js)

**開發環境:**

- Next.js dev server (`npm run dev`)
- Webpack HMR (Hot Module Replacement)
- `next.config.js` 配置 `watchOptions`:
  ```javascript
  webpackDevMiddleware: (config) => {
    config.watchOptions = {
      poll: 1000, // 每秒檢查
      aggregateTimeout: 300, // 300ms 後觸發
    };
    return config;
  };
  ```
- Volume 掛載整個專案

**正式環境:**

- Next.js production server (`node server.js`)
- 無 HMR
- 使用預先建置的檔案
- 需重新建置才能更新

---

## 💡 使用建議

### 何時使用開發環境？

- ✅ 本地開發
- ✅ 功能測試
- ✅ 快速迭代
- ✅ 除錯

### 何時使用正式環境？

- ✅ 部署到伺服器
- ✅ 效能測試
- ✅ 生產環境
- ✅ 最終驗證

---

## 🔄 切換環境

### 從開發切換到正式

```bash
make down-dev
make prod
```

### 從正式切換到開發

```bash
make down-prod
make dev
```

### 同時運行（不建議）

如果需要同時運行，修改其中一個的 port 映射：

```yaml
ports:
  - '3001:3000' # 前端改用 3001
  - '8001:8000' # 後端改用 8001
```

---

## 📈 效能比較

| 指標           | 開發環境        | 正式環境      |
| -------------- | --------------- | ------------- |
| **啟動速度**   | 快              | 中等          |
| **建置時間**   | 快 (無建置)     | 慢 (完整建置) |
| **記憶體使用** | 較高            | 較低          |
| **CPU 使用**   | 較高 (監控檔案) | 較低          |
| **映像檔大小** | 較大            | 較小          |
| **回應速度**   | 中等            | 快            |

---

## 🎯 最佳實踐

1. **開發時使用開發環境**
   - 享受 hot reloading
   - 快速迭代

2. **部署前測試正式環境**
   - 確保建置成功
   - 驗證生產配置

3. **不要在正式環境開發**
   - 沒有 hot reloading
   - 每次修改需重新建置

4. **使用 Makefile 簡化指令**
   - `make dev` 比 `docker-compose up -d` 簡單
   - 統一團隊指令

5. **定期清理**
   - `make clean` 清理未使用的容器和映像檔
   - 釋放磁碟空間
