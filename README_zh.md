# Tech News Agent

這是一個結合了 FastAPI、Discord Bot 與 Groq LLM 的自動化技術資訊策展助理。它能自動從 Notion 讀取 RSS 來源，每週抓取、評分技術文章，在 Notion 建立排版精美的週報頁面，並透過 Discord 推播輕量摘要通知。

## 核心功能

- **自動化抓取**：每週五 17:00 自動從 Notion 取得 RSS 訂閱源並抓取文章。
- **硬核評分**：使用 Groq (Llama 3.1 8B) 進行技術價值與「折騰指數」評估。
- **獨立文章頁面**：每篇精選文章在 Notion Weekly Digests 資料庫建立獨立 Page，方便管理與追蹤。
- **閱讀狀態管理**：支援文章閱讀狀態追蹤（未讀/已讀/已封存），可直接從 Discord 標記已讀。
- **互動式篩選**：使用 Discord 下拉選單即時依分類篩選文章。
- **深度摘要**：一鍵取得 LLM 生成的詳細技術分析。
- **閱讀清單管理**：直接在 Discord 查看、評分（1-5 星）並管理 Notion 待讀清單，支援分頁瀏覽。
- **智慧推薦**：根據你的高評分文章（4 星以上）生成 AI 閱讀推薦。
- **持久化互動介面**：所有按鈕與選單在 Bot 重啟後仍可正常運作，確保無縫使用體驗。
- **雙向互動**：Discord 與 Notion 之間完整的雙向同步文章管理。

---

## 前置準備

> ⚠️ **遷移通知**：本專案正在從 Notion 遷移至 Supabase。Phase 1（資料庫基礎建設）已完成。Phase 2（服務遷移）進行中。

### 1. Supabase 資料庫設定（Phase 1 - 已完成）

本專案現在使用 Supabase (PostgreSQL) 作為主要資料庫，並支援 pgvector 進行語意搜尋。

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

### 2. Notion 資料庫設定（舊版 - Phase 2 遷移待完成）

你需要建立三個資料庫，並將 Notion Integration (Connect) 加入各資料庫的權限。

> ⚠️ 欄位名稱區分大小寫，必須與下表完全一致。

**Feeds 資料庫**（儲存 RSS 訂閱源）：

| 欄位名稱   | 類型     | 備註                      |
| ---------- | -------- | ------------------------- |
| `Name`     | Title    | 預設標題欄，保持原名即可  |
| `URL`      | URL      |                           |
| `Category` | Select   | 例如 DevOps、AI、Security |
| `Active`   | Checkbox | 只有勾選的項目才會被抓取  |

**Read Later 資料庫**（透過 Discord 按鈕儲存文章）：

| 欄位名稱          | 類型   | 備註                                                    |
| ----------------- | ------ | ------------------------------------------------------- |
| `Title`           | Title  | 將預設的「Name」欄位改名為此                            |
| `URL`             | URL    |                                                         |
| `Added_At`        | Date   |                                                         |
| `Source_Category` | Select |                                                         |
| `Status`          | Status | 必須包含一個名為 `Unread` 的選項                        |
| `Rating`          | Number | 文章評分 1-5（選填，用於 `/reading_list` 閱讀清單功能） |

**Weekly Digests 資料庫**（儲存獨立文章頁面）：

| 欄位名稱          | 類型   | 備註                                  |
| ----------------- | ------ | ------------------------------------- |
| `Title`           | Title  | 文章標題                              |
| `URL`             | URL    | 文章原始連結                          |
| `Source_Category` | Select | 文章分類（例如 AI、DevOps、Security） |
| `Published_Week`  | Text   | 發布週次（ISO 格式：YYYY-WW）         |
| `Tinkering_Index` | Number | 折騰指數（1-5）                       |
| `Status`          | Status | 閱讀狀態（Unread / Read / Archived）  |
| `Added_At`        | Date   | 文章加入日期                          |

### 2. Discord Bot 設定

- 至 Discord Developer Portal 建立 Bot。
- 務必開啟 Message Content Intent。
- 取得 Token 並將 Bot 加入你的伺服器。
- 取得要推播的 Channel ID。

### 3. API Key

- 取得 Groq Cloud 的 API Key。

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

| 變數名稱                      | 必填 | 說明                                 | 遷移狀態   |
| ----------------------------- | ---- | ------------------------------------ | ---------- |
| `SUPABASE_URL`                | ✅   | Supabase 專案 URL                    | ✅ Phase 1 |
| `SUPABASE_KEY`                | ✅   | Supabase API key (anon/service_role) | ✅ Phase 1 |
| `NOTION_TOKEN`                | ⚪   | Notion Integration Token（舊版）     | 🔄 Phase 2 |
| `NOTION_FEEDS_DB_ID`          | ⚪   | Feeds 資料庫 ID（舊版）              | 🔄 Phase 2 |
| `NOTION_READ_LATER_DB_ID`     | ⚪   | Read Later 資料庫 ID（舊版）         | 🔄 Phase 2 |
| `NOTION_WEEKLY_DIGESTS_DB_ID` | ⚪   | Weekly Digests 資料庫 ID（舊版）     | 🔄 Phase 2 |
| `DISCORD_TOKEN`               | ✅   | Discord Bot Token                    | -          |
| `DISCORD_CHANNEL_ID`          | ✅   | 推播通知的 Discord 頻道 ID           | -          |
| `GROQ_API_KEY`                | ✅   | Groq Cloud API Key                   | -          |
| `TIMEZONE`                    | ⚪   | 排程器時區（預設：Asia/Taipei）      | -          |

---

## Discord 指令

### `/news_now`

立即觸發本週技術新聞抓取、Notion 週報建立與 Discord 通知。

**執行流程：**

1. 從 Notion Feeds 資料庫取得所有啟用的 RSS 訂閱源
2. 抓取過去 7 天的文章
3. 使用 AI 評估每篇文章的技術價值與「折騰指數」
4. 為每篇精選文章在 Weekly Digests 資料庫建立獨立 Notion 頁面
5. 發送 Discord 通知，附帶互動按鈕

**互動元件：**

- **📋 篩選選單**：選擇分類即時篩選文章
- **📖 深度分析按鈕**：取得 AI 生成的詳細技術分析（最多 5 篇）
- **⭐ 稍後閱讀按鈕**：將文章存入 Notion 待讀清單（最多 10 篇）
- **✅ 標記已讀按鈕**：在 Notion 標記文章為已讀（最多 5 篇）

### `/add_feed`

快速將新的 RSS 訂閱源加入 Notion Feeds 資料庫。

**參數：**

- `name`：訂閱源名稱（例如：Hacker News）
- `url`：RSS/Atom Feed 網址
- `category`：分類標籤（例如：AI、DevOps、Security）

**範例：**

```
/add_feed name:TechCrunch url:https://techcrunch.com/feed/ category:科技新聞
```

### `/reading_list view`

直接在 Discord 查看並管理你的 Notion 待讀清單。

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

### 稍後閱讀按鈕

- **位置**：每則 `/news_now` 通知最多 10 個按鈕
- **標籤**：⭐ 稍後閱讀 後接文章標題
- **功能**：將文章存入 Notion 待讀清單
- **行為**：成功儲存後按鈕會停用
- **回應**：Ephemeral 確認訊息

### 標記已讀按鈕

- **位置**：每則 `/news_now` 通知最多 5 個按鈕
- **標籤**：✅ 後接文章標題
- **功能**：將 Notion Weekly Digests 資料庫中的文章狀態更新為「已讀」
- **行為**：成功更新後按鈕會停用
- **回應**：Ephemeral 確認訊息

### 評分下拉選單

- **位置**：在 `/reading_list view` 分頁介面中
- **選項**：⭐（1 星）到 ⭐⭐⭐⭐⭐（5 星）
- **功能**：為待讀清單中的文章評分
- **用途**：建立閱讀偏好，用於生成個人化推薦

---

## 文章管理系統

### 獨立文章頁面

每篇精選文章都會在 Notion Weekly Digests 資料庫建立專屬頁面，包含：

**頁面屬性：**

- **Title**：文章標題
- **URL**：原始文章連結
- **Source_Category**：文章分類（AI、DevOps、Security 等）
- **Published_Week**：ISO 週次格式（YYYY-WW，例如「2025-28」）
- **Tinkering_Index**：技術複雜度評分（1-5）
- **Status**：閱讀狀態（Unread / Read / Archived）
- **Added_At**：文章加入日期

**頁面內容：**

- 💡 **Callout**：AI 生成的推薦原因
- 🎯 **Callout**：可行動的要點（如有）
- 🔖 **Bookmark**：原始文章的直接連結

### 閱讀狀態追蹤

透過三種狀態追蹤你的閱讀進度：

- **Unread**：新加入的文章（預設）
- **Read**：已完成閱讀的文章
- **Archived**：想保留但從活躍清單移除的文章

更新狀態的方式：

- Discord 的「✅ 標記已讀」按鈕
- `/reading_list view` 介面
- 直接在 Notion 中修改

### 週報通知

當 `/news_now` 執行時（或透過排程任務），你會收到 Discord 通知：

**統計資訊：**

```
本週技術週報已發布

本週統計：抓取 42 篇，精選 7 篇

精選文章：
1. [AI] Building a RAG System with Rust
   https://notion.so/abc123
2. [DevOps] Kubernetes 1.30 新功能解析
   https://notion.so/def456
...
```

**功能特色：**

- 列出所有精選文章與 Notion 頁面連結
- 顯示總抓取數 vs. 精選數統計
- 超過 2000 字元時自動截斷
- 附帶互動按鈕可立即操作

---

## 測試

### Supabase 遷移測試（Phase 1）

Supabase 資料庫基礎建設具備完整的測試覆蓋，包含屬性測試。

**執行所有 Supabase 遷移測試：**

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

### 舊版測試（基於 Notion）

**注意：** 部分舊版 Notion 測試在 Phase 2 遷移完成前會失敗，這是預期行為。

### 單元與屬性測試（不需要真實 API）

```bash
python -m pytest tests/ -v
```

只跑 Notion Weekly Digest 功能相關測試：

```bash
python -m pytest tests/test_notion_digest_builder.py tests/test_notion_service_digest.py tests/test_llm_digest_intro.py tests/test_discord_notifier.py tests/test_scheduler_integration.py -v
```

屬性測試使用 [Hypothesis](https://hypothesis.readthedocs.io/)，每個屬性執行 100 次迭代，驗證訊息長度限制、Block 結構、ISO 週次標題格式等正確性。

### 測試文件

詳細的測試文件請參考：

- [Supabase 遷移測試指南](./docs/testing/supabase-migration-testing.md) - 完整測試指南
- [Test Fixtures 指南](./docs/testing/test-fixtures.md) - Fixture 使用與範例
- [清理機制指南](./docs/testing/cleanup-mechanism.md) - 測試資料清理
- [SQL 整合測試指南](./docs/testing/sql-integration-tests.md) - SQL 初始化測試

### 手動端對端測試

1. 在 `.env` 填入所有環境變數，包含 `NOTION_WEEKLY_DIGESTS_DB_ID`。
2. 啟動 bot，在 Discord 執行 `/news_now`。
3. 確認：
   - Notion Weekly Digests 資料庫出現獨立文章頁面
   - 每個頁面都有正確的屬性（Title、URL、Category、Published_Week、Status 等）
   - Discord 收到含統計與文章連結的通知
   - 互動按鈕正常運作：
     - 篩選選單可依分類篩選
     - 深度分析按鈕生成 AI 摘要
     - 稍後閱讀按鈕存入 Notion
     - 標記已讀按鈕更新文章狀態
4. 測試 `/reading_list view`：
   - 確認分頁功能正常（上一頁/下一頁按鈕）
   - 測試標記已讀按鈕
   - 測試評分下拉選單（1-5 星）
5. 測試 `/reading_list recommend`：
   - 先為一些文章評 4-5 星
   - 確認出現 AI 生成的推薦內容
6. 測試 `/add_feed`：
   - 新增一個 RSS 訂閱源
   - 確認它出現在 Notion Feeds 資料庫，且 Active=true

### 互動介面持久性測試

1. 執行 `/news_now` 並記下有按鈕的訊息
2. 重啟 Bot
3. 點擊舊訊息上的按鈕
4. 確認所有按鈕仍可正常運作（這測試持久化 View）

### 降級測試

將 `.env` 的 `NOTION_WEEKLY_DIGESTS_DB_ID` 留空，執行 `/news_now`。Bot 應優雅處理錯誤並告知文章頁面建立失敗。

---

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
│   │   │   ├── news_commands.py    # /news_now 與 /add_feed 指令
│   │   │   └── reading_list.py     # /reading_list 指令群組
│   │   └── client.py        # Discord Bot 客戶端與持久化 View 註冊
│   ├── core/
│   │   ├── config.py        # 環境變數設定（Pydantic BaseSettings）
│   │   └── exceptions.py    # 自訂例外類別
│   ├── schemas/
│   │   └── article.py       # Pydantic 模型（ArticleSchema、ReadingListItem 等）
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM 整合（評分、摘要、推薦）
│   │   ├── notion_service.py # Notion API 整合（文章、訂閱源、閱讀清單）
│   │   └── rss_service.py   # RSS 訂閱源抓取與解析
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler 週報自動化
│   └── main.py              # FastAPI 進入點與生命週期管理
├── docs/                    # 文件
│   └── testing/             # 測試文件
│       ├── supabase-migration-testing.md  # Supabase 遷移測試指南
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
│   ├── test_cleanup_mechanism.py    # 清理機制測試
│   └── ...                  # 舊版 Notion 測試
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

- 一鍵儲存文章供稍後閱讀
- 為文章評分以建立偏好檔案
- 根據評分取得個人化推薦
- 在 Discord 與 Notion 之間追蹤閱讀狀態

### 🎨 豐富的 Notion 整合

- 每篇文章都有獨立頁面與 AI 生成的見解
- 依週次與分類結構化組織
- 在 Notion 中全文搜尋與篩選
- 與 Discord 雙向同步

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
4. **查看 Notion 完整內容**：Discord 顯示摘要，但 Notion 頁面有完整的 AI 分析
5. **自訂排程時間**：編輯 `scheduler.py` 更改每週抓取時間（預設：週五 17:00）

---

## 疑難排解

**Bot 不回應指令：**

- 檢查 Bot 在 Discord 伺服器中是否有適當權限
- 確認 `DISCORD_TOKEN` 正確
- 查看 Bot 日誌是否有錯誤

**重啟後按鈕無法運作：**

- 這是預期行為，舊訊息（在實作持久化 View 之前建立的）的按鈕無法運作
- Bot 重啟後建立的新訊息會有可運作的按鈕

**Notion 頁面未建立：**

- 確認 `NOTION_WEEKLY_DIGESTS_DB_ID` 設定正確
- 檢查 Notion Integration 是否有資料庫存取權限
- 確保資料庫中所有必要欄位都存在

**閱讀清單沒有文章：**

- 檢查 Read Later 資料庫中的文章 Status 是否為「Unread」
- 確認 `NOTION_READ_LATER_DB_ID` 正確

**推薦功能無法運作：**

- 你需要至少一篇評為 4 或 5 星的文章
- 檢查 `GROQ_API_KEY` 是否有效且有剩餘配額

---

## 專案架構

```text
tech-news-agent/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI 設定
├── app/
│   ├── bot/
│   │   ├── cogs/
│   │   │   ├── interactions.py     # 互動介面元件（按鈕、選單、View）
│   │   │   ├── news_commands.py    # /news_now 與 /add_feed 指令
│   │   │   └── reading_list.py     # /reading_list 指令群組
│   │   └── client.py        # Discord Bot 客戶端與持久化 View 註冊
│   ├── core/
│   │   ├── config.py        # 環境變數設定（Pydantic BaseSettings）
│   │   └── exceptions.py    # 自訂例外類別
│   ├── schemas/
│   │   └── article.py       # Pydantic 模型（ArticleSchema、ReadingListItem 等）
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM 整合（評分、摘要、推薦）
│   │   ├── notion_service.py # Notion API 整合（文章、訂閱源、閱讀清單）
│   │   └── rss_service.py   # RSS 訂閱源抓取與解析
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler 週報自動化
│   └── main.py              # FastAPI 進入點與生命週期管理
├── logs/                    # 應用程式日誌目錄
├── tests/                   # 單元、屬性與整合測試
│   ├── test_article_page_result.py
│   ├── test_bug_conditions.py
│   ├── test_build_article_list_notification.py
│   ├── test_build_week_string.py
│   ├── test_interactions.py
│   ├── test_llm_service.py
│   ├── test_mark_read_view.py
│   ├── test_notion_service_create_article_page.py
│   ├── test_notion_service_mark_article_as_read.py
│   ├── test_notion_service.py
│   ├── test_preservation.py
│   ├── test_reading_list.py
│   ├── test_rss_service.py
│   ├── test_startup_validation.py
│   ├── test_weekly_news_job_integration.py
│   └── test_weekly_news_job_property.py
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
