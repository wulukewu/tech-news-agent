# 需求文件

## 簡介

本功能為 Discord Bot 技術新聞策展系統新增兩項互動增強功能：

**功能 1：互動式文章篩選（Interactive Filtering）**
在報表訊息附上 Discord Select Menu，讓用戶可依分類（如 AI、DevOps、Security）篩選文章，無需每次閱讀完整報表。

**功能 3：文章深度摘要展開（Article Deep Dive）**
在每篇文章旁新增「📖 詳細摘要」按鈕，點擊後由 LLM 即時生成更深入的技術分析，以 ephemeral 訊息回傳給點擊者。

## 詞彙表

- **Bot**：Discord Bot，本系統的主要互動介面
- **報表訊息**：`/news_now` 指令執行後，Bot 發送至 Discord 頻道的 Markdown 格式技術新聞摘要訊息
- **Select_Menu**：Discord UI 元件，允許用戶從下拉選單中選擇一個或多個選項
- **Filter_View**：包含 Select_Menu 的 Discord UI View，附加於報表訊息上
- **Deep_Dive_Button**：附加於每篇文章旁的「📖 詳細摘要」按鈕
- **Deep_Dive_View**：包含所有文章 Deep_Dive_Button 的 Discord UI View
- **LLM_Service**：負責呼叫 Groq API 進行 LLM 推論的服務層（`app/services/llm_service.py`）
- **ArticleSchema**：文章資料結構，包含 `title`、`url`、`source_category`、`ai_analysis` 等欄位
- **Ephemeral_Message**：僅對觸發互動的用戶可見的 Discord 訊息
- **Filtered_Report**：依用戶選擇的分類篩選後重新生成的報表內容
- **Deep_Dive_Analysis**：由 LLM 針對單篇文章生成的深度技術分析文字
- **DISCORD_CHAR_LIMIT**：Discord 單則訊息的字元上限，固定為 2000 字元

---

## 需求

### 需求 1：分類篩選選單顯示

**用戶故事：** 身為一位 Discord 用戶，我希望在收到技術新聞報表後能看到分類篩選選單，以便快速找到我感興趣的技術領域文章。

#### 驗收標準

1. WHEN `/news_now` 指令成功生成報表，THE Bot SHALL 在報表訊息中同時附上包含 Select_Menu 的 Filter_View。
2. THE Select_Menu SHALL 從當次報表所含文章的 `source_category` 欄位動態產生選項清單，每個分類對應一個選項。
3. THE Select_Menu SHALL 包含一個「📋 顯示全部」的預設選項，排列於所有分類選項之前。
4. WHEN 報表中的文章涵蓋超過 24 個不同分類，THE Filter_View SHALL 僅顯示出現頻率最高的前 24 個分類選項，並保留「📋 顯示全部」選項。
5. THE Select_Menu SHALL 設定 `placeholder` 文字為「請選擇分類篩選文章…」。

---

### 需求 2：分類篩選互動處理

**用戶故事：** 身為一位 Discord 用戶，我希望選擇分類後能立即看到篩選結果，以便專注閱讀特定領域的文章。

#### 驗收標準

1. WHEN 用戶從 Select_Menu 選擇一個分類，THE Bot SHALL 以 Ephemeral_Message 回傳僅包含該分類文章的 Filtered_Report。
2. WHEN 用戶從 Select_Menu 選擇「📋 顯示全部」，THE Bot SHALL 以 Ephemeral_Message 回傳包含所有文章的完整報表內容。
3. WHEN Filtered_Report 的字元數超過 DISCORD_CHAR_LIMIT，THE Bot SHALL 截斷內容至 DISCORD_CHAR_LIMIT 減去 3 個字元，並在末尾附加 `...`。
4. WHEN 用戶選擇的分類在當次報表中沒有對應文章，THE Bot SHALL 以 Ephemeral_Message 回傳提示訊息「⚠️ 此分類目前沒有文章。」。
5. WHEN Select_Menu 互動處理過程中發生例外，THE Bot SHALL 以 Ephemeral_Message 回傳錯誤提示「❌ 篩選時發生錯誤，請稍後再試。」，並將例外記錄至日誌。

---

### 需求 3：深度摘要按鈕顯示

**用戶故事：** 身為一位 Discord 用戶，我希望每篇文章旁都有一個深度摘要按鈕，以便在需要時快速取得更詳細的技術分析。

#### 驗收標準

1. WHEN `/news_now` 指令成功生成報表，THE Bot SHALL 在報表訊息中為每篇精選文章附上對應的 Deep_Dive_Button。
2. THE Deep_Dive_Button SHALL 使用標籤格式「📖 {文章標題前 20 字元}」，WHEN 文章標題超過 20 字元，THE Deep_Dive_Button SHALL 在標籤末尾附加 `...`。
3. THE Deep_Dive_Button SHALL 使用文章 URL 的 MD5 雜湊值前 8 碼作為 `custom_id` 的一部分，以確保唯一性。
4. WHEN 報表包含超過 5 篇文章，THE Deep_Dive_View SHALL 僅為前 5 篇文章顯示 Deep_Dive_Button，以符合 Discord View 的元件數量限制。

---

### 需求 4：深度摘要即時生成

**用戶故事：** 身為一位 Discord 用戶，我希望點擊深度摘要按鈕後能收到由 AI 生成的深入技術分析，以便在不離開 Discord 的情況下深入了解文章內容。

#### 驗收標準

1. WHEN 用戶點擊 Deep_Dive_Button，THE Bot SHALL 立即以 `defer` 方式回應互動，並設定 `ephemeral=True`。
2. WHEN 互動被 defer 後，THE LLM_Service SHALL 針對對應的 ArticleSchema 生成 Deep_Dive_Analysis。
3. THE LLM_Service SHALL 使用 `SUMMARIZE_MODEL`（`llama-3.3-70b-versatile`）生成 Deep_Dive_Analysis。
4. THE Deep_Dive_Analysis SHALL 包含以下結構化內容：核心技術概念說明、實際應用場景、潛在風險或限制、以及建議的下一步行動。
5. WHEN Deep_Dive_Analysis 生成完成，THE Bot SHALL 以 Ephemeral_Message 將分析結果回傳給點擊按鈕的用戶。
6. WHEN Deep_Dive_Analysis 的字元數超過 DISCORD_CHAR_LIMIT，THE Bot SHALL 截斷內容至 DISCORD_CHAR_LIMIT 減去 3 個字元，並在末尾附加 `...`。
7. WHEN LLM_Service 呼叫過程中發生例外，THE Bot SHALL 以 Ephemeral_Message 回傳錯誤提示「❌ 生成深度摘要時發生錯誤，請稍後再試。」，並將例外記錄至日誌。

---

### 需求 5：LLM 深度摘要生成方法

**用戶故事：** 身為一位開發者，我希望 LLM_Service 提供專門的深度摘要生成方法，以便與現有的評估和電子報生成功能保持職責分離。

#### 驗收標準

1. THE LLM_Service SHALL 提供一個 `generate_deep_dive` 非同步方法，接受單一 ArticleSchema 作為輸入，並回傳字串型別的 Deep_Dive_Analysis。
2. WHEN `generate_deep_dive` 被呼叫，THE LLM_Service SHALL 使用文章的 `title`、`content_preview`、`source_category` 及 `ai_analysis` 欄位作為 LLM 提示的輸入資料。
3. THE LLM_Service SHALL 在 `generate_deep_dive` 的系統提示中要求 LLM 以繁體中文輸出分析結果。
4. IF `generate_deep_dive` 收到的 ArticleSchema 其 `content_preview` 為空字串，THEN THE LLM_Service SHALL 以文章標題作為唯一輸入，仍嘗試生成分析。
5. THE `generate_deep_dive` 方法 SHALL 設定 `max_tokens` 為 600，以確保輸出長度符合 DISCORD_CHAR_LIMIT 的限制。

---

### 需求 6：View 元件的狀態管理與持久性

**用戶故事：** 身為一位 Discord 用戶，我希望篩選選單和深度摘要按鈕在 Bot 重啟後仍然可以使用，以便不因 Bot 維護而失去互動功能。

#### 驗收標準

1. THE Filter_View SHALL 以 `timeout=None` 初始化，使其在 Bot 重啟後仍保持有效。
2. THE Deep_Dive_View SHALL 以 `timeout=None` 初始化，使其在 Bot 重啟後仍保持有效。
3. WHEN Bot 啟動時，THE Bot SHALL 透過 `bot.add_view()` 在 `setup_hook` 中註冊所有持久性 View，以恢復互動功能。
4. WHEN Filter_View 或 Deep_Dive_View 因缺少文章資料而無法恢復狀態，THE Bot SHALL 記錄警告日誌，並跳過該 View 的註冊，不拋出例外。
