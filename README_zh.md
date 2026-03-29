# Tech News Agent

這是一個結合了 FastAPI、Discord Bot 與 Groq LLM 的自動化技術資訊策展助理。它能自動從 Notion 讀取 RSS 來源，每週抓取、評分技術文章，在 Notion 建立排版精美的週報頁面，並透過 Discord 推播輕量摘要通知。

## 核心功能

- 自動化抓取：每週五 17:00 自動從 Notion 取得 RSS 訂閱源並抓取文章。
- 硬核評分：使用 Groq (Llama 3.1 8B) 進行技術價值與「折騰指數」評估。
- 獨立文章頁面：每篇精選文章在 Notion Weekly Digests 資料庫建立獨立 Page，方便管理與追蹤。
- 閱讀狀態管理：支援文章閱讀狀態追蹤（未讀/已讀/已封存），可直接從 Discord 標記已讀。
- 簡化 Discord 通知：發送文章列表與各文章的 Notion Page 連結，方便快速跳轉閱讀。
- 雙向互動：支援 `/news_now` 斜線指令與按鈕互動（標記已讀、篩選、深度分析、存入稍後閱讀）。

---

## 前置準備

### 1. Notion 資料庫設定

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

| 欄位名稱          | 類型   | 備註                             |
| ----------------- | ------ | -------------------------------- |
| `Title`           | Title  | 將預設的「Name」欄位改名為此     |
| `URL`             | URL    |                                  |
| `Added_At`        | Date   |                                  |
| `Source_Category` | Select |                                  |
| `Status`          | Status | 必須包含一個名為 `Unread` 的選項 |

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

| 變數名稱                      | 必填 | 說明                             |
| ----------------------------- | ---- | -------------------------------- |
| `NOTION_TOKEN`                | ✅   | Notion Integration Token         |
| `NOTION_FEEDS_DB_ID`          | ✅   | Feeds 資料庫 ID                  |
| `NOTION_READ_LATER_DB_ID`     | ✅   | Read Later 資料庫 ID             |
| `NOTION_WEEKLY_DIGESTS_DB_ID` | ✅   | Weekly Digests 資料庫 ID（必填） |
| `DISCORD_TOKEN`               | ✅   | Discord Bot Token                |
| `DISCORD_CHANNEL_ID`          | ✅   | 推播通知的 Discord 頻道 ID       |
| `GROQ_API_KEY`                | ✅   | Groq Cloud API Key               |

---

## Discord 指令

- `/news_now`：立即觸發本週技術新聞抓取、Notion 週報建立與 Discord 通知。
- `/add_feed`：快速將 RSS 加入 Notion（需提供名稱、URL、分類）。

---

## 測試

### 單元與屬性測試（不需要真實 API）

```bash
python -m pytest tests/ -v
```

只跑 Notion Weekly Digest 功能相關測試：

```bash
python -m pytest tests/test_notion_digest_builder.py tests/test_notion_service_digest.py tests/test_llm_digest_intro.py tests/test_discord_notifier.py tests/test_scheduler_integration.py -v
```

屬性測試使用 [Hypothesis](https://hypothesis.readthedocs.io/)，每個屬性執行 100 次迭代，驗證訊息長度限制、Block 結構、ISO 週次標題格式等正確性。

### 手動端對端測試

1. 在 `.env` 填入所有環境變數，包含 `NOTION_WEEKLY_DIGESTS_DB_ID`。
2. 啟動 bot，在 Discord 執行 `/news_now`。
3. 確認：
   - Notion Weekly Digests 資料庫出現新頁面，標題格式為 `週報 YYYY-WW`。
   - 頁面內容包含依分類分組的 Toggle Block，每篇文章含 Bookmark 與 Callout。
   - Discord 收到含統計、Top 5 文章連結與 Notion 頁面連結的通知。

### 降級測試

將 `.env` 的 `NOTION_WEEKLY_DIGESTS_DB_ID` 留空，執行 `/news_now`。Discord 通知應顯示 `（Notion 頁面建立失敗，請查看日誌）` 而非 Notion 連結。

---

## 專案架構

```text
tech-news-agent/
├── app/
│   ├── main.py              # FastAPI 進入點與生命週期管理
│   ├── bot/                 # Discord Bot 邏輯與斜線指令
│   ├── services/            # 核心服務
│   │   ├── notion_service.py  # 含 Digest Builder 相關方法
│   │   ├── llm_service.py     # 含 generate_digest_intro
│   │   └── rss_service.py
│   ├── schemas/             # Pydantic 資料結構（含 WeeklyDigestResult）
│   ├── tasks/               # APScheduler 排程任務
│   │   └── scheduler.py       # weekly_news_job + build_discord_notification
│   └── core/                # 設定與例外處理
└── tests/                   # 單元、屬性與整合測試
```
