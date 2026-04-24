# Requirements Document: Web API OAuth Authentication

## Introduction

本文件定義 Tech News Agent 專案 Phase 5 的需求：訂閱體驗優化與 Web API 基礎建設。此階段將在 FastAPI 後端建立完整的 Discord OAuth2 登入流程、JWT 認證機制，以及個人化的 Web API 端點，為未來的 Next.js Web 前端做準備。

Phase 1-4 已建立完整的多租戶資料庫架構、資料存取層、背景排程器和 Discord Bot 互動介面。Phase 5 將擴展系統能力，讓使用者能夠透過 Web 瀏覽器存取個人化的技術新聞動態，並管理訂閱設定。

核心功能：

1. Discord OAuth2 登入流程：重導向至 Discord 授權頁面，接收 callback 並換取 Access Token
2. JWT Token 認證：生成並驗證 JWT Token，實作 FastAPI Dependency 保護 API 端點
3. 個人化訂閱管理 API：查詢所有 feeds 並標記使用者訂閱狀態，支援訂閱切換
4. 個人專屬文章動態 API：基於使用者訂閱源回傳個人化文章列表

## Glossary

- **OAuth2**: 開放授權標準，允許使用者授權第三方應用存取其資源
- **Discord_OAuth_Provider**: Discord 提供的 OAuth2 授權服務
- **JWT_Token**: JSON Web Token，用於無狀態的使用者認證
- **Access_Token**: Discord OAuth2 授權後取得的存取令牌
- **Authorization_Code**: OAuth2 授權碼流程中的臨時授權碼
- **HttpOnly_Cookie**: 只能透過 HTTP 傳輸的 Cookie，JavaScript 無法存取，提升安全性
- **API_Dependency**: FastAPI 的依賴注入機制，用於保護需要認證的端點
- **User_Subscription**: 使用者訂閱關係，儲存在 user_subscriptions 表
- **Feed_Source**: RSS 來源，儲存在 feeds 表
- **Personal_Feed**: 個人化文章動態，基於使用者訂閱源的文章列表
- **CORS**: Cross-Origin Resource Sharing，跨來源資源共享，允許 Web 前端呼叫 API

## Requirements

### Requirement 1: Discord OAuth2 登入重導向

**User Story:** 作為使用者，我希望點擊「使用 Discord 登入」按鈕時，能被重導向至 Discord 授權頁面

#### Acceptance Criteria

1. THE System SHALL provide a GET endpoint at `/api/auth/discord/login`
2. WHEN a user accesses this endpoint, THE System SHALL construct a Discord OAuth2 authorization URL
3. THE authorization URL SHALL include the client_id from environment variable DISCORD_CLIENT_ID
4. THE authorization URL SHALL include the redirect_uri from environment variable DISCORD_REDIRECT_URI
5. THE authorization URL SHALL request the "identify" scope to access user's Discord ID
6. THE System SHALL redirect the user to the constructed Discord authorization URL using HTTP 302 status code
7. WHEN environment variables are missing, THE System SHALL return HTTP 500 with error message

### Requirement 2: Discord OAuth2 Callback 處理

**User Story:** 作為系統，我需要接收 Discord 的授權回調，並換取 Access Token 以取得使用者資訊

#### Acceptance Criteria

1. THE System SHALL provide a GET endpoint at `/api/auth/discord/callback`
2. WHEN Discord redirects back with an authorization code, THE System SHALL extract the code from query parameters
3. THE System SHALL exchange the authorization code for an Access Token by calling Discord's token endpoint
4. THE token exchange request SHALL include client_id, client_secret, code, redirect_uri, and grant_type="authorization_code"
5. WHEN the token exchange fails, THE System SHALL return HTTP 401 with error message
6. WHEN the token exchange succeeds, THE System SHALL use the Access Token to call Discord's `/users/@me` endpoint
7. THE System SHALL extract the Discord user ID from the API response
8. WHEN Discord API calls fail, THE System SHALL return HTTP 500 with error message

### Requirement 3: 使用者註冊與 JWT Token 生成

**User Story:** 作為系統，我需要在取得 Discord ID 後，註冊或查詢使用者，並生成 JWT Token

#### Acceptance Criteria

1. WHEN the System obtains a Discord ID from OAuth callback, THE System SHALL call `supabase_service.get_or_create_user(discord_id)`
2. THE System SHALL generate a JWT Token containing the user UUID and Discord ID as payload
3. THE JWT Token SHALL be signed using the secret key from environment variable JWT_SECRET
4. THE JWT Token SHALL have an expiration time of 7 days from issuance
5. THE JWT Token SHALL use the HS256 algorithm for signing
6. THE System SHALL return the JWT Token in the response body as JSON: `{"access_token": "...", "token_type": "Bearer"}`
7. WHEN JWT_SECRET environment variable is missing, THE System SHALL raise a configuration error on startup

### Requirement 4: JWT Token Cookie 設置

**User Story:** 作為系統，我希望將 JWT Token 設置為 HttpOnly Cookie，提升安全性

#### Acceptance Criteria

1. WHERE the System generates a JWT Token, THE System SHALL set the token as an HttpOnly Cookie named "access_token"
2. THE Cookie SHALL have the httponly flag set to True
3. THE Cookie SHALL have the secure flag set to True when running in production (HTTPS)
4. THE Cookie SHALL have the samesite attribute set to "lax"
5. THE Cookie SHALL have a max_age of 7 days (604800 seconds)
6. THE Cookie SHALL have the path attribute set to "/"
7. THE System SHALL return both the Cookie and JSON response to support different client implementations

### Requirement 5: JWT Token 驗證 Dependency

**User Story:** 作為開發者，我需要一個 FastAPI Dependency 來驗證 JWT Token 並取得當前使用者

#### Acceptance Criteria

1. THE System SHALL provide a FastAPI Dependency function named `get_current_user`
2. THE Dependency SHALL first attempt to extract the JWT Token from the "Authorization" header (format: "Bearer {token}")
3. IF the Authorization header is not present, THE Dependency SHALL attempt to extract the token from the "access_token" Cookie
4. WHEN no token is found in either location, THE Dependency SHALL raise HTTPException with status 401 and detail "Not authenticated"
5. THE Dependency SHALL decode the JWT Token using the JWT_SECRET and HS256 algorithm
6. WHEN the token is expired, THE Dependency SHALL raise HTTPException with status 401 and detail "Token expired"
7. WHEN the token signature is invalid, THE Dependency SHALL raise HTTPException with status 401 and detail "Invalid token"
8. WHEN the token is valid, THE Dependency SHALL extract the user UUID from the payload
9. THE Dependency SHALL return a dictionary containing user_id (UUID) and discord_id (string)

### Requirement 6: 查詢所有 Feeds 與訂閱狀態

**User Story:** 作為使用者，我希望能夠查看所有可用的 RSS 來源，並知道我訂閱了哪些

#### Acceptance Criteria

1. THE System SHALL provide a GET endpoint at `/api/feeds`
2. THE endpoint SHALL be protected by the `get_current_user` Dependency
3. WHEN a user accesses this endpoint, THE System SHALL query all records from the feeds table where is_active=true
4. THE System SHALL query the user_subscriptions table for the current user's subscriptions
5. FOR EACH feed, THE System SHALL determine if the user is subscribed by checking if a matching record exists in user_subscriptions
6. THE System SHALL return a JSON array of feed objects, each containing: id, name, url, category, is_subscribed (boolean)
7. THE feeds SHALL be ordered by category ascending, then name ascending
8. WHEN the database query fails, THE System SHALL return HTTP 500 with error message

### Requirement 7: 訂閱切換 API

**User Story:** 作為使用者，我希望能夠透過 API 訂閱或取消訂閱 RSS 來源

#### Acceptance Criteria

1. THE System SHALL provide a POST endpoint at `/api/subscriptions/toggle`
2. THE endpoint SHALL be protected by the `get_current_user` Dependency
3. THE endpoint SHALL accept a JSON body containing feed_id (UUID string)
4. WHEN the request body is invalid, THE System SHALL return HTTP 422 with validation error details
5. THE System SHALL query user_subscriptions to check if the user is already subscribed to the feed
6. IF the user is subscribed, THE System SHALL call `supabase_service.unsubscribe_from_feed(discord_id, feed_id)`
7. IF the user is not subscribed, THE System SHALL call `supabase_service.subscribe_to_feed(discord_id, feed_id)`
8. THE System SHALL return a JSON response indicating the new subscription status: `{"feed_id": "...", "is_subscribed": true/false}`
9. WHEN the feed_id does not exist, THE System SHALL return HTTP 404 with error message "Feed not found"
10. WHEN the database operation fails, THE System SHALL return HTTP 500 with error message

### Requirement 8: 個人專屬文章動態 API

**User Story:** 作為使用者，我希望能夠查看基於我訂閱源的個人化文章列表

#### Acceptance Criteria

1. THE System SHALL provide a GET endpoint at `/api/articles/me`
2. THE endpoint SHALL be protected by the `get_current_user` Dependency
3. THE System SHALL query user_subscriptions to get the list of feed_ids the user has subscribed to
4. WHEN the user has no subscriptions, THE System SHALL return an empty array with HTTP 200
5. THE System SHALL query the articles table WHERE feed_id IN (user's subscribed feed_ids)
6. THE System SHALL filter articles WHERE published_at >= 7 days ago
7. THE System SHALL filter articles WHERE tinkering_index IS NOT NULL
8. THE System SHALL order articles by tinkering_index descending, then published_at descending
9. THE System SHALL limit the results to 50 articles
10. THE System SHALL JOIN with the feeds table to include feed name and category for each article
11. THE System SHALL return a JSON array of article objects, each containing: id, title, url, published_at, tinkering_index, ai_summary, feed_name, category
12. WHEN the database query fails, THE System SHALL return HTTP 500 with error message

### Requirement 9: 文章動態分頁支援

**User Story:** 作為使用者，我希望能夠分頁瀏覽我的文章動態，避免一次載入過多資料

#### Acceptance Criteria

1. THE `/api/articles/me` endpoint SHALL accept optional query parameters: page (integer, default 1) and page_size (integer, default 20)
2. THE System SHALL validate that page >= 1
3. THE System SHALL validate that page_size is between 1 and 100
4. WHEN validation fails, THE System SHALL return HTTP 422 with validation error details
5. THE System SHALL calculate the offset as (page - 1) \* page_size
6. THE System SHALL apply LIMIT page_size and OFFSET offset to the database query
7. THE System SHALL return a JSON response containing: articles (array), page (integer), page_size (integer), total_count (integer), has_next_page (boolean)
8. THE total_count SHALL be calculated by counting all matching articles before applying pagination
9. THE has_next_page SHALL be true IF (page \* page_size) < total_count

### Requirement 10: CORS 配置

**User Story:** 作為開發者，我需要配置 CORS 以允許 Next.js Web 前端呼叫 API

#### Acceptance Criteria

1. THE System SHALL configure CORS middleware in the FastAPI application
2. THE CORS configuration SHALL allow origins from environment variable CORS_ORIGINS (comma-separated list)
3. WHEN CORS_ORIGINS is not set, THE System SHALL default to allowing "http://localhost:3000" for development
4. THE CORS configuration SHALL allow credentials (cookies) to be sent with requests
5. THE CORS configuration SHALL allow the following HTTP methods: GET, POST, PUT, DELETE, OPTIONS
6. THE CORS configuration SHALL allow the following headers: Content-Type, Authorization
7. THE CORS configuration SHALL expose the Set-Cookie header to the client

### Requirement 11: 環境變數驗證

**User Story:** 作為系統管理員，我希望在應用啟動時驗證所有必要的環境變數

#### Acceptance Criteria

1. THE System SHALL validate the presence of DISCORD_CLIENT_ID on startup
2. THE System SHALL validate the presence of DISCORD_CLIENT_SECRET on startup
3. THE System SHALL validate the presence of DISCORD_REDIRECT_URI on startup
4. THE System SHALL validate the presence of JWT_SECRET on startup
5. WHEN any required environment variable is missing, THE System SHALL raise a ConfigurationError with a descriptive message
6. THE System SHALL validate that JWT_SECRET is at least 32 characters long
7. WHEN JWT_SECRET is too short, THE System SHALL raise a ConfigurationError with message "JWT_SECRET must be at least 32 characters"
8. THE System SHALL log all configuration validation results at INFO level

### Requirement 12: OAuth2 錯誤處理

**User Story:** 作為使用者，我希望當 OAuth2 登入失敗時，能收到清楚的錯誤訊息

#### Acceptance Criteria

1. WHEN Discord returns an error in the callback (e.g., user denies authorization), THE System SHALL extract the error and error_description from query parameters
2. THE System SHALL return HTTP 400 with JSON response: `{"error": "...", "description": "..."}`
3. WHEN the authorization code is missing from callback, THE System SHALL return HTTP 400 with error message "Authorization code missing"
4. WHEN Discord's token endpoint returns an error, THE System SHALL log the full error response
5. THE System SHALL return HTTP 401 with user-friendly message "Failed to authenticate with Discord"
6. WHEN Discord's user API endpoint fails, THE System SHALL log the error and return HTTP 500 with message "Failed to retrieve user information"
7. THE System SHALL not expose internal error details (e.g., API keys, stack traces) to users

### Requirement 13: JWT Token 刷新機制

**User Story:** 作為使用者，我希望在 Token 即將過期時能夠刷新 Token，避免重新登入

#### Acceptance Criteria

1. THE System SHALL provide a POST endpoint at `/api/auth/refresh`
2. THE endpoint SHALL be protected by the `get_current_user` Dependency
3. WHEN a valid token is provided, THE System SHALL generate a new JWT Token with the same user information
4. THE new token SHALL have a fresh expiration time of 7 days from the refresh time
5. THE System SHALL return the new token in both JSON response and HttpOnly Cookie
6. THE System SHALL invalidate the old token by adding it to a token blacklist (stored in memory or Redis)
7. WHEN the old token is used after refresh, THE System SHALL return HTTP 401 with message "Token has been refreshed, please use the new token"

### Requirement 14: 登出功能

**User Story:** 作為使用者，我希望能夠登出，清除我的認證狀態

#### Acceptance Criteria

1. THE System SHALL provide a POST endpoint at `/api/auth/logout`
2. THE endpoint SHALL be protected by the `get_current_user` Dependency
3. WHEN a user logs out, THE System SHALL add the current JWT Token to a token blacklist
4. THE System SHALL clear the "access_token" Cookie by setting max_age to 0
5. THE System SHALL return HTTP 200 with JSON response: `{"message": "Logged out successfully"}`
6. WHEN the blacklisted token is used, THE System SHALL return HTTP 401 with message "Token has been revoked"

### Requirement 15: API 速率限制

**User Story:** 作為系統管理員，我希望實作 API 速率限制，防止濫用

#### Acceptance Criteria

1. THE System SHALL implement rate limiting middleware for all API endpoints
2. THE rate limit SHALL be 100 requests per minute per IP address for unauthenticated endpoints
3. THE rate limit SHALL be 300 requests per minute per user for authenticated endpoints
4. WHEN the rate limit is exceeded, THE System SHALL return HTTP 429 with JSON response: `{"error": "Rate limit exceeded", "retry_after": <seconds>}`
5. THE System SHALL include the following headers in responses: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
6. THE rate limit configuration SHALL be adjustable via environment variables: RATE_LIMIT_PER_MINUTE_UNAUTH and RATE_LIMIT_PER_MINUTE_AUTH

### Requirement 16: API 文件自動生成

**User Story:** 作為開發者，我希望能夠查看自動生成的 API 文件

#### Acceptance Criteria

1. THE System SHALL expose OpenAPI documentation at `/docs` (Swagger UI)
2. THE System SHALL expose alternative documentation at `/redoc` (ReDoc)
3. THE API documentation SHALL include all endpoint descriptions, parameters, request bodies, and response schemas
4. THE API documentation SHALL include authentication requirements for protected endpoints
5. THE API documentation SHALL include example requests and responses
6. THE System SHALL use Pydantic models to automatically generate request and response schemas
7. THE documentation SHALL be accessible without authentication

### Requirement 17: Pydantic Schema 定義

**User Story:** 作為開發者，我需要定義清晰的 Pydantic Schema 來驗證請求和回應資料

#### Acceptance Criteria

1. THE System SHALL define a Pydantic model `FeedResponse` with fields: id (UUID), name (str), url (str), category (str), is_subscribed (bool)
2. THE System SHALL define a Pydantic model `SubscriptionToggleRequest` with field: feed_id (UUID)
3. THE System SHALL define a Pydantic model `SubscriptionToggleResponse` with fields: feed_id (UUID), is_subscribed (bool)
4. THE System SHALL define a Pydantic model `ArticleResponse` with fields: id (UUID), title (str), url (str), published_at (datetime), tinkering_index (int), ai_summary (str | None), feed_name (str), category (str)
5. THE System SHALL define a Pydantic model `ArticleListResponse` with fields: articles (List[ArticleResponse]), page (int), page_size (int), total_count (int), has_next_page (bool)
6. THE System SHALL define a Pydantic model `TokenResponse` with fields: access_token (str), token_type (str)
7. THE System SHALL define a Pydantic model `ErrorResponse` with fields: error (str), description (str | None)
8. ALL Pydantic models SHALL use appropriate field validators to ensure data integrity

### Requirement 18: 安全性最佳實踐

**User Story:** 作為系統管理員，我希望 API 遵循安全性最佳實踐

#### Acceptance Criteria

1. THE System SHALL use HTTPS in production (enforced by secure Cookie flag)
2. THE System SHALL validate all user inputs using Pydantic models
3. THE System SHALL use parameterized queries for all database operations (already implemented in supabase_service)
4. THE System SHALL not log sensitive information (passwords, tokens, API keys)
5. THE System SHALL set appropriate security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
6. THE System SHALL implement CSRF protection for state-changing operations
7. THE JWT_SECRET SHALL be a cryptographically secure random string of at least 32 characters
8. THE System SHALL use constant-time comparison for token validation to prevent timing attacks

### Requirement 19: 錯誤日誌記錄

**User Story:** 作為開發者，我需要詳細的日誌來追蹤 API 請求和診斷問題

#### Acceptance Criteria

1. THE System SHALL log all API requests with method, path, and user ID (if authenticated)
2. THE System SHALL log all authentication attempts (success and failure)
3. THE System SHALL log all OAuth2 callback events with Discord user ID
4. THE System SHALL log all database operations performed by API endpoints
5. THE System SHALL log all errors with full context and stack traces
6. THE System SHALL use appropriate log levels: INFO for operations, WARNING for recoverable errors, ERROR for failures
7. THE System SHALL not log sensitive information (tokens, passwords, API keys)
8. THE System SHALL include request IDs in logs to correlate related log entries

### Requirement 20: 健康檢查端點擴展

**User Story:** 作為系統管理員，我希望健康檢查端點能夠驗證 OAuth2 和 JWT 配置

#### Acceptance Criteria

1. THE `/health` endpoint SHALL include a check for Discord OAuth2 configuration (client_id, client_secret, redirect_uri present)
2. THE `/health` endpoint SHALL include a check for JWT configuration (JWT_SECRET present and valid length)
3. THE `/health` endpoint SHALL include a check for database connectivity (already implemented)
4. THE health check response SHALL include a "services" object with status for each service: oauth (healthy/unhealthy), jwt (healthy/unhealthy), database (healthy/unhealthy)
5. WHEN any service is unhealthy, THE overall status SHALL be "degraded"
6. WHEN all services are unhealthy, THE overall status SHALL be "unhealthy" and return HTTP 503
7. THE health check SHALL not expose sensitive configuration values
