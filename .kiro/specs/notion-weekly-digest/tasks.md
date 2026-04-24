# 實作計畫：Notion Weekly Digest

## 概覽

依序擴充設定、Schema、LLMService、NotionService，再修改排程任務與 `/news_now` 指令，最後補齊測試。每個任務皆可獨立執行並在完成後立即驗證。

## 任務

- [x] 1. 擴充設定與環境變數
  - 在 `app/core/config.py` 的 `Settings` 類別新增 `notion_weekly_digests_db_id: str = ""` 欄位
  - 在 `.env.example` 新增 `NOTION_WEEKLY_DIGESTS_DB_ID=` 欄位與說明註解
  - _需求：1.1、1.2_

- [x] 2. 新增 `WeeklyDigestResult` Schema
  - 在 `app/schemas/article.py` 新增 `WeeklyDigestResult(BaseModel)`，包含 `page_id: str`、`page_url: str`、`article_count: int`、`top_articles: List[ArticleSchema]` 欄位
  - _需求：6.5_

  - [x] 2.1 撰寫 `WeeklyDigestResult` 單元測試
    - 驗證欄位完整性與型別正確性
    - _需求：6.5_

- [x] 3. 新增 `LLMService.generate_digest_intro` 方法
  - 在 `app/services/llm_service.py` 的 `LLMService` 類別新增 `generate_digest_intro` 非同步方法
  - 接受 `hardcore_articles: List[ArticleSchema]`，使用 `SUMMARIZE_MODEL` 生成不超過 300 字的繁體中文技術趨勢前言
  - 失敗時回傳預設文字「本週精選技術文章，請展開各項目查看詳情。」，不拋出例外
  - _需求：4.1、4.2、4.4_

  - [x] 3.1 撰寫 `generate_digest_intro` 失敗降級單元測試
    - Mock LLM 呼叫拋出例外，驗證回傳預設文字而非拋出例外
    - _需求：4.4_

- [x] 4. 擴充 `NotionService`：新增 `build_digest_blocks` 靜態方法
  - 在 `app/services/notion_service.py` 的 `NotionService` 類別新增 `build_digest_blocks` 靜態方法
  - 接受 `articles: List[ArticleSchema]`、`intro_text: str`、`stats: dict`，回傳 `List[dict]`
  - Block 結構：第一個 paragraph（intro_text）→ callout（統計摘要）→ 依 source_category 分組的 heading_2 + toggle（含 bookmark、推薦原因 callout、行動價值 callout）→ divider
  - 若 `actionable_takeaway` 為空字串則省略行動價值 callout
  - toggle 標題格式：`[折騰指數 N/5] 文章標題`
  - _需求：3.1、3.2、3.3、3.4、3.5、3.6、4.3、6.4_

  - [x] 4.1 撰寫屬性測試：屬性 3（統計 Callout 存在）
    - **屬性 3：統計摘要 Callout 存在且包含正確資料**
    - **驗證：需求 3.1**

  - [x] 4.2 撰寫屬性測試：屬性 4（分類 heading_2 對應）
    - **屬性 4：每個 source_category 對應一個 heading_2 Block**
    - **驗證：需求 3.2**

  - [x] 4.3 撰寫屬性測試：屬性 5（文章 toggle Block）
    - **屬性 5：每篇文章對應一個含折騰指數的 toggle Block**
    - **驗證：需求 3.3**

  - [x] 4.4 撰寫屬性測試：屬性 6（toggle 子 Block 結構）
    - **屬性 6：toggle 子 Block 結構由文章資料決定（bookmark、推薦原因 callout、可選行動價值 callout）**
    - **驗證：需求 3.4、3.6**

  - [x] 4.5 撰寫屬性測試：屬性 7（intro_text 為第一個 paragraph）
    - **屬性 7：intro_text 為 Block 列表的第一個 paragraph**
    - **驗證：需求 4.3**

  - [x] 4.6 撰寫 `build_digest_blocks` 單元測試
    - 測試 `actionable_takeaway` 為空字串時省略行動價值 callout
    - 測試文章列表為空時的輸出結構
    - _需求：3.6_

- [x] 5. 擴充 `NotionService`：新增 `create_weekly_digest_page` 方法
  - 在 `NotionService` 新增 `create_weekly_digest_page` 非同步方法
  - 接受 `title: str`、`published_date: date`、`article_count: int`，在 `notion_weekly_digests_db_id` 資料庫建立新頁面
  - 設定 `Title`（title）、`Published_Date`（date）、`Article_Count`（number）屬性
  - 回傳 `(page_id, page_url)` tuple；失敗時拋出 `NotionServiceError`
  - _需求：2.1、2.2、2.3、2.4、2.5、2.6、6.1_

  - [x] 5.1 撰寫屬性測試：屬性 1（週報標題格式）
    - **屬性 1：週報標題格式符合 ISO 週次規範（`^週報 \d{4}-\d{2}$`，週次 1–53）**
    - **驗證：需求 2.2**

  - [x] 5.2 撰寫屬性測試：屬性 2（Article_Count 一致性）
    - **屬性 2：Article_Count 與 Hardcore 文章列表長度一致**
    - **驗證：需求 2.4**

  - [x] 5.3 撰寫 `create_weekly_digest_page` 單元測試
    - Mock Notion API，驗證 API 失敗時拋出 `NotionServiceError`
    - 驗證 `notion_weekly_digests_db_id` 為空時跳過建立
    - _需求：1.3、2.6_

- [x] 6. 擴充 `NotionService`：新增 `append_digest_blocks` 方法
  - 在 `NotionService` 新增 `append_digest_blocks` 非同步方法
  - 接受 `page_id: str`、`blocks: List[dict]`，自動以每批 100 個 Block 分批呼叫 `blocks.children.append`
  - _需求：3.7、6.2、6.3_

  - [x] 6.1 撰寫屬性測試：屬性 8（分批呼叫 API）
    - **屬性 8：append_digest_blocks 自動分批，每批不超過 100 個**
    - **驗證：需求 3.7、6.3**

- [x] 7. 檢查點 — 確認所有測試通過
  - 確認所有測試通過，如有問題請向使用者提問。

- [x] 8. 修改 `weekly_news_job` 排程任務
  - 在 `app/tasks/scheduler.py` 修改 `weekly_news_job`：
    - 移除 2000 字元截斷邏輯與 `generate_weekly_newsletter` 呼叫
    - 新增步驟：呼叫 `llm.generate_digest_intro` 生成前言
    - 新增步驟：呼叫 `notion.create_weekly_digest_page` 建立 Notion 頁面，失敗時 `digest_result = None` 並繼續執行
    - 新增步驟：呼叫 `notion.build_digest_blocks` 與 `notion.append_digest_blocks` 寫入 Block 內容
    - 新增 `build_discord_notification` 輔助函式，依 `digest_result` 是否為 None 產生正常或降級通知
    - 修改 Discord 發送步驟：改為發送輕量通知（統計 + Top 5 + Notion 連結），保留 `ReadLaterView`
    - 在每個主要步驟完成後記錄 INFO 日誌
  - _需求：5.1、5.2、5.3、5.4、5.5、7.1、7.2、7.3、7.4、7.5_

  - [x] 8.1 撰寫屬性測試：屬性 9（Discord 訊息長度限制）
    - **屬性 9：Discord 通知訊息長度不超過 2000 字元**
    - **驗證：需求 5.2**

  - [x] 8.2 撰寫屬性測試：屬性 10（Discord 訊息包含必要內容）
    - **屬性 10：Discord 通知包含統計數字與 Notion 連結**
    - **驗證：需求 5.1**

  - [x] 8.3 撰寫 `weekly_news_job` 整合測試
    - Mock 所有外部服務，驗證 Notion 失敗時 Discord 仍發送降級通知
    - 驗證 Discord 失敗時不影響已建立的 Notion 頁面（記錄 ERROR 日誌）
    - 驗證降級通知包含警告標示
    - _需求：7.2、7.3、5.4_

- [x] 9. 同步更新 `/news_now` 指令
  - 在 `app/bot/cogs/news_commands.py` 的 `news_now` 方法中：
    - 移除 2000 字元截斷邏輯
    - 新增呼叫 `generate_digest_intro`、`create_weekly_digest_page`、`build_digest_blocks`、`append_digest_blocks` 的步驟（與 `weekly_news_job` 邏輯一致）
    - 改為發送輕量 Discord 通知，保留現有的 `FilterView`、`DeepDiveView`、`ReadLaterView` 互動按鈕
  - _需求：5.1、5.2、5.4、7.4_

- [x] 10. 最終檢查點 — 確認所有測試通過
  - 確認所有測試通過，如有問題請向使用者提問。

## 備註

- 標記 `*` 的子任務為選填，可跳過以加速 MVP 開發
- 每個任務皆參照具體需求條款以確保可追溯性
- 屬性測試使用 Hypothesis，每個測試最少執行 100 次迭代（`@settings(max_examples=100)`）
- 每個屬性測試需以註解標記：`# Feature: notion-weekly-digest, Property N: <property_text>`
- 測試檔案位置：`tests/test_notion_digest_builder.py`、`tests/test_notion_service_digest.py`、`tests/test_discord_notifier.py`、`tests/test_llm_digest_intro.py`、`tests/test_scheduler_integration.py`
