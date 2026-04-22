# Tech News Agent - 專案完整概覽

> 本文件提供 Tech News Agent 專案的完整架構、功能和實作細節，適合快速了解專案現況。
> 最後更新：2026-04-04

---

## 📋 專案簡介

Tech News Agent 是一個自動化技術資訊策展助手，結合 FastAPI、Discord Bot 和 Groq LLM，自動從 RSS 來源抓取技術文章、使用 AI 評分與摘要，並透過 Discord 提供個人化推薦。

### 核心特色

- **多租戶架構**：每個 Discord 使用者擁有獨立的訂閱和閱讀清單
- **背景排程器**：定時抓取 RSS 並分析文章，建立共用文章池
- **AI 驅動**：使用 Groq LLM (Llama 3.1 8B / 3.3 70B) 評估技術深度和生成摘要
- **PostgreSQL + pgvector**：使用 Supabase 儲存資料，支援語義搜尋
- **互動式 Discord UI**：分類篩選、深度分析、閱讀清單管理
- **持久化互動元件**：Bot 重啟後按鈕仍可使用

---

## 🏗️ 系統架構

### 技術棧

```
後端框架：FastAPI 0.111.0+
Discord：discord.py 2.4.0+
資料庫：Supabase (PostgreSQL + pgvector)
AI 模型：Groq Cloud (Llama 3.1 8B, Llama 3.3 70B)
排程器：APScheduler 3.10.4+
部署：Docker + Docker Compose
```

### 專案結構

```
tech-news-agent/
├── app/
│   ├── bot/
│   │   ├── cogs/
│   │   │   ├── interactions.py          # 互動元件（按鈕、選單、視圖）
│   │   │   ├── news_commands.py         # /news_now 指令
│   │   │   ├── reading_list.py          # /reading_list 指令群組
│   │   │   ├── subscription_commands.py # 訂閱管理指令
│   │   │   └── persistent_views.py      # 持久化視圖
│   │   ├── utils/                       # 工具函數
│   │   └── client.py                    # Discord Bot 客戶端
│   ├── core/
│   │   ├── config.py                    # 環境變數設定
│   │   └── exceptions.py                # 自訂例外類別
│   ├── schemas/
│   │   └── article.py                   # Pydantic 資料模型
│   ├── services/
│   │   ├── llm_service.py              # Groq LLM 整合
│   │   ├── supabase_service.py         # Supabase 資料存取層
│   │   └── rss_service.py              # RSS 抓取與解析
│   ├── tasks/
│   │   └── scheduler.py                # APScheduler 背景任務
│   └── main.py                         # FastAPI 入口點
├── scripts/
│   ├── init_supabase.sql               # 資料庫初始化腳本
│   └── seed_feeds.py                   # RSS 來源種子資料
├── tests/                              # 測試套件
├── docs/                               # 文件
├── .kiro/specs/                        # 功能規格文檔
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🗄️ 資料庫架構

### 資料表結構

#### 1. users（使用者表）

```sql
- id: UUID (PK)
- discord_id: TEXT (UNIQUE, NOT NULL)
- created_at: TIMESTAMPTZ
```

#### 2. feeds（RSS 來源表）

```sql
- id: UUID (PK)
- name: TEXT (NOT NULL)
- url: TEXT (UNIQUE, NOT NULL)
- category: TEXT (NOT NULL)
- is_active: BOOLEAN (DEFAULT true)
- created_at: TIMESTAMPTZ
```

#### 3. user_subscriptions（使用者訂閱表）

```sql
- id: UUID (PK)
- user_id: UUID (FK -> users.id, ON DELETE CASCADE)
- feed_id: UUID (FK -> feeds.id, ON DELETE CASCADE)
- subscribed_at: TIMESTAMPTZ
- UNIQUE(user_id, feed_id)
```

#### 4. articles（文章表）

```sql
- id: UUID (PK)
- feed_id: UUID (FK -> feeds.id, ON DELETE CASCADE)
- title: TEXT (NOT NULL)
- url: TEXT (UNIQUE, NOT NULL)
- published_at: TIMESTAMPTZ
- tinkering_index: INTEGER (1-5)
- ai_summary: TEXT
- embedding: VECTOR(1536)
- created_at: TIMESTAMPTZ
```

#### 5. reading_list（閱讀清單表）

```sql
- id: UUID (PK)
- user_id: UUID (FK -> users.id, ON DELETE CASCADE)
- article_id: UUID (FK -> articles.id, ON DELETE CASCADE)
- status: TEXT CHECK (status IN ('Unread', 'Read', 'Archived'))
- rating: INTEGER CHECK (rating >= 1 AND rating <= 5)
- added_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ
- UNIQUE(user_id, article_id)
```

### 索引策略

```sql
-- feeds 表
CREATE INDEX idx_feeds_is_active ON feeds(is_active);
CREATE INDEX idx_feeds_category ON feeds(category);

-- user_subscriptions 表
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_feed_id ON user_subscriptions(feed_id);

-- articles 表
CREATE INDEX idx_articles_feed_id ON articles(feed_id);
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);

-- reading_list 表
CREATE INDEX idx_reading_list_user_id ON reading_list(user_id);
CREATE INDEX idx_reading_list_status ON reading_list(status);
CREATE INDEX idx_reading_list_rating ON reading_list(rating);
```

---

## ⚙️ 核心功能

### 1. 背景排程器（Background Scheduler）

**執行頻率**：每 6 小時（可透過 `SCHEDULER_CRON` 環境變數配置）

**工作流程**：

1. 從資料庫載入所有啟用的 RSS 來源
2. 並發抓取所有來源的文章（過去 7 天內）
3. 透過 URL 去重，過濾已存在的文章
4. 查詢未分析的文章（`tinkering_index IS NULL` 或 `ai_summary IS NULL`）
5. 使用 LLM 批次分析文章：
   - Llama 3.1 8B：評估 `tinkering_index`（技術複雜度 1-5）
   - Llama 3.3 70B：生成 `ai_summary`（繁體中文摘要）
6. 使用 UPSERT 將文章寫入資料庫
7. 記錄統計資訊（處理數量、成功/失敗率）

**錯誤處理**：

- RSS 抓取失敗：記錄錯誤，繼續處理其他來源
- LLM API 失敗：設定欄位為 NULL，繼續處理其他文章
- 資料庫連線失敗：指數退避重試 3 次，失敗則跳過本次執行

**批次處理**：

- 每批最多 50 篇文章
- 超過 100 篇時自動分批
- LLM 並發限制：2 個請求（避免超過 Groq 免費額度 30 RPM）
- 每個請求間隔 4 秒（60s / 30 requests × 2 concurrent）

### 2. Discord 指令

#### `/add_feed` - 訂閱 RSS 來源

```
參數：
  - name: 來源名稱
  - url: RSS/Atom URL
  - category: 分類

功能：
  1. 驗證 URL 格式（必須是 http:// 或 https://）
  2. 檢查 feeds 表是否已存在該 URL
  3. 不存在則建立新 feed，存在則使用現有 feed_id
  4. 在 user_subscriptions 表建立訂閱關係
  5. 處理重複訂閱（UNIQUE 約束）
```

#### `/list_feeds` - 查看訂閱清單

```
功能：
  1. 查詢 user_subscriptions JOIN feeds
  2. 按 category 分組顯示
  3. 顯示來源名稱、URL、分類
  4. 按訂閱時間降序排列
  5. 臨時回應（ephemeral）
```

#### `/unsubscribe_feed` - 取消訂閱

```
參數：
  - feed_identifier: 來源名稱或 UUID

功能：
  1. 從使用者訂閱清單中查找匹配的 feed
  2. 支援按名稱或 UUID 查找
  3. 刪除 user_subscriptions 記錄
  4. 不刪除 feeds 表記錄（其他使用者可能仍在訂閱）
```

#### `/news_now` - 查看最新文章

```
功能：
  1. 查詢使用者訂閱的 feeds
  2. 從 articles 表查詢相關文章：
     - feed_id IN (使用者訂閱的 feeds)
     - published_at >= 7 天前
     - tinkering_index IS NOT NULL
     - ORDER BY tinkering_index DESC
     - LIMIT 20
  3. 按 category 分組顯示
  4. 提供互動元件：
     - 分類篩選選單（最多 24 個分類）
     - Deep Dive 按鈕（前 5 篇）
     - Read Later 按鈕（前 10 篇）
  5. 不觸發 RSS 抓取或 LLM 分析
```

#### `/reading_list view` - 查看閱讀清單

```
功能：
  1. 查詢 reading_list JOIN articles JOIN feeds
  2. 篩選 status='Unread'
  3. 每頁顯示 5 篇文章
  4. 提供互動元件：
     - 上一頁/下一頁按鈕
     - 標記已讀按鈕（每篇文章）
     - 評分選單（1-5 星，每篇文章）
  5. 臨時回應（ephemeral）
```

#### `/reading_list recommend` - 個人化推薦

```
功能：
  1. 查詢使用者評分 >= 4 星的文章
  2. 提取文章標題和分類
  3. 使用 Llama 3.3 70B 生成推薦摘要（繁體中文）
  4. 摘要包含：
     - 使用者關注的技術主題分析
     - 建議追蹤的技術關鍵字
     - 下一步閱讀建議
  5. 最多 500 字
```

### 3. 互動元件

#### 分類篩選選單（Filter Select Menu）

```
- 顯示所有文章的分類（最多 24 個）
- 選擇分類後即時篩選文章
- 臨時回應（只有觸發者可見）
```

#### Deep Dive 按鈕

```
- 每個 /news_now 回應最多 5 個按鈕
- 點擊後生成深度技術分析（Llama 3.3 70B）
- 分析包含：
  - 🔍 核心技術概念
  - 🚀 應用場景
  - ⚠️ 潛在風險
  - 👣 建議下一步
- 最多 600 tokens
- 臨時回應
```

#### Read Later 按鈕

```
- 每個 /news_now 回應最多 10 個按鈕
- 點擊後將文章加入 reading_list
- 使用 UPSERT 處理並發操作
- 點擊後按鈕變為禁用狀態
- 臨時確認訊息
```

#### 標記已讀按鈕

```
- 在 /reading_list view 中每篇文章一個按鈕
- 更新 reading_list.status = 'Read'
- 自動更新 updated_at 時間戳
- 點擊後按鈕變為禁用狀態
```

#### 評分選單

```
- 在 /reading_list view 中每篇文章一個選單
- 選項：⭐ (1) 到 ⭐⭐⭐⭐⭐ (5)
- 更新 reading_list.rating
- 自動更新 updated_at 時間戳
```

### 4. 持久化機制

**問題**：Discord Bot 重啟後，舊訊息的互動元件會失效

**解決方案**：

1. 所有互動視圖使用 `timeout=None`
2. 在 `bot.setup_hook()` 中註冊持久化視圖
3. 使用穩定的 `custom_id` 格式：`{action}_{article_id}`
4. 從 `custom_id` 中提取 `article_id`，從資料庫查詢文章資訊
5. 支援的持久化元件：
   - PersistentReadLaterButton
   - PersistentMarkReadButton
   - PersistentRatingSelect
   - PersistentDeepDiveButton

---

## 🤖 AI 服務

### LLM 模型選擇

| 用途       | 模型                    | 原因                       |
| ---------- | ----------------------- | -------------------------- |
| 文章評分   | Llama 3.1 8B Instant    | 快速、低成本、適合批次處理 |
| 摘要生成   | Llama 3.3 70B Versatile | 高品質、適合複雜分析       |
| 深度分析   | Llama 3.3 70B Versatile | 需要深入理解和推理         |
| 個人化推薦 | Llama 3.3 70B Versatile | 需要理解使用者偏好         |

### API 重試策略

```python
MAX_RETRIES = 2
RETRY_DELAYS = [2, 4]  # 秒
API_TIMEOUT = 30  # 秒

重試條件：
- 網路錯誤
- 超時錯誤
- 速率限制（遵守 Retry-After header）

不重試條件：
- 驗證錯誤
- 無效請求
```

### 錯誤處理

```python
失敗時的行為：
- tinkering_index 評估失敗 → 設為 NULL
- ai_summary 生成失敗 → 設為 NULL
- 繼續處理其他文章
- 記錄失敗率，超過 30% 時發出警告
```

---

## 🔧 環境變數

### 必要變數

```bash
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Discord 配置
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=123456789012345678

# Groq 配置
GROQ_API_KEY=your-groq-api-key
```

### 可選變數

```bash
# 時區配置
TIMEZONE=Asia/Taipei

# RSS 配置
RSS_FETCH_DAYS=7

# 排程器配置
SCHEDULER_CRON=0 */6 * * *  # 每 6 小時
SCHEDULER_TIMEZONE=Asia/Taipei  # 預設使用 TIMEZONE

# 批次處理配置
BATCH_SIZE=50
BATCH_SPLIT_THRESHOLD=100
```

---

## 🚀 部署方式

### Docker Compose（推薦）

```bash
# 1. 複製環境變數範本
cp .env.example .env

# 2. 編輯 .env 填入必要資訊
nano .env

# 3. 啟動服務
docker compose up -d

# 4. 查看日誌
docker compose logs -f
```

### 本地執行

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 配置環境變數
cp .env.example .env
nano .env

# 3. 初始化資料庫
# 在 Supabase Dashboard > SQL Editor 執行 scripts/init_supabase.sql

# 4. 種子資料（可選）
python scripts/seed_feeds.py

# 5. 啟動應用
python -m app.main
```

---

## 📊 監控與健康檢查

### API 端點

```
GET /              # 基本狀態檢查
GET /health        # 整體健康檢查（Bot + Scheduler）
GET /health/scheduler  # 排程器健康檢查
```

### 健康檢查標準

**排程器健康**：

- ✅ 健康（200）：
  - 最近 12 小時內有執行
  - 失敗率 < 50%
- ❌ 不健康（503）：
  - 超過 12 小時未執行
  - 失敗率 >= 50%

**回應格式**：

```json
{
  "last_execution_time": "2026-04-04T10:00:00Z",
  "articles_processed": 150,
  "failed_operations": 5,
  "total_operations": 150,
  "is_healthy": true,
  "issues": []
}
```

---

## 🧪 測試

### 測試覆蓋範圍

```bash
# 執行所有測試
pytest tests/ -v

# 執行特定測試類別
pytest tests/test_database_properties.py -v  # 屬性測試（17 個屬性）
pytest tests/test_config.py -v              # 配置測試
pytest tests/test_seed_feeds.py -v          # 種子腳本測試
pytest tests/test_sql_init_integration.py -v # SQL 初始化測試
```

### 屬性測試（Hypothesis）

使用 Hypothesis 進行屬性測試，驗證：

- CASCADE DELETE 行為
- UNIQUE 約束
- NOT NULL 約束
- CHECK 約束
- 時間戳自動填充
- 資料庫觸發器
- 種子腳本行為

**測試速度配置**：

```bash
# 快速（10 examples）
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v

# 預設（20 examples）
pytest tests/test_database_properties.py -v

# CI/生產（100 examples）
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v
```

---

## 📈 效能特性

### 響應時間目標

| 操作                 | 目標時間   | 實際表現                     |
| -------------------- | ---------- | ---------------------------- |
| `/news_now`          | < 3 秒     | ✅ 從資料庫讀取，無 RSS 抓取 |
| `/reading_list view` | < 2 秒     | ✅ 簡單資料庫查詢            |
| `/add_feed`          | < 2 秒     | ✅ 單筆插入操作              |
| 背景排程器           | 視文章數量 | 每批 50 篇，約 4-5 分鐘      |

### 資料庫優化

- 所有外鍵欄位建立索引
- `articles.embedding` 使用 HNSW 索引（pgvector）
- 批次插入使用 UPSERT 減少查詢次數
- 連線池管理（httpx AsyncClient）

### API 成本優化

**問題**：每次使用者請求都呼叫 LLM 會快速耗盡免費額度

**解決方案**：

1. 背景排程器定時抓取，建立共用文章池
2. 每篇文章只分析一次，結果儲存在資料庫
3. 使用者指令從資料庫讀取已分析的文章
4. LLM API 消耗從「每次請求」降低至「每篇文章一次」

**成本估算**（Groq 免費額度）：

- 30 RPM（每分鐘請求數）
- 14,400 RPD（每天請求數）
- 每篇文章 2 個請求（評分 + 摘要）
- 理論上每天可處理 7,200 篇新文章

---

## 🔄 資料流程

### 文章生命週期

```
1. RSS 抓取
   ↓
2. URL 去重檢查
   ↓
3. 新文章加入待處理佇列
   ↓
4. LLM 批次分析
   ├─ Llama 3.1 8B → tinkering_index
   └─ Llama 3.3 70B → ai_summary
   ↓
5. UPSERT 寫入 articles 表
   ↓
6. 使用者透過 /news_now 查詢
   ↓
7. 使用者點擊 Read Later
   ↓
8. 加入 reading_list 表
   ↓
9. 使用者評分、標記已讀
   ↓
10. 用於個人化推薦
```

### 多租戶資料隔離

```
使用者 A 訂閱 Feed 1, 2
使用者 B 訂閱 Feed 2, 3

共用文章池：
- Feed 1 的文章
- Feed 2 的文章
- Feed 3 的文章

使用者 A 的 /news_now：
- 只顯示 Feed 1, 2 的文章

使用者 B 的 /news_now：
- 只顯示 Feed 2, 3 的文章

使用者 A 的閱讀清單：
- 只包含使用者 A 加入的文章

使用者 B 的閱讀清單：
- 只包含使用者 B 加入的文章
```

---

## 🐛 已知限制

### Discord 限制

1. **訊息長度**：最多 2000 字元
   - 解決：截斷長訊息，提供「查看更多」按鈕
2. **互動元件數量**：每個訊息最多 25 個元件
   - 解決：限制 Deep Dive 按鈕 5 個，Read Later 按鈕 10 個
3. **選單選項數量**：每個選單最多 25 個選項
   - 解決：分類篩選選單最多顯示 24 個分類 + 1 個「顯示全部」

### Groq API 限制

1. **免費額度**：30 RPM
   - 解決：並發限制 2 個請求，每個請求間隔 4 秒
2. **超時**：30 秒
   - 解決：實作重試機制，失敗時設為 NULL

### 資料庫限制

1. **pgvector 維度**：固定 1536（OpenAI embedding 維度）
   - 目前未使用 embedding 功能，預留未來語義搜尋
2. **文字欄位長度**：
   - title: 2000 字元
   - ai_summary: 5000 字元
   - 解決：自動截斷超長文字

---

## 🔮 未來規劃

### Phase 5: 語義搜尋

- 使用 OpenAI Embeddings 生成文章向量
- 實作基於 pgvector 的相似文章推薦
- 支援自然語言查詢文章

### Phase 6: 進階推薦系統

- 基於使用者評分的協同過濾
- 基於閱讀歷史的內容推薦
- 個人化的每週摘要

### Phase 7: Web 介面

- 使用 Next.js 建立 Web 前端
- 支援瀏覽器查看文章和管理訂閱
- OAuth 整合 Discord 登入

### Phase 8: 多語言支援

- 支援英文、簡體中文
- 自動偵測文章語言
- 多語言摘要生成

---

## 📚 相關文件

### 使用者文件

- [README.md](./README.md) - 專案說明（英文）
- [README_zh.md](./README_zh.md) - 專案說明（中文）
- [docs/USER_GUIDE.md](./docs/USER_GUIDE.md) - 使用者指南
- [docs/DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md) - 開發者指南

### 測試文件

- [docs/testing/supabase-migration-testing.md](./docs/testing/supabase-migration-testing.md) - Supabase 測試指南
- [docs/testing/test-fixtures.md](./docs/testing/test-fixtures.md) - 測試 Fixtures 指南
- [docs/testing/cleanup-mechanism.md](./docs/testing/cleanup-mechanism.md) - 清理機制指南
- [docs/testing/sql-integration-tests.md](./docs/testing/sql-integration-tests.md) - SQL 整合測試指南

### 規格文件

- [.kiro/specs/discord-multi-tenant-ui/](./kiro/specs/discord-multi-tenant-ui/) - Discord 多租戶 UI 規格
- [.kiro/specs/background-scheduler-ai-pipeline/](./.kiro/specs/background-scheduler-ai-pipeline/) - 背景排程器規格
- [.kiro/specs/supabase-migration-phase1/](./.kiro/specs/supabase-migration-phase1/) - Supabase 遷移規格

---

## 🤝 貢獻指南

### 開發流程

1. Fork 專案
2. 建立功能分支：`git checkout -b feature/amazing-feature`
3. 提交變更：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 開啟 Pull Request

### 程式碼風格

- 使用 Black 格式化 Python 程式碼
- 遵循 PEP 8 風格指南
- 所有函數需要 docstring
- 所有資料庫操作需要錯誤處理

### 測試要求

- 新功能需要對應的單元測試
- 資料庫操作需要整合測試
- 測試覆蓋率目標：> 80%

---

## 📝 授權

MIT License

---

## 📞 聯絡資訊

如有問題或建議，請開啟 GitHub Issue。

---

**最後更新**：2026-04-04
**專案版本**：1.0.0
**文件版本**：1.0.0
