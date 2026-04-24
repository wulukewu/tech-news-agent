# 任務清單：互動式閱讀清單（Interactive Reading List）

## 任務

- [x] 1. 擴充 Pydantic Schema
  - [x] 1.1 在 `app/schemas/article.py` 新增 `ReadingListItem` 模型，包含 `page_id`、`title`、`url`、`source_category`、`added_at`、`rating` 欄位
  - **相關檔案：** `app/schemas/article.py`

- [x] 2. 擴充 NotionService
  - [x] 2.1 實作 `get_reading_list()` 方法，查詢 Read_Later_DB 中所有 Status 為 `Unread` 的文章，回傳 `List[ReadingListItem]`
  - [x] 2.2 實作 `mark_as_read(page_id: str)` 方法，將指定頁面的 Status 更新為 `Read`
  - [x] 2.3 實作 `rate_article(page_id: str, rating: int)` 方法，更新指定頁面的 Rating 欄位（1–5）
  - [x] 2.4 實作 `get_highly_rated_articles(threshold: int = 4)` 方法，查詢 Rating >= threshold 的文章
  - **相關檔案：** `app/services/notion_service.py`

- [x] 3. 擴充 LLMService
  - [x] 3.1 實作 `generate_reading_recommendation(titles: List[str], categories: List[str]) -> str` 方法，生成不超過 500 字的繁體中文推薦摘要
  - **相關檔案：** `app/services/llm_service.py`

- [x] 4. 建立 ReadingListCog 與 Discord UI 元件
  - [x] 4.1 建立 `app/bot/cogs/reading_list.py`，實作 `MarkAsReadButton`（繼承 `discord.ui.Button`）
  - [x] 4.2 實作 `RatingSelect`（繼承 `discord.ui.Select`），提供 1–5 星選項
  - [x] 4.3 實作 `PaginationView`（繼承 `discord.ui.View`），管理分頁狀態（每頁 5 筆）、上一頁/下一頁按鈕
  - [x] 4.4 實作 `ReadingListCog`，包含 `/reading_list` 指令（ephemeral 回覆）
  - [x] 4.5 實作 `/reading_list recommend` 子指令，呼叫 LLMService 生成推薦摘要
  - **相關檔案：** `app/bot/cogs/reading_list.py`

- [x] 5. 在 Bot 中註冊新 Cog
  - [x] 5.1 在 `app/bot/client.py` 的 `setup_hook` 中載入 `reading_list` cog
  - **相關檔案：** `app/bot/client.py`

- [x] 6. 撰寫屬性測試
  - [x] 6.1 撰寫屬性 P1 的測試：`get_reading_list` 只回傳 Unread 文章
  - [x] 6.2 撰寫屬性 P2 的測試：分頁大小不超過 5 筆
  - [x] 6.3 撰寫屬性 P3 的測試：每篇文章都有標記已讀按鈕
  - [x] 6.4 撰寫屬性 P4 的測試：`mark_as_read` round-trip 正確性
  - [x] 6.5 撰寫屬性 P5 的測試：每篇文章都有包含 1–5 選項的評分選單
  - [x] 6.6 撰寫屬性 P6 的測試：`rate_article` round-trip 正確性
  - [x] 6.7 撰寫屬性 P7 的測試：`get_highly_rated_articles` 只回傳高於閾值的文章
  - [x] 6.8 撰寫屬性 P8 的測試：未評分文章的 rating 為 None
  - **相關檔案：** `tests/test_reading_list.py`

- [x] 7. 撰寫單元測試
  - [x] 7.1 測試 Unread 清單為空時回覆正確訊息
  - [x] 7.2 測試 Notion 錯誤時不顯示部分資料
  - [x] 7.3 測試標記已讀失敗時按鈕狀態不變
  - [x] 7.4 測試高評分文章為 0 時回覆正確訊息
  - [x] 7.5 測試 LLM 錯誤時回覆正確訊息
  - [x] 7.6 測試多頁清單時顯示分頁按鈕
  - [x] 7.7 測試評分成功時 ephemeral 訊息包含星數
  - [x] 7.8 測試 `/reading_list` 回覆為 ephemeral
  - **相關檔案：** `tests/test_reading_list.py`
