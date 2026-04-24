# Requirements Document

## Introduction

本文件定義 Tech News Agent 專案從 Notion 遷移至 Supabase 的第一階段需求。此階段專注於建立支援多租戶架構的資料庫基礎建設，包括清理舊有依賴、建立新的資料庫結構，以及灌入初始資料。

本階段完成後，系統將具備完整的 PostgreSQL 資料庫結構，支援多使用者訂閱管理、文章儲存與向量搜尋能力，為後續的應用程式邏輯遷移奠定基礎。

## Glossary

- **System**: Tech News Agent 應用程式
- **Supabase**: 基於 PostgreSQL 的後端即服務平台
- **Config_Module**: app/core/config.py 配置模組
- **Environment_File**: .env 與 .env.example 環境變數檔案
- **Dependencies_File**: requirements.txt 套件依賴清單
- **Database_Schema**: Supabase PostgreSQL 資料庫結構
- **Seed_Script**: 用於初始化資料的 Python 腳本
- **Init_SQL_Script**: 用於建立資料庫結構的 SQL 腳本
- **pgvector**: PostgreSQL 向量搜尋擴充功能
- **Feed**: RSS 訂閱來源
- **Article**: 從 Feed 抓取的文章內容
- **User**: 使用 Discord 的系統使用者
- **Subscription**: 使用者對特定 Feed 的訂閱關係
- **Reading_List**: 使用者的文章閱讀清單
- **Embedding**: 文章的向量表示，用於語義搜尋

## Requirements

### Requirement 1: 移除 Notion 環境變數

**User Story:** 作為開發者，我希望從環境配置中移除所有 Notion 相關變數，以便系統不再依賴 Notion 服務

#### Acceptance Criteria

1. THE Config_Module SHALL NOT contain any Notion-related configuration fields
2. THE Environment_File SHALL NOT contain any Notion-related environment variables
3. THE Config_Module SHALL contain a supabase_url configuration field
4. THE Config_Module SHALL contain a supabase_key configuration field
5. THE Environment_File SHALL contain SUPABASE_URL environment variable
6. THE Environment_File SHALL contain SUPABASE_KEY environment variable

### Requirement 2: 更新套件依賴

**User Story:** 作為開發者，我希望更新專案依賴套件，以便使用 Supabase 而非 Notion 客戶端

#### Acceptance Criteria

1. THE Dependencies_File SHALL NOT contain notion-client package
2. THE Dependencies_File SHALL contain supabase package
3. THE Dependencies_File SHALL maintain all other existing dependencies

### Requirement 3: 建立資料庫初始化腳本

**User Story:** 作為系統管理員，我希望有一個 SQL 腳本可以建立完整的資料庫結構，以便在 Supabase 後台執行初始化

#### Acceptance Criteria

1. THE Init_SQL_Script SHALL be located at scripts/init_supabase.sql
2. THE Init_SQL_Script SHALL enable pgvector extension
3. THE Init_SQL_Script SHALL create a users table with columns: id (UUID primary key), discord_id (TEXT unique not null), created_at (TIMESTAMPTZ default now())
4. THE Init_SQL_Script SHALL create a feeds table with columns: id (UUID primary key), name (TEXT not null), url (TEXT unique not null), category (TEXT not null), is_active (BOOLEAN default true), created_at (TIMESTAMPTZ default now())
5. THE Init_SQL_Script SHALL create a user_subscriptions table with columns: id (UUID primary key), user_id (UUID references users), feed_id (UUID references feeds), subscribed_at (TIMESTAMPTZ default now()), and a unique constraint on (user_id, feed_id)
6. THE Init_SQL_Script SHALL create an articles table with columns: id (UUID primary key), feed_id (UUID references feeds), title (TEXT not null), url (TEXT unique not null), published_at (TIMESTAMPTZ), tinkering_index (INTEGER), ai_summary (TEXT), embedding (VECTOR(1536)), created_at (TIMESTAMPTZ default now())
7. THE Init_SQL_Script SHALL create a reading_list table with columns: id (UUID primary key), user_id (UUID references users), article_id (UUID references articles), status (TEXT check in ('Unread', 'Read', 'Archived')), rating (INTEGER check between 1 and 5), added_at (TIMESTAMPTZ default now()), updated_at (TIMESTAMPTZ default now()), and a unique constraint on (user_id, article_id)
8. THE Init_SQL_Script SHALL create appropriate indexes for foreign keys and frequently queried columns
9. WHEN a record in users table is deleted, THE Database_Schema SHALL cascade delete related records in user_subscriptions and reading_list tables
10. WHEN a record in feeds table is deleted, THE Database_Schema SHALL cascade delete related records in articles table
11. WHEN a record in articles table is deleted, THE Database_Schema SHALL cascade delete related records in reading_list table

### Requirement 4: 建立種子資料腳本

**User Story:** 作為系統管理員，我希望有一個 Python 腳本可以將預設的 RSS 來源寫入資料庫，以便系統初始化時有可用的訂閱源

#### Acceptance Criteria

1. THE Seed_Script SHALL be located at scripts/seed_feeds.py
2. THE Seed_Script SHALL use Supabase Python client to insert data
3. THE Seed_Script SHALL read SUPABASE_URL and SUPABASE_KEY from environment variables
4. THE Seed_Script SHALL insert feeds with category "前端開發" including: Vue.js News (https://news.vuejs.org/rss.xml), Nuxt (https://nuxt.com/blog/rss.xml), VitePress (https://vitepress.dev/blog/rss.xml), Express (https://expressjs.com/feed.xml), Vue.js Developers (https://vuejsdevelopers.com/atom.xml)
5. THE Seed_Script SHALL insert feeds with category "自架服務" including: Reddit r/selfhosted (https://www.reddit.com/r/selfhosted/.rss), Reddit r/docker (https://www.reddit.com/r/docker/.rss), Home Assistant (https://www.home-assistant.io/atom.xml), Awesome-Selfhosted (https://github.com/awesome-selfhosted/awesome-selfhosted/commits/master.atom)
6. THE Seed_Script SHALL insert feeds with category "AI 應用" including: Simon Willison's Weblog (https://simonwillison.net/atom/everything/), Reddit r/LocalLLaMA (https://www.reddit.com/r/LocalLLaMA/.rss), Vue.js Community Newsletters (https://news.vuejs.org/issues.rss)
7. THE Seed_Script SHALL set is_active to true for all inserted feeds
8. WHEN a feed with duplicate url already exists, THE Seed_Script SHALL skip insertion and continue with next feed
9. WHEN the Supabase connection fails, THE Seed_Script SHALL raise a descriptive error message
10. WHEN the script completes successfully, THE Seed_Script SHALL print the number of feeds inserted

### Requirement 5: 資料庫向量搜尋支援

**User Story:** 作為開發者，我希望資料庫支援向量搜尋功能，以便未來實作 AI 推薦系統

#### Acceptance Criteria

1. THE Database_Schema SHALL enable pgvector extension
2. THE articles table SHALL contain an embedding column of type VECTOR(1536)
3. THE Database_Schema SHALL create an index on the embedding column for efficient similarity search
4. THE embedding column SHALL allow NULL values for articles without generated embeddings

### Requirement 6: 多租戶資料隔離

**User Story:** 作為系統架構師，我希望資料庫結構支援多租戶架構，以便不同使用者的資料互相隔離

#### Acceptance Criteria

1. THE users table SHALL uniquely identify each user by discord_id
2. THE user_subscriptions table SHALL link users to their subscribed feeds
3. THE reading_list table SHALL link users to their article interactions
4. THE Database_Schema SHALL prevent duplicate subscriptions through unique constraint on (user_id, feed_id)
5. THE Database_Schema SHALL prevent duplicate reading list entries through unique constraint on (user_id, article_id)

### Requirement 7: 共用資源池設計

**User Story:** 作為系統架構師，我希望所有訂閱源在全域層級管理，以便避免重複抓取相同的 RSS 來源

#### Acceptance Criteria

1. THE feeds table SHALL store all RSS sources globally without user association
2. THE articles table SHALL store fetched articles globally linked to feeds
3. THE Database_Schema SHALL prevent duplicate feed URLs through unique constraint
4. THE Database_Schema SHALL prevent duplicate article URLs through unique constraint
5. WHEN multiple users subscribe to the same feed, THE System SHALL reference the same feed record in feeds table

### Requirement 8: 時間戳記與審計追蹤

**User Story:** 作為系統管理員，我希望所有資料表都記錄建立時間，以便追蹤資料的時間軸

#### Acceptance Criteria

1. THE users table SHALL record created_at timestamp with default value of current time
2. THE feeds table SHALL record created_at timestamp with default value of current time
3. THE user_subscriptions table SHALL record subscribed_at timestamp with default value of current time
4. THE articles table SHALL record created_at timestamp with default value of current time
5. THE articles table SHALL record published_at timestamp from RSS feed
6. THE reading_list table SHALL record added_at timestamp with default value of current time
7. THE reading_list table SHALL record updated_at timestamp with default value of current time
8. WHEN a reading_list record is modified, THE Database_Schema SHALL update the updated_at timestamp

### Requirement 9: 資料完整性約束

**User Story:** 作為資料庫管理員，我希望資料庫強制執行資料完整性規則，以便防止無效資料進入系統

#### Acceptance Criteria

1. THE reading_list table SHALL only accept status values from the set: 'Unread', 'Read', 'Archived'
2. THE reading_list table SHALL only accept rating values between 1 and 5 inclusive
3. THE users table SHALL require discord_id to be unique and not null
4. THE feeds table SHALL require name to be not null
5. THE feeds table SHALL require url to be unique and not null
6. THE feeds table SHALL require category to be not null
7. THE articles table SHALL require title to be not null
8. THE articles table SHALL require url to be unique and not null

### Requirement 10: 腳本執行環境

**User Story:** 作為開發者，我希望種子資料腳本可以獨立執行，以便在不同環境中初始化資料

#### Acceptance Criteria

1. THE Seed_Script SHALL be executable as a standalone Python script
2. THE Seed_Script SHALL load environment variables from .env file using python-dotenv
3. WHEN required environment variables are missing, THE Seed_Script SHALL raise a descriptive error before attempting database connection
4. THE Seed_Script SHALL provide clear console output indicating progress and completion status
5. THE Seed_Script SHALL handle network errors gracefully with appropriate error messages
