# FastAPI Backend 部署到 Render (免費版)

## 前置準備

確保 `backend/` 資料夾有以下檔案：

```
backend/
├── Dockerfile
├── requirements.txt
└── app/
    └── main.py
```

## 步驟 1: 準備 Render 配置

在專案根目錄創建 `render.yaml`：

```yaml
services:
  - type: web
    name: your-app-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    plan: free
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: PORT
        value: 10000
    healthCheckPath: /health
```

## 步驟 2: 確保 Dockerfile 正確

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render 使用 PORT 環境變數
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 步驟 3: 添加健康檢查端點

在 `backend/app/main.py` 添加：

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## 步驟 4: 部署到 Render

1. 前往 [render.com](https://render.com)
2. 連接 GitHub repository
3. 選擇 "New Web Service"
4. 配置：
   - **Build Command**: (留空，使用 Docker)
   - **Start Command**: (留空，使用 Dockerfile CMD)
   - **Environment**: Docker
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Docker Context**: `./backend`

5. 設定環境變數：

   ```
   DATABASE_URL=<從 Render PostgreSQL 取得>
   SECRET_KEY=<你的密鑰>
   CORS_ORIGINS=https://your-app.vercel.app
   ```

6. 點擊 "Create Web Service"

## 步驟 5: 設定 PostgreSQL (可選)

1. 在 Render Dashboard 點擊 "New PostgreSQL"
2. 選擇免費方案
3. 複製 "Internal Database URL"
4. 在 Backend Web Service 設定環境變數 `DATABASE_URL`

## 免費版限制處理

### 冷啟動問題

免費版 15 分鐘無活動會休眠，解決方案：

**方案 A: 使用 Cron Job 保持喚醒**

使用 [cron-job.org](https://cron-job.org) 每 10 分鐘 ping 一次：

```
GET https://your-app-backend.onrender.com/health
```

**方案 B: 前端顯示載入狀態**

在 Next.js 中處理冷啟動：

```typescript
// frontend/lib/api/client.ts
const fetchWithRetry = async (url: string, options: RequestInit, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, { ...options, timeout: 30000 });
      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
};
```

## 驗證部署

```bash
# 測試健康檢查
curl https://your-app-backend.onrender.com/health

# 測試 API
curl https://your-app-backend.onrender.com/api/v1/...
```

## 常見問題

### Q: 為什麼第一次請求很慢？

A: 免費版會休眠，冷啟動需要 20-30 秒

### Q: 如何查看日誌？

A: Render Dashboard → 你的服務 → Logs

### Q: 資料庫 90 天後會刪除？

A: 是的，但可以匯出資料後重建新的免費資料庫

## 成本

- ✅ **完全免費**
- ⚠️ 有休眠限制
- ⚠️ 資料庫 90 天限制

## 升級選項

如果需要移除限制：

- **Starter Plan**: $7/月 (無休眠)
- **PostgreSQL**: $7/月 (永久保存)
