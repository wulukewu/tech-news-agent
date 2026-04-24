# Bugfix 需求文件

## 簡介

在 `news_now` 指令發送週報時，`combined_view` 只合併了 `FilterView`（分類篩選）與 `DeepDiveView`（深度摘要）的元件，但完全未加入 `ReadLaterView` 的按鈕。這導致使用者在收到週報訊息後，無法看到「⭐ 稍後閱讀」按鈕，整個稍後閱讀功能因此完全失效，使用者無法將文章儲存至 Notion 的稍後閱讀清單。

## Bug 分析

### 當前行為（缺陷）

1.1 WHEN `news_now` 指令執行並發送週報訊息時，THEN 系統只顯示分類篩選下拉選單與深度摘要按鈕，不顯示任何「稍後閱讀」按鈕

1.2 WHEN 使用者嘗試在週報訊息中點擊「稍後閱讀」按鈕時，THEN 系統無法回應，因為該按鈕根本不存在於訊息的 View 中

1.3 WHEN `combined_view` 被組合時，THEN 系統僅將 `DeepDiveView` 的子元件加入，而 `ReadLaterView` 的 `ReadLaterButton` 元件從未被加入

### 預期行為（正確）

2.1 WHEN `news_now` 指令執行並發送週報訊息時，THEN 系統 SHALL 在訊息中同時顯示分類篩選下拉選單、深度摘要按鈕，以及「⭐ 稍後閱讀」按鈕

2.2 WHEN 使用者點擊「⭐ 稍後閱讀」按鈕時，THEN 系統 SHALL 將對應文章儲存至 Notion 稍後閱讀清單，並回傳成功或失敗的 ephemeral 訊息

2.3 WHEN `combined_view` 被組合時，THEN 系統 SHALL 將 `ReadLaterView` 的 `ReadLaterButton` 元件加入，且總元件數量不超過 Discord View 的 25 個上限

### 不變行為（迴歸預防）

3.1 WHEN `news_now` 指令執行時，THEN 系統 SHALL CONTINUE TO 正常顯示分類篩選下拉選單（`FilterSelect`）

3.2 WHEN `news_now` 指令執行時，THEN 系統 SHALL CONTINUE TO 正常顯示最多 5 個深度摘要按鈕（`DeepDiveButton`）

3.3 WHEN 使用者點擊深度摘要按鈕時，THEN 系統 SHALL CONTINUE TO 正常呼叫 LLM 並回傳深度摘要內容

3.4 WHEN 使用者使用分類篩選下拉選單時，THEN 系統 SHALL CONTINUE TO 正常篩選並顯示對應分類的文章列表

3.5 WHEN 週報訊息的 View 元件總數超過 25 個時，THEN 系統 SHALL CONTINUE TO 不超過 Discord View 的元件上限（現有 1 個 FilterSelect + 最多 5 個 DeepDiveButton = 6 個，加入 ReadLaterButton 後需控制總數 ≤ 25）
