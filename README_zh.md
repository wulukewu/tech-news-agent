# Tech News Agent

一個自動化技術資訊策展系統，結合 FastAPI 後端、Next.js Web 介面、Discord Bot 和 Groq LLM。自動抓取 RSS 訂閱源、使用 AI 分析文章，並透過 Web Dashboard 和 Discord DM 提供個人化的技術新聞。

## 🌟 核心功能

### 📱 多平台存取

- **Web Dashboard**：現代化的 Next.js 介面，支援深色模式
- **Discord Bot**：互動式指令和 DM 通知
- **REST API**：完整的 API 供程式化存取

### 🤖 AI 驅動智能

- **智慧評分**：使用 Groq (Llama 3.1 8B) 評估技術深度
- **AI 摘要**：使用 Llama 3.3 70B 生成精簡摘要
- **個人化推薦**：從你的評分學習，推薦相關內容
- **深度分析**：隨選的詳細技術解析

### 👥 多租戶架構

- **個人訂閱**：每個使用者管理自己的 RSS 訂閱源
- **私人閱讀清單**：獨立評分和整理文章
- **自訂通知**：控制何時以及如何接收更新
- **資料隔離**：使用者之間完全隱私

### ⚡ 彈性排程

- **自動抓取**：可配置的背景排程器（預設：每 6 小時）
- **手動觸發**：透過 Web、Discord 或 API 即時抓取文章
- **智慧通知**：文章處理後 10 分鐘發送 DM

### 🗄️ 強大資料層

- **Supabase/PostgreSQL**：可靠的資料儲存，支援 pgvector
- **語義搜尋就緒**：向量嵌入供未來 AI 驅動搜尋
- **高效索引**：使用適當的資料庫索引優化查詢

## 🚀 快速開始

> **⚡ 快速設定**: 查看 [環境變數快速設定指南](./QUICK_ENV_SETUP.md) 5 分鐘完成配置

### 前置需求

1. **Supabase 帳號** - [在 supabase.com 註冊](https://supabase.com)
2. **Discord Bot**（選填）- [在 Discord Developer Portal 建立](https://discord.com/developers/applications)
3. **Groq API Key** - [從 Groq Cloud 取得](https://console.groq.com)

### 安裝

#### 選項 1：Docker Compose（推薦）

```bash
# 1. 複製專案
git clone https://github.com/yourusername/tech-news-agent.git
cd tech-news-agent

# 2. 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的憑證

# 3. 初始化資料庫
# 在 Supabase SQL Editor 執行 backend/scripts/init_supabase.sql

# 4. 啟動服務
docker compose up -d

# 5. 存取應用程式
# Web: http://localhost:3000
# API: http://localhost:8000
# API 文件: http://localhost:8000/docs
```

#### 選項 2：本地開發

```bash
# 後端
cd backend
pip install -r requirements.txt
python -m app.main

# 前端（另開終端機）
cd frontend
npm install
npm run dev
```

### 首次使用

1. **Web 介面**：訪問 http://localhost:3000 並使用 Discord OAuth 登入
2. **訂閱 Feeds**：從 Dashboard 新增你喜愛的 RSS 訂閱源
3. **觸發抓取**：點擊「抓取新文章」取得第一批文章
4. **探索**：瀏覽文章、儲存到閱讀清單、評分內容

詳細設定說明請參考 [快速開始指南](./docs/QUICKSTART.md)。

## 📚 文件

### 快速開始

- **[快速開始指南](./docs/QUICKSTART.md)** - 幾分鐘內啟動並運行
- **[環境設定](./docs/setup/ENV_SETUP_GUIDE.md)** - 完整的環境變數參考
- **[Docker 指南](./docs/docker/DOCKER_GUIDE.md)** - Docker 部署說明

### 使用者指南

- **[使用者指南](./docs/USER_GUIDE.md)** - 使用 Web 介面和 Discord Bot
- **[手動觸發 Scheduler](./docs/MANUAL_SCHEDULER_TRIGGER.md)** - 隨選文章抓取

### 開發者資源

- **[開發者指南](./docs/DEVELOPER_GUIDE.md)** - 架構和 API 參考
- **[專案概覽](./docs/PROJECT_OVERVIEW.md)** - 完整的系統文件
- **[系統架構](./docs/ARCHITECTURE.md)** - 系統架構細節
- **[測試指南](./docs/testing/supabase-migration-testing.md)** - 測試策略和工具

### 部署

- **[部署指南](./docs/deployment/DEPLOYMENT.md)** - 正式環境部署步驟
- **[部署檢查清單](./docs/deployment/DEPLOYMENT_CHECKLIST.md)** - 部署前驗證
- **[公開 Bot 設定](./docs/PUBLIC_BOT_SETUP.md)** - 將你的 Bot 設為公開

📖 **[完整文件索引](./docs/README.md)** - 瀏覽所有文件

## 🎯 主要功能

### Web Dashboard

- **現代化 UI**：使用 Next.js 14、React 18 和 Tailwind CSS 建立
- **深色模式**：使用 next-themes 無縫切換主題
- **即時更新**：React Query 高效資料抓取
- **響應式設計**：在桌面和行動裝置上完美運作
- **Discord OAuth**：安全的認證整合

### Discord Bot

- **Slash 指令**：直覺的指令介面
- **DM 通知**：個人文章摘要直接發送到你的收件匣
- **互動式 UI**：按鈕、選單和分頁
- **持久化元件**：Bot 重啟後仍可運作
- **多伺服器支援**：可邀請到任何 Discord 伺服器

### 後端 API

- **FastAPI**：高效能非同步 Python 框架
- **RESTful 設計**：清晰、有文件的 API 端點
- **JWT 認證**：安全的 Token 認證
- **背景任務**：APScheduler 自動化作業
- **健康檢查**：監控系統狀態

### AI 整合

- **Groq LLM**：快速、經濟實惠的 AI 處理
- **雙模型**：
  - Llama 3.1 8B 快速評分
  - Llama 3.3 70B 詳細分析
- **智慧快取**：文章分析一次，多次服務
- **速率限制**：自動 API 配額管理

## 🏗️ 架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│  FastAPI Backend│────▶│    Supabase     │
│   Dashboard     │     │   + Discord Bot │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                         │
        │                       │                         │
        ▼                       ▼                         ▼
  Discord OAuth          Groq LLM API            pgvector Search
  React Query            APScheduler             Multi-tenant Data
```

### 技術棧

**前端**

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS + shadcn/ui
- React Query (TanStack Query)
- Playwright (E2E 測試)

**後端**

- Python 3.11+
- FastAPI 0.111.0+
- discord.py 2.4.0+
- APScheduler 3.10.4+
- pytest + Hypothesis (測試)

**基礎設施**

- Supabase (PostgreSQL + pgvector)
- Docker + Docker Compose
- Groq Cloud (Llama 模型)

## 📊 資料庫架構

```sql
users                    feeds                   articles
├── id (UUID)           ├── id (UUID)           ├── id (UUID)
├── discord_id          ├── name                ├── feed_id (FK)
├── dm_notifications    ├── url                 ├── title
└── created_at          ├── category            ├── url
                        ├── is_active           ├── published_at
user_subscriptions      └── created_at          ├── tinkering_index
├── id (UUID)                                   ├── ai_summary
├── user_id (FK)        reading_list            ├── embedding (vector)
├── feed_id (FK)        ├── id (UUID)           └── created_at
└── subscribed_at       ├── user_id (FK)
                        ├── article_id (FK)
                        ├── status
                        ├── rating
                        └── updated_at
```

## 📁 專案結構

```
tech-news-agent/
├── backend/                    # FastAPI 後端 + Discord bot
│   ├── app/
│   │   ├── api/               # REST API 端點
│   │   ├── bot/               # Discord bot
│   │   ├── core/              # 核心配置
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 業務邏輯
│   │   ├── tasks/             # 背景作業
│   │   └── main.py            # 應用程式入口
│   ├── scripts/               # 資料庫腳本
│   ├── tests/                 # 後端測試
│   └── requirements.txt       # Python 依賴
│
├── frontend/                  # Next.js Web 介面
│   ├── app/                   # App router 頁面
│   ├── components/            # React 元件
│   ├── lib/                   # 工具函式
│   ├── hooks/                 # 自訂 React hooks
│   └── package.json           # Node 依賴
│
├── docs/                      # 文件
│   ├── setup/                 # 設定指南
│   ├── docker/                # Docker 文件
│   ├── deployment/            # 部署指南
│   └── testing/               # 測試文件
│
├── docker-compose.yml         # 開發 compose
├── docker-compose.prod.yml    # 正式 compose
└── README.md                  # 本文件
```

## ⚙️ 環境變數

### 必要變數

```bash
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI 配置
GROQ_API_KEY=your-groq-api-key

# JWT 認證（使用 openssl rand -hex 32 生成）
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth（用於 Web 登入）
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 選填變數

```bash
# Discord Bot（選填 - 用於 Discord 整合）
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id  # 用於頻道通知

# Scheduler 配置
SCHEDULER_CRON=0 */6 * * *          # 每 6 小時
SCHEDULER_TIMEZONE=Asia/Taipei

# 應用程式設定
TIMEZONE=Asia/Taipei
RSS_FETCH_DAYS=7                    # 抓取最近 N 天的文章
BATCH_SIZE=50                       # 每批文章數
BATCH_SPLIT_THRESHOLD=100           # 何時分批

# 開發
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
```

詳細配置指南請參考 [環境設定指南](./docs/setup/ENV_SETUP_GUIDE.md)。

## 💬 Discord Bot 指令

### Scheduler 管理

```
/trigger_fetch          # 立即手動觸發文章抓取
/scheduler_status       # 檢查 scheduler 執行狀態和健康度
```

### Feed 管理

```
/add_feed name:Hacker News url:https://news.ycombinator.com/rss category:Tech News
/list_feeds             # 查看所有訂閱的 feeds
/unsubscribe_feed feed_name:Hacker News
```

### 文章探索

```
/news_now               # 查看訂閱 feeds 的最新文章
                        # 包含互動式篩選和深度分析
```

### 閱讀清單

```
/reading_list view      # 瀏覽閱讀清單（分頁）
/reading_list recommend # 根據高評分文章獲得 AI 推薦
```

### 通知設定

```
/notifications enabled:開啟通知
/notifications enabled:關閉通知
/notification_status    # 檢查目前通知設定
```

完整指令文件請參考 [使用者指南](./docs/USER_GUIDE.md)。

## 🌐 Web API 端點

### 認證

```http
POST /api/auth/discord/login
POST /api/auth/discord/callback
GET  /api/auth/me
```

### 文章

```http
GET  /api/articles              # 列出文章
GET  /api/articles/{id}         # 取得文章詳情
POST /api/articles/{id}/analyze # 深度分析
```

### Feeds

```http
GET    /api/feeds               # 列出所有 feeds
POST   /api/feeds               # 建立 feed
GET    /api/feeds/subscriptions # 使用者訂閱
POST   /api/feeds/subscribe     # 訂閱 feed
DELETE /api/feeds/unsubscribe   # 取消訂閱
```

### 閱讀清單

```http
GET    /api/reading-list        # 取得閱讀清單
POST   /api/reading-list        # 加入閱讀清單
PATCH  /api/reading-list/{id}   # 更新狀態/評分
DELETE /api/reading-list/{id}   # 從清單移除
GET    /api/reading-list/recommend # 取得推薦
```

### Scheduler

```http
POST /api/scheduler/trigger     # 觸發手動抓取
GET  /api/scheduler/status      # 取得 scheduler 狀態
```

### 健康檢查

```http
GET /                           # 基本健康檢查
GET /health                     # 詳細健康狀態
GET /health/scheduler           # Scheduler 健康度
```

完整 API 文件請訪問 `/docs` (Swagger UI) 或 `/redoc` (ReDoc)。

## 🧪 測試

### 快速 CI 驗證

在推送程式碼前，**務必**執行以下命令：

```bash
# 1. 自動修復格式和 linting 問題
./scripts/ci-fix.sh

# 2. 在本地執行所有 CI 檢查（完全模擬 GitHub Actions）
./scripts/ci-local-test.sh
```

**CI 文件：**

- 📖 [快速開始指南](./docs/ci/QUICK_START.md) - 必要命令和常見修復
- 📚 [完整 CI 指南](./docs/ci/CI_GUIDE.md) - 詳細文件和故障排除
- 🔄 [CI 重新設計總結](./docs/ci/CI_REDESIGN_SUMMARY.md) - 架構和改進

**CI 檢查項目：**

- ✅ 程式碼格式化（Black、Prettier）
- ✅ Linting（Ruff、ESLint）
- ✅ 類型檢查（mypy、TypeScript）
- ✅ 測試覆蓋率（後端 ≥70%、前端 ≥70%）
- ✅ 建置驗證

### 後端測試

```bash
cd backend

# 執行所有測試
pytest -v

# 執行特定測試套件
pytest tests/test_database_properties.py -v  # Property-based 測試（17 個屬性）
pytest tests/test_config.py -v              # 配置測試
pytest tests/test_sql_init_integration.py -v # SQL 初始化測試

# 執行覆蓋率測試
pytest --cov=app --cov-report=html

# 調整 Hypothesis 測試強度
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v  # 快速（10 個範例）
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v   # CI（100 個範例）
```

### 前端測試

```bash
cd frontend

# 單元測試
npm test                    # 執行一次
npm run test:watch          # Watch 模式
npm run test:coverage       # 含覆蓋率

# E2E 測試
npm run test:e2e           # Headless
npm run test:e2e:ui        # 互動式 UI
```

### 測試覆蓋率

- **後端**：17 個 property-based 測試 + 單元測試 + 整合測試
- **前端**：Jest 單元測試 + Playwright E2E 測試
- **資料庫**：使用 Hypothesis 的完整架構驗證

詳細測試文件請參考 [測試指南](./docs/testing/supabase-migration-testing.md)。

## 🤝 貢獻

歡迎貢獻！以下是你可以幫助的方式：

1. **Fork 專案**
2. **建立功能分支**：`git checkout -b feature/amazing-feature`
3. **進行變更**並新增測試
4. **執行測試**：`pytest`（後端）和 `npm test`（前端）
5. **提交**：`git commit -m 'Add amazing feature'`
6. **推送**：`git push origin feature/amazing-feature`
7. **開啟 Pull Request**

### 開發指南

- 遵循現有程式碼風格（Python 使用 Black，TypeScript 使用 ESLint）
- 為新功能撰寫測試
- 根據需要更新文件
- 保持 commit 原子化且描述清楚

## 📝 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [Supabase](https://supabase.com) - 資料庫和認證
- [Groq](https://groq.com) - 快速 LLM 推理
- [Discord](https://discord.com) - Bot 平台和 OAuth
- [Vercel](https://vercel.com) - Next.js 框架
- [shadcn/ui](https://ui.shadcn.com) - UI 元件

## 📞 支援

- 📖 [文件](./docs/README.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/tech-news-agent/issues)
- 💬 [Discussions](https://github.com/yourusername/tech-news-agent/discussions)

---

**用 ❤️ 為技術社群打造**
