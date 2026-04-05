# Tech News Agent

這是一個結合了 FastAPI、Discord Bot 與 Groq LLM 的自動化技術資訊策展助理。它能自動從 Supabase 讀取 RSS 來源，每週抓取、評分技術文章，儲存至 PostgreSQL 資料庫，並透過 Discord 推播通知。

## 核心功能

- **自動化抓取**：每週五 17:00 自動從 Supabase 取得 RSS 訂閱源並抓取文章
- **AI 驅動評分**：使用 Groq (Llama 3.1 8B) 進行技術價值與「折騰指數」評估
- **PostgreSQL 儲存**：所有資料儲存於 Supabase (PostgreSQL)，支援 pgvector 語意搜尋
- **閱讀清單管理**：直接在 Discord 查看、評分（1-5 星）並管理閱讀清單，支援分頁瀏覽
- **智慧推薦**：根據你的高評分文章（4 星以上）生成 AI 閱讀推薦
- **互動式 Discord 介面**：依分類篩選文章、取得深度分析、管理閱讀狀態
- **持久化互動介面**：所有按鈕與選單在 Bot 重啟後仍可正常運作，確保無縫使用體驗

---

## 前置準備

### 1. Supabase 資料庫設定

本專案使用 Supabase (PostgreSQL) 作為主要資料庫，並支援 pgvector 進行語意搜尋。

**設定步驟：**

1. 在 [supabase.com](https://supabase.com) 建立 Supabase 專案
2. 在 SQL Editor 執行初始化腳本：
   ```bash
   # 腳本位於 scripts/init_supabase.sql
   ```
3. 執行種子腳本以填入預設 RSS 訂閱源：
   ```bash
   python scripts/seed_feeds.py
   ```
4. 從 Project Settings > API 取得 Supabase URL 與 API key

**資料庫結構：**

- `users` - Discord 使用者，支援多租戶架構
- `feeds` - RSS 訂閱源與分類
- `user_subscriptions` - 使用者訂閱關係
- `articles` - 抓取的文章，含 AI 摘要與向量嵌入
- `reading_list` - 使用者閱讀清單，含評分與狀態

### 2. Discord Bot 設定

- 至 Discord Developer Portal 建立 Bot
- 務必開啟 Message Content Intent
- 取得 Token 並將 Bot 加入你的伺服器
- 取得要推播的 Channel ID

### 3. API Key

- 取得 Groq Cloud 的 API Key

---

## 如何運行

### 方法一：使用 Docker（推薦，適合 NAS 或伺服器）

1. 複製並設定環境變數：

   ```bash
   cp .env.example .env
   ```

   編輯 `.env` 並填入你的所有 Token 與 ID（參見下方環境變數說明）。

2. 啟動服務：
   ```bash
   docker compose up -d
   ```

### 方法二：本地 Python 運行

1. 安裝依賴：

   ```bash
   pip install -r requirements.txt
   ```

2. 設定環境變數（建立 `.env`）。

3. 啟動應用程式：
   ```bash
   python -m app.main
   ```

---

## 環境變數說明

| 變數名稱             | 必填 | 說明                                 |
| -------------------- | ---- | ------------------------------------ |
| `SUPABASE_URL`       | ✅   | Supabase 專案 URL                    |
| `SUPABASE_KEY`       | ✅   | Supabase API key (anon/service_role) |
| `DISCORD_TOKEN`      | ✅   | Discord Bot Token                    |
| `DISCORD_CHANNEL_ID` | ✅   | 推播通知的 Discord 頻道 ID           |
| `GROQ_API_KEY`       | ✅   | Groq Cloud API Key                   |
| `TIMEZONE`           | ⚪   | 排程器時區（預設：Asia/Taipei）      |

---

## Discord 指令

### `/news_now`

立即觸發本週技術新聞抓取與 Discord 通知。

**執行流程：**

1. 從 Supabase 取得所有啟用的 RSS 訂閱源
2. 抓取過去 7 天的文章
3. 使用 AI 評估每篇文章的技術價值與「折騰指數」
4. 發送 Discord 通知，附帶互動按鈕

**互動元件：**

- **📋 篩選選單**：選擇分類即時篩選文章
- **📖 深度分析按鈕**：取得 AI 生成的詳細技術分析（最多 5 篇）

**注意：** 部分功能仍在開發中（稍後閱讀、標記已讀）。

### `/reading_list view`

直接在 Discord 查看並管理你的閱讀清單。

**功能特色：**

- **分頁瀏覽**：每頁顯示 5 篇文章，可使用上一頁/下一頁按鈕切換
- **標記已讀**：點擊 ✅ 按鈕將文章標記為已讀
- **文章評分**：使用下拉選單為文章評分 1-5 星（⭐）
- **私密回應**：只有你能看到自己的閱讀清單（ephemeral 訊息）

**顯示格式：**
每篇文章顯示：

- 標題與網址
- 分類
- 目前評分（或「未評分」）

### `/reading_list recommend`

根據你的高評分文章（4 星以上）生成 AI 閱讀推薦。

**運作方式：**

1. 取得所有你評為 4 或 5 星的文章
2. 分析標題與分類
3. 生成繁體中文的個人化推薦摘要
4. 根據你的興趣建議接下來該讀什麼

---

## 互動介面元件

所有互動元件都具備持久性，即使 Bot 重啟，按鈕與選單仍可正常運作。

### 篩選下拉選單

- **位置**：每則 `/news_now` 通知都會附帶
- **功能**：即時依分類篩選文章
- **選項**：「📋 顯示全部」+ 最多 24 個最常見的分類
- **回應**：Ephemeral 訊息（只有你看得到）顯示篩選結果

### 深度分析按鈕

- **位置**：每則 `/news_now` 通知最多 5 個按鈕
- **標籤**：📖 後接文章標題（截斷至 20 字元）
- **功能**：生成詳細技術分析，包含：
  - 核心技術概念
  - 應用場景
  - 潛在風險
  - 建議下一步
- **模型**：使用 Llama 3.3 70B 生成高品質摘要
- **回應**：Ephemeral 訊息，最多 600 tokens 的分析內容

### 評分下拉選單

- **位置**：在 `/reading_list view` 分頁介面中
- **選項**：⭐（1 星）到 ⭐⭐⭐⭐⭐（5 星）
- **功能**：為閱讀清單中的文章評分
- **用途**：建立閱讀偏好，用於生成個人化推薦

---

## 測試

### Supabase 資料庫測試

Supabase 資料庫基礎建設具備完整的測試覆蓋，包含屬性測試。

**執行所有 Supabase 測試：**

```bash
pytest tests/test_database_properties.py tests/test_config.py tests/test_seed_feeds.py tests/test_sql_init_integration.py -v
```

**測試分類：**

- **配置測試** (`test_config.py`)：驗證 Supabase 配置欄位
- **SQL 初始化測試** (`test_sql_init_integration.py`)：驗證資料庫結構建立
- **種子腳本測試** (`test_seed_feeds.py`)：驗證 RSS 訂閱源灌入
- **屬性測試** (`test_database_properties.py`)：使用 Hypothesis 驗證 17 個正確性屬性

**屬性測試驗證項目：**

- CASCADE DELETE 行為（使用者、訂閱源、文章）
- UNIQUE 約束（discord_id、URL、訂閱關係）
- NOT NULL 約束（必填欄位）
- CHECK 約束（狀態值、評分範圍）
- 時間戳記自動填入
- 資料庫觸發器（updated_at）
- 種子腳本行為

**調整測試速度：**

```bash
# 快速（每個屬性 10 次迭代）
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v

# 預設（每個屬性 20 次迭代）
pytest tests/test_database_properties.py -v

# CI/生產環境（每個屬性 100 次迭代）
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v
```

### 測試文件

詳細的測試文件請參考：

- [Supabase 測試指南](./docs/testing/supabase-migration-testing.md) - 完整測試指南
- [Test Fixtures 指南](./docs/testing/test-fixtures.md) - Fixture 使用與範例
- [清理機制指南](./docs/testing/cleanup-mechanism.md) - 測試資料清理
- [SQL 整合測試指南](./docs/testing/sql-integration-tests.md) - SQL 初始化測試

### 手動端對端測試

1. 在 `.env` 填入所有環境變數
2. 啟動 bot，在 Discord 執行 `/news_now`
3. 確認：
   - Discord 收到含統計與文章清單的通知
   - 互動按鈕正常運作：
     - 篩選選單可依分類篩選
     - 深度分析按鈕生成 AI 摘要
4. 測試 `/reading_list view`：
   - 確認分頁功能正常（上一頁/下一頁按鈕）
   - 測試標記已讀按鈕
   - 測試評分下拉選單（1-5 星）
5. 測試 `/reading_list recommend`：
   - 先為一些文章評 4-5 星
   - 確認出現 AI 生成的推薦內容

---

## 專案架構

```text
tech-news-agent/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI 設定
├── .hypothesis/             # Hypothesis 屬性測試快取
├── .kiro/
│   └── specs/               # 功能規格與設計文件
├── app/
│   ├── bot/
│   │   ├── cogs/
│   │   │   ├── interactions.py     # 互動介面元件（按鈕、選單、View）
│   │   │   ├── news_commands.py    # /news_now 指令
│   │   │   └── reading_list.py     # /reading_list 指令群組
│   │   └── client.py        # Discord Bot 客戶端與持久化 View 註冊
│   ├── core/
│   │   ├── config.py        # 環境變數設定（Pydantic BaseSettings）
│   │   └── exceptions.py    # 自訂例外類別
│   ├── schemas/
│   │   └── article.py       # Pydantic 模型（ArticleSchema、ReadingListItem 等）
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM 整合（評分、摘要、推薦）
│   │   ├── supabase_service.py # Supabase 資料庫服務
│   │   └── rss_service.py   # RSS 訂閱源抓取與解析
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler 週報自動化
│   └── main.py              # FastAPI 進入點與生命週期管理
├── docs/                    # 文件
│   └── testing/             # 測試文件
│       ├── supabase-migration-testing.md  # Supabase 測試指南
│       ├── test-fixtures.md               # Test fixtures 指南
│       ├── cleanup-mechanism.md           # 清理機制指南
│       └── sql-integration-tests.md       # SQL 整合測試指南
├── logs/                    # 應用程式日誌目錄
├── scripts/                 # 資料庫與工具腳本
│   ├── init_supabase.sql    # Supabase 資料庫初始化腳本
│   └── seed_feeds.py        # RSS 訂閱源種子腳本
├── tests/                   # 單元、屬性與整合測試
│   ├── conftest.py          # Pytest fixtures 與配置
│   ├── test_config.py       # Supabase 配置測試
│   ├── test_database_properties.py  # 屬性測試（17 個屬性）
│   ├── test_seed_feeds.py   # 種子腳本測試
│   ├── test_sql_init_integration.py # SQL 初始化測試
│   └── ...                  # 其他測試
├── .env.example             # 環境變數範例
├── .gitignore
├── docker-compose.yml       # Docker Compose 設定
├── Dockerfile               # Docker 映像定義
├── pytest.ini               # Pytest 設定
├── README.md                # 英文文件
├── README_zh.md             # 中文文件
├── requirements.txt         # 生產環境依賴
└── requirements-dev.txt     # 開發環境依賴
```

---

## 功能亮點

### 🎯 智慧文章策展

- AI 評估每篇文章的技術深度與「折騰指數」
- 只有最有價值的內容才會進入你的週報
- 自動依主題分類

### 📚 完整閱讀管理

- 為文章評分以建立偏好檔案
- 根據評分取得個人化推薦
- 在 Supabase 中追蹤閱讀狀態

### 🗄️ PostgreSQL + pgvector

- 所有資料儲存於 Supabase (PostgreSQL)
- pgvector 支援未來的語意搜尋功能
- 使用 HNSW 演算法進行高效索引

### ⚡ 互動式 Discord 體驗

- 即時依分類篩選文章
- 隨選取得深度分析
- 不離開 Discord 就能管理閱讀清單
- 所有互動在 Bot 重啟後仍可運作

### 🤖 AI 驅動

- **Groq Llama 3.1 8B**：快速文章評估與評分
- **Groq Llama 3.3 70B**：高品質摘要與推薦
- 所有 AI 生成內容皆為繁體中文輸出

---

## 使用技巧與最佳實踐

1. **統一分類命名**：在訂閱源中使用相同的分類名稱，以獲得更好的篩選效果
2. **定期評分文章**：累積評分歷史以獲得更好的推薦
3. **謹慎使用深度分析**：每次深度分析都會消耗 API tokens，只用於真正感興趣的文章
4. **自訂排程時間**：編輯 `scheduler.py` 更改每週抓取時間（預設：週五 17:00）

---

## 疑難排解

**Bot 不回應指令：**

- 檢查 Bot 在 Discord 伺服器中是否有適當權限
- 確認 `DISCORD_TOKEN` 正確
- 查看 Bot 日誌是否有錯誤

**重啟後按鈕無法運作：**

- 這是預期行為，舊訊息（在實作持久化 View 之前建立的）的按鈕無法運作
- Bot 重啟後建立的新訊息會有可運作的按鈕

**資料庫連線錯誤：**

- 確認 `SUPABASE_URL` 與 `SUPABASE_KEY` 設定正確
- 檢查 Supabase 專案是否啟用
- 確保資料庫結構已初始化（執行 `scripts/init_supabase.sql`）

**閱讀清單沒有文章：**

- 檢查 reading_list 表格中的文章 status 是否為 'Unread'
- 確認你已將文章加入閱讀清單

**推薦功能無法運作：**

- 你需要至少一篇評為 4 或 5 星的文章
- 檢查 `GROQ_API_KEY` 是否有效且有剩餘配額

---

## 授權

MIT
