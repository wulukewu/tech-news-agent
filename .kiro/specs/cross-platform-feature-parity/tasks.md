f# Implementation Plan: Cross-Platform Feature Parity

## Overview

本實作計畫將 Discord Bot 的完整功能（閱讀清單、評分、標記已讀、深度摘要、推薦系統）補齊到網頁端，確保兩個平台功能一致且資料即時同步。實作分為 6 個階段，按照資料庫 → Backend API → Frontend → Discord Bot 整合 → 測試 → 部署的順序進行。

## Tasks

- [x] 1. Phase 1: 資料庫 Schema 擴充
  - [x] 1.1 建立 reading_list 資料表
    - 建立包含 id, user_id, article_id, status, rating, added_at, updated_at 欄位的資料表
    - 設定 (user_id, article_id) 唯一性約束
    - 設定外鍵約束（user_id → users.id, article_id → articles.id）
    - 設定 status CHECK 約束（只允許 'Unread', 'Read', 'Archived'）
    - 設定 rating CHECK 約束（1-5 或 NULL）
    - _Requirements: 6.8, 7.7, 8.6_

  - [x] 1.2 建立資料庫索引
    - 建立 idx_reading_list_user_id 索引（user_id）
    - 建立 idx_reading_list_status 索引（user_id, status）
    - 建立 idx_reading_list_rating 索引（user_id, rating WHERE rating IS NOT NULL）
    - 建立 idx_reading_list_added_at 索引（user_id, added_at DESC）
    - _Requirements: 14.4_

  - [x] 1.3 建立 updated_at 自動更新觸發器
    - 建立 update_reading_list_updated_at() 函式
    - 建立 BEFORE UPDATE 觸發器自動更新 updated_at 欄位
    - _Requirements: 1.7_

  - [x] 1.4 擴充 articles 表支援深度摘要
    - 新增 deep_summary TEXT 欄位
    - 新增 deep_summary_generated_at TIMESTAMPTZ 欄位
    - 建立 idx_articles_deep_summary 索引（id WHERE deep_summary IS NOT NULL）
    - _Requirements: 4.7, 9.7_

  - [x] 1.5 設定 Row Level Security (RLS) 政策
    - 啟用 reading_list 表的 RLS
    - 建立 SELECT 政策（user_id = auth.uid()）
    - 建立 INSERT 政策（user_id = auth.uid()）
    - 建立 UPDATE 政策（user_id = auth.uid()）
    - 建立 DELETE 政策（user_id = auth.uid()）
    - _Requirements: 10.8_

- [x] 2. Phase 2: Backend API 開發
  - [x] 2.1 實作 Reading List API 端點
    - 實作 POST /api/reading-list（加入文章到閱讀清單）
    - 實作 GET /api/reading-list（查詢閱讀清單，支援 status 篩選和分頁）
    - 實作 DELETE /api/reading-list/{article_id}（移除文章）
    - 使用 UPSERT 確保冪等性
    - _Requirements: 1.1, 1.3, 1.6, 6.1, 6.7, 13.1, 13.2, 13.3_

  - [x] 2.2 撰寫 Reading List API 的 property-based 測試
    - **Property 1: 閱讀清單加入操作**
    - **Validates: Requirements 1.1, 1.3, 6.1**
    - **Property 2: 閱讀清單移除操作**
    - **Validates: Requirements 1.6, 6.6**
    - **Property 21: 閱讀清單冪等性**
    - **Validates: Requirements 6.7, 6.8**

  - [x] 2.3 實作 Rating API 端點
    - 實作 POST /api/articles/{article_id}/rating（設定或更新評分）
    - 實作 GET /api/articles/{article_id}/rating（查詢評分）
    - 驗證評分範圍（1-5）
    - 使用 UPSERT 更新現有評分
    - _Requirements: 2.2, 2.4, 2.5, 2.7, 7.1, 7.8, 13.4_

  - [x] 2.4 撰寫 Rating API 的 property-based 測試
    - **Property 5: 評分設定與查詢**
    - **Validates: Requirements 2.2, 2.5, 7.1**
    - **Property 6: 評分更新**
    - **Validates: Requirements 2.4, 7.8**
    - **Property 7: 評分範圍驗證**
    - **Validates: Requirements 2.7, 2.8**
    - **Property 22: 評分唯一性**
    - **Validates: Requirements 7.6, 7.7**

  - [x] 2.5 實作 Read Status API 端點
    - 實作 POST /api/articles/{article_id}/status（更新閱讀狀態）
    - 驗證狀態值（'Unread', 'Read', 'Archived'）
    - _Requirements: 3.2, 8.1, 8.6, 8.7, 13.5_

  - [x] 2.6 撰寫 Read Status API 的 property-based 測試
    - **Property 9: 狀態更新**
    - **Validates: Requirements 3.2, 8.1**
    - **Property 11: 狀態 Round-Trip**
    - **Validates: Requirements 3.7**
    - **Property 12: 狀態值驗證**
    - **Validates: Requirements 8.6, 8.7**

  - [x] 2.7 實作 Deep Summary API 端點
    - 實作 POST /api/articles/{article_id}/deep-summary（生成深度摘要）
    - 實作 GET /api/articles/{article_id}/deep-summary（查詢已生成的摘要）
    - 檢查快取，避免重複呼叫 LLM
    - 設定 30 秒超時
    - 實作錯誤處理和重試機制
    - _Requirements: 4.2, 4.6, 4.7, 4.8, 9.5, 9.6, 13.6_

  - [x] 2.8 撰寫 Deep Summary API 的 property-based 測試
    - **Property 13: 深度摘要快取**
    - **Validates: Requirements 4.6, 9.5, 9.6**
    - **Property 14: 深度摘要持久化**
    - **Validates: Requirements 4.7, 9.8**
    - **Property 15: 深度摘要錯誤處理**
    - **Validates: Requirements 4.8**

  - [x] 2.9 實作 Recommendations API 端點
    - 實作 GET /api/recommendations（取得個人化推薦）
    - 查詢 rating >= 4 的文章
    - 支援 time_range 參數（week, month）
    - 呼叫 LLM Service 生成推薦
    - 處理無高評分文章的情況
    - _Requirements: 5.2, 5.3, 5.4, 5.7, 5.8, 13.7_

  - [x] 2.10 撰寫 Recommendations API 的 property-based 測試
    - **Property 16: 高評分文章查詢**
    - **Validates: Requirements 5.2**
    - **Property 17: 推薦系統時間範圍篩選**
    - **Validates: Requirements 5.7, 5.8**

  - [x] 2.11 擴充現有 Articles API
    - 更新 GET /api/articles 端點，加入 deep_summary 欄位
    - 確保回應包含 rating 和 status（如果用戶已評分/標記）
    - _Requirements: 1.7_

  - [x] 2.12 實作 API 認證中介層
    - 實作 get_current_user 依賴注入函式
    - 驗證 JWT token
    - 從 token 提取 user_id 和 discord_id
    - 處理 401 錯誤
    - _Requirements: 13.8_

  - [x] 2.13 實作 API 錯誤處理
    - 實作統一的錯誤回應格式
    - 處理驗證錯誤（400）
    - 處理認證錯誤（401）
    - 處理授權錯誤（403）
    - 處理資源不存在錯誤（404）
    - 處理外部服務錯誤（502, 503）
    - 處理內部錯誤（500）
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 2.14 實作 Rate Limiting 中介層
    - 使用 slowapi 實作速率限制
    - 一般端點：100 次/分鐘
    - 深度摘要端點：10 次/小時
    - _Requirements: 14.7_

- [x] 3. Checkpoint - Backend API 測試
  - 確保所有 API 端點通過單元測試和 property-based 測試，詢問用戶是否有問題。

- [x] 4. Phase 3: Frontend 開發
  - [x] 4.1 建立閱讀清單頁面
    - 建立 app/reading-list/page.tsx
    - 實作文章列表顯示（標題、來源、分類、加入時間）
    - 實作狀態篩選器（全部/未讀/已讀/已封存）
    - 實作分頁或無限滾動
    - 實作空狀態顯示
    - _Requirements: 1.3, 1.4, 1.7, 1.8, 3.4_

  - [x] 4.2 建立推薦頁面
    - 建立 app/recommendations/page.tsx
    - 實作時間範圍選擇器（本週/本月）
    - 顯示推薦內容和推薦理由
    - 處理無高評分文章的情況
    - _Requirements: 5.1, 5.6, 5.7_

  - [x] 4.3 實作 StarRating 組件
    - 建立 components/StarRating.tsx
    - 支援 1-5 星顯示
    - 支援互動式評分（onChange）
    - 支援唯讀模式
    - 實作 hover 效果
    - _Requirements: 2.1, 2.3_

  - [x] 4.4 撰寫 StarRating 組件測試
    - 測試星級顯示正確性
    - 測試點擊事件觸發
    - 測試唯讀模式

  - [x] 4.5 實作 ReadStatusBadge 組件
    - 建立 components/ReadStatusBadge.tsx
    - 顯示 Unread/Read/Archived 狀態
    - 使用不同顏色區分狀態
    - _Requirements: 3.3, 3.8_

  - [x] 4.6 實作 DeepSummaryModal 組件
    - 建立 components/DeepSummaryModal.tsx
    - 顯示深度摘要內容
    - 實作載入指示器
    - 實作錯誤顯示和重試按鈕
    - 使用 dynamic import 優化效能
    - _Requirements: 4.3, 4.4, 4.8_

  - [x] 4.7 實作 ReadingListItem 組件
    - 建立 components/ReadingListItem.tsx
    - 顯示文章資訊（標題、來源、分類、時間）
    - 整合 StarRating 組件
    - 整合 ReadStatusBadge 組件
    - 實作「標記已讀/未讀」按鈕
    - 實作「從清單移除」按鈕
    - 實作「生成深度摘要」按鈕
    - _Requirements: 1.5, 1.6, 3.1, 4.1_

  - [x] 4.8 擴充 ArticleCard 組件
    - 在現有 ArticleCard 加入「加入閱讀清單」按鈕
    - 顯示成功提示訊息
    - 處理已加入的狀態（顯示「已在清單中」）
    - _Requirements: 1.1, 1.2_

  - [x] 4.9 實作 Reading List API Client 函式
    - 建立 lib/api/readingList.ts
    - 實作 addToReadingList(articleId)
    - 實作 getReadingList(status?, page?, pageSize?)
    - 實作 removeFromReadingList(articleId)
    - _Requirements: 13.1, 13.2, 13.3_

  - [x] 4.10 實作 Rating API Client 函式
    - 建立 lib/api/ratings.ts
    - 實作 rateArticle(articleId, rating)
    - 實作 getArticleRating(articleId)
    - _Requirements: 13.4_

  - [x] 4.11 實作 Status API Client 函式
    - 建立 lib/api/status.ts
    - 實作 updateArticleStatus(articleId, status)
    - _Requirements: 13.5_

  - [x] 4.12 實作 Deep Summary API Client 函式
    - 建立 lib/api/deepSummary.ts
    - 實作 generateDeepSummary(articleId)
    - 實作 getDeepSummary(articleId)
    - _Requirements: 13.6_

  - [x] 4.13 實作 Recommendations API Client 函式
    - 建立 lib/api/recommendations.ts
    - 實作 getRecommendations(timeRange?)
    - _Requirements: 13.7_

  - [x] 4.14 實作統一的 API Client 錯誤處理
    - 建立 lib/api/client.ts
    - 實作 apiCall 包裝函式
    - 處理各種 HTTP 狀態碼（400, 401, 404, 500）
    - 顯示使用者友善的錯誤訊息（使用 toast）
    - 401 時重定向到登入頁面
    - _Requirements: 12.1, 12.2, 12.3, 12.5_

  - [x] 4.15 實作前端資料快取策略
    - 使用 SWR 或 React Query 實作資料快取
    - 設定 revalidation 策略
    - 實作樂觀更新（評分、狀態變更）
    - _Requirements: 14.3_

  - [x] 4.16 實作前端效能優化
    - 使用 Next.js Image 組件優化圖片載入
    - 實作 Code Splitting（dynamic import）
    - 實作搜尋輸入防抖（debounce）
    - _Requirements: 14.1, 14.2_

  - [x] 4.17 撰寫前端組件單元測試
    - 測試 StarRating 組件
    - 測試 ReadStatusBadge 組件
    - 測試 ReadingListItem 組件

  - [x] 4.18 撰寫 API Client 單元測試
    - 使用 MSW 模擬 API 回應
    - 測試 addToReadingList
    - 測試 getReadingList
    - 測試錯誤處理

- [x] 5. Checkpoint - Frontend 功能測試
  - 確保所有前端組件和 API Client 正常運作，詢問用戶是否有問題。

- [x] 6. Phase 4: Discord Bot 整合
  - [x] 6.1 確認 Discord Bot 現有功能
    - 檢查 /reading_list 指令實作
    - 檢查 /rate 指令實作
    - 檢查 /mark_read 指令實作
    - 檢查 /deep_summary 指令實作
    - 檢查 /recommendations 指令實作
    - _Requirements: 6.2, 7.2, 8.2, 9.2_

  - [x] 6.2 更新 Discord Bot 資料庫整合
    - 確認 Discord Bot 使用 SupabaseService
    - 確認所有操作寫入 reading_list 表（而非舊的資料結構）
    - 確認 RLS 政策正確應用
    - _Requirements: 6.3, 6.5_

  - [x] 6.3 測試跨平台同步
    - 在 Web 加入文章，在 Discord 查詢驗證
    - 在 Discord 評分，在 Web 查詢驗證
    - 在 Web 標記已讀，在 Discord 查詢驗證
    - 在 Discord 生成摘要，在 Web 查詢驗證
    - _Requirements: 6.2, 6.4, 7.2, 7.4, 8.2, 8.4, 9.2, 9.4_

  - [x] 6.4 撰寫跨平台同步整合測試
    - **Property 18: 跨平台閱讀清單同步**
    - **Validates: Requirements 6.2, 6.4**
    - **Property 19: 跨平台評分同步**
    - **Validates: Requirements 7.2, 7.4**
    - **Property 20: 跨平台狀態同步**
    - **Validates: Requirements 8.2, 8.4, 8.8**

- [x] 7. Phase 5: 測試與品質保證
  - [x] 7.1 執行完整的 Backend Property-Based 測試套件
    - 執行所有 property-based 測試（最少 100 次迭代）
    - 驗證所有 25 個 correctness properties
    - 修復發現的問題

  - [x] 7.2 執行 Backend 單元測試
    - 測試邊界值（rating 1 和 5）
    - 測試空閱讀清單
    - 測試狀態轉換
    - 測試錯誤處理

  - [x] 7.3 執行 Backend 整合測試
    - 測試跨平台同步
    - 測試並發更新
    - 測試資料隔離

  - [x] 7.4 執行 Frontend E2E 測試
    - 測試加入閱讀清單流程
    - 測試評分流程
    - 測試標記已讀流程
    - 測試深度摘要生成流程
    - 測試推薦查詢流程
    - 測試篩選功能

  - [x] 7.5 執行效能測試
    - 驗證閱讀清單查詢 < 500ms
    - 驗證評分操作 < 300ms
    - 驗證深度摘要生成 < 30s
    - 使用 Lighthouse 測試前端效能

  - [x] 7.6 執行安全性測試
    - 測試 RLS 政策（用戶無法存取其他用戶資料）
    - 測試 JWT token 驗證
    - 測試輸入驗證（SQL injection, XSS）
    - 測試 Rate Limiting

  - [x] 7.7 程式碼審查與重構
    - 審查所有新增的程式碼
    - 確保符合專案編碼規範
    - 重構重複的程式碼
    - 新增必要的註解和文件

- [x] 8. Phase 6: 部署與監控
  - [x] 8.1 準備資料庫遷移腳本
    - 建立 Supabase migration 檔案
    - 包含所有 Schema 變更（表、索引、觸發器、RLS）
    - 測試 migration 在開發環境
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 8.2 部署 Backend API
    - 更新環境變數（SUPABASE_URL, SUPABASE_KEY, JWT_SECRET_KEY）
    - 部署到生產環境
    - 執行資料庫 migration
    - 驗證 API 端點可存取

  - [x] 8.3 部署 Frontend
    - 更新環境變數（NEXT_PUBLIC_API_URL）
    - 建置生產版本
    - 部署到 Vercel 或其他平台
    - 驗證頁面可存取

  - [x] 8.4 更新 Discord Bot
    - 確認 Discord Bot 使用新的資料庫結構
    - 重新部署 Discord Bot
    - 驗證指令正常運作

  - [x] 8.5 設定監控與日誌
    - 設定 API 效能監控（Prometheus + Grafana）
    - 設定錯誤追蹤（Sentry）
    - 設定日誌聚合（CloudWatch 或 Datadog）
    - 設定告警規則（回應時間、錯誤率）
    - _Requirements: 12.4_

  - [x] 8.6 撰寫使用者文件
    - 更新 README.md
    - 撰寫 API 文件（OpenAPI/Swagger）
    - 撰寫部署指南
    - 撰寫故障排除指南

  - [x] 8.7 執行生產環境驗證
    - 在生產環境測試所有主要流程
    - 驗證跨平台同步正常運作
    - 驗證效能符合要求
    - 驗證安全性設定正確

- [x] 9. Final Checkpoint - 生產環境驗證
  - 確保所有功能在生產環境正常運作，詢問用戶是否有問題或需要調整。

## Notes

- 標記 `*` 的任務為可選測試任務，可根據專案時程決定是否執行
- 每個 Checkpoint 任務應暫停並等待用戶確認後再繼續
- Property-based 測試使用 Hypothesis (Backend) 和 fast-check (Frontend)
- 所有 API 端點都需要 JWT 認證
- RLS 政策自動確保用戶資料隔離
- 使用 UPSERT 確保操作冪等性
- 深度摘要使用快取避免重複呼叫 LLM
- 前端使用 SWR 或 React Query 實作資料快取
- 效能目標：閱讀清單查詢 < 500ms，評分操作 < 300ms
