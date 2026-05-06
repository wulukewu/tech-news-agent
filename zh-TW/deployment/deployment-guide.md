# 部署指南

## 1. 先決條件

### 所需帳戶

- **Supabase** — [supabase.com](https://supabase.com) (資料庫 + pgvector)
- **Groq** — [console.groq.com](https://console.groq.com) (LLM API)
- **Discord** — [discord.com/developers](https://discord.com/developers/applications) (OAuth + 機器人)
- **Netlify** 或 **Vercel** — 前端託管
- **Render** 或 **Railway** — 後端託管

### 所需軟體

- Docker + Docker Compose
- Node.js >= 18
- Python >= 3.11

---

## 2. 環境配置

將 `.env.example` 複製到 `.env` 並填寫值：

```bash
cp .env.example .env
```

### 必需變數

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI
GROQ_API_KEY=your-groq-api-key

# JWT
JWT_SECRET_KEY=your-secret-key   # 生成：openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth (網頁登入)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# 前端
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 可選變數

```bash
# Discord 機器人
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id

# 排程器
SCHEDULER_CRON=0 */6 * * *
SCHEDULER_TIMEZONE=Asia/Taipei
TIMEZONE=Asia/Taipei
```

---

## 3. 資料庫設定

專案使用 Supabase (PostgreSQL + pgvector)。沒有 Alembic — 所有 Schema 管理都透過純 SQL 文件完成。

### 初始設定

1. 打開您的 Supabase 專案 → **SQL 編輯器**
2. 運行 `backend/scripts/init_supabase.sql` 的全部內容
3. 在 **表格編輯器** 中驗證表格是否已創建

### 應用遷移

對於後續的 Schema 變更，請按順序運行遷移文件：

**選項 A — Supabase SQL 編輯器 (手動)：**

打開 `backend/scripts/migrations/` 中的每個文件，並在 SQL 編輯器中按順序運行它們。

**選項 B — 遷移腳本：**

```bash
python3 scripts/run_migrations.py
```

---

## 4. 開發部署

### Docker Compose (推薦)

```bash
# 啟動所有服務並熱重載
make dev
# 或
docker-compose up -d

# 查看日誌
make logs-dev
# 或
docker-compose logs -f

# 停止並清理
make clean
```

啟動的服務：
- 後端 (FastAPI + Discord 機器人)：`http://localhost:8000`
- 前端 (Next.js)：`http://localhost:3000`
- API 文件：`http://localhost:8000/docs`

### 本地 (無 Docker)

```bash
# 後端
cd backend
pip install -r requirements.txt
python -m app.main

# 前端 (另一個終端機)
cd frontend
npm install
npm run dev
```

---

## 5. 生產部署

### Docker Compose (自託管)

```bash
# 啟動生產堆棧
make prod
# 或
docker-compose -f docker-compose.prod.yml up -d

# 查看日誌
make logs-prod
# 或
docker-compose -f docker-compose.prod.yml logs -f
```

在啟動前更新 `.env` 中的生產值：
- 將 `DISCORD_REDIRECT_URI` 設定為您的生產前端 URL
- 將 `NEXT_PUBLIC_API_URL` 設定為您的生產後端 URL

### 前端 — Netlify

有關完整設定，請參閱 [netlify-frontend.md](./netlify-frontend.md)。

快速步驟：
1. 將您的 GitHub 儲存庫連接到 Netlify
2. 設定建置命令：`npm run build`
3. 設定發布目錄：`.next` (或用於靜態導出的 `out`)
4. 在 Netlify 儀表板中添加所有 `NEXT_PUBLIC_*` 環境變數

### 後端 — Render

有關完整設定，請參閱 [render-deployment.md](./render-deployment.md)。

快速步驟：
1. 在 Render 上創建一個指向您的儲存庫的新的 **Web Service**
2. 設定啟動命令：`python -m app.main`
3. 在 Render 儀表板中添加所有必需的環境變數
4. 將 `DISCORD_REDIRECT_URI` 和 `NEXT_PUBLIC_API_URL` 設定為生產 URL

---

## 6. 健康檢查

```bash
# 應用程式健康
GET /health

# 排程器健康
GET /health/scheduler
```

範例：

```bash
curl https://your-backend-url/health
curl https://your-backend-url/health/scheduler
```

這兩個端點都返回帶有狀態信息的 JSON。將它們用於運行時間監控和部署驗證。

---

## 7. 故障排除

**缺少表格 / 資料庫錯誤：**

```bash
cd backend
python3 scripts/verify_bot_health.py
python3 scripts/apply_missing_migration.py
```

**Discord 機器人沒有回應：**
- 驗證 `DISCORD_TOKEN` 已設定且有效
- 檢查機器人在開發者門戶中是否具有正確的權限和 OAuth 範圍

**文章無法抓取：**
- 檢查排程器日誌：`make logs-dev` 或 `docker-compose logs -f backend`
- 驗證 RSS Feed URL 可訪問
- 確認 `GROQ_API_KEY` 有效且有可用額度

**前端無法連接後端：**
- 確認 `NEXT_PUBLIC_API_URL` 指向正確的後端 URL
- 如果前端和後端在不同的網域，請檢查 CORS 設定

**Auth 回調錯誤：**
- 確保 `DISCORD_REDIRECT_URI` 與 Discord 開發者門戶中註冊的 URI 完全匹配
