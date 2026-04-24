# 實作計畫

## 探索與驗證階段（修復前）

- [x] 1. 撰寫 Bug Condition 探索測試（修復前執行）
  - **Property 1: Bug Condition** - 五個 Bug 的觸發條件驗證
  - **重要**：此測試必須在實作修復前撰寫並執行
  - **目標**：產生反例，確認五個 Bug 確實存在
  - **Scoped PBT 方法**：針對每個 Bug 的具體觸發條件縮小測試範圍
  - Bug 1：mock `notion-client` 2.x 的 `databases` endpoint，呼叫 `get_active_feeds()`，預期拋出 `AttributeError`（來自 design.md Bug Condition 1：`notion_client_version >= "2.2.1" AND uses_deprecated_databases_query_api(X)`）
  - Bug 2：在 Linux 環境模擬啟動，驗證 SSL patch 無條件執行（`sys.platform != "darwin"` 時仍執行）
  - Bug 3：設定 `TIMEZONE=UTC`，驗證 `settings.model_config.get("timezone", "Asia/Taipei")` 永遠回傳 `"Asia/Taipei"` 而非 `"UTC"`
  - Bug 4：呼叫 `/add_feed` 指令，驗證 `notion.pages.create` 未被呼叫（call count == 0）
  - Bug 5：模擬 Bot 重啟後的 button interaction，驗證 `ReadLaterView` 未透過 `bot.add_view()` 註冊
  - 在未修復的程式碼上執行測試
  - **預期結果**：測試失敗（這是正確的，證明 Bug 存在）
  - 記錄反例（例如：`AttributeError: 'DatabasesEndpoint' object has no attribute 'query'`、`scheduler.timezone == 'Asia/Taipei'` 即使 `.env` 設定 `TIMEZONE=UTC`）
  - 當測試撰寫完成、執行並記錄失敗後，標記任務完成
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2_

- [x] 2. 撰寫 Preservation 屬性測試（修復前執行）
  - **Property 2: Preservation** - 現有正常行為不受影響
  - **重要**：遵循觀察優先方法論（observation-first methodology）
  - 觀察：`add_to_read_later(article)` 在未修復程式碼上呼叫 `pages.create` 並帶有正確屬性
  - 觀察：macOS 環境下 SSL patch 正常執行（`sys.platform == "darwin"` 分支）
  - 觀察：Bot 未重啟時，`ReadLaterButton.callback` 成功呼叫 `notion.add_to_read_later()`
  - 觀察：`get_active_feeds()` 回傳空清單時，系統回傳提示訊息而非拋出例外
  - 撰寫屬性測試：對所有不觸發 Bug Condition 的輸入，修復前後行為應完全相同（來自 design.md Preservation Requirements）
  - 在未修復的程式碼上執行測試
  - **預期結果**：測試通過（確認基準行為）
  - 當測試撰寫完成、執行並通過後，標記任務完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

---

## 實作修復階段

- [x] 3. 修復 Bug 1：Notion API `databases.query` AttributeError
  - [x] 3.1 修正 `NotionService.get_active_feeds()` 的 API 呼叫路徑
    - 檔案：`app/services/notion_service.py`
    - 確認 `notion-client` 2.x 正確的 `databases.query` 呼叫方式
    - 若 `await self.client.databases.query(database_id=...)` 在 2.x 已失效，改用 `await self.client.request(path=f"databases/{self.feeds_db_id}/query", method="POST", body={...})`
    - 確保回傳格式仍為 `{"results": [...]}` 並正確解析為 `List[RSSSource]`
    - _Bug_Condition: `notion_client_version >= "2.2.1" AND uses_deprecated_databases_query_api(X)`（來自 design.md Bug 1）_
    - _Expected_Behavior: `no_attribute_error(result) AND returns_list_of_feeds(result)`_
    - _Preservation: `add_to_read_later()` 的 `pages.create` 呼叫不受影響_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 驗證 Bug Condition 探索測試現在通過
    - **Property 1: Expected Behavior** - Notion API 正確呼叫
    - **重要**：重新執行任務 1 中的同一個測試，不要撰寫新測試
    - 執行 Bug 1 的探索測試（mock `notion-client` 2.x，呼叫修復後的 `get_active_feeds()`）
    - **預期結果**：測試通過（確認 Bug 1 已修復，不再拋出 `AttributeError`）
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 驗證 Preservation 測試仍然通過
    - **Property 2: Preservation** - `add_to_read_later()` 行為不變
    - **重要**：重新執行任務 2 中的同一個測試，不要撰寫新測試
    - **預期結果**：測試通過（確認無迴歸）

- [x] 4. 修復 Bug 2：Docker 環境 `certifi` 依賴與 SSL 平台限制
  - [x] 4.1 在 `requirements.txt` 新增 `certifi` 依賴
    - 檔案：`requirements.txt`
    - 新增 `certifi>=2024.2.2`
    - _Bug_Condition: `is_docker_or_linux(X) AND certifi_not_in_requirements(X)`（來自 design.md Bug 2）_
    - _Requirements: 2.3_

  - [x] 4.2 將 SSL patch 包裹在 macOS 平台判斷中
    - 檔案：`app/main.py`
    - 將 `import certifi, ssl` 及 `os.environ["SSL_CERT_FILE"]` 等程式碼包裹在 `if sys.platform == "darwin":` 條件中
    - 在檔案頂部加入 `import sys`
    - _Bug_Condition: `is_linux(X) AND ssl_patch_runs_unconditionally(X)`_
    - _Expected_Behavior: `ssl_patch_skipped_on_linux(result)`_
    - _Preservation: macOS 環境下 SSL patch 仍正常執行_
    - _Requirements: 2.4_

  - [x] 4.3 驗證 Bug Condition 探索測試現在通過
    - **Property 1: Expected Behavior** - Docker/Linux 環境啟動成功
    - **重要**：重新執行任務 1 中的同一個測試
    - 模擬 Linux 環境，驗證 SSL patch 不再無條件執行
    - **預期結果**：測試通過（確認 Bug 2 已修復）
    - _Requirements: 2.3, 2.4_

  - [x] 4.4 驗證 Preservation 測試仍然通過
    - **Property 2: Preservation** - macOS SSL 修復行為不變
    - **重要**：重新執行任務 2 中的同一個測試
    - **預期結果**：測試通過（確認無迴歸）

- [x] 5. 修復 Bug 3：Scheduler timezone 設定錯誤
  - [x] 5.1 在 `Settings` 類別新增 `timezone` 欄位
    - 檔案：`app/core/config.py`
    - 在 `Settings` 類別新增 `timezone: str = "Asia/Taipei"`
    - 此欄位將從 `.env` 的 `TIMEZONE` 環境變數讀取
    - _Bug_Condition: `uses_model_config_get_for_timezone(X) AND model_config_is_pydantic_meta_object(X)`（來自 design.md Bug 3）_
    - _Requirements: 2.5, 2.6_

  - [x] 5.2 修正 Scheduler 的 timezone 讀取方式
    - 檔案：`app/tasks/scheduler.py`
    - 將 `settings.model_config.get("timezone", "Asia/Taipei")` 改為 `settings.timezone`
    - _Expected_Behavior: `scheduler_timezone_is_valid(result) AND not_from_model_config_meta(result)`_
    - _Preservation: 排程任務每週五 17:00 觸發行為不變_
    - _Requirements: 2.5, 2.6_

  - [x] 5.3 驗證 Bug Condition 探索測試現在通過
    - **Property 1: Expected Behavior** - Scheduler 正確讀取 timezone
    - **重要**：重新執行任務 1 中的同一個測試
    - 設定 `TIMEZONE=UTC`，驗證 `settings.timezone == "UTC"` 且 Scheduler 使用正確值
    - **預期結果**：測試通過（確認 Bug 3 已修復）
    - _Requirements: 2.5, 2.6_

  - [x] 5.4 驗證 Preservation 測試仍然通過
    - **Property 2: Preservation** - 排程觸發行為不變
    - **重要**：重新執行任務 2 中的同一個測試
    - **預期結果**：測試通過（確認無迴歸）

- [x] 6. 修復 Bug 4：實作 `/add_feed` 指令的 Notion 寫入邏輯
  - [x] 6.1 在 `NotionService` 新增 `add_feed()` 方法
    - 檔案：`app/services/notion_service.py`
    - 新增 `async def add_feed(self, name: str, url: str, category: str) -> None` 方法
    - 呼叫 `await self.client.pages.create(parent={"database_id": self.feeds_db_id}, properties={...})`
    - 屬性包含：`Name`（title）、`URL`（url）、`Category`（select）、`Active`（checkbox，預設 `True`）
    - _Bug_Condition: `add_feed_has_no_notion_write_logic(X) AND notion_service_missing_add_feed_method(X)`（來自 design.md Bug 4）_
    - _Requirements: 2.7, 2.8_

  - [x] 6.2 修改 `NewsCommands.add_feed()` 指令呼叫 `NotionService.add_feed()`
    - 檔案：`app/bot/cogs/news_commands.py`
    - 移除佔位訊息，改為 `await interaction.response.defer(thinking=True)`
    - 建立 `NotionService()` 實例並呼叫 `await notion.add_feed(name, url, category)`
    - 成功時回傳 `✅ 已成功新增 \`{name}\` ({category}) 至 Notion！\n🔗 {url}`
    - 失敗時捕捉例外並回傳 `❌ 新增失敗：{e}`
    - _Expected_Behavior: `notion_page_created(result) AND success_message_sent(result)`_
    - _Preservation: `/news_now` 完整流程不受影響_
    - _Requirements: 2.7, 2.8_

  - [x] 6.3 驗證 Bug Condition 探索測試現在通過
    - **Property 1: Expected Behavior** - `/add_feed` 寫入 Notion
    - **重要**：重新執行任務 1 中的同一個測試
    - 呼叫修復後的 `/add_feed`，驗證 `notion.pages.create` 被呼叫一次且參數正確
    - **預期結果**：測試通過（確認 Bug 4 已修復）
    - _Requirements: 2.7, 2.8_

  - [x] 6.4 驗證 Preservation 測試仍然通過
    - **Property 2: Preservation** - `/news_now` 流程不受影響
    - **重要**：重新執行任務 2 中的同一個測試
    - **預期結果**：測試通過（確認無迴歸）

- [x] 7. 修復 Bug 5：`ReadLaterView` 重啟後按鈕失效
  - [x] 7.1 修改 `ReadLaterButton` 使用 URL hash 作為 `custom_id`
    - 檔案：`app/bot/cogs/interactions.py`
    - 新增 `import hashlib`
    - 將 `custom_id=f"read_later_{index}"` 改為 `custom_id=f"read_later_{hashlib.md5(article.url.encode()).hexdigest()[:8]}"`
    - 確保 `custom_id` 固定且唯一（基於 URL 內容，不依賴 index）
    - _Bug_Condition: `bot_restarted(X) AND view_not_reregistered(X) AND interaction_targets_ReadLaterView_button(X)`（來自 design.md Bug 5）_
    - _Requirements: 2.9, 2.10_

  - [x] 7.2 在 `setup_hook()` 中呼叫 `bot.add_view()` 註冊 persistent view
    - 檔案：`app/bot/client.py`
    - 在 `setup_hook()` 中加入 `from app.bot.cogs.interactions import ReadLaterView`
    - 呼叫 `self.add_view(ReadLaterView(articles=[]))` 以在 Bot 啟動時重新註冊 persistent view
    - _Expected_Behavior: `not interaction_failed(result)`_
    - _Preservation: Bot 未重啟時，按鈕點擊行為不變_
    - _Requirements: 2.9, 2.10_

  - [x] 7.3 驗證 Bug Condition 探索測試現在通過
    - **Property 1: Expected Behavior** - ReadLaterView 重啟後持久化
    - **重要**：重新執行任務 1 中的同一個測試
    - 模擬 Bot 重啟後的 button interaction，驗證 callback 正確執行
    - **預期結果**：測試通過（確認 Bug 5 已修復）
    - _Requirements: 2.9, 2.10_

  - [x] 7.4 驗證 Preservation 測試仍然通過
    - **Property 2: Preservation** - Bot 未重啟時按鈕行為不變
    - **重要**：重新執行任務 2 中的同一個測試
    - **預期結果**：測試通過（確認無迴歸）

---

## 最終驗收

- [x] 8. Checkpoint — 確認所有測試通過
  - 執行所有 Bug Condition 探索測試（任務 1 的測試），確認全部通過
  - 執行所有 Preservation 屬性測試（任務 2 的測試），確認全部通過
  - 確認五個 Bug 均已修復且無迴歸
  - 若有疑問，請詢問使用者
