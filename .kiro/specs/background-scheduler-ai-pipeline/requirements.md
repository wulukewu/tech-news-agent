# Requirements Document

## Introduction

本文件定義 Tech News Agent 專案 Phase 3 的需求：背景排程器與 AI 管線解耦（Decoupled Pipeline）。此階段將系統架構從「使用者觸發式抓取」轉變為「背景共用池定時抓取」，大幅降低 LLM API 消耗並提升系統效能。

Phase 1 已建立 Supabase PostgreSQL 資料庫結構，Phase 2 已實作資料存取層（supabase_service.py）。Phase 3 將重構排程器與服務層，實現以下核心改變：

1. 排程器定時抓取所有 RSS 來源，將新文章寫入共用資料池
2. LLM 服務只處理資料庫中尚未分析的文章，避免重複消耗 API
3. 背景排程器不主動發送 Discord 訊息，僅負責「豐富資料庫」
4. 使用者指令（如 /news_now）從資料庫讀取已處理的文章，按需推送

此架構將 API 消耗從「每次使用者請求」降低至「每篇文章一次」，並支援未來的多租戶推薦系統。

## Glossary

- **System**: Tech News Agent 應用程式
- **Scheduler**: app/tasks/scheduler.py 背景排程器模組
- **RSS_Service**: app/services/rss_service.py RSS 抓取服務
- **LLM_Service**: app/services/llm_service.py LLM 分析服務
- **Supabase_Service**: app/services/supabase_service.py 資料存取層
- **Article_Pool**: articles 資料表，儲存所有已抓取與分析的文章
- **Feed**: RSS 訂閱來源
- **Tinkering_Index**: 文章的技術複雜度評分（1-5）
- **AI_Summary**: LLM 生成的文章摘要
- **Deduplication**: 透過 URL 檢查避免重複處理文章
- **Decoupled_Pipeline**: 將資料抓取、AI 分析與使用者通知分離的架構模式
- **Background_Job**: 定時執行的背景任務，不由使用者直接觸發
- **User_Command**: 使用者透過 Discord 指令觸發的操作

## Requirements

### Requirement 1: 排程器初始化與訂閱源載入

**User Story:** 作為背景排程器，我需要在啟動時載入所有啟用的 RSS 訂閱源，以便定時抓取文章

#### Acceptance Criteria

1. WHEN the Scheduler starts, THE Scheduler SHALL call Supabase_Service.get_active_feeds() to retrieve all feeds
2. THE Scheduler SHALL filter feeds where is_active is true
3. THE Scheduler SHALL log the count of active feeds loaded
4. WHEN no active feeds exist, THE Scheduler SHALL log a warning and continue without error
5. WHEN Supabase_Service.get_active_feeds() fails, THE Scheduler SHALL log the error and retry after 5 minutes

### Requirement 2: RSS 文章抓取與去重

**User Story:** 作為 RSS 服務，我需要抓取文章並檢查是否已存在於資料庫，以便只處理新文章

#### Acceptance Criteria

1. THE RSS_Service SHALL fetch articles from all active feeds
2. FOR EACH fetched article, THE RSS_Service SHALL query Supabase_Service to check if the article URL exists in Article_Pool
3. WHEN an article URL already exists in Article_Pool, THE RSS_Service SHALL skip that article
4. WHEN an article URL does not exist in Article_Pool, THE RSS_Service SHALL add it to the new articles list
5. THE RSS_Service SHALL return only new articles for further processing
6. THE RSS_Service SHALL log the count of total fetched articles and new articles
7. WHEN URL checking fails for a specific article, THE RSS_Service SHALL log the error and continue with remaining articles

### Requirement 3: LLM 批次分析與評分

**User Story:** 作為 LLM 服務，我需要批次分析新文章並計算 tinkering_index 與摘要，以便豐富資料庫內容

#### Acceptance Criteria

1. THE LLM_Service SHALL accept a list of new articles for batch processing
2. FOR EACH article, THE LLM_Service SHALL call the Groq API to evaluate tinkering_index
3. FOR EACH article, THE LLM_Service SHALL call the Groq API to generate ai_summary
4. THE LLM_Service SHALL use Llama 3.1 8B model for tinkering_index evaluation
5. THE LLM_Service SHALL use Llama 3.3 70B model for ai_summary generation
6. THE LLM_Service SHALL limit concurrent API calls to 5 using a semaphore
7. WHEN an API call fails for a specific article, THE LLM_Service SHALL set tinkering_index to NULL and ai_summary to NULL for that article
8. THE LLM_Service SHALL log the count of successfully analyzed articles and failed articles
9. THE LLM_Service SHALL return the list of articles with populated ai_analysis fields

### Requirement 4: 文章寫入共用資料池

**User Story:** 作為背景排程器，我需要將分析完成的文章寫入資料庫，以便使用者指令可以讀取

#### Acceptance Criteria

1. WHEN LLM analysis completes, THE Scheduler SHALL call Supabase_Service.insert_articles() with the analyzed articles
2. THE Supabase_Service.insert_articles() method SHALL use UPSERT operation based on article URL
3. WHEN an article URL already exists, THE Supabase_Service SHALL update the existing record with new ai_summary and tinkering_index
4. WHEN an article URL does not exist, THE Supabase_Service SHALL insert a new record
5. THE Supabase_Service.insert_articles() method SHALL validate that feed_id exists before insertion
6. THE Supabase_Service.insert_articles() method SHALL return the count of inserted and updated articles
7. THE Scheduler SHALL log the insertion results including success count and failure count
8. WHEN insertion fails for specific articles, THE Scheduler SHALL log the failing article URLs and continue

### Requirement 5: 背景排程器不發送通知

**User Story:** 作為系統架構師，我希望背景排程器只負責資料抓取與分析，不發送 Discord 訊息，以便實現解耦架構

#### Acceptance Criteria

1. THE Scheduler background job SHALL NOT call any Discord API methods
2. THE Scheduler background job SHALL NOT import Discord bot client
3. THE Scheduler background job SHALL NOT send notifications to any Discord channel
4. THE Scheduler background job SHALL only perform data fetching, analysis, and database insertion
5. THE Scheduler SHALL log completion status including total articles processed

### Requirement 6: 可配置的排程時間

**User Story:** 作為系統管理員，我希望可以配置背景排程器的執行時間，以便根據需求調整抓取頻率

#### Acceptance Criteria

1. THE Scheduler SHALL read schedule configuration from environment variables
2. THE Scheduler SHALL support CRON expression format for schedule configuration
3. THE Scheduler SHALL default to running every 6 hours when no configuration is provided
4. THE Scheduler SHALL log the configured schedule on startup
5. WHEN the CRON expression is invalid, THE Scheduler SHALL raise a configuration error on startup
6. THE Scheduler SHALL support multiple schedule configurations for different time zones

### Requirement 7: RSS 抓取失敗處理

**User Story:** 作為背景排程器，我需要優雅處理 RSS 抓取失敗，以便一個來源失敗不影響其他來源

#### Acceptance Criteria

1. WHEN RSS_Service fails to fetch a specific feed, THE RSS_Service SHALL log the error with feed name and URL
2. WHEN RSS_Service fails to fetch a specific feed, THE RSS_Service SHALL continue processing remaining feeds
3. THE RSS_Service SHALL use exponential backoff retry for transient network errors
4. THE RSS_Service SHALL retry failed requests up to 3 times before giving up
5. WHEN all retries fail, THE RSS_Service SHALL mark the feed as temporarily unavailable in logs
6. THE Scheduler SHALL report the count of successful and failed feed fetches
7. WHEN more than 50% of feeds fail, THE Scheduler SHALL log a critical warning

### Requirement 8: LLM API 失敗處理

**User Story:** 作為 LLM 服務，我需要優雅處理 API 失敗，以便部分文章失敗不影響整體處理

#### Acceptance Criteria

1. WHEN Groq API returns an error for a specific article, THE LLM_Service SHALL log the error with article title and URL
2. WHEN Groq API returns an error for a specific article, THE LLM_Service SHALL set tinkering_index to NULL and ai_summary to NULL
3. THE LLM_Service SHALL continue processing remaining articles after a failure
4. WHEN Groq API rate limit is exceeded, THE LLM_Service SHALL wait for the specified retry-after duration
5. THE LLM_Service SHALL implement exponential backoff for transient API errors
6. THE LLM_Service SHALL retry failed API calls up to 2 times before marking as failed
7. THE LLM_Service SHALL log the total count of API successes and failures
8. WHEN more than 30% of articles fail analysis, THE LLM_Service SHALL log a warning

### Requirement 9: 資料庫連線失敗處理

**User Story:** 作為背景排程器，我需要處理資料庫連線失敗，以便系統可以自動恢復

#### Acceptance Criteria

1. WHEN Supabase connection fails during feed loading, THE Scheduler SHALL retry after 5 minutes
2. WHEN Supabase connection fails during article insertion, THE Scheduler SHALL cache the articles in memory
3. THE Scheduler SHALL retry database operations up to 3 times with exponential backoff
4. WHEN all database retries fail, THE Scheduler SHALL log a critical error and skip the current job execution
5. THE Scheduler SHALL not crash when database operations fail
6. THE Scheduler SHALL resume normal operation on the next scheduled execution
7. WHEN database connection is restored, THE Scheduler SHALL process cached articles if any exist

### Requirement 10: 排程器健康檢查

**User Story:** 作為系統管理員，我需要監控排程器的健康狀態，以便及時發現問題

#### Acceptance Criteria

1. THE Scheduler SHALL expose a health check endpoint at /health/scheduler
2. THE health check endpoint SHALL return the last execution timestamp
3. THE health check endpoint SHALL return the count of articles processed in the last execution
4. THE health check endpoint SHALL return the count of failed operations in the last execution
5. THE health check endpoint SHALL return HTTP 200 when the scheduler is healthy
6. THE health check endpoint SHALL return HTTP 503 when the scheduler has not run in the last 12 hours
7. THE health check endpoint SHALL return HTTP 503 when the last execution had more than 50% failures

### Requirement 11: 文章時效性過濾

**User Story:** 作為背景排程器，我需要只處理最近的文章，以便避免處理過時內容

#### Acceptance Criteria

1. THE RSS_Service SHALL only fetch articles published within the last 7 days
2. THE RSS_Service SHALL parse the published_at timestamp from RSS feed entries
3. WHEN published_at is not available, THE RSS_Service SHALL use the current timestamp
4. THE RSS_Service SHALL filter out articles older than 7 days before deduplication check
5. THE time window SHALL be configurable via environment variable RSS_FETCH_DAYS
6. THE RSS_Service SHALL default to 7 days when RSS_FETCH_DAYS is not set
7. THE RSS_Service SHALL log the count of articles filtered by time window

### Requirement 12: 批次處理效能優化

**User Story:** 作為系統，我需要高效處理大量文章，以便支援大規模 RSS 抓取

#### Acceptance Criteria

1. THE Scheduler SHALL process articles in batches of maximum 50 articles per batch
2. THE LLM_Service SHALL use connection pooling for Groq API requests
3. THE Supabase_Service.insert_articles() method SHALL use batch insert operations
4. THE Scheduler SHALL limit memory usage by processing articles in chunks
5. WHEN processing more than 100 articles, THE Scheduler SHALL split them into multiple batches
6. THE Scheduler SHALL log the processing time for each batch
7. THE Scheduler SHALL log the total processing time for the entire job

### Requirement 13: 重複文章更新策略

**User Story:** 作為系統，我需要決定何時更新已存在的文章，以便保持資料新鮮度

#### Acceptance Criteria

1. WHEN an article URL already exists in Article_Pool, THE System SHALL check if ai_summary is NULL
2. WHEN ai_summary is NULL, THE System SHALL re-process the article with LLM
3. WHEN ai_summary is not NULL, THE System SHALL skip LLM processing
4. THE System SHALL update the article's updated_at timestamp when re-processing
5. THE System SHALL log the count of articles re-processed due to missing ai_summary
6. THE System SHALL not re-process articles that already have complete ai_analysis
7. WHEN tinkering_index is NULL but ai_summary exists, THE System SHALL re-process only the tinkering_index

### Requirement 14: 排程器日誌記錄

**User Story:** 作為開發者，我需要詳細的排程器日誌，以便診斷問題和監控效能

#### Acceptance Criteria

1. THE Scheduler SHALL log the start time of each job execution at INFO level
2. THE Scheduler SHALL log the end time and total duration of each job execution at INFO level
3. THE Scheduler SHALL log the count of feeds processed at INFO level
4. THE Scheduler SHALL log the count of new articles found at INFO level
5. THE Scheduler SHALL log the count of articles analyzed by LLM at INFO level
6. THE Scheduler SHALL log the count of articles inserted into database at INFO level
7. THE Scheduler SHALL log all errors at ERROR level with full stack traces
8. THE Scheduler SHALL log warnings at WARNING level when failure rates exceed thresholds

### Requirement 15: 使用者指令與資料池整合

**User Story:** 作為使用者，我希望 /news_now 指令從資料池讀取已分析的文章，以便快速獲得推薦

#### Acceptance Criteria

1. WHEN a user executes /news_now, THE System SHALL query Article_Pool for articles published in the last 7 days
2. THE System SHALL filter articles where tinkering_index is not NULL
3. THE System SHALL order articles by tinkering_index descending
4. THE System SHALL limit results to top 20 articles
5. THE System SHALL not trigger RSS fetching or LLM analysis during /news_now execution
6. THE System SHALL send Discord notification with the filtered articles
7. WHEN no articles are found in Article_Pool, THE System SHALL inform the user to wait for the next scheduled fetch

### Requirement 16: 訂閱源管理與排程器同步

**User Story:** 作為系統管理員，我希望新增或停用訂閱源時，排程器可以自動同步，以便無需重啟

#### Acceptance Criteria

1. THE Scheduler SHALL reload active feeds at the start of each job execution
2. WHEN a feed is marked as is_active=false, THE Scheduler SHALL exclude it from the next execution
3. WHEN a new feed is added with is_active=true, THE Scheduler SHALL include it in the next execution
4. THE Scheduler SHALL not require restart when feeds are added or removed
5. THE Scheduler SHALL log the count of feeds added or removed since last execution
6. THE Scheduler SHALL cache feed list in memory between executions for performance
7. THE Scheduler SHALL refresh the feed cache every 6 hours

### Requirement 17: 解析器與序列化器的 Round-Trip 測試

**User Story:** 作為開發者，我需要確保 RSS 解析與資料序列化的正確性，以便避免資料損壞

#### Acceptance Criteria

1. THE RSS_Service SHALL parse RSS feed entries into ArticleSchema objects
2. THE Supabase_Service SHALL serialize ArticleSchema objects into database records
3. FOR ALL valid ArticleSchema objects, serializing then deserializing SHALL produce an equivalent object
4. THE System SHALL preserve all required fields during round-trip conversion
5. THE System SHALL handle NULL values correctly during round-trip conversion
6. THE System SHALL handle special characters in titles and URLs during round-trip conversion
7. THE System SHALL validate that published_at timestamps are preserved with correct timezone information
