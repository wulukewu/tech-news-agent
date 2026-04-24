# Bugfix 需求文件

## 簡介

本文件描述 Python 技術新聞 Agent（FastAPI + Discord Bot + APScheduler + Notion API + Groq LLM）中已確認的五個問題。這些問題涵蓋 API 相容性錯誤、環境依賴問題、設定錯誤、功能缺失以及 UI 穩定性問題，其中 Notion API AttributeError 為最嚴重的問題，導致核心功能完全無法使用。

---

## Bug 分析

### 現有行為（缺陷）

**Bug 1：Notion API `databases.query` AttributeError**

1.1 WHEN 呼叫 `/news_now` 指令或排程任務觸發時，THEN 系統在 `notion_service.py` 第 22 行拋出 `AttributeError: 'DatabasesEndpoint' object has no attribute 'query'`，導致指令完全失敗

1.2 WHEN `NotionService.get_active_feeds()` 被呼叫時，THEN 系統使用已廢棄的 `self.client.databases.query(database_id=...)` API，在 `notion-client>=2.2.1` 版本下無法執行

**Bug 2：Docker 環境中 `certifi` 缺少依賴**

2.1 WHEN 在 Docker（Linux）環境下執行 `pip install -r requirements.txt` 並啟動應用程式時，THEN 系統因 `requirements.txt` 缺少 `certifi` 套件而在 import 階段拋出 `ModuleNotFoundError`

2.2 WHEN 應用程式在 Linux/Docker 環境啟動時，THEN 系統無條件執行 macOS 專用的 SSL 憑證修復程式碼（`os.environ["SSL_CERT_FILE"] = certifi.where()`），在非 macOS 環境下造成不必要的依賴與潛在錯誤

**Bug 3：Scheduler timezone 設定錯誤**

3.1 WHEN `AsyncIOScheduler` 初始化時，THEN 系統使用 `settings.model_config.get("timezone", "Asia/Taipei")`，但 `model_config` 是 Pydantic 的 meta 設定物件而非 `.env` 的值，導致 `.get()` 永遠回傳預設值 `"Asia/Taipei"` 而非實際設定

3.2 WHEN 使用者在 `.env` 中設定 `TIMEZONE` 環境變數時，THEN 系統忽略該設定，Scheduler 無法正確讀取使用者自訂的 timezone

**Bug 4：`/add_feed` 指令為空殼，Notion 寫入邏輯未實作**

4.1 WHEN 使用者執行 `/add_feed` 指令並提供 `name`、`url`、`category` 參數時，THEN 系統只回傳佔位訊息，不執行任何 Notion 資料庫寫入操作

4.2 WHEN `NewsCommands.add_feed()` 被呼叫時，THEN 系統不呼叫 `NotionService`，因為 `NotionService` 缺少 `add_feed()` 方法

**Bug 5：`ReadLaterView` 重啟後按鈕失效**

5.1 WHEN Discord Bot 重啟後，使用者點擊舊訊息中的「稍後閱讀」按鈕時，THEN 系統回應 `interaction failed`，因為 `ReadLaterView` 未在 Bot 啟動時重新註冊為 persistent view

5.2 WHEN `ReadLaterView` 以 `timeout=None` 初始化但未呼叫 `bot.add_view()` 時，THEN 系統在 Bot 重啟後無法處理該 View 的 interaction 回呼

---

### 預期行為（正確）

**Bug 1：Notion API 修正**

2.1 WHEN 呼叫 `/news_now` 指令或排程任務觸發時，THEN 系統 SHALL 成功查詢 Notion Feeds 資料庫並回傳啟用的 RSS 訂閱源清單，不拋出任何例外

2.2 WHEN `NotionService.get_active_feeds()` 被呼叫時，THEN 系統 SHALL 使用與 `notion-client>=2.2.1` 相容的正確 API（`self.client.databases.query(database_id=...)` 若仍有效，或改用正確的新版 API）完成查詢

**Bug 2：Docker 環境依賴修正**

2.3 WHEN 在 Docker（Linux）環境下執行 `pip install -r requirements.txt` 時，THEN 系統 SHALL 成功安裝所有依賴，不因缺少套件而失敗

2.4 WHEN 應用程式啟動時，THEN 系統 SHALL 僅在 macOS 環境下執行 SSL 憑證修復程式碼，在 Linux/Docker 環境下 SHALL 跳過該段邏輯

**Bug 3：Scheduler timezone 修正**

2.5 WHEN `AsyncIOScheduler` 初始化時，THEN 系統 SHALL 使用正確的 timezone 值（hardcode `"Asia/Taipei"` 或從 `Settings` 中讀取正確的 `timezone` 欄位）

2.6 WHEN 使用者在 `.env` 中設定 `TIMEZONE` 環境變數時，THEN 系統 SHALL 正確讀取並套用該設定至 Scheduler

**Bug 4：`/add_feed` 功能實作**

2.7 WHEN 使用者執行 `/add_feed` 指令並提供有效的 `name`、`url`、`category` 參數時，THEN 系統 SHALL 在 Notion Feeds 資料庫中建立新的頁面記錄，並回傳成功訊息

2.8 WHEN `add_feed` 被呼叫時，THEN `NotionService` SHALL 提供 `add_feed(name, url, category)` 方法，執行實際的 Notion API 寫入操作

**Bug 5：`ReadLaterView` 持久化修正**

2.9 WHEN Discord Bot 重啟後，使用者點擊舊訊息中的「稍後閱讀」按鈕時，THEN 系統 SHALL 正確處理 interaction，不回應 `interaction failed`

2.10 WHEN Bot 啟動時，THEN 系統 SHALL 呼叫 `bot.add_view()` 重新註冊 `ReadLaterView`，或改用有合理 timeout 的設計以避免殭屍按鈕問題

---

### 不變行為（迴歸預防）

3.1 WHEN 使用者執行 `/news_now` 且 Notion 中有啟用的 RSS 訂閱源時，THEN 系統 SHALL CONTINUE TO 完整執行抓取、評分、生成、發送的完整流程

3.2 WHEN `NotionService.add_to_read_later()` 被呼叫時，THEN 系統 SHALL CONTINUE TO 正確將文章寫入 Notion Read Later 資料庫

3.3 WHEN 使用者點擊「稍後閱讀」按鈕（Bot 未重啟的情況下），THEN 系統 SHALL CONTINUE TO 成功將文章存入 Notion 並停用該按鈕

3.4 WHEN 排程任務在每週五 17:00 觸發時，THEN 系統 SHALL CONTINUE TO 自動執行新聞彙整並發送至指定 Discord 頻道

3.5 WHEN 應用程式在 macOS 本地環境啟動時，THEN 系統 SHALL CONTINUE TO 正確套用 SSL 憑證修復，不影響本地開發體驗

3.6 WHEN `NotionService.get_active_feeds()` 回傳空清單時，THEN 系統 SHALL CONTINUE TO 回傳適當的提示訊息而非拋出例外

---

## Bug Condition 推導

### Bug 1 — Notion API AttributeError

```pascal
FUNCTION isBugCondition_1(X)
  INPUT: X 為任何觸發 get_active_feeds() 的呼叫
  OUTPUT: boolean
  RETURN notion_client_version >= "2.2.1" AND uses_deprecated_databases_query_api(X)
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition_1(X) DO
  result ← get_active_feeds'(X)
  ASSERT no_attribute_error(result) AND returns_list_of_feeds(result)
END FOR

// Preservation Checking
FOR ALL X WHERE NOT isBugCondition_1(X) DO
  ASSERT get_active_feeds(X) = get_active_feeds'(X)
END FOR
```

### Bug 2 — certifi 環境依賴

```pascal
FUNCTION isBugCondition_2(X)
  INPUT: X 為應用程式啟動環境
  OUTPUT: boolean
  RETURN is_docker_or_linux(X) AND certifi_not_in_requirements(X)
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition_2(X) DO
  result ← startup'(X)
  ASSERT no_module_not_found_error(result) AND ssl_patch_skipped_on_linux(result)
END FOR
```

### Bug 3 — Scheduler timezone

```pascal
FUNCTION isBugCondition_3(X)
  INPUT: X 為 Scheduler 初始化呼叫
  OUTPUT: boolean
  RETURN uses_model_config_get_for_timezone(X)
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition_3(X) DO
  result ← init_scheduler'(X)
  ASSERT scheduler_timezone_is_valid(result) AND not_from_model_config_meta(result)
END FOR
```

### Bug 4 — /add_feed 空殼

```pascal
FUNCTION isBugCondition_4(X)
  INPUT: X 為 /add_feed 指令呼叫，包含 name, url, category
  OUTPUT: boolean
  RETURN add_feed_has_no_notion_write_logic(X)
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition_4(X) DO
  result ← add_feed'(X)
  ASSERT notion_page_created(result) AND success_message_sent(result)
END FOR
```

### Bug 5 — ReadLaterView 重啟失效

```pascal
FUNCTION isBugCondition_5(X)
  INPUT: X 為 Bot 重啟後的 button interaction
  OUTPUT: boolean
  RETURN bot_restarted(X) AND view_not_reregistered(X)
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition_5(X) DO
  result ← handle_interaction'(X)
  ASSERT not interaction_failed(result)
END FOR
```
