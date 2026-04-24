# Implementation Plan: Web API OAuth Authentication

## Overview

本實作計畫將為 Tech News Agent 建立完整的 Discord OAuth2 登入流程、JWT 認證機制，以及個人化的 Web API 端點。實作將按照設計文件中的 Implementation Roadmap 分為 7 個階段，每個階段都包含具體的編碼任務和測試任務。

## Tasks

- [ ] 1. Phase 1: 基礎認證
  - [ ] 1.1 擴展環境配置模組
    - 在 `app/core/config.py` 中加入 Discord OAuth2 配置欄位（discord_client_id, discord_client_secret, discord_redirect_uri）
    - 加入 JWT 配置欄位（jwt_secret, jwt_algorithm, jwt_expiration_days）
    - 加入 CORS 配置欄位（cors_origins）
    - 加入速率限制配置欄位（rate_limit_per_minute_unauth, rate_limit_per_minute_auth）
    - 加入安全配置欄位（cookie_secure）
    - 實作 `validate_jwt_secret()` 方法驗證 JWT_SECRET 長度 >= 32
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [ ] 1.2 撰寫環境配置單元測試
    - 測試缺失必要環境變數時拋出 ConfigurationError
    - 測試 JWT_SECRET 過短時拋出錯誤
    - 測試所有配置欄位的預設值
    - _Requirements: 11.5, 11.6, 11.7_

  - [ ] 1.3 建立 JWT 工具模組
    - 建立 `app/api/auth.py` 檔案
    - 實作 `create_access_token(user_id: UUID, discord_id: str, expires_delta: Optional[timedelta] = None) -> str`
    - 實作 `decode_token(token: str) -> Dict[str, Any]`，處理 JWTError 和 ExpiredSignatureError
    - 實作 `set_token_cookie(response: Response, token: str) -> None`，設定 HttpOnly Cookie
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 1.4 撰寫 JWT 工具屬性測試
    - **Property 2: JWT Token Structure**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    - 使用 Hypothesis 生成隨機 user_id 和 discord_id，驗證生成的 Token 解碼後包含正確的 payload

  - [ ] 1.5 撰寫 JWT Round Trip 屬性測試
    - **Property 3: JWT Token Round Trip**
    - **Validates: Requirements 3.1, 3.2, 3.5**
    - 驗證 Token 編碼後解碼再編碼能產生等效的 Token

  - [ ] 1.6 撰寫 Cookie 安全屬性測試
    - **Property 4: Cookie Security Attributes**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    - 驗證設定的 Cookie 包含所有必要的安全屬性

  - [ ] 1.7 實作 Token 黑名單管理
    - 在 `app/api/auth.py` 中建立 `TokenBlacklist` 類別
    - 實作 `add(token: str) -> None` 方法
    - 實作 `is_blacklisted(token: str) -> bool` 方法
    - 實作 `cleanup_expired() -> None` 方法
    - 使用 asyncio.Lock 確保執行緒安全
    - _Requirements: 13.6, 14.3_

  - [ ] 1.8 實作 Discord OAuth2 登入端點
    - 在 `app/api/auth.py` 中建立 FastAPI Router
    - 實作 `GET /api/auth/discord/login` 端點
    - 構建 Discord OAuth2 授權 URL（包含 client_id, redirect_uri, response_type, scope）
    - 返回 302 重導向至 Discord
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 1.9 撰寫 OAuth2 URL 構建屬性測試
    - **Property 1: OAuth2 URL Construction**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    - 驗證構建的 URL 包含所有必要參數

  - [ ] 1.10 實作 Discord OAuth2 Callback 端點
    - 實作 `GET /api/auth/discord/callback` 端點
    - 處理錯誤情況（使用者拒絕授權）
    - 使用 httpx.AsyncClient 交換 authorization code 取得 Access Token
    - 使用 Access Token 呼叫 Discord `/users/@me` API
    - 呼叫 `supabase_service.get_or_create_user(discord_id)` 註冊使用者
    - 生成 JWT Token 並設定 Cookie
    - 返回 JSON 回應
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.1, 3.6, 4.7_

  - [ ] 1.11 撰寫 OAuth2 錯誤處理單元測試
    - 測試使用者拒絕授權時返回 400
    - 測試 Token 交換失敗時返回 401
    - 測試 Discord API 失敗時返回 500
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ] 1.12 實作認證 Dependency
    - 在 `app/api/auth.py` 中實作 `get_current_user()` Dependency
    - 從 Authorization Header 或 Cookie 提取 Token
    - 驗證 Token 並檢查黑名單
    - 提取 user_id 和 discord_id
    - 處理各種錯誤情況（Token 缺失、過期、無效、已撤銷）
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [ ] 1.13 撰寫 Token 驗證屬性測試
    - **Property 5: Token Validation Consistency**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.8, 5.9**
    - 驗證 get_current_user 提取的資訊與建立 Token 時一致

  - [ ] 1.14 撰寫 Token 過期測試
    - **Property 6: Token Expiration Enforcement**
    - **Validates: Requirements 5.6**
    - 測試過期 Token 被正確拒絕

  - [ ] 1.15 撰寫無效 Token 測試
    - **Property 7: Invalid Token Rejection**
    - **Validates: Requirements 5.7**
    - 測試無效簽名的 Token 被拒絕

- [ ] 2. Checkpoint - 基礎認證完成
  - 確保所有測試通過，詢問使用者是否有問題

- [ ] 3. Phase 2: 訂閱管理 API
  - [ ] 3.1 建立訂閱管理 Pydantic Schema
    - 建立 `app/schemas/feed.py` 檔案
    - 定義 `FeedResponse` 模型（id, name, url, category, is_subscribed）
    - 定義 `SubscriptionToggleRequest` 模型（feed_id）
    - 定義 `SubscriptionToggleResponse` 模型（feed_id, is_subscribed）
    - _Requirements: 17.1, 17.2, 17.3_

  - [ ] 3.2 撰寫 Pydantic Schema 驗證測試
    - **Property 17: Pydantic Schema Validation**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8**
    - 測試無效資料被正確拒絕

  - [ ] 3.3 實作查詢所有 Feeds 端點
    - 建立 `app/api/feeds.py` 檔案
    - 建立 FastAPI Router
    - 實作 `GET /api/feeds` 端點
    - 使用 `get_current_user` Dependency 保護端點
    - 查詢所有啟用的 feeds
    - 查詢使用者訂閱狀態
    - 標記每個 feed 的 is_subscribed 欄位
    - 按 category 和 name 排序
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [ ] 3.4 撰寫訂閱狀態準確性屬性測試
    - **Property 8: Feed Subscription Status Accuracy**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    - 驗證 is_subscribed 欄位正確反映訂閱狀態

  - [ ] 3.5 實作訂閱切換端點
    - 在 `app/api/feeds.py` 中實作 `POST /api/subscriptions/toggle` 端點
    - 使用 `get_current_user` Dependency 保護端點
    - 驗證 feed_id 存在
    - 檢查當前訂閱狀態
    - 呼叫 `supabase_service.subscribe_to_feed()` 或 `unsubscribe_from_feed()`
    - 返回新的訂閱狀態
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

  - [ ] 3.6 撰寫訂閱切換冪等性屬性測試
    - **Property 9: Subscription Toggle Idempotence**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7**
    - 驗證切換兩次回到原始狀態

- [ ] 4. Phase 3: 文章動態 API
  - [ ] 4.1 建立文章動態 Pydantic Schema
    - 擴展 `app/schemas/article.py`
    - 定義 `ArticleResponse` 模型（id, title, url, published_at, tinkering_index, ai_summary, feed_name, category）
    - 定義 `ArticleListResponse` 模型（articles, page, page_size, total_count, has_next_page）
    - _Requirements: 17.4, 17.5_

  - [ ] 4.2 實作個人專屬文章動態端點
    - 建立 `app/api/articles.py` 檔案
    - 建立 FastAPI Router
    - 實作 `GET /api/articles/me` 端點
    - 使用 `get_current_user` Dependency 保護端點
    - 接受分頁參數（page, page_size）
    - 查詢使用者訂閱的 feeds
    - 查詢相關文章（7 天內、tinkering_index 不為 NULL）
    - JOIN feeds 表取得 feed_name 和 category
    - 按 tinkering_index 和 published_at 排序
    - 實作分頁邏輯
    - 計算 total_count 和 has_next_page
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

  - [ ] 4.3 撰寫文章過濾屬性測試
    - **Property 10: Article Filtering by Subscription**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    - 驗證只返回訂閱源的文章

  - [ ] 4.4 撰寫文章時間窗口屬性測試
    - **Property 11: Article Time Window Filter**
    - **Validates: Requirements 8.6**
    - 驗證所有文章都在 7 天內

  - [ ] 4.5 撰寫分頁計算屬性測試
    - **Property 12: Pagination Calculation Correctness**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.9**
    - 驗證分頁計算的數學正確性

- [ ] 5. Checkpoint - API 端點完成
  - 確保所有測試通過，詢問使用者是否有問題

- [ ] 6. Phase 4: 安全性強化
  - [ ] 6.1 配置 CORS Middleware
    - 在 `app/main.py` 中加入 CORSMiddleware
    - 從環境變數讀取 CORS_ORIGINS
    - 設定 allow_credentials=True
    - 設定允許的 HTTP 方法和 Headers
    - 設定 expose_headers 包含 Set-Cookie
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ] 6.2 撰寫 CORS Headers 屬性測試
    - **Property 13: CORS Headers Presence**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**
    - 驗證回應包含正確的 CORS Headers

  - [ ] 6.3 實作速率限制 Middleware
    - 在 `app/main.py` 中整合 slowapi
    - 配置未認證端點的速率限制（100 requests/minute/IP）
    - 配置認證端點的速率限制（300 requests/minute/user）
    - 設定速率限制超過時的錯誤處理
    - 加入 X-RateLimit-\* Headers
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ] 6.4 撰寫速率限制屬性測試
    - **Property 16: Rate Limit Enforcement**
    - **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5**
    - 驗證超過限制時返回 429

  - [ ] 6.5 實作安全 Headers Middleware
    - 在 `app/main.py` 中建立 Security Headers Middleware
    - 設定 X-Content-Type-Options: nosniff
    - 設定 X-Frame-Options: DENY
    - 設定 X-XSS-Protection: 1; mode=block
    - _Requirements: 18.5_

  - [ ] 6.6 撰寫安全 Headers 屬性測試
    - **Property 18: Security Headers Presence**
    - **Validates: Requirements 18.5**
    - 驗證所有回應包含安全 Headers

  - [ ] 6.7 撰寫輸入驗證屬性測試
    - **Property 19: Input Validation Prevents Injection**
    - **Validates: Requirements 18.2, 18.3**
    - 驗證 Pydantic 正確驗證和清理輸入

- [ ] 7. Phase 5: Token 管理
  - [ ] 7.1 實作 Token 刷新端點
    - 在 `app/api/auth.py` 中實作 `POST /api/auth/refresh` 端點
    - 使用 `get_current_user` Dependency 驗證當前 Token
    - 生成新的 JWT Token
    - 將舊 Token 加入黑名單
    - 設定新 Token 為 Cookie
    - 返回新 Token JSON
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ] 7.2 撰寫 Token 刷新屬性測試
    - **Property 14: Token Refresh Invalidates Old Token**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.6, 13.7**
    - 驗證刷新後舊 Token 被撤銷

  - [ ] 7.3 實作登出端點
    - 在 `app/api/auth.py` 中實作 `POST /api/auth/logout` 端點
    - 使用 `get_current_user` Dependency 驗證當前 Token
    - 將 Token 加入黑名單
    - 清除 Cookie（設定 max_age=0）
    - 返回成功訊息
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [ ] 7.4 撰寫登出屬性測試
    - **Property 15: Logout Revokes Token**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.5, 14.6**
    - 驗證登出後 Token 被撤銷

  - [ ] 7.5 實作黑名單清理背景任務
    - 在 `app/tasks/scheduler.py` 中加入黑名單清理任務
    - 定期執行 `TokenBlacklist.cleanup_expired()`
    - 解碼所有黑名單中的 Token，移除已過期的
    - 設定執行頻率（例如每小時）
    - _Requirements: 13.6, 14.3_

- [ ] 8. Phase 6: 測試與文件
  - [ ] 8.1 撰寫認證流程整合測試
    - 測試完整的 OAuth2 登入流程（使用 Mock Discord API）
    - 測試 Token 刷新流程
    - 測試登出流程
    - 測試錯誤處理路徑
    - _Requirements: 1.*, 2.*, 3.*, 12.*, 13.*, 14.*_

  - [ ] 8.2 撰寫 API 端點整合測試
    - 測試 /api/feeds 端點（包含認證）
    - 測試 /api/subscriptions/toggle 端點
    - 測試 /api/articles/me 端點（包含分頁）
    - 測試未認證請求被拒絕
    - _Requirements: 6.*, 7.*, 8.*, 9.*_

  - [ ] 8.3 完善 OpenAPI 文件
    - 為所有端點加入詳細描述
    - 加入請求和回應範例
    - 標記需要認證的端點
    - 加入錯誤回應範例
    - 測試 /docs 和 /redoc 端點
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [ ] 8.4 執行所有屬性測試
    - 執行所有 20 個屬性測試
    - 確保每個測試至少執行 100 次迭代
    - 驗證所有屬性都通過

- [ ] 9. Phase 7: 健康檢查與監控
  - [ ] 9.1 擴展健康檢查端點
    - 在 `app/main.py` 中擴展 `/health` 端點
    - 加入 OAuth2 配置檢查（client_id, client_secret, redirect_uri）
    - 加入 JWT 配置檢查（JWT_SECRET 存在且長度 >= 32）
    - 加入資料庫連線檢查（使用現有邏輯）
    - 返回各服務的健康狀態
    - 當任何服務不健康時返回 503
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

  - [ ] 9.2 撰寫健康檢查屬性測試
    - **Property 20: Health Check Configuration Validation**
    - **Validates: Requirements 20.1, 20.2, 20.3, 20.4**
    - 驗證健康檢查正確報告各服務狀態

  - [ ] 9.3 實作結構化日誌記錄
    - 在 `app/main.py` 中配置日誌格式
    - 記錄所有 API 請求（method, path, user_id）
    - 記錄所有認證事件
    - 記錄所有錯誤（包含上下文和 stack trace）
    - 過濾敏感資訊（Token, 密碼, API Keys）
    - 加入請求 ID 追蹤
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8_

  - [ ] 9.4 在 main.py 中註冊所有路由
    - 使用 `app.include_router()` 註冊 auth.router
    - 註冊 feeds.router
    - 註冊 articles.router
    - 設定適當的 prefix 和 tags
    - 確保所有 Middleware 正確配置

  - [ ] 9.5 更新 requirements.txt
    - 加入 python-jose[cryptography]==3.3.0
    - 加入 httpx==0.27.0
    - 加入 slowapi==0.1.9
    - 確認現有套件版本

  - [ ] 9.6 建立 .env.example 範本
    - 加入所有新的環境變數
    - 提供範例值和說明
    - 標記必要和可選的變數

- [ ] 10. Final Checkpoint - 完整測試
  - 執行所有單元測試和屬性測試
  - 測試完整的使用者流程（登入 → 查詢 feeds → 訂閱 → 查詢文章 → 登出）
  - 驗證所有 API 文件正確顯示
  - 確認健康檢查端點正常運作
  - 詢問使用者是否有問題或需要調整

## Notes

- 標記 `*` 的任務為可選測試任務，可跳過以加快 MVP 開發
- 每個任務都明確引用對應的需求編號，確保可追溯性
- Checkpoint 任務確保階段性驗證，及早發現問題
- 屬性測試使用 Hypothesis 框架，每個測試至少執行 100 次迭代
- 所有 API 端點都使用 `get_current_user` Dependency 保護
- 安全性是首要考量，包含多層防護措施
