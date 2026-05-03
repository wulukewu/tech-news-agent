# Tech News Agent

一個結合 FastAPI 後端、Next.js 網頁介面、Discord Bot 和 Groq LLM 的自動化技術資訊整理系統。自動抓取 RSS 訂閱源、以 AI 分析文章，並透過網頁儀表板和 Discord DM 提供個人化技術新聞——包含完整的對話式 AI 層、智慧提醒、學習路徑和每週洞察。

## 🌟 核心功能

### 📱 多平台存取

- **網頁儀表板**：現代化 Next.js 介面，支援深色模式、i18n（中英文）和完整響應式設計
- **Discord Bot**：斜線指令、DM 通知和互動式 UI 元件
- **REST API**：完整功能的 API，附 Swagger/ReDoc 文件

### 🤖 AI 驅動智慧

- **智慧評分**：使用 Groq（Llama 3.1 8B）評估技術深度
- **AI 摘要**：使用 Llama 3.3 70B 生成簡潔摘要
- **個人化推薦**：從你的評分中學習，推薦相關內容
- **深度分析**：按需提供詳細技術解析
- **QA Agent**：完整的對話式問答系統，支援向量搜尋、多輪記憶和用戶偏好學習
- **每週洞察**：AI 生成的每週摘要，包含趨勢偵測和主題聚類
- **智慧提醒**：根據閱讀行為和興趣提供情境感知提醒
- **學習路徑**：技能樹、目標追蹤和自適應內容推薦

### 👥 多租戶架構

- **個人訂閱**：每位用戶管理自己的 RSS 訂閱源
- **私人閱讀清單**：獨立評分和整理文章
- **自訂通知**：細粒度控制頻率、時間、靜音時段和內容類型閾值
- **資料隔離**：用戶之間完全隱私

### ⚡ 彈性排程

- **自動抓取**：可設定的背景排程器（預設：每 6 小時）
- **每用戶動態排程**：每位用戶的通知遵循自己的排程和時區
- **手動觸發**：透過網頁、Discord 或 API 即時刷新文章
- **智慧通知**：DM 傳送，支援重複防止和靜音時段

### 🗄️ 強健的資料層

- **Supabase/PostgreSQL**：可靠的資料儲存，支援 pgvector
- **語意搜尋**：向量嵌入，支援 AI 驅動的文章搜尋
- **對話持久化**：完整的聊天記錄，支援搜尋和匯出
- **知識圖譜**：文章依賴關係和概念連結

---

## 🚀 快速開始

### 前置需求

1. **Supabase 帳號** — [supabase.com](https://supabase.com)
2. **Discord Bot**（可選）— [Discord 開發者入口](https://discord.com/developers/applications)
3. **Groq API 金鑰** — [console.groq.com](https://console.groq.com)

### 安裝

#### 方式一：Docker Compose（推薦）

```bash
# 1. 複製儲存庫
git clone https://github.com/yourusername/tech-news-agent.git
cd tech-news-agent

# 2. 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的憑證

# 3. 初始化資料庫
# 在 Supabase SQL 編輯器中執行 backend/scripts/init_supabase.sql

# 4. 啟動服務
docker compose up -d

# 5. 存取應用程式
# 網頁：      http://localhost:3000
# API：       http://localhost:8000
# API 文件：  http://localhost:8000/docs
```

#### 方式二：本地開發

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

### 第一步

1. **網頁介面**：前往 http://localhost:3000，使用 Discord OAuth 登入
2. **訂閱訂閱源**：從訂閱頁面新增你喜愛的 RSS 訂閱源
3. **觸發抓取**：點擊「抓取新文章」或在 Discord 使用 `/trigger_fetch`
4. **探索**：瀏覽文章、儲存到閱讀清單、評分內容，並與 AI 對話

---

## 如何執行

### 方式一：Docker Compose（推薦）

#### 🔧 開發環境（支援熱重載）

```bash
make dev
# 或
docker-compose up -d
```

#### 🚀 正式環境

```bash
make prod
# 或
docker-compose -f docker-compose.prod.yml up -d
```

### 方式二：本地 Python

```bash
pip install -r requirements.txt
python -m app.main
```

---

## ⚙️ 環境變數

### 必要

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI
GROQ_API_KEY=your-groq-api-key

# JWT 認證
JWT_SECRET_KEY=your-secret-key-here   # openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth（網頁登入用）
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# 前端
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 可選

```bash
# Discord Bot
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id

# 排程器
SCHEDULER_CRON=0 */6 * * *
SCHEDULER_TIMEZONE=Asia/Taipei

# 應用程式
TIMEZONE=Asia/Taipei
RSS_FETCH_DAYS=7
BATCH_SIZE=50
LOG_LEVEL=INFO
```

---

## 💬 Discord Bot 指令

### 排程器

| 指令 | 說明 |
|------|------|
| `/trigger_fetch` | 手動觸發文章抓取 |
| `/scheduler_status` | 檢查排程器健康狀態 |

### 訂閱源管理

| 指令 | 說明 |
|------|------|
| `/add_feed name: url: category:` | 訂閱 RSS/Atom 訂閱源 |
| `/list_feeds` | 查看所有已訂閱的訂閱源 |
| `/unsubscribe_feed feed_identifier:` | 取消訂閱 |

### 文章探索

| 指令 | 說明 |
|------|------|
| `/news_now` | 最新文章，附分類篩選、深度分析和儲存按鈕 |
| `/ask question:` | 用自然語言詢問你的文章 |

### 閱讀清單

| 指令 | 說明 |
|------|------|
| `/reading_list view` | 瀏覽，支援分頁、標記已讀和評分（1–5 星） |
| `/reading_list remove article_id:` | 依 ID 移除文章 |
| `/reading_list recommend` | 根據 4 星以上評分的 AI 推薦 |

### 對話

| 指令 | 說明 |
|------|------|
| `/conversations` | 列出過去的 DM 對話 |
| `/continue id:` | 繼續過去的對話 |
| `/search query:` | 搜尋對話記錄 |

### 個人資料與推薦

| 指令 | 說明 |
|------|------|
| `/my_profile` | 查看偏好摘要和分類權重 |
| `/update_profile` | 從 DM 記錄重建偏好摘要 |
| `/recommend_now` | 觸發個人化推薦到 DM |
| `/stats` | 閱讀統計：已儲存、已讀/未讀、平均評分、熱門分類 |
| `/export` | 將閱讀清單匯出為 CSV |

### 通知設定

| 指令 | 說明 |
|------|------|
| `/notifications enabled:` | 開關 DM 通知 |
| `/notification_status` | 查看目前通知設定 |
| `/set-notification-frequency frequency:` | 設定每日/每週頻率 |
| `/set-notification-time hour: minute:` | 設定傳送時間 |
| `/set-timezone timezone:` | 設定你的時區 |
| `/toggle-notifications` | 快速切換 |
| `/quiet-hours` | 查看靜音時段設定 |
| `/set-quiet-hours start_time: end_time: enabled:` | 設定靜音時段 |
| `/toggle-quiet-hours` | 快速切換靜音時段 |

---

## 🌐 Web API 端點

### 認證
```
POST /api/auth/discord/login
POST /api/auth/discord/callback
GET  /api/auth/me
```

### 文章
```
GET  /api/articles
GET  /api/articles/{id}
POST /api/articles/{id}/analyze
```

### 訂閱源
```
GET    /api/feeds
POST   /api/feeds
GET    /api/feeds/subscriptions
POST   /api/feeds/subscribe
DELETE /api/feeds/unsubscribe
```

### 閱讀清單
```
GET    /api/reading-list
POST   /api/reading-list
PATCH  /api/reading-list/{id}
DELETE /api/reading-list/{id}
GET    /api/reading-list/recommend
```

### QA / 對話
```
POST /api/qa/ask
GET  /api/conversations
GET  /api/conversations/{id}
GET  /api/conversations/{id}/messages
POST /api/conversations/{id}/ai
GET  /api/conversations/{id}/insights
GET  /api/conversations/{id}/related
POST /api/conversations/{id}/share
GET  /api/conversations/{id}/export
```

### 通知
```
GET  /api/notifications/preferences
PUT  /api/notifications/preferences
GET  /api/notifications/quiet-hours
PUT  /api/notifications/quiet-hours
GET  /api/notifications/history
GET  /api/notifications/settings
PUT  /api/notifications/settings
POST /api/notifications/proactive
```

### 學習
```
GET  /api/learning/goals
POST /api/learning/goals
GET  /api/learning/progress
GET  /api/learning/evaluation
GET  /api/learning-content
GET  /api/weekly-insights
POST /api/intelligent-reminder
GET  /api/reminder-settings
PUT  /api/reminder-settings
```

### 分析與系統
```
GET  /api/analytics
GET  /api/knowledge-graph
GET  /api/user/platforms
POST /api/scheduler/trigger
GET  /api/scheduler/status
GET  /health
GET  /health/scheduler
```

後端執行時，完整互動文件在 `/docs`（Swagger）或 `/redoc`。

---

## 🧪 測試

```bash
# 推送前——在本地執行 CI 檢查
./scripts/ci-fix.sh          # 自動修復格式/lint
./scripts/ci-local-test.sh   # 完整 CI 檢查（與 GitHub Actions 一致）
```

### 後端

```bash
cd backend
pytest -v
pytest --cov=app --cov-report=html

# Hypothesis 設定檔
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v   # 快速（10 個範例）
HYPOTHESIS_PROFILE=ci  pytest tests/test_database_properties.py -v   # CI（100 個範例）
```

### 前端

```bash
cd frontend
npm test                 # 單元測試
npm run test:coverage    # 含覆蓋率
npm run test:e2e         # Playwright E2E
```

---

## 📁 專案結構

```
tech-news-agent/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API 端點
│   │   │   ├── auth.py
│   │   │   ├── articles.py
│   │   │   ├── feeds.py
│   │   │   ├── reading_list.py
│   │   │   ├── scheduler.py
│   │   │   ├── qa.py
│   │   │   ├── conversations/  # 對話 CRUD、訊息、AI、洞察、分享、匯出
│   │   │   ├── notifications/  # 偏好、靜音時段、記錄、設定、主動通知
│   │   │   ├── learning_path/  # 目標、進度、評估
│   │   │   ├── weekly_insights.py
│   │   │   ├── intelligent_reminder.py
│   │   │   ├── knowledge_graph.py
│   │   │   ├── analytics.py
│   │   │   └── ...
│   │   ├── bot/
│   │   │   ├── cogs/
│   │   │   │   ├── news_commands.py
│   │   │   │   ├── reading_list.py
│   │   │   │   ├── subscription_commands.py
│   │   │   │   ├── notification_settings.py
│   │   │   │   ├── quiet_hours_settings.py
│   │   │   │   ├── conversation_commands.py
│   │   │   │   ├── qa_commands.py
│   │   │   │   ├── proactive_dm.py
│   │   │   │   ├── dm_conversation_listener.py
│   │   │   │   ├── conversation_auto_manager.py
│   │   │   │   ├── persistent_views.py
│   │   │   │   ├── interactions.py
│   │   │   │   └── admin_commands.py
│   │   │   └── client.py
│   │   ├── services/          # ~50 個服務檔案（mixin 模式）
│   │   │   ├── supabase_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── rss_service.py
│   │   │   ├── dynamic_scheduler.py
│   │   │   ├── smart_conversation.py
│   │   │   ├── enhanced_recommendation_engine.py
│   │   │   ├── intelligent_reminder_generator.py
│   │   │   ├── cross_platform_sync.py
│   │   │   └── _mixins/       # article、feed、reading_list、notification、user
│   │   ├── qa_agent/          # 完整 QA 子系統
│   │   │   ├── qa_agent_controller.py
│   │   │   ├── query_processor.py
│   │   │   ├── retrieval_engine.py
│   │   │   ├── response_generator.py
│   │   │   ├── conversation_manager.py
│   │   │   ├── user_profile_manager.py
│   │   │   ├── knowledge_graph/
│   │   │   ├── intelligent_reminder/
│   │   │   ├── weekly_insights/
│   │   │   ├── proactive_learning/
│   │   │   └── learning_path/
│   │   ├── core/              # 設定、例外、日誌、驗證器
│   │   ├── repositories/      # 資料存取層
│   │   ├── schemas/           # Pydantic 模型
│   │   └── tasks/             # APScheduler 任務
│   ├── scripts/               # 資料庫腳本、遷移、工具
│   ├── tests/                 # pytest 測試套件
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── (public)/          # /、/login、/auth/callback、/chat、/conversations、/demo
│   │   └── app/               # 需認證的路由
│   │       ├── articles/
│   │       ├── reading-list/
│   │       ├── subscriptions/
│   │       ├── recommendations/
│   │       ├── chat/
│   │       ├── learning/
│   │       ├── insights/
│   │       ├── knowledge-graph/
│   │       ├── reminders/
│   │       ├── analytics/
│   │       └── settings/      # 通知、提醒、偏好、外觀、帳號
│   ├── features/              # 功能切片元件
│   │   ├── articles/
│   │   ├── ai-analysis/
│   │   ├── notifications/
│   │   ├── recommendations/
│   │   ├── subscriptions/
│   │   └── system-monitor/
│   ├── components/            # 共用 UI 元件（shadcn/ui）
│   ├── lib/                   # API 客戶端、hooks、工具
│   ├── locales/               # i18n（中英文）
│   └── package.json
│
├── docs/                      # 所有文件
├── scripts/                   # 開發、CI、遷移腳本
├── .github/workflows/ci.yml
├── docker-compose.yml         # 開發環境
├── docker-compose.prod.yml    # 正式環境
├── Makefile
└── README.md
```

---

## 🏗️ 架構

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Next.js 網頁  │────▶│   FastAPI 後端        │────▶│    Supabase     │
│   儀表板        │     │   + Discord Bot       │     │   PostgreSQL    │
│   (i18n 中英文) │     │   + QA Agent          │     │   + pgvector    │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                         │                           │
        ▼                         ▼                           ▼
  Discord OAuth            Groq LLM API              向量搜尋
  React Query              APScheduler               對話儲存
  功能切片                  動態排程器                知識圖譜
```

### 技術棧

**前端**：Next.js 14（App Router）、React 18、TypeScript、Tailwind CSS、shadcn/ui、React Query、next-intl、Playwright

**後端**：Python 3.11+、FastAPI、discord.py 2.4+、APScheduler 3.10+、Supabase Python 客戶端

**基礎設施**：Supabase（PostgreSQL + pgvector）、Docker + Docker Compose、Groq Cloud（Llama 3.1 8B / 3.3 70B）

---

## 📊 資料庫結構

```
users                    feeds                   articles
├── id (UUID)           ├── id (UUID)           ├── id (UUID)
├── discord_id          ├── name                ├── feed_id (FK)
├── dm_notifications    ├── url                 ├── title
└── created_at          ├── category            ├── url
                        └── is_active           ├── published_at
user_subscriptions                              ├── tinkering_index
├── user_id (FK)        reading_list            ├── ai_summary
└── feed_id (FK)        ├── user_id (FK)        ├── embedding (vector)
                        ├── article_id (FK)     └── created_at
conversations           ├── status
├── id (UUID)           └── rating              user_notification_preferences
├── user_id (FK)                                ├── user_id (FK)
├── title               messages                ├── frequency
└── created_at          ├── conversation_id     ├── notification_time
                        ├── role                ├── timezone
knowledge_graph         └── content             └── quiet_hours_*
├── article_id (FK)
├── concept
└── relationships
```

---

## 🔧 故障排除

**資料庫錯誤 / 缺少資料表：**
```bash
cd backend
python3 scripts/verify_bot_health.py
python3 scripts/apply_missing_migration.py
```

**Discord Bot 沒有回應：** 檢查 `DISCORD_TOKEN`、Bot 權限和 OAuth 範圍。

**文章沒有抓取：** 檢查排程器日誌（`docker-compose logs -f backend`），確認 RSS 訂閱源有效，並確認 Groq API 金鑰有額度。

更多資訊請見 [docs/troubleshooting/](./docs/troubleshooting/)。

---

## 📚 文件

- [快速開始指南](./docs/guides/quick-start.md)
- [環境設定](./docs/setup/env-setup-guide.md)
- [Docker 指南](./docs/docker/docker-guide.md)
- [用戶指南](./docs/guides/user-guide.md)
- [開發者指南](./docs/development/developer-guide.md)
- [架構概覽](./docs/architecture/architecture-overview.md)
- [部署指南](./docs/deployment/deployment-guide.md)
- [完整文件索引](./docs/README.md)

---

## 🤝 貢獻

1. Fork 儲存庫
2. 建立功能分支：`git checkout -b feature/amazing-feature`
3. 修改並新增測試
4. 執行檢查：`./scripts/ci-fix.sh && ./scripts/ci-local-test.sh`
5. 提交：`git commit -m 'feat(scope): add amazing feature'`
6. 推送並開啟 Pull Request

---

## 📝 授權

MIT 授權 — 詳見 [LICENSE](LICENSE)。

## 🙏 致謝

[Supabase](https://supabase.com) · [Groq](https://groq.com) · [Discord](https://discord.com) · [Vercel/Next.js](https://nextjs.org) · [shadcn/ui](https://ui.shadcn.com)
