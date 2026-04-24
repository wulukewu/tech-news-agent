# Requirements Document

## Introduction

本文件定義 Tech News Agent 專案的跨平台功能對齊需求。目標是將 Discord Bot 已有的完整功能（閱讀清單、評分、標記已讀、深度摘要、推薦系統）補齊到網頁端，確保兩個平台功能一致且資料即時同步。所有功能以用戶為單位獨立運作，使用 Supabase 作為統一資料來源。

## Glossary

- **Web_Frontend**: Next.js 網頁應用程式，提供瀏覽器存取介面
- **Discord_Bot**: Discord 機器人應用程式，提供 Discord 平台存取介面
- **Reading_List**: 用戶的「稍後閱讀」文章清單
- **Article**: 從 RSS 來源抓取的技術新聞文章
- **User**: 使用平台的個別用戶（透過 Discord OAuth 認證）
- **Rating**: 用戶對文章的評分（1-5 星）
- **Read_Status**: 文章的閱讀狀態（Unread, Read, Archived）
- **Deep_Summary**: AI 生成的文章深度分析摘要
- **Recommendation**: 基於用戶評分生成的個人化推薦
- **Supabase**: 統一的資料庫服務，作為跨平台資料同步的單一真實來源
- **Sync_State**: 跨平台資料同步狀態
- **LLM_Service**: 使用 Groq API 的大型語言模型服務

## Requirements

### Requirement 1: 網頁端閱讀清單管理

**User Story:** 作為用戶，我想在網頁端管理我的閱讀清單，這樣我可以在瀏覽器中方便地儲存和查看想稍後閱讀的文章。

#### Acceptance Criteria

1. WHEN 用戶在網頁端點擊文章的「加入閱讀清單」按鈕，THE Web_Frontend SHALL 將該文章加入用戶的 Reading_List
2. WHEN 文章成功加入 Reading_List，THE Web_Frontend SHALL 顯示成功提示訊息
3. WHEN 用戶導航到閱讀清單頁面，THE Web_Frontend SHALL 顯示該用戶所有 Reading_List 中的文章
4. THE Web_Frontend SHALL 按加入時間降序排列 Reading_List 中的文章
5. WHEN 用戶在 Reading_List 中點擊文章，THE Web_Frontend SHALL 在新分頁開啟該文章的原始 URL
6. WHEN 用戶點擊「從清單移除」按鈕，THE Web_Frontend SHALL 從 Reading_List 中移除該文章
7. THE Web_Frontend SHALL 顯示每篇文章的標題、來源、分類、加入時間
8. WHEN Reading_List 為空，THE Web_Frontend SHALL 顯示友善的空狀態訊息

### Requirement 2: 網頁端文章評分功能

**User Story:** 作為用戶，我想在網頁端對文章評分，這樣系統可以學習我的偏好並提供更好的推薦。

#### Acceptance Criteria

1. THE Web_Frontend SHALL 在每篇文章旁顯示 1-5 星的評分介面
2. WHEN 用戶選擇星級評分，THE Web_Frontend SHALL 將 Rating 儲存到 Supabase
3. WHEN Rating 成功儲存，THE Web_Frontend SHALL 即時更新顯示的星級
4. WHEN 用戶修改已有的 Rating，THE Web_Frontend SHALL 更新該 Rating 值
5. THE Web_Frontend SHALL 顯示用戶當前對該文章的 Rating（如果已評分）
6. WHEN 用戶尚未對文章評分，THE Web_Frontend SHALL 顯示空星級狀態
7. THE Web_Frontend SHALL 驗證 Rating 值在 1-5 範圍內
8. IF Rating 值無效，THEN THE Web_Frontend SHALL 顯示錯誤訊息且不儲存

### Requirement 3: 網頁端標記已讀功能

**User Story:** 作為用戶，我想在網頁端標記文章為已讀，這樣我可以追蹤哪些文章已經閱讀過。

#### Acceptance Criteria

1. THE Web_Frontend SHALL 在每篇文章旁顯示「標記已讀」按鈕
2. WHEN 用戶點擊「標記已讀」按鈕，THE Web_Frontend SHALL 更新該文章的 Read_Status 為 'Read'
3. WHEN Read_Status 更新成功，THE Web_Frontend SHALL 視覺化標示該文章為已讀（例如：灰色文字、勾選圖示）
4. THE Web_Frontend SHALL 提供篩選器以顯示「全部」、「未讀」或「已讀」文章
5. WHEN 用戶選擇「未讀」篩選，THE Web_Frontend SHALL 只顯示 Read_Status 為 'Unread' 的文章
6. WHEN 用戶選擇「已讀」篩選，THE Web_Frontend SHALL 只顯示 Read_Status 為 'Read' 的文章
7. WHEN 用戶點擊已讀文章的「標記未讀」按鈕，THE Web_Frontend SHALL 更新 Read_Status 為 'Unread'
8. THE Web_Frontend SHALL 在文章列表顯示已讀/未讀狀態指示器

### Requirement 4: 網頁端深度摘要生成

**User Story:** 作為用戶，我想在網頁端請求文章的深度分析，這樣我可以快速了解文章的關鍵要點和技術細節。

#### Acceptance Criteria

1. THE Web_Frontend SHALL 在每篇文章旁顯示「生成深度摘要」按鈕
2. WHEN 用戶點擊「生成深度摘要」按鈕，THE Web_Frontend SHALL 呼叫 LLM_Service 生成 Deep_Summary
3. WHILE Deep_Summary 生成中，THE Web_Frontend SHALL 顯示載入指示器
4. WHEN Deep_Summary 生成完成，THE Web_Frontend SHALL 在模態視窗或展開區域顯示摘要內容
5. THE Deep_Summary SHALL 包含關鍵要點、技術細節、實用性評估
6. WHEN Deep_Summary 已存在，THE Web_Frontend SHALL 直接顯示快取的摘要而不重新生成
7. THE Web_Frontend SHALL 將生成的 Deep_Summary 儲存到 Supabase 供重複查看
8. IF LLM_Service 生成失敗，THEN THE Web_Frontend SHALL 顯示錯誤訊息並提供重試選項

### Requirement 5: 網頁端個人化推薦系統

**User Story:** 作為用戶，我想在網頁端查看基於我的評分的個人化推薦，這樣我可以發現更多符合我興趣的文章。

#### Acceptance Criteria

1. THE Web_Frontend SHALL 提供「查看推薦」功能入口
2. WHEN 用戶點擊「查看推薦」，THE Web_Frontend SHALL 查詢該用戶所有 Rating >= 4 的文章
3. IF 用戶沒有高評分文章（Rating >= 4），THEN THE Web_Frontend SHALL 顯示提示訊息要求用戶先評分
4. WHEN 用戶有高評分文章，THE Web_Frontend SHALL 呼叫 LLM_Service 生成 Recommendation
5. THE Recommendation SHALL 基於高評分文章的標題和分類生成
6. THE Web_Frontend SHALL 顯示 Recommendation 內容，包含推薦理由和相關主題
7. THE Web_Frontend SHALL 提供「每週推薦」和「每月推薦」兩種時間範圍選項
8. WHEN 用戶選擇時間範圍，THE Web_Frontend SHALL 只考慮該時間範圍內的高評分文章

### Requirement 6: 跨平台閱讀清單同步

**User Story:** 作為用戶，我想在任一平台加入閱讀清單的文章能在另一平台即時看到，這樣我可以無縫切換使用環境。

#### Acceptance Criteria

1. WHEN 用戶在 Web_Frontend 加入文章到 Reading_List，THE Supabase SHALL 立即儲存該記錄
2. WHEN 用戶在 Discord_Bot 查詢 Reading_List，THE Discord_Bot SHALL 顯示包含從 Web_Frontend 加入的文章
3. WHEN 用戶在 Discord_Bot 加入文章到 Reading_List，THE Supabase SHALL 立即儲存該記錄
4. WHEN 用戶在 Web_Frontend 查詢 Reading_List，THE Web_Frontend SHALL 顯示包含從 Discord_Bot 加入的文章
5. FOR ALL 平台操作，THE Supabase SHALL 作為單一真實來源（Single Source of Truth）
6. WHEN 用戶在任一平台移除 Reading_List 項目，THE 另一平台 SHALL 反映該移除操作
7. THE 系統 SHALL 確保 Reading_List 操作的冪等性（重複加入相同文章不產生重複記錄）
8. THE 系統 SHALL 使用 (user_id, article_id) 作為 Reading_List 的唯一性約束

### Requirement 7: 跨平台評分同步

**User Story:** 作為用戶，我想在任一平台的評分能在另一平台即時同步，這樣我的偏好資料保持一致。

#### Acceptance Criteria

1. WHEN 用戶在 Web_Frontend 對文章評分，THE Supabase SHALL 立即儲存該 Rating
2. WHEN 用戶在 Discord_Bot 查詢該文章，THE Discord_Bot SHALL 顯示從 Web_Frontend 設定的 Rating
3. WHEN 用戶在 Discord_Bot 對文章評分，THE Supabase SHALL 立即儲存該 Rating
4. WHEN 用戶在 Web_Frontend 查詢該文章，THE Web_Frontend SHALL 顯示從 Discord_Bot 設定的 Rating
5. WHEN 用戶在任一平台修改 Rating，THE 另一平台 SHALL 顯示更新後的 Rating 值
6. THE 系統 SHALL 確保每個用戶對每篇文章只有一個 Rating 值
7. THE 系統 SHALL 使用 (user_id, article_id) 作為 Rating 的唯一性約束
8. WHEN 用戶在平台 A 評分後在平台 B 再次評分，THE 系統 SHALL 更新而非建立新記錄

### Requirement 8: 跨平台已讀狀態同步

**User Story:** 作為用戶，我想在任一平台標記的已讀狀態能在另一平台即時同步，這樣我不會重複閱讀已讀文章。

#### Acceptance Criteria

1. WHEN 用戶在 Web_Frontend 標記文章為已讀，THE Supabase SHALL 立即更新該文章的 Read_Status
2. WHEN 用戶在 Discord_Bot 查詢該文章，THE Discord_Bot SHALL 顯示 Read_Status 為 'Read'
3. WHEN 用戶在 Discord_Bot 標記文章為已讀，THE Supabase SHALL 立即更新該文章的 Read_Status
4. WHEN 用戶在 Web_Frontend 查詢該文章，THE Web_Frontend SHALL 顯示 Read_Status 為 'Read'
5. WHEN 用戶在任一平台標記文章為未讀，THE 另一平台 SHALL 顯示 Read_Status 為 'Unread'
6. THE 系統 SHALL 支援三種 Read_Status 值：'Unread', 'Read', 'Archived'
7. THE 系統 SHALL 驗證 Read_Status 值只能是允許的三種狀態之一
8. WHEN 用戶在平台 A 更新 Read_Status 後在平台 B 查詢，THE 平台 B SHALL 顯示最新的 Read_Status

### Requirement 9: 跨平台深度摘要共享

**User Story:** 作為用戶，我想在任一平台生成的深度摘要能在另一平台查看，這樣我不需要重複生成相同內容。

#### Acceptance Criteria

1. WHEN 用戶在 Web_Frontend 生成 Deep_Summary，THE Supabase SHALL 儲存該摘要內容
2. WHEN 用戶在 Discord_Bot 請求相同文章的深度摘要，THE Discord_Bot SHALL 顯示已儲存的 Deep_Summary
3. WHEN 用戶在 Discord_Bot 生成 Deep_Summary，THE Supabase SHALL 儲存該摘要內容
4. WHEN 用戶在 Web_Frontend 請求相同文章的深度摘要，THE Web_Frontend SHALL 顯示已儲存的 Deep_Summary
5. THE 系統 SHALL 檢查 Deep_Summary 是否已存在於 Supabase
6. IF Deep_Summary 已存在，THEN THE 系統 SHALL 直接返回快取的摘要而不呼叫 LLM_Service
7. THE 系統 SHALL 將 Deep_Summary 儲存在 articles 表的 ai_summary 欄位
8. THE Deep_Summary SHALL 對所有用戶共享（非用戶特定資料）

### Requirement 10: 用戶資料隔離

**User Story:** 作為用戶，我想確保我的閱讀清單、評分和已讀狀態只有我能看到，這樣我的個人資料保持私密。

#### Acceptance Criteria

1. THE 系統 SHALL 使用 user_id 作為所有用戶特定資料的隔離鍵
2. WHEN 用戶 A 查詢 Reading_List，THE 系統 SHALL 只返回 user_id 等於用戶 A 的記錄
3. WHEN 用戶 B 查詢 Reading_List，THE 系統 SHALL 只返回 user_id 等於用戶 B 的記錄
4. THE 系統 SHALL 確保用戶 A 無法查詢或修改用戶 B 的 Reading_List
5. THE 系統 SHALL 確保用戶 A 無法查詢或修改用戶 B 的 Rating
6. THE 系統 SHALL 確保用戶 A 無法查詢或修改用戶 B 的 Read_Status
7. THE 系統 SHALL 在所有資料庫查詢中強制執行 user_id 篩選
8. THE 系統 SHALL 使用 Row Level Security (RLS) 政策確保資料隔離

### Requirement 11: 資料一致性保證

**User Story:** 作為用戶，我想確保我的資料在兩個平台之間保持一致，這樣我不會遇到資料衝突或遺失。

#### Acceptance Criteria

1. THE Supabase SHALL 作為唯一的資料寫入目標（Single Source of Truth）
2. THE Web_Frontend SHALL 不在本地快取用戶特定資料（Reading_List, Rating, Read_Status）
3. THE Discord_Bot SHALL 不在本地快取用戶特定資料（Reading_List, Rating, Read_Status）
4. WHEN 用戶在任一平台執行操作，THE 系統 SHALL 立即寫入 Supabase
5. WHEN 用戶在任一平台查詢資料，THE 系統 SHALL 從 Supabase 讀取最新資料
6. THE 系統 SHALL 使用資料庫交易確保複合操作的原子性
7. THE 系統 SHALL 使用樂觀鎖定或時間戳處理並發更新
8. WHEN 並發更新發生，THE 系統 SHALL 確保最後寫入的操作生效

### Requirement 12: 錯誤處理與使用者回饋

**User Story:** 作為用戶，我想在操作失敗時收到清楚的錯誤訊息，這樣我知道發生了什麼問題以及如何解決。

#### Acceptance Criteria

1. WHEN 資料庫操作失敗，THE Web_Frontend SHALL 顯示使用者友善的錯誤訊息
2. WHEN LLM_Service 呼叫失敗，THE Web_Frontend SHALL 顯示錯誤訊息並提供重試選項
3. WHEN 網路連線失敗，THE Web_Frontend SHALL 顯示連線錯誤訊息
4. THE Web_Frontend SHALL 記錄詳細錯誤資訊到後端日誌系統
5. THE Web_Frontend SHALL 不向用戶顯示技術性錯誤細節（如堆疊追蹤）
6. WHEN 操作成功，THE Web_Frontend SHALL 顯示成功確認訊息
7. THE Web_Frontend SHALL 在長時間操作時顯示進度指示器
8. IF 操作超時，THEN THE Web_Frontend SHALL 顯示超時訊息並建議用戶重試

### Requirement 13: API 端點實作

**User Story:** 作為開發者，我需要 RESTful API 端點來支援網頁端的所有功能，這樣前端可以與後端服務互動。

#### Acceptance Criteria

1. THE 系統 SHALL 提供 POST /api/reading-list 端點以加入文章到 Reading_List
2. THE 系統 SHALL 提供 GET /api/reading-list 端點以查詢用戶的 Reading_List
3. THE 系統 SHALL 提供 DELETE /api/reading-list/{article_id} 端點以移除 Reading_List 項目
4. THE 系統 SHALL 提供 POST /api/articles/{article_id}/rating 端點以設定或更新 Rating
5. THE 系統 SHALL 提供 POST /api/articles/{article_id}/status 端點以更新 Read_Status
6. THE 系統 SHALL 提供 POST /api/articles/{article_id}/deep-summary 端點以生成 Deep_Summary
7. THE 系統 SHALL 提供 GET /api/recommendations 端點以取得個人化 Recommendation
8. THE 所有 API 端點 SHALL 要求有效的認證 token
9. THE 所有 API 端點 SHALL 驗證請求參數並返回適當的 HTTP 狀態碼
10. THE 所有 API 端點 SHALL 返回 JSON 格式的回應

### Requirement 14: 效能與可擴展性

**User Story:** 作為用戶，我想要快速的回應時間，這樣我可以流暢地使用平台功能。

#### Acceptance Criteria

1. WHEN 用戶查詢 Reading_List，THE 系統 SHALL 在 500ms 內返回結果
2. WHEN 用戶執行評分或標記已讀操作，THE 系統 SHALL 在 300ms 內完成
3. THE 系統 SHALL 對 Deep_Summary 實作快取機制以避免重複生成
4. THE 系統 SHALL 使用資料庫索引優化查詢效能
5. THE 系統 SHALL 對 Reading_List 查詢實作分頁（每頁 20 筆）
6. THE 系統 SHALL 對文章列表查詢實作分頁（每頁 20 筆）
7. WHEN LLM_Service 生成 Deep_Summary，THE 系統 SHALL 設定合理的超時時間（30 秒）
8. THE 系統 SHALL 使用連線池管理資料庫連線

### Requirement 15: 正確性屬性 - 跨平台同步

**User Story:** 作為系統架構師，我需要驗證跨平台同步的正確性，這樣我可以確保資料一致性。

#### Acceptance Criteria (Property-Based)

1. **Round-Trip Property**: FOR ALL 用戶操作 op（加入閱讀清單、評分、標記已讀），IF 用戶在平台 A 執行 op，THEN 在平台 B 查詢 SHALL 返回 op 的結果
2. **Idempotence Property**: FOR ALL 操作 op，IF 用戶執行 op 兩次，THEN 系統狀態 SHALL 等同於執行 op 一次
3. **Commutativity Property**: FOR ALL 不同文章的操作 op1 和 op2，IF 用戶執行 op1 然後 op2，THEN 最終狀態 SHALL 等同於執行 op2 然後 op1
4. **User Isolation Property**: FOR ALL 用戶 A 和 B，IF 用戶 A 執行操作 op，THEN 用戶 B 的資料 SHALL 不受影響
5. **Monotonicity Property**: FOR ALL Reading_List 操作，IF 用戶加入文章 X，THEN Reading_List 大小 SHALL 增加或保持不變（如果已存在）
6. **Consistency Property**: FOR ALL 時間點 t，IF 用戶在平台 A 查詢資料，AND 在平台 B 查詢相同資料，THEN 兩個查詢 SHALL 返回相同結果（在沒有並發寫入的情況下）
7. **Eventual Consistency Property**: FOR ALL 並發操作，THE 系統 SHALL 在操作完成後達到一致狀態
8. **Data Integrity Property**: FOR ALL Rating 值，THE 系統 SHALL 確保 1 <= Rating <= 5

### Requirement 16: 正確性屬性 - 資料隔離

**User Story:** 作為系統架構師，我需要驗證用戶資料隔離的正確性，這樣我可以確保隱私安全。

#### Acceptance Criteria (Property-Based)

1. **Isolation Property**: FOR ALL 用戶 A 和 B (A ≠ B)，IF 用戶 A 查詢 Reading_List，THEN 結果 SHALL NOT 包含用戶 B 的任何記錄
2. **Authorization Property**: FOR ALL 用戶 A 和文章 X，IF 用戶 A 嘗試修改用戶 B 對文章 X 的 Rating，THEN 系統 SHALL 拒絕該操作
3. **Query Filtering Property**: FOR ALL 資料庫查詢 q，THE 系統 SHALL 自動加入 user_id 篩選條件
4. **No Leakage Property**: FOR ALL API 回應，THE 回應 SHALL NOT 包含其他用戶的 user_id 或個人資料
5. **Unique Constraint Property**: FOR ALL 用戶 U 和文章 A，THE 系統 SHALL 確保 (user_id, article_id) 組合在 Reading_List 中唯一
6. **Referential Integrity Property**: FOR ALL Reading_List 記錄，THE article_id SHALL 參照存在的 Article，AND user_id SHALL 參照存在的 User

### Requirement 17: 正確性屬性 - 深度摘要與推薦

**User Story:** 作為系統架構師，我需要驗證 AI 功能的正確性，這樣我可以確保服務品質。

#### Acceptance Criteria (Property-Based)

1. **Caching Property**: FOR ALL 文章 A，IF Deep_Summary 已生成，THEN 後續請求 SHALL 返回快取的摘要而不呼叫 LLM_Service
2. **Sharing Property**: FOR ALL 用戶 U1 和 U2，IF U1 生成文章 A 的 Deep_Summary，THEN U2 請求文章 A 的深度摘要 SHALL 返回相同內容
3. **Recommendation Dependency Property**: FOR ALL 用戶 U，IF U 沒有 Rating >= 4 的文章，THEN Recommendation 請求 SHALL 返回提示訊息而非推薦內容
4. **Recommendation Consistency Property**: FOR ALL 用戶 U，IF U 的高評分文章集合不變，THEN 在短時間內多次請求 Recommendation SHALL 返回一致的推薦理由
5. **Error Handling Property**: FOR ALL LLM_Service 呼叫，IF 呼叫失敗，THEN 系統 SHALL 返回錯誤訊息且不儲存不完整的 Deep_Summary
6. **Timeout Property**: FOR ALL LLM_Service 呼叫，IF 呼叫時間超過 30 秒，THEN 系統 SHALL 中止請求並返回超時錯誤

### Requirement 18: Parser 與序列化需求

**User Story:** 作為開發者，我需要可靠的資料解析和序列化，這樣前後端可以正確交換資料。

#### Acceptance Criteria

1. THE 系統 SHALL 提供 JSON Parser 以解析 API 請求 body
2. WHEN 收到無效的 JSON，THE Parser SHALL 返回 400 Bad Request 錯誤
3. THE 系統 SHALL 提供 JSON Serializer 以格式化 API 回應
4. THE Pretty_Printer SHALL 格式化 JSON 回應為可讀格式（開發模式）
5. FOR ALL 有效的資料物件 obj，parse(serialize(obj)) SHALL 產生等價的物件（round-trip property）
6. THE 系統 SHALL 驗證 API 請求的 schema（使用 Pydantic）
7. WHEN schema 驗證失敗，THE 系統 SHALL 返回 422 Unprocessable Entity 錯誤並說明驗證失敗的欄位
8. THE 系統 SHALL 支援 ISO 8601 格式的日期時間解析和序列化
