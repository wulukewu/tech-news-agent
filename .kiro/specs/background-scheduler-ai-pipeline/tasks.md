# 實作計畫：背景排程器與 AI 管線解耦

## 概述

本實作計畫將 Tech News Agent 從「使用者觸發式抓取」轉變為「背景共用池定時抓取」架構。此重構將大幅降低 LLM API 消耗，提升系統效能，並為未來的多租戶推薦系統奠定基礎。

核心改變：

- 背景排程器定時抓取 RSS 來源並寫入共用資料池
- LLM 服務只處理尚未分析的文章，避免重複消耗 API
- 使用者指令從資料庫讀取已處理的文章，實現即時回應
- 排程器與 Discord 通知完全解耦

## 任務清單

- [x] 1. 增強 Supabase Service 資料存取方法
  - [x] 1.1 實作 check_article_exists 方法
    - 新增 `async def check_article_exists(self, url: str) -> bool` 方法
    - 查詢 articles 表檢查 URL 是否存在
    - 使用 `SELECT id FROM articles WHERE url = ?` 進行高效查詢
    - 返回 True（存在）或 False（不存在）
    - _需求：2.2, 2.3_

  - [x] 1.2 實作 get_unanalyzed_articles 方法
    - 新增 `async def get_unanalyzed_articles(self, limit: int = 100) -> List[dict]` 方法
    - 查詢 ai_summary IS NULL 或 tinkering_index IS NULL 的文章
    - 返回包含 id, url, title, feed_id 的字典列表
    - 支援 limit 參數限制返回數量
    - _需求：13.1, 13.2, 13.7_

  - [x] 1.3 增強 insert_articles 方法的錯誤處理
    - 修改 `insert_articles()` 方法以支援部分失敗
    - 實作批次處理（每批 100 筆）
    - 使用 UPSERT 邏輯：INSERT ... ON CONFLICT (url) DO UPDATE
    - 分別追蹤 inserted_count, updated_count, failed_count
    - 在 BatchResult 中記錄失敗文章的詳細資訊
    - 個別文章失敗時繼續處理其他文章
    - _需求：4.2, 4.3, 4.4, 4.6, 4.8, 15.2, 15.3_

  - [x] 1.4 撰寫 Supabase Service 增強功能的屬性測試
    - **屬性 6：文章插入冪等性**
    - **驗證需求：4.2, 4.3, 4.4**
    - 使用 Hypothesis 生成隨機文章資料
    - 測試多次插入相同 URL 不會產生重複記錄
    - 驗證 UPSERT 行為：新 URL 插入，已存在 URL 更新
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 6: Article Insertion Idempotence`

  - [x] 1.5 撰寫 Supabase Service 增強功能的單元測試
    - 測試 check_article_exists 對已存在和不存在的 URL
    - 測試 get_unanalyzed_articles 返回 NULL summary 的文章
    - 測試 insert_articles 的 UPSERT 行為
    - 測試 insert_articles 的外鍵驗證
    - 測試 BatchResult 的準確性
    - _需求：4.5, 4.6_

- [x] 2. 重構 RSS Service 實作去重邏輯
  - [x] 2.1 實作 fetch_new_articles 方法
    - 新增 `async def fetch_new_articles(self, sources: List[RSSSource], supabase_service: SupabaseService) -> List[ArticleSchema]` 方法
    - 呼叫現有的 `fetch_all_feeds()` 取得所有文章
    - 對每篇文章呼叫 `supabase_service.check_article_exists(url)` 檢查是否存在
    - 過濾掉已存在的文章
    - 只返回新文章
    - 記錄統計：總抓取數、已存在數、新文章數
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 2.2 增強時效性過濾邏輯
    - 修改 RSS Service 只抓取最近 7 天的文章
    - 在去重檢查前先過濾舊文章
    - 支援透過環境變數 RSS_FETCH_DAYS 配置時間窗口
    - 預設值為 7 天
    - 記錄被時間窗口過濾的文章數量
    - _需求：11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x] 2.3 撰寫 RSS Service 的屬性測試
    - **屬性 2：文章去重正確性**
    - **驗證需求：2.3, 2.4, 2.5**
    - 使用 Hypothesis 生成隨機文章列表和已存在 URL 集合
    - 驗證輸出只包含 URL 不在資料庫中的文章
    - 驗證輸出包含所有新文章（不多不少）
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness`

  - [x] 2.4 撰寫 RSS Service 的屬性測試
    - **屬性 12：文章時間過濾**
    - **驗證需求：11.1, 11.4**
    - 使用 Hypothesis 生成隨機時間戳的文章
    - 驗證所有超過時間窗口的文章都被過濾
    - 驗證所有在時間窗口內的文章都被保留
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 12: Article Time Filtering`

  - [x] 2.5 撰寫 RSS Service 的單元測試
    - 測試 fetch_new_articles 過濾已存在文章
    - 測試時效性過濾（舊文章被排除）
    - 測試 published_at 缺失時使用當前時間
    - 測試個別 feed 失敗不影響其他 feed
    - 測試可配置的時間窗口
    - 測試預設 7 天時間窗口
    - _需求：2.7, 11.2, 11.3_

- [x] 3. 改進 LLM Service 錯誤處理
  - [x] 3.1 增強 evaluate_batch 方法的錯誤處理
    - 修改 `evaluate_batch()` 方法以支援部分失敗
    - 為每篇文章的處理包裝 try-except
    - API 失敗時設定 `tinkering_index=NULL`, `ai_summary=NULL`
    - 記錄失敗文章的 URL 和錯誤訊息
    - 繼續處理剩餘文章
    - 返回所有文章（成功和失敗的）
    - 當超過 30% 文章失敗時記錄警告
    - _需求：3.7, 3.9, 8.1, 8.2, 8.3, 8.7, 8.8_

  - [x] 3.2 實作 API 重試邏輯
    - 為暫時性 API 錯誤實作指數退避重試
    - 最多重試 2 次
    - 重試延遲：2 秒、4 秒
    - 尊重 Groq API 的 Retry-After header
    - 使用 semaphore 限制並發請求（最多 5 個）
    - 記錄每次重試嘗試
    - 超時設定為 30 秒
    - _需求：8.4, 8.5, 8.6_

  - [x] 3.3 分離評估和摘要生成方法
    - 將 tinkering_index 評估和 ai_summary 生成分為獨立方法
    - 支援只重新處理 tinkering_index（當 ai_summary 已存在時）
    - 支援只重新處理 ai_summary（當 tinkering_index 已存在時）
    - 更新 evaluate_batch 以呼叫這兩個獨立方法
    - _需求：13.7_

  - [x] 3.4 撰寫 LLM Service 的屬性測試
    - **屬性 4：LLM 批次處理完整性**
    - **驗證需求：3.2, 3.3, 3.9**
    - 使用 Hypothesis 生成隨機文章列表
    - 驗證輸出包含相同的文章
    - 驗證成功的文章有 tinkering_index 和 ai_summary 值
    - 驗證失敗的文章這些欄位為 NULL
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness`

  - [x] 3.5 撰寫 LLM Service 的屬性測試
    - **屬性 5：LLM 錯誤處理**
    - **驗證需求：3.7, 8.2**
    - 使用 Hypothesis 生成隨機文章列表
    - 模擬隨機 API 失敗
    - 驗證失敗文章的欄位設為 NULL
    - 驗證處理繼續進行其他文章
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 5: LLM Error Handling`

  - [x] 3.6 撰寫 LLM Service 的單元測試
    - 測試 API 失敗時設定 NULL 值
    - 測試個別文章失敗不影響其他文章
    - 測試 semaphore 限制並發數
    - 測試重試邏輯
    - 測試超時處理
    - _需求：3.7, 8.3_

- [x] 4. 完全重寫 Scheduler 模組
  - [x] 4.1 移除 Discord 依賴
    - 從 app/tasks/scheduler.py 移除所有 Discord bot 匯入
    - 移除 `from app.bot.client import bot`
    - 移除 `from app.bot.cogs.interactions import ReadLaterView, MarkReadView`
    - 移除所有 Discord 通知相關程式碼
    - 移除 `build_article_list_notification()` 函數
    - 移除 `channel.send()` 呼叫
    - _需求：5.1, 5.2, 5.3, 5.4_

  - [x] 4.2 實作新的背景任務管線
    - 重寫 `weekly_news_job()` 為 `background_fetch_job()`
    - 實作管線流程：載入 feeds → 抓取文章 → 去重 → LLM 分析 → 資料庫插入
    - 在任務開始時呼叫 `supabase_service.get_active_feeds()`
    - 呼叫 `rss_service.fetch_new_articles()` 進行去重抓取
    - 呼叫 `llm_service.evaluate_batch()` 進行批次分析
    - 呼叫 `supabase_service.insert_articles()` 插入資料庫
    - 記錄每個階段的統計資訊
    - _需求：1.1, 1.3, 2.1, 3.1, 4.1, 5.4, 5.5_

  - [x] 4.3 實作可配置的排程時間
    - 從環境變數讀取 SCHEDULER_CRON（預設：`0 */6 * * *`）
    - 從環境變數讀取 SCHEDULER_TIMEZONE（預設：從 settings）
    - 在 `setup_scheduler()` 中使用 CronTrigger 配置排程
    - 驗證 CRON 表達式的有效性
    - 無效的 CRON 表達式在啟動時拋出配置錯誤
    - 啟動時記錄配置的排程
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 4.4 實作全面的錯誤處理
    - 用 try-except 包裝整個任務以防止排程器崩潰
    - 記錄所有例外的完整堆疊追蹤
    - 資料庫操作失敗時實作重試邏輯（最多 3 次，指數退避）
    - 連線失敗時在記憶體中快取文章
    - 所有重試失敗時記錄嚴重錯誤並跳過當前執行
    - 在下次排程執行時繼續正常運作
    - _需求：9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 4.5 實作健康檢查端點
    - 新增 `async def get_scheduler_health() -> dict` 函數
    - 返回最後執行時間戳
    - 返回最後執行處理的文章數量
    - 返回最後執行的失敗操作數量
    - 排程器健康時返回 HTTP 200
    - 超過 12 小時未執行時返回 HTTP 503
    - 最後執行失敗率超過 50% 時返回 HTTP 503
    - _需求：10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 4.6 實作批次處理邏輯
    - 將文章分批處理（每批最多 50 篇）
    - 超過 100 篇文章時分成多個批次
    - 記錄每個批次的處理時間
    - 記錄整個任務的總處理時間
    - 批次之間清理記憶體
    - _需求：12.1, 12.4, 12.5, 12.6, 12.7_

  - [x] 4.7 實作全面的日誌記錄
    - 在 INFO 層級記錄任務開始時間
    - 在 INFO 層級記錄任務結束時間和總持續時間
    - 在 INFO 層級記錄處理的 feeds 數量
    - 在 INFO 層級記錄找到的新文章數量
    - 在 INFO 層級記錄 LLM 分析的文章數量
    - 在 INFO 層級記錄插入資料庫的文章數量
    - 在 ERROR 層級記錄所有錯誤及完整堆疊追蹤
    - 失敗率超過閾值時在 WARNING 層級記錄警告
    - _需求：14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

  - [x] 4.8 撰寫 Scheduler 的屬性測試
    - **屬性 3：批次處理韌性**
    - **驗證需求：2.7, 7.2, 8.3, 4.8**
    - 使用 Hypothesis 生成隨機批次項目
    - 注入隨機失敗
    - 驗證個別項目失敗不阻止其他項目處理
    - 驗證所有項目都被嘗試處理
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 3: Batch Processing Resilience`

  - [x] 4.9 撰寫 Scheduler 的屬性測試
    - **屬性 8：批次結果準確性**
    - **驗證需求：4.6, 7.6**
    - 使用 Hypothesis 生成隨機批次操作
    - 驗證 success_count + failure_count = total_count
    - 驗證 inserted_count + updated_count + failed_count = total_articles
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 8: Batch Result Accuracy`

  - [x] 4.10 撰寫 Scheduler 的屬性測試
    - **屬性 9：CRON 表達式驗證**
    - **驗證需求：6.2, 6.5**
    - 使用 Hypothesis 生成有效和無效的 CRON 表達式
    - 驗證無效表達式在啟動時拋出配置錯誤
    - 驗證有效表達式被接受
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation`

  - [x] 4.11 撰寫 Scheduler 的屬性測試
    - **屬性 11：排程器穩健性**
    - **驗證需求：9.5**
    - 使用 Hypothesis 生成隨機資料庫錯誤
    - 驗證排程器不會崩潰
    - 驗證錯誤被記錄
    - 驗證繼續到下次排程執行
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 11: Scheduler Robustness`

  - [x] 4.12 撰寫 Scheduler 的屬性測試
    - **屬性 14：批次大小限制**
    - **驗證需求：12.1, 12.5**
    - 使用 Hypothesis 生成不同大小的文章列表
    - 驗證超過 50 篇的列表被分批
    - 驗證每批最多 50 篇文章
    - 驗證超過 100 篇時建立多個批次
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 14: Batch Size Limiting`

  - [x] 4.13 撰寫 Scheduler 的單元測試
    - 測試有效 CRON 表達式的排程器初始化
    - 測試無效 CRON 表達式的排程器初始化
    - 測試空 feed 列表的處理
    - 測試資料庫連線失敗的處理
    - 測試排程器不匯入 Discord client
    - 測試排程器不呼叫 Discord API
    - 測試預設排程為 6 小時
    - 測試健康檢查在健康時返回 200
    - 測試健康檢查在過時時返回 503
    - 測試健康檢查在高失敗率時返回 503
    - _需求：6.3, 9.5, 10.5, 10.6, 10.7_

- [x] 5. 實作重新處理邏輯
  - [x] 5.1 實作未分析文章的重新處理
    - 在背景任務中查詢 `get_unanalyzed_articles()`
    - 對 ai_summary IS NULL 的文章重新執行 LLM 分析
    - 對 tinkering_index IS NULL 但 ai_summary IS NOT NULL 的文章只重新處理 tinkering_index
    - 重新處理時更新 updated_at 時間戳
    - 記錄重新處理的文章數量
    - _需求：13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [x] 5.2 撰寫重新處理邏輯的屬性測試
    - **屬性 15：重新處理邏輯**
    - **驗證需求：13.1, 13.2, 13.3, 13.4, 13.6, 13.7**
    - 使用 Hypothesis 生成隨機文章狀態
    - 驗證 ai_summary IS NULL 時重新處理
    - 驗證 ai_summary IS NOT NULL 時跳過 LLM 處理
    - 驗證 tinkering_index IS NULL 但 ai_summary IS NOT NULL 時只重新處理 tinkering_index
    - 驗證重新處理時更新 updated_at
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 15: Re-processing Logic`

  - [x] 5.3 撰寫重新處理邏輯的單元測試
    - 測試 ai_summary IS NULL 時重新處理
    - 測試 ai_summary IS NOT NULL 時跳過處理
    - 測試部分欄位 NULL 時的選擇性重新處理
    - 測試 updated_at 時間戳更新
    - _需求：13.4, 13.6_

- [x] 6. 實作動態訂閱源配置
  - [x] 6.1 實作每次執行時重新載入 feeds
    - 在每次任務執行開始時呼叫 `get_active_feeds()`
    - 不在執行之間快取 feed 列表
    - 記錄自上次執行以來新增或移除的 feeds 數量
    - _需求：16.1, 16.5_

  - [x] 6.2 實作 feed 快取機制（可選）
    - 在記憶體中快取 feed 列表以提升效能
    - 每 6 小時刷新快取
    - 支援手動快取刷新
    - _需求：16.6, 16.7_

  - [x] 6.3 撰寫動態配置的屬性測試
    - **屬性 17：動態 Feed 配置**
    - **驗證需求：16.2, 16.3**
    - 使用 Hypothesis 生成隨機 feed 狀態變更
    - 驗證 is_active=false 的 feed 不出現在下次執行
    - 驗證 is_active=true 的新 feed 出現在下次執行
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 17: Dynamic Feed Configuration`

  - [x] 6.4 撰寫動態配置的單元測試
    - 測試每次執行時重新載入 feeds
    - 測試停用的 feed 被排除
    - 測試新增的 feed 被包含
    - 測試不需要重啟
    - _需求：16.2, 16.3, 16.4_

- [x] 7. 實作序列化與解析測試
  - [x] 7.1 撰寫序列化 Round-Trip 屬性測試
    - **屬性 18：序列化 Round-Trip**
    - **驗證需求：17.3, 17.4, 17.5, 17.7**
    - 使用 Hypothesis 生成隨機 ArticleSchema 物件
    - 序列化為資料庫記錄後再反序列化
    - 驗證產生等效物件
    - 驗證所有必要欄位被保留（title, url, feed_id, category）
    - 驗證 published_at 時間戳保留正確時區資訊
    - 驗證 NULL 值正確處理
    - 驗證特殊字元在標題和 URL 中正確處理
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 18: Serialization Round-Trip`

  - [x] 7.2 撰寫 RSS 解析的單元測試
    - 測試 RSS feed 條目解析為 ArticleSchema
    - 測試 published_at 時間戳解析
    - 測試時區資訊保留
    - 測試特殊字元處理
    - 測試 NULL 值處理
    - _需求：17.1, 17.2, 17.6, 17.7_

- [x] 8. 整合與連線
  - [x] 8.1 連接所有元件
    - 在 scheduler 中整合所有服務（Supabase, RSS, LLM）
    - 確保資料在元件之間正確流動
    - 驗證錯誤處理在整個管線中正常運作
    - 測試端到端流程
    - _需求：1.1, 2.1, 3.1, 4.1, 5.4_

  - [x] 8.2 撰寫整合測試
    - 測試使用模擬 feeds 的完整管線
    - 測試管線處理部分失敗
    - 測試跨執行的去重
    - 測試時間窗口尊重
    - 測試使用真實資料庫的文章插入
    - 測試使用真實資料庫的 UPSERT 行為
    - 測試使用真實資料庫的外鍵驗證

- [x] 9. 檢查點 - 確保所有測試通過
  - 執行所有屬性測試（最少 100 次迭代）
  - 執行所有單元測試
  - 執行所有整合測試
  - 驗證測試覆蓋率
  - 如有問題請詢問使用者

- [x] 10. 更新使用者指令整合
  - [x] 10.1 修改 /news_now 指令從資料池讀取
    - 修改指令處理器查詢 articles 表
    - 過濾最近 7 天發布的文章
    - 過濾 tinkering_index IS NOT NULL 的文章
    - 按 tinkering_index 降序排序
    - 限制結果為前 20 篇文章
    - 移除 RSS 抓取和 LLM 分析呼叫
    - 當資料池為空時新增後備訊息
    - _需求：15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [x] 10.2 撰寫使用者查詢的屬性測試
    - **屬性 16：使用者查詢結果過濾**
    - **驗證需求：15.2, 15.3, 15.4**
    - 使用 Hypothesis 生成隨機文章資料
    - 驗證所有返回文章的 tinkering_index IS NOT NULL
    - 驗證所有返回文章的 published_at 在最近 7 天內
    - 驗證結果按 tinkering_index 降序排序
    - 驗證結果數量 ≤ 20
    - 最少 100 次迭代
    - 標籤：`# Feature: background-scheduler-ai-pipeline, Property 16: User Query Result Filtering`

  - [x] 10.3 撰寫使用者指令的單元測試
    - 測試從資料庫查詢文章
    - 測試過濾條件（時間、tinkering_index）
    - 測試排序和限制
    - 測試不觸發 RSS 抓取
    - 測試不觸發 LLM 分析
    - 測試空資料池的後備訊息
    - _需求：15.5, 15.7_

- [x] 11. 配置與環境變數
  - [x] 11.1 新增環境變數配置
    - 在 .env.example 中新增 SCHEDULER_CRON（預設：`0 */6 * * *`）
    - 新增 SCHEDULER_TIMEZONE（預設：`Asia/Taipei`）
    - 新增 RSS_FETCH_DAYS（預設：7）
    - 新增 RSS_TIMEOUT（預設：15）
    - 新增 RSS_MAX_RETRIES（預設：3）
    - 新增 LLM_CONCURRENT_LIMIT（預設：5）
    - 新增 LLM_TIMEOUT（預設：30）
    - 新增 LLM_MAX_RETRIES（預設：2）
    - 新增 DB_MAX_RETRIES（預設：3）
    - 新增 DB_RETRY_DELAY（預設：1）
    - 新增 BATCH_SIZE（預設：50）
    - 新增 BATCH_SPLIT_THRESHOLD（預設：100）

  - [x] 11.2 更新 config.py 讀取新環境變數
    - 在 app/core/config.py 中新增配置欄位
    - 為所有新配置設定預設值
    - 驗證配置值的有效性
    - 新增配置驗證邏輯

  - [x] 11.3 撰寫配置的單元測試
    - 測試預設配置值
    - 測試從環境變數讀取配置
    - 測試無效配置值的驗證
    - 測試配置覆寫

- [x] 12. 效能優化
  - [x] 12.1 實作資料庫查詢優化
    - 使用 `SELECT id FROM articles WHERE url = ?` 進行存在性檢查（僅索引掃描）
    - 將存在性檢查批次化為單一查詢 `WHERE url IN (...)`
    - 對重複查詢使用預備語句
    - 考慮為並發操作使用連線池
    - _需求：12.2_

  - [x] 12.2 實作記憶體管理
    - 批次處理文章以限制記憶體使用
    - 在下一批次前清理已處理批次的記憶體
    - 對大結果集使用生成器
    - 在生產環境監控記憶體使用
    - _需求：12.4_

  - [x] 12.3 撰寫效能測試
    - 測試 50、100、500 篇文章批次的處理時間
    - 驗證記憶體使用保持在可接受限制內
    - 確保並發 LLM 呼叫尊重 semaphore 限制
    - 測試 100、500、1000 篇文章批次的插入時間
    - 驗證不同重複率的 UPSERT 效能
    - 測試使用者指令的查詢效能

- [x] 13. 文件與部署準備
  - [x] 13.1 更新 README 文件
    - 記錄新的背景排程器架構
    - 說明配置選項
    - 新增部署指南
    - 新增監控建議
    - 新增故障排除提示

  - [x] 13.2 建立部署檢查清單
    - 驗證環境變數已設定
    - 驗證資料庫索引存在
    - 驗證排程器健康檢查端點可訪問
    - 設定監控告警
    - 驗證只有一個排程器實例在執行

  - [x] 13.3 建立回滾計畫
    - 記錄回滾到 Phase 2 的步驟
    - 驗證資料庫狀態不需要回滾
    - 準備使用者指令的回滾版本
    - 記錄監控檢查點

- [x] 14. 最終檢查點 - 確保所有測試通過
  - 執行完整測試套件
  - 驗證所有屬性測試通過（最少 100 次迭代）
  - 驗證所有單元測試通過
  - 驗證所有整合測試通過
  - 驗證效能測試符合要求
  - 檢查測試覆蓋率報告
  - 如有問題請詢問使用者

## 注意事項

### 測試要求

- 標記為 `*` 的子任務為可選測試任務，可跳過以加快 MVP 開發
- 每個屬性測試必須執行最少 100 次迭代
- 每個屬性測試必須使用標籤格式：`# Feature: background-scheduler-ai-pipeline, Property {number}: {property_text}`
- 使用 Hypothesis 框架進行屬性測試
- 所有測試必須參考設計文件中的屬性編號

### 實作順序

1. 先實作核心功能（Supabase Service、RSS Service、LLM Service 增強）
2. 再實作排程器重寫
3. 然後實作整合與連線
4. 最後實作測試和文件

### 錯誤處理原則

- 個別項目失敗不應阻止批次處理
- 所有錯誤必須記錄完整上下文
- 暫時性錯誤使用指數退避重試
- 永久性錯誤記錄並繼續
- 排程器永不崩潰

### 效能考量

- 批次大小：50 篇文章/批次
- 並發限制：5 個 LLM API 呼叫
- 資料庫批次插入：100 筆/批次
- 記憶體管理：批次之間清理
- 連線池：重用資料庫連線

### 向後相容性

- Phase 1 資料庫結構不變
- Phase 2 資料存取層保持相容
- 現有 API 不受影響
- 使用者指令介面保持一致

## 參考資料

- **需求文件**：`.kiro/specs/background-scheduler-ai-pipeline/requirements.md`
- **設計文件**：`.kiro/specs/background-scheduler-ai-pipeline/design.md`
- **Phase 1 資料庫結構**：`scripts/init_supabase.sql`
- **Phase 2 資料存取層**：`app/services/supabase_service.py`
- **現有 RSS Service**：`app/services/rss_service.py`
- **現有 LLM Service**：`app/services/llm_service.py`
- **現有 Scheduler**：`app/tasks/scheduler.py`
