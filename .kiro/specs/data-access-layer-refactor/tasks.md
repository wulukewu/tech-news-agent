# Implementation Plan: Data Access Layer Refactor

## Overview

本實作計畫將完全移除 Notion 服務依賴，實作基於 Supabase 的資料存取層。實作順序遵循：基礎設施 → 核心功能 → 測試驗證，確保每個步驟都可以獨立驗證。

## Tasks

- [x] 1. 建立基礎設施與例外處理
  - [x] 1.1 實作 SupabaseServiceError 例外類別
    - 在 `app/core/exceptions.py` 中建立 SupabaseServiceError 類別
    - 實作 `__init__` 方法接受 message, original_error, context 參數
    - 實作 `__str__` 方法格式化錯誤訊息
    - _Requirements: 13.7, 13.8_

  - [x] 1.2 撰寫 SupabaseServiceError 的屬性測試
    - **Property 27: Exception Wrapping**
    - **Validates: Requirements 13.8**
    - 驗證所有資料庫例外都被正確包裝
    - 驗證原始例外被保留

  - [x] 1.3 更新配置檔案移除 Notion 設定
    - 在 `app/core/config.py` 中移除 notion_token, notion_feeds_db_id, notion_read_later_db_id, notion_weekly_digests_db_id
    - 確保保留 supabase_url 和 supabase_key 配置
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.4 更新 requirements.txt 移除 Notion 依賴
    - 移除 notion-client 套件
    - 確保 supabase>=2.0.0 存在
    - _Requirements: 1.3_

- [x] 2. 更新資料模型結構
  - [x] 2.1 更新 ArticleSchema 以匹配 Supabase 結構
    - 在 `app/schemas/article.py` 中更新 ArticleSchema
    - 新增 feed_id (UUID), published_at (Optional[datetime]), created_at (datetime)
    - 新增 ai_summary (Optional[str]), embedding (Optional[List[float]])
    - 將 tinkering_index 移至頂層，設定範圍 1-5
    - 重新命名 source_category → category, source_name → feed_name
    - 移除 content_preview 和 raw_data 欄位
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 2.2 撰寫 ArticleSchema 的屬性測試
    - **Property 1: Article Schema Structure Validation**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8**
    - 驗證所有必要欄位存在且型別正確
    - 驗證移除的欄位不存在

  - [x] 2.3 建立 BatchResult 資料類別
    - 在 `app/schemas/article.py` 中建立 BatchResult 類別
    - 實作 inserted_count, updated_count, failed_count, failed_articles 欄位
    - 實作 total_processed 和 success_rate 屬性
    - _Requirements: 5.7, 15.4_

  - [x] 2.4 建立 ReadingListItem 資料類別
    - 在 `app/schemas/article.py` 中建立 ReadingListItem 類別
    - 包含 article_id, title, url, category, status, rating, added_at, updated_at 欄位
    - _Requirements: 9.5, 9.7_

  - [x] 2.5 建立 Subscription 資料類別
    - 在 `app/schemas/article.py` 中建立 Subscription 類別
    - 包含 feed_id, name, url, category, subscribed_at 欄位
    - _Requirements: 12.3, 12.5_

- [x] 3. 實作 SupabaseService 核心架構
  - [x] 3.1 建立 SupabaseService 類別與初始化
    - 在 `app/services/supabase_service.py` 建立 SupabaseService 類別
    - 實作 `__init__` 方法，接受可選的 client 參數（用於測試）
    - 從 settings 讀取 supabase_url 和 supabase_key
    - 驗證配置存在，否則拋出 SupabaseServiceError
    - 初始化 logger
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 17.1_

  - [x] 3.2 實作連線驗證與錯誤處理
    - 在初始化時驗證 Supabase 連線
    - 實作連線失敗時的描述性錯誤訊息與故障排除提示
    - _Requirements: 14.4, 14.5, 14.7_

  - [x] 3.3 實作 context manager 支援
    - 實作 `__aenter__` 和 `__aexit__` 方法
    - 實作 `close` 方法清理資源
    - _Requirements: 17.2, 17.3_

  - [x] 3.4 撰寫 context manager 的屬性測試
    - **Property 36: Context Manager Resource Cleanup**
    - **Validates: Requirements 17.3**
    - 驗證資源在退出 context 時被清理
    - 驗證例外發生時資源仍被清理

- [x] 4. 實作資料驗證輔助方法
  - [x] 4.1 實作 \_validate_status 方法
    - 驗證 status 是 'Unread', 'Read', 或 'Archived' 之一（不區分大小寫）
    - 正規化為 Title Case
    - 無效時拋出 ValueError 並列出允許的值
    - _Requirements: 7.2, 7.3, 16.6_

  - [x] 4.2 撰寫 status 驗證的屬性測試
    - **Property 11: Status Validation**
    - **Validates: Requirements 7.2, 7.3**
    - 驗證無效狀態被拒絕
    - **Property 34: Status Normalization**
    - **Validates: Requirements 16.6**
    - 驗證狀態被正規化為 Title Case

  - [x] 4.3 實作 \_validate_rating 方法
    - 驗證 rating 是 1-5 之間的整數
    - 無效時拋出 ValueError 並說明允許範圍
    - _Requirements: 8.2, 8.3_

  - [x] 4.4 撰寫 rating 驗證的屬性測試
    - **Property 13: Rating Validation**
    - **Validates: Requirements 8.2, 8.3**
    - 驗證範圍外的評分被拒絕

  - [x] 4.5 實作 \_validate_uuid 方法
    - 驗證 UUID 格式
    - 無效時拋出 ValueError 並說明預期格式
    - _Requirements: 16.5_

  - [x] 4.6 撰寫 UUID 驗證的屬性測試
    - **Property 33: UUID Format Validation**
    - **Validates: Requirements 16.5**
    - 驗證無效 UUID 格式被拒絕

  - [x] 4.7 實作 \_validate_url 方法
    - 驗證 URL 是有效的 HTTP/HTTPS URL
    - 無效時拋出驗證錯誤
    - _Requirements: 16.1_

  - [x] 4.8 撰寫 URL 驗證的屬性測試
    - **Property 30: URL Validation**
    - **Validates: Requirements 16.1**
    - 驗證無效 URL 被拒絕

  - [x] 4.9 實作 \_truncate_text 方法
    - 截斷文字至指定長度
    - _Requirements: 16.3, 16.4_

  - [x] 4.10 撰寫文字截斷的屬性測試
    - **Property 32: Text Truncation**
    - **Validates: Requirements 16.3, 16.4**
    - 驗證超長標題和摘要被自動截斷

  - [x] 4.11 實作 \_handle_database_error 方法
    - 解析 PostgreSQL 錯誤訊息
    - 識別約束類型（UNIQUE, FOREIGN KEY, CHECK, NOT NULL）
    - 包裝為 SupabaseServiceError 並提供使用者友善訊息
    - _Requirements: 13.3, 13.4, 13.5, 13.6_

  - [x] 4.12 撰寫資料庫錯誤處理的屬性測試
    - **Property 26: Constraint Violation Error Messages**
    - **Validates: Requirements 13.3, 13.4, 13.5, 13.6**
    - 驗證各種約束違反都有描述性錯誤訊息

  - [x] 4.13 實作 \_execute_with_retry 方法
    - 實作指數退避重試邏輯（最多 3 次）
    - 識別暫時性錯誤（timeout, connection, temporary, unavailable）
    - 記錄每次重試嘗試
    - _Requirements: 15.6_

  - [x] 4.14 撰寫重試邏輯的屬性測試
    - **Property 29: Transient Error Retry**
    - **Validates: Requirements 15.6**
    - 驗證暫時性錯誤會被重試
    - 驗證非暫時性錯誤不會被重試

- [x] 5. Checkpoint - 驗證基礎設施
  - 確保所有驗證方法和錯誤處理都正常運作
  - 執行已實作的屬性測試
  - 如有問題請詢問使用者

- [x] 6. 實作使用者管理功能
  - [x] 6.1 實作 get_or_create_user 方法
    - 接受 discord_id 參數
    - 查詢 users 表是否存在該 discord_id
    - 若存在則返回 user UUID
    - 若不存在則建立新使用者並返回 UUID
    - 處理 unique constraint 違反（返回現有 UUID）
    - 記錄操作日誌
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.1, 13.2_

  - [x] 6.2 撰寫使用者建立的屬性測試
    - **Property 2: User Creation Idempotency**
    - **Validates: Requirements 3.2, 3.3, 3.4**
    - 驗證多次呼叫返回相同 UUID
    - 驗證不會建立重複記錄

- [x] 7. 實作訂閱源查詢功能
  - [x] 7.1 實作 get_active_feeds 方法
    - 查詢 feeds 表中 is_active=true 的記錄
    - 返回包含 id, name, url, category 的 RSSSource 列表
    - 按 category 和 name 排序
    - 空結果返回空列表
    - 記錄操作日誌
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 13.1, 13.2_

  - [x] 7.2 撰寫訂閱源查詢的屬性測試
    - **Property 3: Active Feeds Filtering**
    - **Validates: Requirements 4.2, 4.3**
    - 驗證只返回啟用的訂閱源
    - **Property 4: Active Feeds Ordering**
    - **Validates: Requirements 4.4**
    - 驗證結果按 category 和 name 排序

- [x] 8. 實作文章批次插入功能
  - [x] 8.1 實作 insert_articles 方法核心邏輯
    - 接受文章字典列表
    - 空列表返回零計數的 BatchResult
    - 分批處理（每批 100 筆）
    - 對每篇文章進行驗證（URL, tinkering_index, 文字長度）
    - 使用 UPSERT 操作（基於 URL）
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 15.1, 15.2, 16.1, 16.2, 16.3, 16.4_

  - [x] 8.2 實作批次操作的錯誤處理
    - 捕獲個別文章的失敗
    - 繼續處理剩餘文章
    - 記錄失敗的文章與原因
    - 返回詳細的 BatchResult 統計
    - 記錄 WARNING 級別日誌
    - _Requirements: 5.6, 5.7, 5.9, 15.3, 15.4, 13.1, 13.2_

  - [x] 8.3 撰寫文章插入的屬性測試
    - **Property 5: Article UPSERT Idempotency**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - 驗證相同 URL 的文章只有一筆記錄
    - **Property 6: Article Foreign Key Validation**
    - **Validates: Requirements 5.5**
    - 驗證無效 feed_id 會失敗
    - **Property 7: Batch Operation Statistics Accuracy**
    - **Validates: Requirements 5.7, 15.4**
    - 驗證 BatchResult 統計準確
    - **Property 28: Partial Batch Failure Handling**
    - **Validates: Requirements 15.3**
    - 驗證部分失敗時繼續處理

- [x] 9. 實作閱讀清單管理功能
  - [x] 9.1 實作 save_to_reading_list 方法
    - 接受 discord_id 和 article_id 參數
    - 呼叫 get_or_create_user 取得 user UUID
    - 驗證 article_id 格式
    - 使用 UPSERT 操作（基於 user_id + article_id）
    - 新記錄設定 status='Unread'
    - 現有記錄更新 updated_at
    - 處理 foreign key constraint 違反
    - 記錄操作日誌
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 13.1, 13.2_

  - [x] 9.2 撰寫閱讀清單儲存的屬性測試
    - **Property 8: Reading List UPSERT Idempotency**
    - **Validates: Requirements 6.3, 6.4**
    - 驗證不會建立重複記錄
    - **Property 9: Reading List Initial Status**
    - **Validates: Requirements 6.5**
    - 驗證新記錄的初始狀態為 'Unread'
    - **Property 10: Reading List Article Validation**
    - **Validates: Requirements 6.6**
    - 驗證無效 article_id 會失敗

  - [x] 9.3 實作 update_article_status 方法
    - 接受 discord_id, article_id, status 參數
    - 驗證 status 值
    - 呼叫 get_or_create_user 取得 user UUID
    - 更新 reading_list 表的 status 欄位
    - 自動更新 updated_at
    - 處理記錄不存在的情況
    - 記錄操作日誌
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 13.1, 13.2_

  - [x] 9.4 撰寫狀態更新的屬性測試
    - **Property 12: Status Update Persistence**
    - **Validates: Requirements 7.5, 7.6**
    - 驗證狀態更新被持久化
    - 驗證 updated_at 被更新

  - [x] 9.5 實作 update_article_rating 方法
    - 接受 discord_id, article_id, rating 參數
    - 驗證 rating 範圍（1-5）
    - 呼叫 get_or_create_user 取得 user UUID
    - 更新 reading_list 表的 rating 欄位
    - 自動更新 updated_at
    - 處理記錄不存在的情況
    - 記錄操作日誌
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 13.1, 13.2_

  - [x] 9.6 撰寫評分更新的屬性測試
    - **Property 14: Rating Update Persistence**
    - **Validates: Requirements 8.5, 8.6**
    - 驗證評分更新被持久化
    - 驗證 updated_at 被更新

- [x] 10. 實作閱讀清單查詢功能
  - [x] 10.1 實作 get_reading_list 方法
    - 接受 discord_id 和可選的 status 參數
    - 呼叫 get_or_create_user 取得 user UUID
    - JOIN articles 表取得文章詳細資訊
    - 根據 status 篩選（若提供）
    - 按 added_at 降序排序
    - 返回 ReadingListItem 列表
    - 空結果返回空列表
    - 記錄操作日誌
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 13.1, 13.2_

  - [x] 10.2 撰寫閱讀清單查詢的屬性測試
    - **Property 15: Reading List Status Filtering**
    - **Validates: Requirements 9.3**
    - 驗證狀態篩選正確
    - **Property 16: Reading List Complete Retrieval**
    - **Validates: Requirements 9.4**
    - 驗證無篩選時返回所有狀態
    - **Property 17: Reading List Data Completeness**
    - **Validates: Requirements 9.5, 9.7**
    - 驗證返回所有必要欄位
    - **Property 18: Reading List Ordering**
    - **Validates: Requirements 9.6**
    - 驗證按 added_at 降序排序

  - [x] 10.3 實作 get_highly_rated_articles 方法
    - 接受 discord_id 和可選的 threshold 參數（預設 4）
    - 呼叫 get_or_create_user 取得 user UUID
    - JOIN articles 表取得文章詳細資訊
    - 篩選 rating >= threshold 的文章
    - 按 rating 降序、added_at 降序排序
    - 返回 ReadingListItem 列表
    - 空結果返回空列表
    - 記錄操作日誌
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 13.1, 13.2_

  - [x] 10.4 撰寫高評分文章查詢的屬性測試
    - **Property 19: Highly Rated Articles Threshold**
    - **Validates: Requirements 10.4, 10.5**
    - 驗證門檻篩選正確
    - **Property 20: Highly Rated Articles Ordering**
    - **Validates: Requirements 10.6**
    - 驗證排序正確

- [x] 11. Checkpoint - 驗證核心功能
  - 確保所有 CRUD 操作正常運作
  - 執行已實作的屬性測試
  - 如有問題請詢問使用者

- [x] 12. 實作訂閱管理功能
  - [x] 12.1 實作 subscribe_to_feed 方法
    - 接受 discord_id 和 feed_id 參數
    - 呼叫 get_or_create_user 取得 user UUID
    - 插入 user_subscriptions 表
    - 處理重複訂閱（使用 UPSERT 或忽略錯誤）
    - 記錄操作日誌
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.9, 13.1, 13.2_

  - [x] 12.2 撰寫訂閱的屬性測試
    - **Property 21: Subscription Idempotency**
    - **Validates: Requirements 11.3, 11.4**
    - 驗證不會建立重複訂閱記錄

  - [x] 12.3 實作 unsubscribe_from_feed 方法
    - 接受 discord_id 和 feed_id 參數
    - 呼叫 get_or_create_user 取得 user UUID
    - 刪除 user_subscriptions 表的記錄
    - 訂閱不存在時不拋出錯誤
    - 記錄操作日誌
    - _Requirements: 11.5, 11.6, 11.7, 11.8, 11.9, 13.1, 13.2_

  - [x] 12.4 撰寫取消訂閱的屬性測試
    - **Property 22: Unsubscription Idempotency**
    - **Validates: Requirements 11.7, 11.8**
    - 驗證取消不存在的訂閱不會出錯

  - [x] 12.5 實作 get_user_subscriptions 方法
    - 接受 discord_id 參數
    - 呼叫 get_or_create_user 取得 user UUID
    - JOIN feeds 表取得訂閱源詳細資訊
    - 按 subscribed_at 降序排序
    - 返回 Subscription 列表
    - 空結果返回空列表
    - 記錄操作日誌
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 13.1, 13.2_

  - [x] 12.6 撰寫訂閱查詢的屬性測試
    - **Property 23: User Subscriptions Data Completeness**
    - **Validates: Requirements 12.3, 12.5**
    - 驗證返回所有必要欄位
    - **Property 24: User Subscriptions Ordering**
    - **Validates: Requirements 12.4**
    - 驗證按 subscribed_at 降序排序

- [x] 13. 實作日誌記錄策略
  - [x] 13.1 為所有方法新增 INFO 級別日誌
    - 記錄成功的資料庫操作
    - 包含相關參數和結果統計
    - _Requirements: 13.1_

  - [x] 13.2 為所有錯誤處理新增 ERROR 級別日誌
    - 記錄資料庫錯誤
    - 包含完整上下文和 stack trace
    - _Requirements: 13.2_

  - [x] 13.3 撰寫日誌記錄的屬性測試
    - **Property 25: Database Operation Logging**
    - **Validates: Requirements 13.1, 13.2**
    - 驗證操作被記錄
    - 驗證錯誤被記錄

- [x] 14. 移除舊有 Notion 服務
  - [x] 14.1 刪除 notion_service.py 檔案
    - 刪除 `app/services/notion_service.py`
    - _Requirements: 1.1_

  - [x] 14.2 移除所有 NotionService 的 import
    - 搜尋並移除所有模組中的 NotionService import
    - 更新相關程式碼使用 SupabaseService
    - _Requirements: 1.2_

  - [x] 14.3 驗證沒有 Notion 依賴殘留
    - 搜尋專案中是否還有 notion 相關的程式碼
    - 確保所有測試都通過
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 15. 整合與端到端測試
  - [x] 15.1 撰寫完整工作流程的整合測試
    - 測試從插入文章到閱讀清單管理的完整流程
    - 使用真實的 Supabase 連線（測試環境）
    - 驗證多使用者並發操作

  - [x] 15.2 撰寫驗證錯誤的屬性測試
    - **Property 35: Validation Error Details**
    - **Validates: Requirements 16.7**
    - 驗證所有驗證錯誤都有具體細節

  - [x] 15.3 執行所有屬性測試
    - 執行 `pytest tests/property/ -v`
    - 確保所有 36 個屬性都通過測試
    - 檢查測試覆蓋率 ≥ 90%

- [x] 16. Final Checkpoint - 完整驗證
  - 執行所有測試（單元測試 + 屬性測試 + 整合測試）
  - 驗證所有 17 個需求都被滿足
  - 驗證所有 36 個屬性都通過測試
  - 檢查程式碼品質和文件完整性
  - 如有問題請詢問使用者

## Notes

- 任務標記 `*` 為可選的測試任務，可跳過以加快 MVP 開發
- 每個任務都參照具體的需求編號以確保可追溯性
- Checkpoint 任務確保增量驗證，及早發現問題
- 屬性測試驗證通用正確性屬性，單元測試驗證特定例子
- 所有資料庫操作都使用 async/await 模式
- 錯誤處理遵循「快速失敗」原則，提供清晰的錯誤訊息
