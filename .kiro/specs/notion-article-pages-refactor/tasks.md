# 實作計畫：Notion Article Pages 重構

## 概覽

將 Weekly Digests DB 從「週報容器」重構為「文章管理中心」，每篇精選文章建立獨立 Page，並支援閱讀狀態追蹤與 Discord 互動。

## 任務

### 階段 1：Schema 與基礎設施

- [x] 1. 更新 Schema 與設定
  - 在 `app/schemas/article.py` 新增 `ArticlePageResult(BaseModel)`，包含 `page_id: str`、`page_url: str`、`title: str`、`category: str`、`tinkering_index: int` 欄位
  - 在 `app/core/config.py` 將 `notion_weekly_digests_db_id` 改為必填（移除預設值 `= ""`）
  - 在 `app/main.py` 的啟動檢查中，驗證 `notion_weekly_digests_db_id` 不為空，否則拋出 `ConfigurationError`
  - _需求：1.1, 6.1, 6.2_

  - [x] 1.1 撰寫 `ArticlePageResult` 單元測試
    - 驗證欄位完整性與型別正確性
    - _需求：設計文件 Schema 章節_

  - [x] 1.2 撰寫啟動檢查單元測試
    - 驗證 `notion_weekly_digests_db_id` 為空時拋出 `ConfigurationError`
    - _需求：6.1_

- [x] 2. 更新環境變數與文件
  - 在 `.env.example` 將 `NOTION_WEEKLY_DIGESTS_DB_ID` 改為必填（移除「leave empty to skip」註解）
  - 更新 `README.md` 與 `README_zh.md`：
    - 更新 Weekly Digests DB Schema 說明（新增 `URL`, `Source_Category`, `Published_Week`, `Tinkering_Index`, `Status`, `Added_At`，移除 `Published_Date`, `Article_Count`）
    - 將 `NOTION_WEEKLY_DIGESTS_DB_ID` 標記為必填
    - 更新功能描述（每篇文章獨立 Page、Discord 通知簡化、閱讀狀態管理）
  - _需求：6.3, 6.4_

### 階段 2：NotionService 核心方法

- [x] 3. 新增 `create_article_page` 方法
  - 在 `app/services/notion_service.py` 的 `NotionService` 類別新增 `create_article_page` 非同步方法
  - 接受 `article: ArticleSchema`、`published_week: str`（格式 `YYYY-WW`）
  - 在 `notion_weekly_digests_db_id` 資料庫建立新頁面，設定屬性：
    - `Title`: `article.title`
    - `URL`: `article.url`
    - `Source_Category`: `article.source_category`
    - `Published_Week`: `published_week`
    - `Tinkering_Index`: `article.ai_analysis.tinkering_index`
    - `Status`: `"Unread"`
    - `Added_At`: 當前日期（UTC+8）
  - 在 Page Body 插入 Block：
    - Callout Block：推薦原因（`ai_analysis.reason`）
    - Callout Block：行動價值（`ai_analysis.actionable_takeaway`，若非空）
    - Bookmark Block：文章連結
  - 回傳 `(page_id, page_url)` tuple；失敗時拋出 `NotionServiceError`
  - _需求：2.1, 2.2, 2.3_

  - [x] 3.1 撰寫 `create_article_page` 單元測試
    - Mock Notion API，驗證屬性設定正確
    - 驗證 Page Body Block 結構正確
    - 驗證 API 失敗時拋出 `NotionServiceError`
    - 驗證 `actionable_takeaway` 為空時省略該 Callout
    - _需求：2.2, 2.3_

- [x] 4. 新增 `mark_article_as_read` 方法
  - 在 `NotionService` 新增 `mark_article_as_read` 非同步方法
  - 接受 `page_id: str`
  - 更新指定 Page 的 `Status` 屬性為 `"Read"`
  - 失敗時拋出 `NotionServiceError`
  - _需求：4.2_

  - [x] 4.1 撰寫 `mark_article_as_read` 單元測試
    - Mock Notion API，驗證 API 呼叫參數正確
    - 驗證 API 失敗時拋出 `NotionServiceError`
    - _需求：4.2_

- [x] 5. 新增 `build_article_list_notification` 方法
  - 在 `NotionService` 新增 `build_article_list_notification` 靜態方法
  - 接受 `article_pages: List[ArticlePageResult]`、`stats: dict`
  - 回傳 Discord 通知訊息字串（格式見設計文件）
  - 確保訊息長度不超過 2000 字元，超過時截斷並加上 `...（共 N 篇，查看 Notion 資料庫以瀏覽完整列表）`
  - _需求：3.1, 3.2, 3.3_

  - [x] 5.1 撰寫屬性測試：屬性 11（Discord 訊息長度限制）
    - **屬性 11：Discord 通知訊息長度不超過 2000 字元（任意文章數量）**
    - **驗證：需求 3.2**

  - [x] 5.2 撰寫 `build_article_list_notification` 單元測試
    - 測試正常模式（文章數量少）
    - 測試截斷模式（文章數量多，超過 2000 字元）
    - 測試空文章列表
    - _需求：3.1, 3.3_

- [x] 6. 新增 `build_week_string` 輔助函式
  - 在 `app/services/notion_service.py` 新增模組級函式 `build_week_string(dt: datetime) -> str`
  - 回傳格式 `YYYY-WW` 的週次字串（使用 `dt.isocalendar()`）
  - _需求：2.2_

  - [x] 6.1 撰寫屬性測試：屬性 13（Published_Week 格式）
    - **屬性 13：Published_Week 格式符合 `^\\d{4}-\\d{2}$` 且週次 1-53**
    - **驗證：需求 2.2**

### 階段 3：Discord 互動

- [x] 7. 新增 `MarkReadView` Discord View
  - 在 `app/bot/cogs/interactions.py` 新增 `MarkReadView(discord.ui.View)` 類別
  - 接受 `article_pages: List[ArticlePageResult]`（最多 25 篇）
  - 為每篇文章建立「✅ 標記已讀」按鈕（使用 `custom_id` 儲存 `page_id`）
  - 按鈕點擊時呼叫 `notion.mark_article_as_read(page_id)`
  - 成功時回應 `✅ 已標記「{title}」為已讀`（ephemeral）
  - 失敗時回應 `❌ 標記失敗，請稍後再試`（ephemeral）
  - _需求：4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 7.1 撰寫 `MarkReadView` 單元測試
    - Mock Notion API，驗證按鈕點擊正確呼叫 `mark_article_as_read`
    - 驗證成功與失敗的回應訊息
    - 驗證按鈕數量不超過 25 個
    - _需求：4.2, 4.3, 4.4, 4.5_

### 階段 4：Scheduler 與指令修改

- [x] 8. 修改 `weekly_news_job` 排程任務
  - 在 `app/tasks/scheduler.py` 修改 `weekly_news_job`：
    - 移除 `generate_digest_intro`、`build_digest_blocks`、`append_digest_blocks` 呼叫
    - 移除 `build_discord_notification` 函式（改用 `build_article_list_notification`）
    - 新增步驟：計算當週週次（`build_week_string`）
    - 新增步驟：批次建立文章 Page（使用 `asyncio.Semaphore(5)` 限制並行）
    - 新增步驟：收集成功建立的 `ArticlePageResult`
    - 新增步驟：呼叫 `build_article_list_notification` 建立通知訊息
    - 修改 Discord 發送步驟：改用 `MarkReadView`（限制 25 個按鈕）
    - 單篇文章失敗時記錄 ERROR 日誌，但繼續處理其他文章
    - 所有文章失敗時跳過 Discord 通知
  - _需求：2.1, 2.4, 3.1, 4.1_

  - [x] 8.1 撰寫屬性測試：屬性 12（Page 數量一致性）
    - **屬性 12：成功建立的 Page 數量 = 成功的文章數量**
    - **驗證：需求 2.1**

  - [x] 8.2 撰寫 `weekly_news_job` 整合測試
    - Mock 所有外部服務，驗證完整流程
    - 驗證單篇文章失敗不影響其他文章
    - 驗證所有文章失敗時跳過 Discord 通知
    - 驗證 Discord 通知包含正確的文章連結
    - 驗證 `MarkReadView` 正確附加
    - _需求：2.4, 3.1, 4.1_

- [x] 9. 同步更新 `/news_now` 指令
  - 在 `app/bot/cogs/news_commands.py` 的 `news_now` 方法中：
    - 套用與 `weekly_news_job` 相同的邏輯變更
    - 保留現有的 `FilterView`、`DeepDiveView`（可選）
    - 新增 `MarkReadView`
  - _需求：2.1, 3.1, 4.1_

### 階段 5：清理與測試

- [x] 10. 移除舊功能
  - 移除 `LLMService.generate_digest_intro` 方法
  - 移除 `NotionService.build_digest_blocks` 方法
  - 移除 `NotionService.append_digest_blocks` 方法
  - 移除 `NotionService.create_weekly_digest_page` 方法
  - 移除 `NotionService.build_digest_title` 函式
  - 移除 `app/schemas/article.py` 的 `WeeklyDigestResult` Schema
  - 移除 `app/tasks/scheduler.py` 的 `build_discord_notification` 函式
  - 移除相關測試檔案：
    - `tests/test_llm_digest_intro.py`
    - `tests/test_notion_digest_builder.py`（保留 `ArticlePageResult` 測試）
    - `tests/test_discord_notifier.py`（保留屬性 11 測試）
  - _需求：設計文件「移除功能」章節_

- [x] 11. 最終檢查點 — 確認所有測試通過
  - 執行完整測試套件：`python -m pytest tests/ -v`
  - 確認所有新測試通過
  - 確認移除舊功能後無殘留測試失敗
  - 如有問題請向使用者提問

- [x] 12. 手動端對端測試
  - 在 Notion 建立新的 Weekly Digests DB（或調整現有 DB Schema）
  - 更新 `.env` 的 `NOTION_WEEKLY_DIGESTS_DB_ID`
  - 執行 `/news_now` 指令
  - 驗證：
    - Notion 出現多個文章 Page（每篇精選文章一個）
    - 每個 Page 包含正確的屬性與 Block 內容
    - Discord 收到簡化通知（文章連結列表）
    - 點擊「✅ 標記已讀」按鈕，Notion Page 的 Status 更新為 `Read`

## 備註

- 每個任務皆參照具體需求條款以確保可追溯性
- 屬性測試使用 Hypothesis，每個測試最少執行 100 次迭代（`@settings(max_examples=100)`）
- 每個屬性測試需以註解標記：`# Feature: notion-article-pages-refactor, Property N: <property_text>`
- 測試檔案位置：
  - `tests/test_article_page_result.py`（新增）
  - `tests/test_notion_article_pages.py`（新增）
  - `tests/test_mark_read_view.py`（新增）
  - `tests/test_scheduler_article_pages.py`（新增）
  - `tests/test_discord_notifier.py`（保留並更新）

## 實作順序建議

1. **階段 1**（基礎設施）→ **階段 2**（NotionService 核心）→ **階段 3**（Discord 互動）
2. **階段 4**（Scheduler 整合）→ **階段 5**（清理與測試）
3. 每完成一個階段，執行該階段的測試確認無誤後再進入下一階段

## 遷移注意事項

- 舊版 Weekly Digests DB 若已有週報 Page，可保留或手動刪除（不影響新系統）
- 新系統啟動後，將以新 Schema 建立文章 Page
- 建議在測試環境先執行一次完整流程，確認無誤後再部署至生產環境
