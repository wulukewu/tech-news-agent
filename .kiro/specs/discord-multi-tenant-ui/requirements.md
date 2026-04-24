# Requirements Document: Discord Multi-tenant UI

## Introduction

本文件定義 Tech News Agent 專案 Phase 4 的需求：Discord 多租戶互動體驗（Multi-tenant Discord UI）。此階段將改寫所有 Discord 指令與互動按鈕，實現真正的多租戶架構，讓系統能夠識別並追蹤每個使用者的個人化操作。

Phase 1-3 已建立完整的資料庫基礎設施、資料存取層和背景排程器。Phase 4 將重構 Discord Bot 的所有使用者互動介面，從「單一使用者」模式轉變為「多租戶」模式，讓每個 Discord 使用者都能擁有獨立的訂閱、閱讀清單和個人化推薦。

核心改變：

1. 所有指令執行前自動註冊使用者（透過 `get_or_create_user`）
2. `/add_feed` 改為個人訂閱模式（寫入 `user_subscriptions` 表）
3. `/news_now` 從資料庫讀取使用者訂閱的文章，不再即時抓取
4. 互動按鈕（稍後閱讀、標記已讀）正確傳遞 `article_id` 並寫入資料庫
5. `/reading_list` 完全基於資料庫實作，支援分頁和評分

## Glossary

- **Multi-tenant**: 多租戶架構，每個 Discord 使用者視為獨立租戶
- **User Registration**: 使用者註冊，透過 `get_or_create_user` 確保使用者存在於資料庫
- **Personal Subscription**: 個人訂閱，每個使用者可以訂閱不同的 RSS 來源
- **Article Pool**: 共用文章池，背景排程器抓取的所有文章
- **Reading List**: 閱讀清單，使用者個人的待讀文章列表
- **Persistent View**: 持久化視圖，Discord 互動元件在 bot 重啟後仍可運作
- **Ephemeral Response**: 臨時回應，只有觸發互動的使用者可見
- **Custom ID**: 自訂 ID，用於識別互動元件的唯一標識符

## Requirements

### Requirement 1: 自動使用者註冊中間件

**User Story:** 作為系統，我需要在任何指令執行前自動註冊使用者，以便確保所有操作都有對應的使用者記錄

#### Acceptance Criteria

1. WHEN any Discord command is executed, THE System SHALL call `get_or_create_user(interaction.user.id)` before processing the command
2. THE System SHALL use the returned user UUID for all subsequent database operations
3. WHEN user registration fails, THE System SHALL log the error and inform the user
4. THE System SHALL cache the user UUID during the command execution to avoid repeated database calls
5. THE System SHALL handle concurrent user registrations gracefully (idempotent operation)

### Requirement 2: 個人化訂閱管理 - /add_feed

**User Story:** 作為使用者，我希望可以訂閱自己感興趣的 RSS 來源，而不影響其他使用者

#### Acceptance Criteria

1. WHEN a user executes `/add_feed`, THE System SHALL first check if the feed URL already exists in the `feeds` table
2. WHEN the feed does not exist, THE System SHALL insert a new feed record with `is_active=true`
3. WHEN the feed already exists, THE System SHALL use the existing feed_id
4. THE System SHALL insert a record into `user_subscriptions` table linking the user to the feed
5. WHEN the user is already subscribed to the feed, THE System SHALL inform the user without error
6. THE System SHALL return a success message with the feed name and category
7. THE System SHALL validate the feed URL format before insertion
8. THE System SHALL handle duplicate subscription attempts gracefully (UPSERT or ignore)

### Requirement 3: 從資料池讀取文章 - /news_now

**User Story:** 作為使用者，我希望 `/news_now` 指令能快速顯示我訂閱的最新文章，而不需要等待 RSS 抓取

#### Acceptance Criteria

1. WHEN a user executes `/news_now`, THE System SHALL NOT trigger RSS fetching or LLM analysis
2. THE System SHALL query the `articles` table for articles from feeds the user has subscribed to
3. THE System SHALL filter articles published within the last 7 days
4. THE System SHALL filter articles where `tinkering_index IS NOT NULL`
5. THE System SHALL order articles by `tinkering_index` descending
6. THE System SHALL limit results to top 20 articles
7. THE System SHALL group articles by category in the display
8. WHEN the user has no subscriptions, THE System SHALL inform the user to subscribe to feeds first
9. WHEN no articles are found, THE System SHALL inform the user to wait for the next scheduled fetch

### Requirement 4: 稍後閱讀按鈕整合

**User Story:** 作為使用者，我希望點擊「稍後閱讀」按鈕時，文章能正確加入我的閱讀清單

#### Acceptance Criteria

1. WHEN a user clicks the "稍後閱讀" button, THE System SHALL retrieve the article_id from the button's custom_id
2. THE System SHALL call `supabase_service.save_to_reading_list(discord_id, article_id)`
3. THE System SHALL set the initial status to 'Unread'
4. WHEN the article is already in the reading list, THE System SHALL update the `updated_at` timestamp
5. THE System SHALL disable the button after successful save
6. THE System SHALL send an ephemeral confirmation message to the user
7. WHEN the save operation fails, THE System SHALL log the error and inform the user
8. THE button custom_id SHALL include the article_id (UUID) for reliable identification

### Requirement 5: 標記已讀按鈕整合

**User Story:** 作為使用者，我希望點擊「標記已讀」按鈕時，文章狀態能正確更新

#### Acceptance Criteria

1. WHEN a user clicks the "標記已讀" button, THE System SHALL retrieve the article_id from the button's custom_id
2. THE System SHALL call `supabase_service.update_article_status(discord_id, article_id, 'Read')`
3. THE System SHALL update the `updated_at` timestamp automatically
4. THE System SHALL disable the button after successful update
5. THE System SHALL send an ephemeral confirmation message to the user
6. WHEN the article is not in the reading list, THE System SHALL add it with status 'Read'
7. WHEN the update operation fails, THE System SHALL log the error and inform the user

### Requirement 6: 閱讀清單分頁顯示

**User Story:** 作為使用者，我希望能夠瀏覽我的閱讀清單，並對文章進行評分和狀態管理

#### Acceptance Criteria

1. WHEN a user executes `/reading_list view`, THE System SHALL query `reading_list` table for the user's articles
2. THE System SHALL JOIN with `articles` table to get article details
3. THE System SHALL filter by status='Unread' by default
4. THE System SHALL display 5 articles per page
5. THE System SHALL provide "上一頁" and "下一頁" buttons for navigation
6. THE System SHALL provide "標記已讀" buttons for each article
7. THE System SHALL provide rating dropdowns (1-5 stars) for each article
8. THE System SHALL send the response as ephemeral (only visible to the user)
9. WHEN the reading list is empty, THE System SHALL inform the user

### Requirement 7: 文章評分功能

**User Story:** 作為使用者，我希望能夠對閱讀清單中的文章評分，以便系統了解我的偏好

#### Acceptance Criteria

1. WHEN a user selects a rating from the dropdown, THE System SHALL call `supabase_service.update_article_rating(discord_id, article_id, rating)`
2. THE System SHALL validate that rating is between 1 and 5
3. THE System SHALL update the `updated_at` timestamp automatically
4. THE System SHALL send an ephemeral confirmation message with the rating
5. WHEN the article is not in the reading list, THE System SHALL add it with the specified rating
6. WHEN the rating update fails, THE System SHALL log the error and inform the user

### Requirement 8: 個人化推薦

**User Story:** 作為使用者，我希望根據我的高評分文章獲得個人化推薦

#### Acceptance Criteria

1. WHEN a user executes `/reading_list recommend`, THE System SHALL query articles rated 4 or 5 stars by the user
2. THE System SHALL pass the article titles and categories to LLM service
3. THE System SHALL generate a personalized recommendation summary in Traditional Chinese
4. THE System SHALL send the recommendation as an ephemeral message
5. WHEN the user has no high-rated articles, THE System SHALL inform the user to rate articles first
6. WHEN LLM generation fails, THE System SHALL log the error and inform the user

### Requirement 9: 文章 ID 傳遞機制

**User Story:** 作為開發者，我需要確保所有互動按鈕都能正確傳遞 article_id，以便進行資料庫操作

#### Acceptance Criteria

1. ALL interactive buttons SHALL include article_id (UUID) in their custom_id
2. THE custom*id format SHALL be `{action}*{article_id}`(e.g.,`read_later_123e4567-e89b-12d3-a456-426614174000`)
3. WHEN creating buttons, THE System SHALL validate that article_id is available
4. WHEN article_id is not available, THE System SHALL query the database by URL to retrieve it
5. THE System SHALL handle custom_id length limits (max 100 characters)
6. THE System SHALL use UUID format for article_id (not URL hash or other identifiers)

### Requirement 10: 訂閱源查詢

**User Story:** 作為使用者，我希望能夠查看我訂閱的所有 RSS 來源

#### Acceptance Criteria

1. WHEN a user executes `/list_feeds`, THE System SHALL query `user_subscriptions` table for the user's subscriptions
2. THE System SHALL JOIN with `feeds` table to get feed details
3. THE System SHALL display feed name, URL, and category
4. THE System SHALL order feeds by `subscribed_at` descending
5. THE System SHALL send the response as ephemeral
6. WHEN the user has no subscriptions, THE System SHALL inform the user
7. THE System SHALL provide a link or instruction to subscribe to feeds

### Requirement 11: 取消訂閱功能

**User Story:** 作為使用者，我希望能夠取消訂閱不再感興趣的 RSS 來源

#### Acceptance Criteria

1. WHEN a user executes `/unsubscribe_feed`, THE System SHALL accept a feed_id or feed_name parameter
2. THE System SHALL call `supabase_service.unsubscribe_from_feed(discord_id, feed_id)`
3. THE System SHALL delete the record from `user_subscriptions` table
4. WHEN the subscription does not exist, THE System SHALL inform the user without error
5. THE System SHALL send a confirmation message with the feed name
6. THE System SHALL not delete the feed from the `feeds` table (other users may still be subscribed)

### Requirement 12: 錯誤處理與使用者反饋

**User Story:** 作為使用者，我希望當操作失敗時能收到清楚的錯誤訊息

#### Acceptance Criteria

1. WHEN any database operation fails, THE System SHALL log the error with full context
2. THE System SHALL send a user-friendly error message in Traditional Chinese
3. THE System SHALL not expose internal error details (e.g., SQL errors, stack traces) to users
4. THE System SHALL provide actionable suggestions when possible (e.g., "請稍後再試")
5. THE System SHALL use ephemeral messages for error notifications
6. THE System SHALL handle timeout errors gracefully (e.g., database connection timeout)

### Requirement 13: 並發操作處理

**User Story:** 作為系統，我需要正確處理多個使用者同時操作的情況

#### Acceptance Criteria

1. THE System SHALL handle concurrent user registrations without creating duplicate records
2. THE System SHALL handle concurrent subscription operations using database constraints
3. THE System SHALL handle concurrent reading list operations using UPSERT logic
4. THE System SHALL not block other users when one user's operation is slow
5. THE System SHALL use database transactions where appropriate to ensure data consistency

### Requirement 14: 互動元件持久化

**User Story:** 作為使用者，我希望即使 bot 重啟，之前的互動按鈕仍然可以使用

#### Acceptance Criteria

1. ALL interactive views SHALL use `timeout=None` for persistence
2. THE System SHALL register persistent views in the bot's `setup_hook`
3. THE System SHALL use stable custom_id patterns that can be reconstructed after restart
4. WHEN a button is clicked after bot restart, THE System SHALL retrieve necessary data from the database
5. THE System SHALL handle cases where the original message context is lost

### Requirement 15: 效能優化

**User Story:** 作為系統，我需要確保 Discord 指令響應迅速，不讓使用者等待過久

#### Acceptance Criteria

1. THE `/news_now` command SHALL respond within 3 seconds (no RSS fetching)
2. THE `/reading_list view` command SHALL respond within 2 seconds
3. THE System SHALL use database indexes for efficient queries (user_id, article_id, feed_id)
4. THE System SHALL cache user UUID during command execution to avoid repeated queries
5. THE System SHALL use `defer()` for operations that may take longer than 3 seconds
6. THE System SHALL limit the number of articles displayed to avoid message size limits

### Requirement 16: 資料驗證

**User Story:** 作為系統，我需要驗證所有使用者輸入，以防止無效資料進入資料庫

#### Acceptance Criteria

1. THE System SHALL validate feed URL format (must be valid HTTP/HTTPS URL)
2. THE System SHALL validate rating values (must be 1-5)
3. THE System SHALL validate status values (must be 'Unread', 'Read', or 'Archived')
4. THE System SHALL validate UUID format for article_id and feed_id
5. THE System SHALL truncate long text fields to database limits (title: 2000 chars, summary: 5000 chars)
6. THE System SHALL sanitize user input to prevent SQL injection (use parameterized queries)

### Requirement 17: 日誌記錄

**User Story:** 作為開發者，我需要詳細的日誌來追蹤使用者操作和診斷問題

#### Acceptance Criteria

1. THE System SHALL log all command executions with user ID and command name
2. THE System SHALL log all button interactions with user ID and button custom_id
3. THE System SHALL log all database operations with operation type and affected records
4. THE System SHALL log all errors with full context and stack traces
5. THE System SHALL use appropriate log levels (INFO for operations, ERROR for failures)
6. THE System SHALL not log sensitive information (e.g., API keys, passwords)

### Requirement 18: 向後相容性

**User Story:** 作為系統管理員，我希望 Phase 4 的改動不會破壞現有功能

#### Acceptance Criteria

1. THE System SHALL maintain compatibility with Phase 3 database schema
2. THE System SHALL not require database migrations (use existing tables)
3. THE System SHALL handle articles created by the background scheduler (Phase 3)
4. THE System SHALL handle users who have not yet subscribed to any feeds
5. THE System SHALL provide migration path for existing users (if any)
