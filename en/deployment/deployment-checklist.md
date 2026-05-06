# Netlify + Render 部署檢查清單

完整的免費版部署指南，確保順利上線。

## 📋 部署前檢查

### Backend (FastAPI)

- [ ] `backend/Dockerfile` 存在且正確
- [ ] `backend/requirements.txt` 包含所有依賴
- [ ] 有 `/health` 健康檢查端點
- [ ] 環境變數已準備好（`.env.example`）
- [ ] CORS 設定包含 Netlify 網域
- [ ] 資料庫連線使用環境變數

### Frontend (Next.js)

- [ ] `frontend/package.json` 包含所有依賴
- [ ] `@netlify/plugin-nextjs` 已安裝
- [ ] `netlify.toml` 配置正確
- [ ] `next.config.js` 配置正確
- [ ] API client 使用環境變數
- [ ] 處理 Render 冷啟動的 UI

## 🚀 部署步驟

### 第一步：部署 Backend 到 Render

1. **創建 Render 帳號**
   - 前往 https://render.com
   - 使用 GitHub 登入

2. **創建 Web Service**
   - Dashboard → New → Web Service
   - 連接 GitHub repository
   - 配置：
     ```
     Name: your-app-backend
     Environment: Docker
     Dockerfile Path: ./backend/Dockerfile
     Docker Context: ./backend
     Plan: Free
     ```

3. **設定環境變數**

   ```
   PORT=10000
   DATABASE_URL=<稍後設定>
   SECRET_KEY=<生成一個強密碼>
   CORS_ORIGINS=https://your-app.netlify.app,http://localhost:3000
   ```

4. **創建 PostgreSQL (可選)**
   - Dashboard → New → PostgreSQL
   - 選擇 Free plan
   - 複製 "Internal Database URL"
   - 回到 Web Service → Environment → 設定 `DATABASE_URL`

5. **部署並測試**

   ```bash
   # 等待部署完成（約 5-10 分鐘）
   # 測試健康檢查
   curl https://your-app-backend.onrender.com/health
   ```

6. **記錄 Backend URL**
   ```
   Backend URL: https://your-app-backend.onrender.com
   ```

### 第二步：部署 Frontend 到 Netlify

1. **創建 Netlify 帳號**
   - 前往 https://netlify.com
   - 使用 GitHub 登入

2. **創建 netlify.toml**

   在**專案根目錄**創建：

   ```toml
   [build]
     base = "frontend/"
     command = "npm run build"
     publish = ".next"

   [[plugins]]
     package = "@netlify/plugin-nextjs"

   [build.environment]
     NODE_VERSION = "18"

   [[redirects]]
     from = "/api/*"
     to = "https://your-app-backend.onrender.com/api/:splat"
     status = 200
     force = true

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

3. **安裝 Netlify Plugin**

   ```bash
   cd frontend
   npm install -D @netlify/plugin-nextjs
   git add package.json package-lock.json
   git commit -m "Add Netlify Next.js plugin"
   git push
   ```

4. **創建 Netlify Site**
   - Dashboard → Add new site → Import an existing project
   - 選擇 GitHub repository
   - 配置：
     ```
     Base directory: frontend
     Build command: npm run build
     Publish directory: .next
     ```

5. **設定環境變數**

   在 Netlify Dashboard → Site settings → Environment variables：

   ```
   NEXT_PUBLIC_API_URL=https://your-app-backend.onrender.com
   NEXT_PUBLIC_API_TIMEOUT=30000
   NODE_VERSION=18
   ```

6. **部署並測試**
   ```bash
   # 等待部署完成（約 3-5 分鐘）
   # 測試網站
   curl https://your-app.netlify.app
   ```

### 第三步：更新 Backend CORS

1. **更新 FastAPI CORS 設定**

   ```python
   # backend/app/main.py
   from fastapi.middleware.cors import CORSMiddleware

   origins = [
       "http://localhost:3000",
       "https://your-app.netlify.app",  # 替換成你的 Netlify URL
   ]

   app.add_middleware(
       CORSMiddleware,
       allow_origins=origins,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **推送更新**

   ```bash
   git add backend/app/main.py
   git commit -m "Update CORS for Netlify"
   git push
   ```

3. **等待 Render 自動重新部署**

### 第四步：設定 Cron Job (避免冷啟動)

1. **前往 cron-job.org**
   - 註冊免費帳號
   - 創建新的 Cron Job

2. **配置**

   ```
   Title: Keep Backend Alive
   URL: https://your-app-backend.onrender.com/health
   Schedule: Every 10 minutes
   ```

3. **啟用**

## ✅ 部署後驗證

### Backend 檢查

```bash
# 健康檢查
curl https://your-app-backend.onrender.com/health

# API 端點測試
curl https://your-app-backend.onrender.com/api/v1/...

# 檢查 CORS
curl -H "Origin: https://your-app.netlify.app" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://your-app-backend.onrender.com/api/v1/...
```

### Frontend 檢查

```bash
# 網站可訪問
curl https://your-app.netlify.app

# API 代理工作
curl https://your-app.netlify.app/api/health

# 檢查環境變數
# 在瀏覽器 Console:
console.log(process.env.NEXT_PUBLIC_API_URL)
```

### 功能測試

- [ ] 首頁載入正常
- [ ] API 請求成功
- [ ] 冷啟動時顯示載入訊息
- [ ] 表單提交正常
- [ ] 圖片載入正常
- [ ] 路由切換正常
- [ ] 手機版顯示正常

## 🔧 常見問題排查

### Backend 問題

**問題：部署失敗**

```bash
# 檢查 Render 日誌
# Dashboard → 你的服務 → Logs

# 常見原因：
# 1. Dockerfile 路徑錯誤
# 2. requirements.txt 缺少依賴
# 3. PORT 環境變數未設定
```

**問題：API 請求 500 錯誤**

```bash
# 檢查環境變數
# Dashboard → 你的服務 → Environment

# 檢查資料庫連線
# 確保 DATABASE_URL 正確
```

**問題：CORS 錯誤**

```python
# 確認 CORS origins 包含 Netlify URL
origins = [
    "https://your-app.netlify.app",
    "https://your-custom-domain.com",
]
```

### Frontend 問題

**問題：建置失敗**

```bash
# 檢查 Netlify 建置日誌
# Dashboard → Deploys → 點擊失敗的部署

# 常見原因：
# 1. Node 版本不符
# 2. 依賴安裝失敗
# 3. TypeScript 錯誤
```

**問題：API 請求失敗**

```javascript
// 檢查環境變數
console.log(process.env.NEXT_PUBLIC_API_URL);

// 檢查 netlify.toml 重定向規則
// 確保 /api/* 正確代理到 Render
```

**問題：頁面 404**

```toml
# 確保 netlify.toml 有重定向規則
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## 📊 監控與維護

### Render 監控

- **日誌**: Dashboard → 你的服務 → Logs
- **指標**: Dashboard → 你的服務 → Metrics
- **健康檢查**: 設定 `/health` 端點

### Netlify 監控

- **Analytics**: Dashboard → Analytics
- **建置歷史**: Dashboard → Deploys
- **Function 日誌**: Dashboard → Functions

### 定期檢查

- [ ] 每週檢查 Render 是否正常運行
- [ ] 每月檢查 Netlify 頻寬使用量
- [ ] 每月檢查 Render 資料庫（90 天限制）
- [ ] 定期更新依賴套件

## 💰 成本追蹤

### 免費額度

**Render:**

- ✅ 750 小時/月運行時間
- ⚠️ 15 分鐘無活動會休眠
- ⚠️ PostgreSQL 90 天後刪除

**Netlify:**

- ✅ 100GB 頻寬/月
- ✅ 300 分鐘建置時間/月
- ✅ 125k Function 請求/月

### 升級時機

**需要升級 Render ($7/月) 如果：**

- 無法接受冷啟動延遲
- 需要永久資料庫
- 需要更多 RAM

**需要升級 Netlify ($19/月) 如果：**

- 超過 100GB 頻寬
- 需要更多建置時間
- 需要團隊協作功能

## 🎉 部署完成！

恭喜！你的應用已經成功部署到：

- **Frontend**: https://your-app.netlify.app
- **Backend**: https://your-app-backend.onrender.com

### 下一步

1. **設定自訂網域** (可選)
   - Netlify: Dashboard → Domain settings
   - Render: Dashboard → Settings → Custom Domain

2. **設定 Analytics** (可選)
   - Google Analytics
   - Netlify Analytics

3. **設定監控** (可選)
   - Sentry (錯誤追蹤)
   - LogRocket (使用者行為)

4. **優化效能**
   - 啟用圖片優化
   - 使用 ISR
   - 添加快取策略

## 📚 相關文件

- [Netlify Frontend 詳細指南](./netlify-frontend.md)
- [Render Backend 詳細指南](./render-backend.md)
- [Vercel Frontend 替代方案](./vercel-frontend.md)
