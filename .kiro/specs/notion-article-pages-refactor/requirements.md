# 需求文件：Notion Article Pages 重構

## 簡介

將現有的「週報 Page」模式重構為「每篇文章獨立 Page」模式，讓 Weekly Digests 資料庫成為主要的文章管理中心，並支援閱讀狀態追蹤與 Discord 互動。

---

## 核心變更

### 變更 1：Weekly Digests DB 角色轉變

**現況：** 每週建立一篇包含所有文章的週報 Page（使用 Toggle Block）

**目標：** 每篇精選文章建立獨立 Page，Weekly Digests DB 成為文章庫

**理由：**

- 更細緻的文章管理（每篇文章可獨立標記狀態）
- 更好的搜尋與篩選體驗
- 支援未來的評分、筆記等功能擴充

---

### 變更 2：Discord 通知簡化

**現況：** 顯示統計 + Top 5 文章標題/連結 + Notion 週報連結

**目標：** 只顯示統計 + 文章 Notion Page 連結列表

**範例：**

```
本週技術週報已發布

本週統計：抓取 42 篇，精選 7 篇

精選文章：
1. [AI] Building a RAG System with Rust
   https://notion.so/article-page-id-1
2. [DevOps] Kubernetes 1.30 新功能解析
   https://notion.so/article-page-id-2
...
```

---

### 變更 3：閱讀狀態管理

**新增功能：** 在 Discord 通知加入「標記已讀」按鈕，點擊後更新 Notion Page 的 Status 屬性

**互動流程：**

1. 使用者在 Discord 看到文章列表
2. 點擊 Notion 連結閱讀文章
3. 點擊「✅ 標記已讀」按鈕
4. Notion Page 的 Status 更新為 `Read`

---

## 詞彙表

- **Article_Page**：每篇精選文章在 Weekly Digests DB 中的獨立 Page
- **Weekly_Batch**：每週五執行時產生的一批文章（用 `Published_Week` 屬性標記）
- **Article_Status**：文章閱讀狀態（Unread / Read / Archived）
- **Mark_Read_Button**：Discord 按鈕，用於標記文章為已讀

---

## 需求

### 需求 1：Weekly Digests DB Schema 重構

**User Story：** 身為使用者，我希望每篇精選文章在 Notion 有獨立 Page，以便我能更好地管理與追蹤閱讀進度。

#### 驗收標準

1. THE System SHALL 將 Weekly Digests DB 的 Schema 調整為以下結構：

| 屬性名稱          | Notion 類型 | 說明                                 |
| ----------------- | ----------- | ------------------------------------ |
| `Title`           | Title       | 文章標題                             |
| `URL`             | URL         | 文章原始連結                         |
| `Source_Category` | Select      | 文章分類（AI, DevOps, Security 等）  |
| `Published_Week`  | Text        | 發布週次（格式：`YYYY-WW`）          |
| `Tinkering_Index` | Number      | 折騰指數（1-5）                      |
| `Status`          | Status      | 閱讀狀態（Unread / Read / Archived） |
| `Added_At`        | Date        | 加入日期                             |

2. THE System SHALL 移除原有的 `Article_Count` 屬性（改用 DB 查詢統計）

3. THE System SHALL 確保 `Status` 屬性包含三個選項：`Unread`（預設）、`Read`、`Archived`

---

### 需求 2：文章 Page 建立邏輯

**User Story：** 身為系統，我希望每週五執行時，為每篇精選文章建立獨立 Notion Page，並填入完整的文章資訊。

#### 驗收標準

1. WHEN `weekly_news_job` 執行且 `hardcore_articles` 不為空，THE System SHALL 為每篇文章呼叫 `create_article_page` 建立 Notion Page

2. THE System SHALL 在每個 Article_Page 中設定以下屬性：
   - `Title`：文章標題
   - `URL`：文章原始連結
   - `Source_Category`：文章分類
   - `Published_Week`：當週週次（格式 `YYYY-WW`）
   - `Tinkering_Index`：AI 評估的折騰指數
   - `Status`：預設為 `Unread`
   - `Added_At`：當前日期（UTC+8）

3. THE System SHALL 在 Article_Page 的內容區塊（Page Body）插入以下 Block：
   - Callout Block：推薦原因（`ai_analysis.reason`）
   - Callout Block：行動價值（`ai_analysis.actionable_takeaway`，若非空）
   - Bookmark Block：文章原始連結

4. IF `create_article_page` 失敗，THE System SHALL 記錄 ERROR 日誌並繼續處理下一篇文章，不中斷整體流程

---

### 需求 3：Discord 通知格式調整

**User Story：** 身為 Discord 使用者，我希望收到簡潔的文章列表通知，每篇文章都有 Notion Page 連結，以便我能快速跳轉閱讀。

#### 驗收標準

1. THE System SHALL 產生以下格式的 Discord 通知：

```
本週技術週報已發布

本週統計：抓取 {total} 篇，精選 {hardcore} 篇

精選文章：
1. [{category}] {title}
   {notion_page_url}
2. ...
```

2. THE System SHALL 確保通知訊息長度不超過 2000 字元

3. IF 文章列表過長導致超過 2000 字元，THE System SHALL 截斷文章列表並在結尾加上 `...（共 N 篇，查看 Notion 資料庫以瀏覽完整列表）`

4. THE System SHALL 移除原有的「Top 5 文章標題 + 原始連結」格式

---

### 需求 4：Discord 標記已讀按鈕

**User Story：** 身為 Discord 使用者，我希望能在 Discord 直接標記文章為已讀，而不需要切換到 Notion。

#### 驗收標準

1. THE System SHALL 在 Discord 通知中附加 `MarkReadView`，包含每篇文章的「標記已讀」按鈕

2. WHEN 使用者點擊「✅ 標記已讀」按鈕，THE System SHALL 呼叫 `notion.mark_article_as_read(page_id)` 更新 Notion Page 的 `Status` 為 `Read`

3. THE System SHALL 在按鈕點擊後回應使用者：`✅ 已標記「{article_title}」為已讀`

4. IF Notion API 呼叫失敗，THE System SHALL 回應使用者：`❌ 標記失敗，請稍後再試`

5. THE System SHALL 限制按鈕數量不超過 Discord 的 25 個元件限制（若文章超過 25 篇，只顯示前 25 篇的按鈕）

---

### 需求 5：Read Later DB 整合（選填）

**User Story：** 身為使用者，我希望 Read Later DB 與 Weekly Digests DB 能整合，避免資料重複。

#### 驗收標準（選填，可延後實作）

1. THE System MAY 將 Read Later DB 的功能合併至 Weekly Digests DB

2. THE System MAY 新增 `Source` 屬性（Select 類型），選項為 `Weekly_Digest` / `Manual_Save`

3. THE System MAY 保留 `ReadLaterView` 按鈕，但改為在 Weekly Digests DB 建立 Page（`Source = Manual_Save`）

---

### 需求 6：環境變數調整

**User Story：** 身為系統管理員，我希望 `NOTION_WEEKLY_DIGESTS_DB_ID` 成為必填項目，因為它是系統的核心資料表。

#### 驗收標準

1. THE System SHALL 在啟動時檢查 `NOTION_WEEKLY_DIGESTS_DB_ID` 是否為空

2. IF `NOTION_WEEKLY_DIGESTS_DB_ID` 為空，THE System SHALL 拋出 `ConfigurationError` 並拒絕啟動

3. THE System SHALL 在 `.env.example` 中將 `NOTION_WEEKLY_DIGESTS_DB_ID` 標記為必填（移除「leave empty to skip」註解）

4. THE System SHALL 更新 README 說明此變數為必填

---

## 非功能需求

### 效能

- 批次建立文章 Page 時，應使用 `asyncio.gather` 並行處理，但限制並行數量（建議 5 個）以避免 Notion API rate limit

### 錯誤處理

- 單篇文章 Page 建立失敗不應中斷整體流程
- Discord 通知失敗不應影響已建立的 Notion Pages

### 向後相容

- 保留現有的 `/news_now` 指令與 `weekly_news_job` 排程任務
- 保留現有的 Feeds DB 與 Read Later DB（暫不合併）

---

## 實作優先順序

1. **P0（必須）**：需求 1, 2, 3, 6
2. **P1（重要）**：需求 4
3. **P2（可延後）**：需求 5

---

## 測試策略

### 單元測試

- `create_article_page` 方法測試（驗證屬性設定與 Block 結構）
- `build_article_list_notification` 方法測試（驗證訊息格式與長度限制）
- `mark_article_as_read` 方法測試（驗證 Notion API 呼叫）

### 屬性測試

- 屬性 11：Discord 通知訊息長度不超過 2000 字元（任意文章數量）
- 屬性 12：每篇文章對應一個 Notion Page（Page 數量 = 文章數量）
- 屬性 13：Published_Week 格式符合 `YYYY-WW` 規範

### 整合測試

- Mock 所有外部服務，驗證完整流程（RSS → LLM → Notion → Discord）
- 驗證單篇文章失敗不影響其他文章
- 驗證 Discord 按鈕互動正確更新 Notion Status

---

## 遷移計畫

### 現有資料處理

- 現有的 Weekly Digests DB 若已有週報 Page，可保留或手動刪除
- 新系統啟動後，將以新 Schema 建立文章 Page

### 使用者溝通

- 在 README 中說明新舊版本的差異
- 提供 Notion Template 連結，方便使用者快速建立新 DB

---

## 附錄：新舊對比

| 項目             | 舊版                                | 新版                                   |
| ---------------- | ----------------------------------- | -------------------------------------- |
| Notion 儲存單位  | 每週一篇週報 Page                   | 每篇文章一個 Page                      |
| Discord 通知內容 | 統計 + Top 5 標題/連結 + 週報連結   | 統計 + 所有文章 Notion Page 連結       |
| 閱讀狀態管理     | 無                                  | 支援（Unread / Read / Archived）       |
| Discord 互動     | ReadLaterView（存入 Read Later DB） | MarkReadView（更新 Weekly Digests DB） |
| DB 必填性        | Optional                            | Required                               |
