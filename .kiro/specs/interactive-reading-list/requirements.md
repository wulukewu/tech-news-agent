# 需求文件

## 簡介

本功能為 Tech News Agent 新增「互動式閱讀清單」，讓使用者能直接在 Discord 中管理 Notion 待讀清單，無需切換至 Notion 介面。

目前系統已支援透過「稍後閱讀」按鈕將文章單向存入 Notion，但缺乏後續管理能力。本功能將新增 `/reading_list` 指令，支援查看清單、標記已讀、對文章評分，以及根據閱讀歷史推薦相似文章。

## 詞彙表

- **Reading_List_Command**：處理 `/reading_list` Discord 斜線指令的模組
- **Notion_Service**：負責與 Notion API 溝通的服務層，現有元件
- **LLM_Service**：負責與 Groq LLM 溝通的服務層，現有元件
- **Read_Later_DB**：Notion 中儲存待讀文章的資料庫，現有資料庫
- **Article_Item**：Read_Later_DB 中的單筆文章記錄，包含標題、URL、狀態、評分等欄位
- **Discord_Bot**：現有的 Discord Bot 實例
- **Pagination_View**：Discord UI 元件，用於分頁顯示文章清單
- **Rating_Select**：Discord UI 下拉選單元件，用於選擇文章評分（1–5 星）
- **Status**：Article_Item 的狀態欄位，可為 `Unread`（未讀）或 `Read`（已讀）
- **Rating**：Article_Item 的評分欄位，數值範圍 1–5，對應 Notion Number 欄位

---

## 需求

### 需求 1：查看待讀清單

**使用者故事：** 身為 Discord 使用者，我希望能透過 `/reading_list` 指令查看 Notion 待讀清單，以便在不切換應用程式的情況下掌握待讀文章。

#### 驗收標準

1. WHEN 使用者執行 `/reading_list` 指令，THE Reading_List_Command SHALL 向 Notion_Service 查詢 Read_Later_DB 中所有 Status 為 `Unread` 的 Article_Item。
2. WHEN Notion_Service 成功回傳文章清單，THE Reading_List_Command SHALL 以分頁方式在 Discord 顯示文章清單，每頁最多顯示 5 筆 Article_Item。
3. WHEN 文章清單包含多頁，THE Pagination_View SHALL 提供「上一頁」與「下一頁」按鈕供使用者切換。
4. WHEN 文章清單為空，THE Reading_List_Command SHALL 回覆「📭 目前待讀清單是空的！」的提示訊息。
5. IF Notion_Service 回傳錯誤，THEN THE Reading_List_Command SHALL 回覆包含錯誤說明的提示訊息，且不顯示部分資料。
6. THE Reading_List_Command SHALL 以 ephemeral 方式回覆，確保清單內容僅對執行指令的使用者可見。

---

### 需求 2：標記文章為已讀

**使用者故事：** 身為 Discord 使用者，我希望能直接在 Discord 將待讀文章標記為已讀，以便維護清單的準確性。

#### 驗收標準

1. WHEN 文章清單顯示時，THE Pagination_View SHALL 為每筆 Article_Item 提供「✅ 標記已讀」按鈕。
2. WHEN 使用者點擊「✅ 標記已讀」按鈕，THE Reading_List_Command SHALL 呼叫 Notion_Service 將對應 Article_Item 的 Status 更新為 `Read`。
3. WHEN Notion_Service 成功更新狀態，THE Reading_List_Command SHALL 停用該按鈕並以 ephemeral 訊息通知使用者操作成功。
4. IF Notion_Service 更新失敗，THEN THE Reading_List_Command SHALL 以 ephemeral 訊息通知使用者操作失敗，且不修改按鈕狀態。
5. WHEN 文章被標記為已讀後，THE Reading_List_Command SHALL 從下次查詢的 `Unread` 清單中排除該 Article_Item。

---

### 需求 3：對文章評分

**使用者故事：** 身為 Discord 使用者，我希望能對文章給予 1–5 星評分，以便記錄個人閱讀評價並作為推薦依據。

#### 驗收標準

1. WHEN 文章清單顯示時，THE Pagination_View SHALL 為每筆 Article_Item 提供 Rating_Select 下拉選單，選項為 1 至 5 星（⭐ 至 ⭐⭐⭐⭐⭐）。
2. WHEN 使用者透過 Rating_Select 選擇評分，THE Reading_List_Command SHALL 呼叫 Notion_Service 將對應 Article_Item 的 Rating 欄位更新為所選數值（1–5）。
3. WHEN Notion_Service 成功更新評分，THE Reading_List_Command SHALL 以 ephemeral 訊息確認評分已儲存，並顯示所選星數。
4. IF Notion_Service 更新評分失敗，THEN THE Reading_List_Command SHALL 以 ephemeral 訊息通知使用者操作失敗。
5. THE Notion_Service SHALL 支援對 Read_Later_DB 中的 Article_Item 寫入 Rating 欄位（Notion Number 類型，範圍 1–5）。

---

### 需求 4：根據閱讀歷史推薦相似文章

**使用者故事：** 身為 Discord 使用者，我希望系統能根據我評分較高的文章推薦相似內容，以便發現更多感興趣的技術文章。

#### 驗收標準

1. WHEN 使用者執行 `/reading_list recommend` 子指令，THE Reading_List_Command SHALL 向 Notion_Service 查詢 Read_Later_DB 中 Rating 大於等於 4 的 Article_Item 作為偏好樣本。
2. WHEN 偏好樣本數量大於等於 1 筆，THE Reading_List_Command SHALL 將偏好樣本的標題與分類傳遞給 LLM_Service，請求生成推薦關鍵字與分類偏好摘要。
3. WHEN LLM_Service 回傳推薦摘要，THE Reading_List_Command SHALL 以 ephemeral 訊息顯示推薦摘要，內容包含建議關注的技術主題與關鍵字。
4. WHEN 偏好樣本數量為 0 筆，THE Reading_List_Command SHALL 回覆「尚無足夠的高評分文章，請先對文章評分（4 星以上）後再試。」的提示訊息。
5. IF LLM_Service 回傳錯誤，THEN THE Reading_List_Command SHALL 以 ephemeral 訊息通知使用者推薦功能暫時無法使用。
6. THE LLM_Service SHALL 接受文章標題清單與分類清單作為輸入，並回傳不超過 500 字的繁體中文推薦摘要。

---

### 需求 5：Notion 資料庫欄位擴充

**使用者故事：** 身為系統管理員，我希望 Read_Later_DB 具備評分欄位，以便支援評分與推薦功能。

#### 驗收標準

1. THE Read_Later_DB SHALL 包含名為 `Rating` 的 Notion Number 欄位，用於儲存 1–5 的整數評分。
2. WHEN Article_Item 尚未被評分，THE Notion_Service SHALL 將 `Rating` 欄位視為空值（null）處理，不預設任何數值。
3. THE Notion_Service SHALL 提供 `get_reading_list` 方法，回傳 Read_Later_DB 中所有 Status 為 `Unread` 的 Article_Item 清單，每筆包含 Notion Page ID、標題、URL、分類、新增時間。
4. THE Notion_Service SHALL 提供 `mark_as_read` 方法，接受 Notion Page ID 並將對應 Article_Item 的 Status 更新為 `Read`。
5. THE Notion_Service SHALL 提供 `rate_article` 方法，接受 Notion Page ID 與整數評分（1–5），並更新對應 Article_Item 的 Rating 欄位。
6. THE Notion_Service SHALL 提供 `get_highly_rated_articles` 方法，回傳 Read_Later_DB 中 Rating 大於等於指定閾值的 Article_Item 清單。
