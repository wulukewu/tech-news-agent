# Requirements Document: Web Dashboard Frontend

## Introduction

本文件定義 Tech News Agent 專案 Phase 6 的需求：Web Dashboard Frontend（網頁控制台前端）。此階段將建立一個基於 Next.js 的現代化 Web 前端應用，讓使用者能夠透過瀏覽器更直覺地管理大量訂閱源、瀏覽專屬文章動態與閱讀清單。

Phase 1-4 已建立完整的多租戶資料庫架構、資料存取層、背景排程器和 Discord Bot 互動介面。Phase 5 已完成 FastAPI 後端的 Discord OAuth2 登入流程、JWT 認證機制，以及個人化的 Web API 端點。Phase 6 將建立與這些 API 對接的 Web 前端，提供與 Discord Bot 功能對等但更適合桌面瀏覽的使用者體驗。
ff
核心功能：

1. Discord OAuth2 登入整合：實作「Login with Discord」按鈕，對接 FastAPI 的認證流程
2. 全域狀態管理：管理使用者登入狀態、個人資訊與 JWT Token
3. 訂閱管理介面：顯示所有 RSS 來源卡片，支援即時訂閱切換
4. 個人專屬文章動態：顯示基於使用者訂閱源的文章列表，支援分頁與篩選
5. 閱讀清單管理：同步顯示使用者的閱讀清單，提供標記已讀與評分功能
6. 響應式設計：支援桌面和行動裝置

## Glossary

- **Next.js**: React 框架，支援 Server-Side Rendering 和 App Router
- **App_Router**: Next.js 14+ 的路由系統，基於檔案系統的路由
- **TailwindCSS**: Utility-first CSS 框架
- **shadcn/ui**: 基於 Radix UI 的可組合 UI 元件庫
- **React_Context**: React 的狀態管理機制，用於全域狀態共享
- **JWT_Token**: JSON Web Token，用於 API 認證
- **HttpOnly_Cookie**: 只能透過 HTTP 傳輸的 Cookie，由後端設置
- **Feed_Card**: 顯示單個 RSS 來源的卡片元件
- **Article_Card**: 顯示單篇文章的卡片元件
- **Subscription_Toggle**: 訂閱切換開關元件
- **Infinite_Scroll**: 無限滾動載入機制
- **Responsive_Design**: 響應式設計，適應不同螢幕尺寸
- **Loading_State**: 載入狀態，顯示資料正在載入中
- **Error_Boundary**: React 錯誤邊界，捕捉並處理元件錯誤
- **API_Client**: 封裝 API 呼叫的客戶端模組

## Requirements

### Requirement 1: Next.js 專案初始化

**User Story:** 作為開發者，我希望建立一個 Next.js 14+ 專案，使用 App Router 和 TypeScript

#### Acceptance Criteria

1. THE System SHALL initialize a Next.js project using version 14 or higher
2. THE System SHALL use the App Router architecture (not Pages Router)
3. THE System SHALL use TypeScript as the primary language
4. THE System SHALL configure TailwindCSS for styling
5. THE System SHALL integrate shadcn/ui component library
6. THE System SHALL create a project structure with app/, components/, lib/, and types/ directories
7. THE System SHALL configure environment variables for API base URL and other settings

### Requirement 2: 環境變數配置

**User Story:** 作為開發者,我需要配置環境變數以連接 FastAPI 後端

#### Acceptance Criteria

1. THE System SHALL define NEXT_PUBLIC_API_BASE_URL environment variable for the FastAPI backend URL
2. THE System SHALL define NEXT_PUBLIC_APP_URL environment variable for the frontend URL
3. THE System SHALL provide .env.example file with example values
4. THE System SHALL validate required environment variables on application startup
5. WHEN environment variables are missing, THE System SHALL display an error message
6. THE System SHALL support different configurations for development and production environments

### Requirement 3: Discord OAuth2 登入頁面

**User Story:** 作為使用者，我希望看到一個登入頁面，能夠點擊「Login with Discord」按鈕進行登入

#### Acceptance Criteria

1. THE System SHALL provide a login page at the root path "/"
2. THE login page SHALL display a "Login with Discord" button
3. THE button SHALL use Discord brand colors and icon
4. WHEN a user clicks the button, THE System SHALL redirect to the FastAPI login endpoint (/api/auth/discord/login)
5. THE login page SHALL display the application name and description
6. THE login page SHALL be responsive and work on mobile devices
7. WHEN a user is already logged in, THE System SHALL redirect from the login page to the dashboard

### Requirement 4: OAuth2 Callback 處理

**User Story:** 作為系統，我需要處理 Discord OAuth2 callback 並儲存認證狀態

#### Acceptance Criteria

1. THE System SHALL provide a callback page at "/auth/callback"
2. WHEN Discord redirects back with authorization, THE System SHALL extract the JWT Token from the response
3. THE System SHALL store the user information in global state
4. THE System SHALL redirect the user to the dashboard page after successful authentication
5. WHEN authentication fails, THE System SHALL display an error message and provide a retry button
6. THE System SHALL handle the case where the user denies authorization
7. THE callback page SHALL display a loading indicator while processing authentication

### Requirement 5: 全域認證狀態管理

**User Story:** 作為開發者，我需要一個全域狀態管理系統來管理使用者認證狀態

#### Acceptance Criteria

1. THE System SHALL implement a React Context for authentication state management
2. THE authentication context SHALL store: isAuthenticated (boolean), user (user object or null), loading (boolean)
3. THE System SHALL provide a useAuth hook for components to access authentication state
4. THE System SHALL provide login, logout, and checkAuth functions in the context
5. THE checkAuth function SHALL verify the JWT Token validity by calling a backend endpoint
6. WHEN the Token is invalid or expired, THE System SHALL set isAuthenticated to false
7. THE System SHALL persist authentication state across page refreshes by checking for HttpOnly Cookie
8. THE System SHALL provide a loading state while checking authentication

### Requirement 6: 受保護路由機制

**User Story:** 作為開發者，我需要保護需要認證的頁面，未登入使用者應被重導向至登入頁

#### Acceptance Criteria

1. THE System SHALL implement a ProtectedRoute component or middleware
2. THE ProtectedRoute SHALL check if the user is authenticated before rendering protected pages
3. WHEN a user is not authenticated, THE System SHALL redirect to the login page
4. THE System SHALL preserve the intended destination URL and redirect back after login
5. THE System SHALL display a loading indicator while checking authentication status
6. THE System SHALL protect the following routes: /dashboard, /subscriptions, /articles, /reading-list
7. THE login page and callback page SHALL be accessible without authentication

### Requirement 7: API 客戶端模組

**User Story:** 作為開發者，我需要一個封裝的 API 客戶端來呼叫 FastAPI 後端

#### Acceptance Criteria

1. THE System SHALL provide an API client module with functions for all backend endpoints
2. THE API client SHALL automatically include credentials (cookies) in all requests
3. THE API client SHALL handle CORS configuration
4. THE API client SHALL provide error handling for network failures and HTTP errors
5. THE API client SHALL provide the following functions: fetchFeeds(), toggleSubscription(feedId), fetchMyArticles(page, pageSize), fetchReadingList()
6. WHEN an API call returns 401 Unauthorized, THE API client SHALL trigger a logout action
7. THE API client SHALL use the NEXT_PUBLIC_API_BASE_URL environment variable for the base URL
8. THE API client SHALL set appropriate headers including Content-Type: application/json

### Requirement 8: 訂閱管理頁面

**User Story:** 作為使用者，我希望看到所有可用的 RSS 來源，並能夠訂閱或取消訂閱

#### Acceptance Criteria

1. THE System SHALL provide a subscriptions page at "/subscriptions"
2. THE page SHALL fetch all feeds from GET /api/feeds endpoint
3. THE page SHALL display feeds as cards in a grid layout
4. EACH feed card SHALL display: feed name, category, URL, and subscription status
5. EACH feed card SHALL include a toggle switch or checkbox for subscription control
6. WHEN a user toggles a subscription, THE System SHALL call POST /api/subscriptions/toggle
7. THE System SHALL update the UI immediately to reflect the new subscription status (optimistic update)
8. WHEN the API call fails, THE System SHALL revert the UI change and display an error message
9. THE page SHALL provide a search input to filter feeds by name or category
10. THE page SHALL provide category filter buttons to show feeds from specific categories
11. THE page SHALL display a loading skeleton while fetching feeds
12. THE page SHALL handle the case where no feeds are available

### Requirement 9: Feed 卡片元件

**User Story:** 作為開發者，我需要一個可重用的 Feed 卡片元件來顯示 RSS 來源資訊

#### Acceptance Criteria

1. THE System SHALL provide a FeedCard component
2. THE component SHALL accept props: id, name, url, category, isSubscribed, onToggle
3. THE component SHALL display the feed name as a heading
4. THE component SHALL display the category as a badge or tag
5. THE component SHALL display the URL as a clickable link that opens in a new tab
6. THE component SHALL include a subscription toggle switch
7. WHEN the toggle is clicked, THE component SHALL call the onToggle callback with the feed ID
8. THE component SHALL display a loading state on the toggle while the API call is in progress
9. THE component SHALL use different visual styles for subscribed vs unsubscribed feeds
10. THE component SHALL be responsive and work on mobile devices

### Requirement 10: 個人文章動態頁面

**User Story:** 作為使用者，我希望看到基於我訂閱源的個人化文章列表

#### Acceptance Criteria

1. THE System SHALL provide an articles page at "/articles" or "/dashboard"
2. THE page SHALL fetch articles from GET /api/articles/me endpoint
3. THE page SHALL display articles as cards in a list or grid layout
4. EACH article card SHALL display: title, feed name, category, published date, tinkering index, and AI summary
5. THE article title SHALL be a clickable link that opens the article URL in a new tab
6. THE page SHALL display the tinkering index as a visual indicator (e.g., stars or badges)
7. THE page SHALL support pagination with "Load More" button or infinite scroll
8. WHEN a user scrolls to the bottom, THE System SHALL automatically load the next page of articles
9. THE page SHALL display a loading indicator while fetching articles
10. WHEN the user has no subscriptions, THE page SHALL display a message prompting them to subscribe to feeds
11. WHEN there are no articles, THE page SHALL display an appropriate empty state message
12. THE page SHALL provide filter options for category and tinkering index

### Requirement 11: Article 卡片元件

**User Story:** 作為開發者，我需要一個可重用的 Article 卡片元件來顯示文章資訊

#### Acceptance Criteria

1. THE System SHALL provide an ArticleCard component
2. THE component SHALL accept props: id, title, url, feedName, category, publishedAt, tinkeringIndex, aiSummary
3. THE component SHALL display the article title as a clickable heading
4. THE component SHALL display the feed name and category as metadata
5. THE component SHALL display the published date in a human-readable format (e.g., "2 days ago")
6. THE component SHALL display the tinkering index as a visual rating (1-5 scale)
7. THE component SHALL display the AI summary with a "Read More" expansion if the text is long
8. THE component SHALL include an "Add to Reading List" button
9. WHEN the "Add to Reading List" button is clicked, THE component SHALL call the appropriate API endpoint
10. THE component SHALL provide visual feedback when the article is added to the reading list
11. THE component SHALL be responsive and work on mobile devices

### Requirement 12: 無限滾動實作

**User Story:** 作為使用者，我希望在滾動到頁面底部時自動載入更多文章

#### Acceptance Criteria

1. THE System SHALL implement infinite scroll for the articles page
2. THE System SHALL detect when the user scrolls near the bottom of the page (e.g., within 200px)
3. WHEN the user reaches the scroll threshold, THE System SHALL fetch the next page of articles
4. THE System SHALL append new articles to the existing list without replacing them
5. THE System SHALL prevent duplicate API calls while a fetch is in progress
6. THE System SHALL display a loading indicator at the bottom while fetching more articles
7. WHEN there are no more articles to load, THE System SHALL display an "End of list" message
8. THE System SHALL handle errors gracefully and allow the user to retry loading more articles

### Requirement 13: 閱讀清單頁面

**User Story:** 作為使用者，我希望查看我的閱讀清單，並能標記文章為已讀或評分

#### Acceptance Criteria

1. THE System SHALL provide a reading list page at "/reading-list"
2. THE page SHALL fetch the reading list from a backend endpoint (to be implemented in Phase 5.5)
3. THE page SHALL display articles in the reading list with their current status (Unread, Read, Archived)
4. EACH article SHALL include a "Mark as Read" button
5. EACH article SHALL include a rating selector (1-5 stars)
6. WHEN a user marks an article as read, THE System SHALL call the appropriate API endpoint
7. WHEN a user rates an article, THE System SHALL call the appropriate API endpoint
8. THE System SHALL update the UI immediately to reflect changes (optimistic update)
9. THE page SHALL provide filter tabs for Unread, Read, and Archived articles
10. THE page SHALL display a loading skeleton while fetching the reading list
11. WHEN the reading list is empty, THE page SHALL display an appropriate empty state message

### Requirement 14: 導航列元件

**User Story:** 作為使用者，我希望有一個導航列來在不同頁面間切換

#### Acceptance Criteria

1. THE System SHALL provide a navigation bar component displayed on all authenticated pages
2. THE navigation bar SHALL include links to: Dashboard/Articles, Subscriptions, Reading List
3. THE navigation bar SHALL display the user's Discord username and avatar
4. THE navigation bar SHALL include a logout button
5. WHEN the logout button is clicked, THE System SHALL call the logout API endpoint and clear authentication state
6. THE navigation bar SHALL highlight the current active page
7. THE navigation bar SHALL be responsive and collapse to a hamburger menu on mobile devices
8. THE navigation bar SHALL display the application logo or name

### Requirement 15: 載入狀態處理

**User Story:** 作為使用者，我希望在資料載入時看到適當的載入指示器

#### Acceptance Criteria

1. THE System SHALL display loading skeletons for feed cards while fetching feeds
2. THE System SHALL display loading skeletons for article cards while fetching articles
3. THE System SHALL display a spinner or progress indicator for button actions (e.g., toggle subscription)
4. THE System SHALL display a full-page loading indicator during authentication checks
5. THE loading indicators SHALL match the layout of the actual content
6. THE System SHALL use skeleton screens instead of spinners for better perceived performance
7. THE loading states SHALL be accessible and announce to screen readers

### Requirement 16: 錯誤處理與顯示

**User Story:** 作為使用者，我希望在發生錯誤時看到清楚的錯誤訊息

#### Acceptance Criteria

1. THE System SHALL display user-friendly error messages for API failures
2. THE System SHALL provide a retry button for failed operations
3. THE System SHALL implement an Error Boundary to catch React component errors
4. WHEN a network error occurs, THE System SHALL display a message indicating connection issues
5. WHEN a 401 error occurs, THE System SHALL redirect to the login page
6. WHEN a 404 error occurs, THE System SHALL display a "Not Found" page
7. THE System SHALL display validation errors for form inputs
8. THE error messages SHALL be displayed using toast notifications or inline alerts
9. THE System SHALL log errors to the console for debugging purposes

### Requirement 17: 響應式設計

**User Story:** 作為使用者，我希望網站在桌面和行動裝置上都能正常使用

#### Acceptance Criteria

1. THE System SHALL implement responsive design using TailwindCSS breakpoints
2. THE layout SHALL adapt to screen sizes: mobile (<640px), tablet (640px-1024px), desktop (>1024px)
3. THE feed cards SHALL display in a single column on mobile, 2 columns on tablet, and 3-4 columns on desktop
4. THE article cards SHALL display in a single column on mobile and 2 columns on desktop
5. THE navigation bar SHALL collapse to a hamburger menu on mobile devices
6. THE text sizes and spacing SHALL scale appropriately for different screen sizes
7. THE System SHALL be usable with touch gestures on mobile devices
8. THE System SHALL test on common mobile browsers (Safari, Chrome Mobile)

### Requirement 18: 搜尋與篩選功能

**User Story:** 作為使用者，我希望能夠搜尋和篩選訂閱源與文章

#### Acceptance Criteria

1. THE subscriptions page SHALL provide a search input to filter feeds by name
2. THE search SHALL be case-insensitive and match partial strings
3. THE search SHALL update results in real-time as the user types (debounced)
4. THE subscriptions page SHALL provide category filter buttons
5. WHEN a category filter is selected, THE System SHALL show only feeds from that category
6. THE articles page SHALL provide category filter buttons
7. THE articles page SHALL provide a tinkering index filter (e.g., show only 4-5 rated articles)
8. THE filters SHALL be combinable (e.g., category AND tinkering index)
9. THE System SHALL display the count of filtered results
10. THE System SHALL provide a "Clear Filters" button to reset all filters

### Requirement 19: 效能優化

**User Story:** 作為開發者，我需要優化應用效能以提供流暢的使用者體驗

#### Acceptance Criteria

1. THE System SHALL implement code splitting for different routes
2. THE System SHALL lazy load images using Next.js Image component
3. THE System SHALL implement debouncing for search inputs (300ms delay)
4. THE System SHALL implement throttling for scroll events (100ms delay)
5. THE System SHALL cache API responses using React Query or SWR
6. THE System SHALL implement optimistic updates for subscription toggles
7. THE System SHALL prefetch data for likely next actions (e.g., next page of articles)
8. THE System SHALL minimize bundle size by tree-shaking unused code
9. THE System SHALL achieve a Lighthouse performance score > 80

### Requirement 20: 可訪問性 (Accessibility)

**User Story:** 作為使用者，我希望網站符合可訪問性標準，能夠使用鍵盤和螢幕閱讀器

#### Acceptance Criteria

1. THE System SHALL provide proper semantic HTML elements (header, nav, main, article)
2. THE System SHALL provide alt text for all images
3. THE System SHALL provide ARIA labels for interactive elements without visible text
4. THE System SHALL support keyboard navigation for all interactive elements
5. THE System SHALL provide visible focus indicators for keyboard navigation
6. THE System SHALL ensure color contrast ratios meet WCAG AA standards (4.5:1 for normal text)
7. THE System SHALL announce dynamic content changes to screen readers using ARIA live regions
8. THE System SHALL provide skip links to jump to main content
9. THE System SHALL test with screen readers (NVDA, JAWS, or VoiceOver)

### Requirement 21: 深色模式支援

**User Story:** 作為使用者，我希望能夠切換深色模式以減少眼睛疲勞

#### Acceptance Criteria

1. THE System SHALL provide a theme toggle button in the navigation bar
2. THE System SHALL support light and dark color schemes
3. THE System SHALL persist the user's theme preference in localStorage
4. THE System SHALL respect the user's system theme preference on first visit
5. THE theme toggle SHALL smoothly transition between light and dark modes
6. THE System SHALL ensure all components are styled for both themes
7. THE System SHALL use TailwindCSS dark mode utilities for styling

### Requirement 22: 統計數據顯示

**User Story:** 作為使用者，我希望看到我的訂閱和閱讀統計數據

#### Acceptance Criteria

1. THE dashboard page SHALL display a statistics section
2. THE statistics SHALL include: total subscriptions count, total articles in feed, unread articles count, articles read this week
3. THE statistics SHALL be displayed as cards or badges
4. THE System SHALL fetch statistics from backend endpoints
5. THE statistics SHALL update in real-time when the user performs actions
6. THE statistics cards SHALL use visual indicators (icons, colors) to enhance readability

### Requirement 23: 文章分類標籤

**User Story:** 作為使用者，我希望看到文章的分類標籤，並能點擊篩選同類文章

#### Acceptance Criteria

1. EACH article card SHALL display the category as a clickable badge
2. WHEN a user clicks a category badge, THE System SHALL filter articles to show only that category
3. THE category badges SHALL use distinct colors for different categories
4. THE System SHALL display a list of all available categories
5. THE active category filter SHALL be visually highlighted

### Requirement 24: 閱讀進度追蹤

**User Story:** 作為使用者，我希望系統能追蹤我的閱讀進度

#### Acceptance Criteria

1. WHEN a user clicks an article link, THE System SHALL record the click event
2. THE System SHALL mark the article as "viewed" in the backend
3. THE article card SHALL display a visual indicator for viewed articles (e.g., dimmed or marked)
4. THE System SHALL provide a "Mark all as read" button on the articles page
5. THE reading list SHALL show reading progress (e.g., "5 of 20 articles read")

### Requirement 25: 匯出與分享功能

**User Story:** 作為使用者，我希望能夠匯出我的閱讀清單或分享文章

#### Acceptance Criteria

1. THE reading list page SHALL provide an "Export" button
2. THE export function SHALL generate a JSON or CSV file with the reading list
3. EACH article card SHALL include a "Share" button
4. THE share button SHALL provide options to copy the article URL or share via social media
5. THE System SHALL use the Web Share API when available on mobile devices

### Requirement 26: 通知與提示

**User Story:** 作為使用者，我希望收到操作成功或失敗的即時反饋

#### Acceptance Criteria

1. THE System SHALL display toast notifications for successful operations (e.g., "Subscribed successfully")
2. THE System SHALL display toast notifications for failed operations with error details
3. THE notifications SHALL auto-dismiss after 3-5 seconds
4. THE notifications SHALL be dismissible by clicking a close button
5. THE System SHALL stack multiple notifications vertically
6. THE notifications SHALL be accessible and announced to screen readers

### Requirement 27: 離線支援 (Progressive Web App)

**User Story:** 作為使用者，我希望在網路不穩定時仍能瀏覽已載入的內容

#### Acceptance Criteria

1. THE System SHALL implement a service worker for offline caching
2. THE System SHALL cache static assets (CSS, JS, images)
3. THE System SHALL cache previously loaded articles for offline viewing
4. WHEN the user is offline, THE System SHALL display a banner indicating offline mode
5. THE System SHALL queue write operations (e.g., toggle subscription) and sync when back online
6. THE System SHALL provide a manifest.json for PWA installation
7. THE System SHALL be installable as a PWA on mobile devices

### Requirement 28: 效能監控

**User Story:** 作為開發者，我需要監控前端效能以識別瓶頸

#### Acceptance Criteria

1. THE System SHALL integrate Web Vitals monitoring
2. THE System SHALL track Core Web Vitals: LCP, FID, CLS
3. THE System SHALL log performance metrics to the console in development mode
4. THE System SHALL send performance metrics to an analytics service in production (optional)
5. THE System SHALL provide a performance budget and alert when exceeded

### Requirement 29: 測試覆蓋

**User Story:** 作為開發者，我需要撰寫測試以確保程式碼品質

#### Acceptance Criteria

1. THE System SHALL use Jest and React Testing Library for unit tests
2. THE System SHALL test all major components (FeedCard, ArticleCard, Navigation)
3. THE System SHALL test API client functions with mocked responses
4. THE System SHALL test authentication flows with integration tests
5. THE System SHALL achieve at least 70% code coverage
6. THE System SHALL use Playwright or Cypress for end-to-end tests
7. THE System SHALL test responsive behavior on different screen sizes

### Requirement 30: 部署配置

**User Story:** 作為開發者，我需要配置部署流程以將應用部署到生產環境

#### Acceptance Criteria

1. THE System SHALL provide a Dockerfile for containerized deployment
2. THE System SHALL configure Next.js for static export or server-side rendering
3. THE System SHALL provide deployment scripts for Vercel, Netlify, or Docker
4. THE System SHALL configure environment variables for production
5. THE System SHALL implement health check endpoints
6. THE System SHALL configure CORS to allow requests from the production domain
7. THE System SHALL use HTTPS in production
8. THE System SHALL implement security headers (CSP, HSTS, X-Frame-Options)
