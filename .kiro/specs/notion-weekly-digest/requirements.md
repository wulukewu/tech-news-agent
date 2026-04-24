# 需求文件

## 簡介

本功能「Notion Weekly Digest」旨在將現有的每週技術週報從 Discord Markdown 廣播，升級為以 Notion 作為主要呈現層的完整閱讀體驗。

目前系統每週五 17:00 透過 `weekly_news_job` 排程任務，將 AI 篩選後的技術文章以 Markdown 格式廣播至 Discord，但受限於 Discord 的 2000 字元上限，內容必須截斷，閱讀體驗不佳。

新功能的核心目標：

1. 在 Notion 的 "Weekly Digests" 資料庫中自動建立一篇排版精美的週報 Page，充分運用 Notion Block 的豐富呈現能力。
2. 將 Discord 廣播訊息改為輕量通知，僅顯示摘要統計、Top 文章列表，以及指向 Notion 完整週報的連結。

---

## 詞彙表

- **Weekly_Digest_Page**：每週自動建立於 Notion "Weekly Digests" 資料庫中的一篇週報頁面。
- **Digest_Builder**：負責將 AI 分析結果轉換為 Notion Block 結構並呼叫 Notion API 建立頁面的服務元件。
- **Notion_Block**：Notion API 中的內容單元，包含 Heading、Toggle、Callout、Bookmark、Divider 等類型。
- **Discord_Notifier**：負責在 Discord 頻道發送輕量通知訊息的元件（現有 `weekly_news_job` 的廣播邏輯）。
- **Weekly_Digests_DB**：Notion 中用於存放所有 Weekly_Digest_Page 的資料庫，需在 Notion 中預先建立並設定整合權限。
- **LLMService**：現有的 AI 服務，負責文章評估（`evaluate_batch`）與週報生成（`generate_weekly_newsletter`）。
- **NotionService**：現有的 Notion 整合服務，將擴充 Digest_Builder 相關方法。
- **Hardcore_Article**：經 LLMService 評估後 `is_hardcore = True` 的精選文章。
- **Top_Articles**：從 Hardcore_Article 中依折騰指數排序後取出的前 N 篇文章（預設 7 篇）。
- **Tinkering_Index**：AI 評估的部署難易度，範圍 1–5，數值越高代表越硬核。
- **Discord_Notification**：取代原有完整 Markdown 廣播的輕量 Discord 訊息，包含統計摘要、Top 文章列表與 Notion 連結。

---

## 需求

### 需求 1：建立 Notion Weekly Digests 資料庫設定

**User Story：** 身為系統管理員，我希望能在設定檔中指定 Weekly Digests 資料庫的 ID，以便系統能自動將週報寫入正確的 Notion 資料庫。

#### 驗收標準

1. THE System SHALL 在 `app/core/config.py` 的 `Settings` 類別中新增 `notion_weekly_digests_db_id` 設定欄位，型別為 `str`。
2. THE System SHALL 在 `.env.example` 中新增 `NOTION_WEEKLY_DIGESTS_DB_ID` 範例欄位與說明註解。
3. IF `notion_weekly_digests_db_id` 未設定或為空字串，THEN THE Digest_Builder SHALL 記錄錯誤日誌並跳過 Notion 頁面建立步驟，不中斷整體排程任務。

---

### 需求 2：Digest_Builder 建立 Notion 週報頁面

**User Story：** 身為系統，我希望每週五處理完新聞後，能自動在 Notion 的 Weekly Digests 資料庫中建立一篇結構完整的週報頁面，以便使用者能在 Notion 中閱讀完整內容。

#### 驗收標準

1. WHEN `weekly_news_job` 執行且 Hardcore_Article 列表不為空，THE Digest_Builder SHALL 在 Weekly_Digests_DB 中建立一個新的 Notion Page。
2. THE Digest_Builder SHALL 將新頁面的標題（Title 屬性）設定為 `週報 YYYY-WW`（例如：`週報 2025-28`），其中 `YYYY` 為西元年，`WW` 為 ISO 週次（兩位數補零）。
3. THE Digest_Builder SHALL 將新頁面的 `Published_Date` 屬性（Date 類型）設定為當次執行的日期（UTC+8 台北時間）。
4. THE Digest_Builder SHALL 將新頁面的 `Article_Count` 屬性（Number 類型）設定為本週 Hardcore_Article 的總數量。
5. WHEN Notion API 回傳建立成功，THE Digest_Builder SHALL 記錄新頁面的 `page_id` 與頁面 URL 至應用程式日誌。
6. IF Notion API 呼叫失敗，THEN THE Digest_Builder SHALL 記錄包含錯誤詳情的錯誤日誌，並向上拋出 `NotionServiceError`，不中斷 Discord 通知步驟。

---

### 需求 3：Notion 頁面 Block 內容結構

**User Story：** 身為讀者，我希望 Notion 週報頁面能以清晰、美觀的排版呈現所有精選文章，以便我能快速瀏覽並深入閱讀感興趣的內容。

#### 驗收標準

1. THE Digest_Builder SHALL 在頁面頂部插入一個 `callout` Block，內容包含本週統計摘要：總抓取文章數、Hardcore_Article 數量，以及執行日期。
2. THE Digest_Builder SHALL 依照 `source_category` 將 Top_Articles 分組，每個分類以一個 `heading_2` Block 作為區隔標題。
3. WHEN 一篇 Hardcore_Article 屬於某分類，THE Digest_Builder SHALL 在對應分類標題下方為該文章建立一個 `toggle` Block，Toggle 標題格式為 `[折騰指數 N/5] 文章標題`。
4. THE Digest_Builder SHALL 在每個 `toggle` Block 的子內容中包含以下 Block：
   - 一個 `bookmark` Block，URL 設定為文章連結。
   - 一個 `callout` Block，內容為 AI 推薦原因（`reason`）。
   - 一個 `callout` Block，內容為行動價值（`actionable_takeaway`）。
5. THE Digest_Builder SHALL 在所有分類內容結尾插入一個 `divider` Block。
6. IF 一篇文章的 `actionable_takeaway` 為空字串，THEN THE Digest_Builder SHALL 省略該文章的行動價值 `callout` Block。
7. THE Digest_Builder SHALL 確保單一 API 呼叫中的 Block 數量不超過 Notion API 的 100 個子 Block 限制；WHEN Block 數量超過限制，THE Digest_Builder SHALL 分批呼叫 `blocks.children.append` API 完成所有 Block 的插入。

---

### 需求 4：LLMService 生成 Notion 專用週報摘要

**User Story：** 身為讀者，我希望 Notion 週報頁面頂部有一段 AI 生成的本週前言，以便快速掌握本週技術趨勢的整體脈絡。

#### 驗收標準

1. THE LLMService SHALL 新增 `generate_digest_intro` 非同步方法，接受 `hardcore_articles: List[ArticleSchema]` 作為輸入，回傳一個繁體中文字串。
2. WHEN `generate_digest_intro` 被呼叫，THE LLMService SHALL 生成一段不超過 300 字的本週技術趨勢前言，風格幽默且具極客氣息。
3. THE Digest_Builder SHALL 將 `generate_digest_intro` 的回傳內容插入為頁面的第一個 `paragraph` Block，位於統計摘要 Callout 之前。
4. IF `generate_digest_intro` 呼叫失敗，THEN THE Digest_Builder SHALL 使用預設文字「本週精選技術文章，請展開各項目查看詳情。」作為替代內容，不中斷頁面建立流程。

---

### 需求 5：Discord 輕量通知訊息

**User Story：** 身為 Discord 使用者，我希望每週五收到一則簡潔的通知訊息，包含本週摘要統計與 Notion 完整週報的連結，以便我能快速決定是否前往閱讀。

#### 驗收標準

1. WHEN `weekly_news_job` 執行完成且 Weekly_Digest_Page 建立成功，THE Discord_Notifier SHALL 發送一則 Discord 訊息至設定的頻道，訊息內容包含：
   - 本週統計：總抓取文章數與 Hardcore_Article 數量。
   - Top 5 Hardcore_Article 的標題列表（含 Markdown 超連結）。
   - 指向 Weekly_Digest_Page 的 Notion 連結，格式為可點擊的 URL。
2. THE Discord_Notifier SHALL 確保 Discord 通知訊息的總字元數不超過 2000 字元。
3. IF Top_Articles 數量少於 5 篇，THEN THE Discord_Notifier SHALL 顯示實際可用的文章數量，不補足至 5 篇。
4. WHEN `weekly_news_job` 執行完成但 Weekly_Digest_Page 建立失敗，THE Discord_Notifier SHALL 發送不含 Notion 連結的降級通知訊息，並在訊息中標示「（Notion 頁面建立失敗，請查看日誌）」。
5. THE Discord_Notifier SHALL 保留現有的 `ReadLaterView` 互動按鈕，附加於 Discord 通知訊息中。

---

### 需求 6：NotionService 擴充 Digest_Builder 方法

**User Story：** 身為開發者，我希望 `NotionService` 提供清晰的 Digest_Builder 相關方法，以便 `weekly_news_job` 能以簡潔的方式呼叫 Notion 頁面建立邏輯。

#### 驗收標準

1. THE NotionService SHALL 新增 `create_weekly_digest_page` 非同步方法，接受 `title: str`、`published_date: date`、`article_count: int` 作為參數，回傳新建頁面的 `page_id`（`str`）與 `page_url`（`str`）。
2. THE NotionService SHALL 新增 `append_digest_blocks` 非同步方法，接受 `page_id: str` 與 `blocks: List[dict]` 作為參數，負責將 Notion Block 列表寫入指定頁面。
3. THE NotionService SHALL 在 `append_digest_blocks` 內部自動處理 Notion API 的 100 個子 Block 批次限制，WHEN `blocks` 長度超過 100，THE NotionService SHALL 自動分批呼叫 API。
4. THE NotionService SHALL 新增 `build_digest_blocks` 靜態方法（或獨立的 Builder 函式），接受 `articles: List[ArticleSchema]`、`intro_text: str`、`stats: dict` 作為參數，回傳符合 Notion API 格式的 Block 列表（`List[dict]`）。
5. THE System SHALL 在 `app/schemas/article.py` 中新增 `WeeklyDigestResult` Pydantic 模型，包含 `page_id: str`、`page_url: str`、`article_count: int`、`top_articles: List[ArticleSchema]` 欄位，作為 Digest_Builder 流程的回傳結果。

---

### 需求 7：排程任務整合

**User Story：** 身為系統，我希望 `weekly_news_job` 能依序完成新聞抓取、AI 評估、Notion 頁面建立、Discord 通知等步驟，並在任一步驟失敗時優雅降級，不影響後續步驟的執行。

#### 驗收標準

1. WHEN `weekly_news_job` 執行，THE System SHALL 依照以下順序執行各步驟：抓取 RSS → AI 評估 → 生成 Notion 頁面 → 發送 Discord 通知。
2. IF Notion 頁面建立步驟失敗，THEN THE System SHALL 繼續執行 Discord 通知步驟，並在通知中標示降級狀態（參見需求 5.4）。
3. IF Discord 通知步驟失敗，THEN THE System SHALL 記錄錯誤日誌，不影響已建立的 Notion 頁面。
4. THE System SHALL 移除 `weekly_news_job` 中原有的 2000 字元截斷邏輯，改由 Discord_Notifier 的輕量通知格式取代。
5. WHILE `weekly_news_job` 執行中，THE System SHALL 在每個主要步驟完成後記錄 INFO 等級的進度日誌。
