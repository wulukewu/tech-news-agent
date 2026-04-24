# Requirements Document

## Introduction

本文件定義 Tech News Agent 專案資料存取層重構（Phase 2）的需求。此階段將完全移除 Notion 服務依賴，實作基於 Supabase 的資料存取層，支援多租戶架構的 CRUD 操作。

Phase 1 已建立完整的 PostgreSQL 資料庫結構，包含 users、feeds、user_subscriptions、articles、reading_list 五個表。Phase 2 將實作 supabase_service.py 模組，提供型別安全的資料庫操作介面，並更新資料模型以匹配新的資料庫結構。

## Glossary

- **System**: Tech News Agent 應用程式
- **Supabase_Service**: app/services/supabase_service.py 資料存取層模組
- **Notion_Service**: app/services/notion_service.py 舊有資料存取層模組（將被移除）
- **Article_Schema**: app/schemas/article.py 中的 Pydantic 資料模型
- **Database**: Supabase PostgreSQL 資料庫
- **User**: 透過 Discord ID 識別的系統使用者
- **Feed**: RSS 訂閱來源
- **Article**: 從 Feed 抓取的文章內容
- **Reading_List**: 使用者的文章閱讀清單與互動記錄
- **Discord_ID**: Discord 平台的使用者唯一識別碼
- **UUID**: 資料庫內部使用的通用唯一識別碼
- **UPSERT**: 若記錄存在則更新，否則插入的資料庫操作
- **Scheduler**: 背景排程器，定期抓取 RSS 文章

## Requirements

### Requirement 1: 移除舊有 Notion 服務

**User Story:** 作為開發者，我希望完全移除 Notion 服務依賴，以便系統只使用 Supabase 作為資料儲存

#### Acceptance Criteria

1. THE System SHALL NOT contain app/services/notion_service.py file
2. THE System SHALL NOT import NotionService class in any module
3. THE System SHALL NOT contain notion-client package in requirements.txt

### Requirement 2: 更新資料模型結構

**User Story:** 作為開發者，我希望資料模型與 Supabase 資料庫結構一致，以便進行型別安全的資料操作

#### Acceptance Criteria

1. THE Article_Schema SHALL contain a feed_id field of type UUID
2. THE Article_Schema SHALL contain a published_at field of type Optional[datetime]
3. THE Article_Schema SHALL contain a tinkering_index field of type Optional[int] with range constraint 1-5
4. THE Article_Schema SHALL contain an ai_summary field of type Optional[str]
5. THE Article_Schema SHALL contain an embedding field of type Optional[List[float]]
6. THE Article_Schema SHALL contain a created_at field of type datetime
7. THE Article_Schema SHALL remove the content_preview field
8. THE Article_Schema SHALL remove the raw_data field
9. THE Article_Schema SHALL rename source_category to category
10. THE Article_Schema SHALL rename source_name to feed_name

### Requirement 3: 實作使用者管理功能

**User Story:** 作為系統，我需要透過 Discord ID 管理使用者，以便支援多租戶架構

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a get_or_create_user method accepting discord_id parameter
2. WHEN a user with the given discord_id exists, THE get_or_create_user method SHALL return the user's UUID
3. WHEN a user with the given discord_id does not exist, THE get_or_create_user method SHALL create a new user record and return the UUID
4. THE get_or_create_user method SHALL handle database unique constraint violations gracefully
5. WHEN database connection fails, THE get_or_create_user method SHALL raise a descriptive error

### Requirement 4: 實作訂閱源查詢功能

**User Story:** 作為背景排程器，我需要取得所有啟用的 RSS 訂閱源，以便定期抓取文章

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a get_active_feeds method
2. THE get_active_feeds method SHALL return a list of feeds where is_active is true
3. THE get_active_feeds method SHALL return feed records with id, name, url, category fields
4. THE get_active_feeds method SHALL order results by category and name
5. WHEN no active feeds exist, THE get_active_feeds method SHALL return an empty list
6. WHEN database query fails, THE get_active_feeds method SHALL raise a descriptive error

### Requirement 5: 實作文章批次插入功能

**User Story:** 作為背景排程器，我需要批次插入抓取的文章，以便高效地儲存大量文章資料

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide an insert_articles method accepting a list of article dictionaries
2. THE insert_articles method SHALL use UPSERT operation based on article URL
3. WHEN an article with the same URL exists, THE insert_articles method SHALL update the existing record
4. WHEN an article with the same URL does not exist, THE insert_articles method SHALL insert a new record
5. THE insert_articles method SHALL validate that feed_id exists in feeds table
6. THE insert_articles method SHALL handle foreign key constraint violations with descriptive errors
7. THE insert_articles method SHALL return the count of inserted and updated articles
8. WHEN the articles list is empty, THE insert_articles method SHALL return zero counts without database operations
9. WHEN database operation fails, THE insert_articles method SHALL raise a descriptive error with the failing article information

### Requirement 6: 實作閱讀清單儲存功能

**User Story:** 作為使用者，我希望將文章加入我的閱讀清單，以便稍後閱讀

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a save_to_reading_list method accepting discord_id and article_id parameters
2. THE save_to_reading_list method SHALL resolve discord_id to user UUID using get_or_create_user
3. THE save_to_reading_list method SHALL use UPSERT operation based on (user_id, article_id) combination
4. WHEN the reading list entry exists, THE save_to_reading_list method SHALL update the updated_at timestamp
5. WHEN the reading list entry does not exist, THE save_to_reading_list method SHALL insert a new record with status 'Unread'
6. THE save_to_reading_list method SHALL validate that article_id exists in articles table
7. THE save_to_reading_list method SHALL handle foreign key constraint violations with descriptive errors
8. WHEN database operation fails, THE save_to_reading_list method SHALL raise a descriptive error

### Requirement 7: 實作文章狀態更新功能

**User Story:** 作為使用者，我希望更新文章的閱讀狀態，以便追蹤我的閱讀進度

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide an update_article_status method accepting discord_id, article_id, and status parameters
2. THE update_article_status method SHALL validate status is one of 'Unread', 'Read', 'Archived'
3. WHEN status is invalid, THE update_article_status method SHALL raise a ValueError with allowed values
4. THE update_article_status method SHALL resolve discord_id to user UUID
5. THE update_article_status method SHALL update the status field in reading_list table
6. THE update_article_status method SHALL update the updated_at timestamp automatically
7. WHEN the reading list entry does not exist, THE update_article_status method SHALL raise a descriptive error
8. WHEN database operation fails, THE update_article_status method SHALL raise a descriptive error

### Requirement 8: 實作文章評分功能

**User Story:** 作為使用者，我希望為文章評分，以便系統了解我的偏好

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide an update_article_rating method accepting discord_id, article_id, and rating parameters
2. THE update_article_rating method SHALL validate rating is an integer between 1 and 5 inclusive
3. WHEN rating is invalid, THE update_article_rating method SHALL raise a ValueError with allowed range
4. THE update_article_rating method SHALL resolve discord_id to user UUID
5. THE update_article_rating method SHALL update the rating field in reading_list table
6. THE update_article_rating method SHALL update the updated_at timestamp automatically
7. WHEN the reading list entry does not exist, THE update_article_rating method SHALL raise a descriptive error
8. WHEN database operation fails, THE update_article_rating method SHALL raise a descriptive error

### Requirement 9: 實作閱讀清單查詢功能

**User Story:** 作為使用者，我希望查詢我的閱讀清單，以便查看我儲存的文章

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a get_reading_list method accepting discord_id and optional status filter
2. THE get_reading_list method SHALL resolve discord_id to user UUID
3. WHEN status filter is provided, THE get_reading_list method SHALL return only articles with matching status
4. WHEN status filter is not provided, THE get_reading_list method SHALL return all articles in the reading list
5. THE get_reading_list method SHALL join with articles table to include article details
6. THE get_reading_list method SHALL return results ordered by added_at descending
7. THE get_reading_list method SHALL include fields: article_id, title, url, category, status, rating, added_at, updated_at
8. WHEN no articles match the criteria, THE get_reading_list method SHALL return an empty list
9. WHEN database query fails, THE get_reading_list method SHALL raise a descriptive error

### Requirement 10: 實作高評分文章查詢功能

**User Story:** 作為系統，我需要查詢使用者的高評分文章，以便生成個人化推薦

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a get_highly_rated_articles method accepting discord_id and optional threshold parameter
2. THE get_highly_rated_articles method SHALL default threshold to 4 when not provided
3. THE get_highly_rated_articles method SHALL resolve discord_id to user UUID
4. THE get_highly_rated_articles method SHALL return articles with rating greater than or equal to threshold
5. THE get_highly_rated_articles method SHALL join with articles table to include article details
6. THE get_highly_rated_articles method SHALL return results ordered by rating descending, then added_at descending
7. WHEN no articles meet the threshold, THE get_highly_rated_articles method SHALL return an empty list
8. WHEN database query fails, THE get_highly_rated_articles method SHALL raise a descriptive error

### Requirement 11: 實作使用者訂閱管理功能

**User Story:** 作為使用者，我希望管理我的 RSS 訂閱，以便自訂我接收的內容

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a subscribe_to_feed method accepting discord_id and feed_id parameters
2. THE subscribe_to_feed method SHALL resolve discord_id to user UUID
3. THE subscribe_to_feed method SHALL insert a record into user_subscriptions table
4. THE subscribe_to_feed method SHALL handle duplicate subscription attempts gracefully by ignoring them
5. THE Supabase_Service SHALL provide an unsubscribe_from_feed method accepting discord_id and feed_id parameters
6. THE unsubscribe_from_feed method SHALL resolve discord_id to user UUID
7. THE unsubscribe_from_feed method SHALL delete the record from user_subscriptions table
8. WHEN the subscription does not exist, THE unsubscribe_from_feed method SHALL complete without error
9. WHEN database operation fails, THE subscribe_to_feed and unsubscribe_from_feed methods SHALL raise descriptive errors

### Requirement 12: 實作使用者訂閱查詢功能

**User Story:** 作為使用者，我希望查看我訂閱的所有 RSS 源，以便了解我的訂閱狀態

#### Acceptance Criteria

1. THE Supabase_Service SHALL provide a get_user_subscriptions method accepting discord_id parameter
2. THE get_user_subscriptions method SHALL resolve discord_id to user UUID
3. THE get_user_subscriptions method SHALL join with feeds table to include feed details
4. THE get_user_subscriptions method SHALL return results ordered by subscribed_at descending
5. THE get_user_subscriptions method SHALL include fields: feed_id, name, url, category, subscribed_at
6. WHEN the user has no subscriptions, THE get_user_subscriptions method SHALL return an empty list
7. WHEN database query fails, THE get_user_subscriptions method SHALL raise a descriptive error

### Requirement 13: 錯誤處理與日誌記錄

**User Story:** 作為開發者，我希望所有資料庫錯誤都有清晰的錯誤訊息和日誌，以便快速診斷問題

#### Acceptance Criteria

1. THE Supabase_Service SHALL log all database operations at INFO level
2. THE Supabase_Service SHALL log all database errors at ERROR level with full context
3. WHEN a unique constraint violation occurs, THE Supabase_Service SHALL provide error message indicating which field caused the conflict
4. WHEN a foreign key constraint violation occurs, THE Supabase_Service SHALL provide error message indicating which reference is invalid
5. WHEN a check constraint violation occurs, THE Supabase_Service SHALL provide error message indicating which validation rule failed
6. WHEN a not null constraint violation occurs, THE Supabase_Service SHALL provide error message indicating which required field is missing
7. THE Supabase_Service SHALL define a custom SupabaseServiceError exception class
8. THE Supabase_Service SHALL wrap all database exceptions in SupabaseServiceError with descriptive messages

### Requirement 14: 連線管理與初始化

**User Story:** 作為系統，我需要安全地管理 Supabase 連線，以便確保資料庫操作的可靠性

#### Acceptance Criteria

1. THE Supabase_Service SHALL initialize Supabase client in **init** method
2. THE Supabase_Service SHALL read supabase_url and supabase_key from settings
3. WHEN supabase_url or supabase_key is missing, THE Supabase_Service SHALL raise a configuration error
4. THE Supabase_Service SHALL validate Supabase connection on initialization
5. WHEN connection validation fails, THE Supabase_Service SHALL raise a descriptive error with troubleshooting hints
6. THE Supabase_Service SHALL support async operations for all database methods
7. THE Supabase_Service SHALL handle connection timeouts with appropriate error messages

### Requirement 15: 批次操作效能優化

**User Story:** 作為系統，我需要高效地處理大量文章資料，以便支援大規模 RSS 抓取

#### Acceptance Criteria

1. THE insert_articles method SHALL use batch insert operations when inserting multiple articles
2. THE insert_articles method SHALL process articles in chunks of maximum 100 records per batch
3. WHEN a batch operation partially fails, THE insert_articles method SHALL log which articles failed and continue with remaining batches
4. THE insert_articles method SHALL return detailed statistics including success count, update count, and failure count
5. THE Supabase_Service SHALL use database connection pooling for concurrent operations
6. THE Supabase_Service SHALL implement retry logic for transient database errors with exponential backoff

### Requirement 16: 資料驗證與清理

**User Story:** 作為系統，我需要驗證和清理輸入資料，以便防止無效資料進入資料庫

#### Acceptance Criteria

1. THE insert_articles method SHALL validate that article URLs are valid HTTP/HTTPS URLs
2. THE insert_articles method SHALL validate that tinkering_index is between 1 and 5 when provided
3. THE insert_articles method SHALL truncate article titles to 2000 characters if longer
4. THE insert_articles method SHALL truncate ai_summary to 5000 characters if longer
5. THE save_to_reading_list method SHALL validate that article_id is a valid UUID format
6. THE update_article_status method SHALL normalize status values to title case
7. WHEN validation fails, THE Supabase_Service SHALL raise a ValueError with specific validation error details

### Requirement 17: 測試支援與可測試性

**User Story:** 作為開發者，我希望服務易於測試，以便確保程式碼品質

#### Acceptance Criteria

1. THE Supabase_Service SHALL accept an optional client parameter in **init** for dependency injection
2. THE Supabase_Service SHALL provide a close method to cleanup resources
3. THE Supabase_Service SHALL support context manager protocol for automatic resource cleanup
4. THE Supabase_Service SHALL expose all database operations as public methods with clear interfaces
5. THE Supabase_Service SHALL not contain hardcoded values that prevent testing
6. THE Supabase_Service SHALL use type hints for all method parameters and return values
