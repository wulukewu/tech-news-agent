# Requirements Document

## Introduction

本文件定義技術新聞訂閱工具的新用戶引導系統（New User Onboarding System）需求。此系統旨在改善首次使用體驗，幫助新用戶快速理解平台功能並完成初始設定，包含網頁介面和 Discord Bot 兩個管道的引導流程。

## Glossary

- **Onboarding_System**: 新用戶引導系統，包含首次登入引導、互動式教學、進度追蹤等功能
- **Web_Interface**: Next.js + React 建構的網頁介面，用戶可透過瀏覽器存取
- **Discord_Bot**: Discord 機器人介面，用戶可透過 Discord 指令互動
- **Dashboard**: 網頁介面的主要文章瀏覽頁面
- **Subscription_Page**: 網頁介面的訂閱管理頁面
- **Empty_State**: 當頁面沒有內容時顯示的狀態畫面
- **CTA**: Call-to-Action，引導用戶執行特定動作的按鈕或連結
- **Onboarding_Progress**: 用戶完成引導流程的進度狀態
- **Recommended_Feeds**: 系統推薦給新用戶的預設 RSS 來源清單
- **Scheduler_Status**: 背景排程器的執行狀態資訊
- **User_Preferences**: 用戶的個人化設定，包含已完成的引導步驟

## Requirements

### Requirement 1: 網頁端首次登入引導流程

**User Story:** 作為新用戶，我希望首次登入後能看到清楚的引導流程，讓我知道如何開始使用平台。

#### Acceptance Criteria

1. WHEN a user logs in for the first time, THE Onboarding_System SHALL display a welcome modal with platform introduction
2. THE Welcome_Modal SHALL include a "開始使用" button to start the onboarding flow
3. WHEN the user clicks "開始使用", THE Onboarding_System SHALL navigate to the subscription recommendation step
4. THE Onboarding_System SHALL track onboarding progress in User_Preferences table
5. WHEN the user completes all onboarding steps, THE Onboarding_System SHALL mark onboarding as completed
6. THE Onboarding_System SHALL allow users to skip onboarding with a "稍後再說" option
7. WHEN the user skips onboarding, THE Onboarding_System SHALL store the skip status and not show the modal again unless user manually triggers it

### Requirement 2: 推薦訂閱來源選擇

**User Story:** 作為新用戶，我希望系統能推薦一些優質的 RSS 來源，讓我不需要自己尋找就能快速開始。

#### Acceptance Criteria

1. THE Onboarding_System SHALL provide a curated list of Recommended_Feeds grouped by category
2. THE Recommended_Feeds SHALL include at least 3 categories (AI, Web Development, Security)
3. WHEN displaying Recommended_Feeds, THE Onboarding_System SHALL show feed name, description, and category
4. THE Onboarding_System SHALL allow users to select multiple feeds with checkboxes
5. THE Onboarding_System SHALL pre-select 3-5 popular feeds as default recommendations
6. WHEN the user confirms feed selection, THE Onboarding_System SHALL subscribe the user to selected feeds
7. THE Onboarding_System SHALL display a success message showing the number of subscribed feeds

### Requirement 3: Dashboard 空狀態改善

**User Story:** 作為新用戶，當我的 Dashboard 沒有文章時，我希望看到明確的指引告訴我該做什麼。

#### Acceptance Criteria

1. WHEN Dashboard has no articles, THE Web_Interface SHALL display an Empty_State component
2. THE Empty_State SHALL include a clear heading "還沒有文章"
3. THE Empty_State SHALL explain why there are no articles (no subscriptions or scheduler not run yet)
4. THE Empty_State SHALL include a primary CTA button "管理訂閱" linking to Subscription_Page
5. THE Empty_State SHALL include a secondary CTA button "手動觸發抓取" to trigger the scheduler
6. THE Empty_State SHALL display an illustration or icon to make it visually appealing
7. WHEN the user has subscriptions but no articles, THE Empty_State SHALL show Scheduler_Status information

### Requirement 4: 訂閱頁面資訊分層

**User Story:** 作為新用戶，我希望訂閱頁面不要一次顯示所有來源，而是能按分類瀏覽，並看到推薦標記。

#### Acceptance Criteria

1. THE Subscription_Page SHALL display feeds grouped by category with collapsible sections
2. THE Subscription_Page SHALL mark recommended feeds with a "推薦" badge
3. THE Subscription_Page SHALL show recommended categories expanded by default
4. THE Subscription_Page SHALL show non-recommended categories collapsed by default
5. WHEN a category is collapsed, THE Subscription_Page SHALL display the number of feeds in that category
6. THE Subscription_Page SHALL provide a "訂閱所有推薦" quick action button
7. THE Subscription_Page SHALL display subscription count at the top (e.g., "已訂閱 5/30 個來源")

### Requirement 5: 進度和狀態指示

**User Story:** 作為用戶，我希望知道背景排程器的狀態，以及訂閱後大約多久會有文章。

#### Acceptance Criteria

1. THE Web_Interface SHALL display Scheduler_Status in Dashboard header
2. THE Scheduler_Status SHALL show last execution time in user's timezone
3. THE Scheduler_Status SHALL show next scheduled execution time
4. WHEN scheduler is running, THE Scheduler_Status SHALL display a loading indicator
5. WHEN user triggers manual fetch, THE Web_Interface SHALL show a progress toast notification
6. THE Web_Interface SHALL display estimated time until articles appear (e.g., "預計 5-10 分鐘後會有新文章")
7. WHEN scheduler completes, THE Web_Interface SHALL show a success notification with article count

### Requirement 6: Discord Bot 首次使用引導

**User Story:** 作為 Discord 用戶，我希望第一次使用 Bot 時能看到清楚的指令說明和使用建議。

#### Acceptance Criteria

1. THE Discord_Bot SHALL provide a `/start` command for first-time users
2. WHEN a user executes `/start`, THE Discord_Bot SHALL send a welcome message with platform overview
3. THE Welcome_Message SHALL list available commands with brief descriptions
4. THE Welcome_Message SHALL include a "快速開始" section with recommended first steps
5. THE Welcome_Message SHALL provide Recommended_Feeds with quick subscribe buttons
6. THE Discord_Bot SHALL detect first-time command usage and automatically trigger `/start` guidance
7. WHEN a user executes any command for the first time, THE Discord_Bot SHALL include a hint about `/start` command

### Requirement 7: Discord Bot 指令說明改善

**User Story:** 作為 Discord 用戶，我希望每個指令都有清楚的說明和使用範例。

#### Acceptance Criteria

1. THE Discord_Bot SHALL provide a `/help` command listing all available commands
2. THE `/help` Command SHALL group commands by category (訂閱管理, 文章瀏覽, 閱讀清單)
3. THE `/help` Command SHALL show command syntax and parameter descriptions
4. THE `/help` Command SHALL include usage examples for each command
5. WHEN a command fails due to missing prerequisites, THE Discord_Bot SHALL suggest the next action
6. THE Discord_Bot SHALL provide contextual help in error messages
7. THE `/help` Command SHALL be ephemeral (only visible to the user who triggered it)

### Requirement 8: Discord Bot 錯誤訊息改善

**User Story:** 作為 Discord 用戶，當我遇到錯誤時，我希望看到友善的訊息和解決建議，而不是技術性錯誤。

#### Acceptance Criteria

1. WHEN a user executes `/news_now` without subscriptions, THE Discord_Bot SHALL explain why no articles are shown
2. THE Error_Message SHALL include a CTA button or command suggestion for next action
3. WHEN a user tries to use deep dive without articles, THE Discord_Bot SHALL suggest subscribing to feeds first
4. THE Discord_Bot SHALL replace technical error messages with user-friendly explanations
5. WHEN API quota is exceeded, THE Discord_Bot SHALL explain the limitation and suggest alternatives
6. THE Discord_Bot SHALL include estimated wait time in rate limit messages
7. WHEN database errors occur, THE Discord_Bot SHALL show a generic friendly message without exposing technical details

### Requirement 9: Discord Bot 互動元件說明

**User Story:** 作為 Discord 用戶，我希望按鈕和選單的功能更明確，並了解使用它們的影響。

#### Acceptance Criteria

1. THE Deep_Dive_Button SHALL include a tooltip or description explaining it uses API quota
2. THE Rating_Select SHALL include a description explaining how ratings affect recommendations
3. WHEN a user first clicks Deep_Dive_Button, THE Discord_Bot SHALL show a one-time explanation
4. THE Filter_Menu SHALL show the number of articles in each category
5. THE Read_Later_Button SHALL show feedback when article is successfully added
6. WHEN Reading_List is empty, THE Discord_Bot SHALL suggest using Read_Later buttons
7. THE Discord_Bot SHALL provide visual feedback for all button interactions within 2 seconds

### Requirement 10: 引導進度持久化

**User Story:** 作為用戶，我希望系統記住我已完成的引導步驟，不要重複顯示相同的提示。

#### Acceptance Criteria

1. THE Onboarding_System SHALL store onboarding progress in user_preferences table
2. THE User_Preferences SHALL include fields: onboarding_completed, onboarding_step, onboarding_skipped
3. WHEN a user completes an onboarding step, THE Onboarding_System SHALL update User_Preferences
4. THE Onboarding_System SHALL check User_Preferences before showing onboarding UI
5. WHEN onboarding_completed is true, THE Onboarding_System SHALL not show onboarding modals
6. THE Onboarding_System SHALL allow users to restart onboarding from settings page
7. WHEN a user restarts onboarding, THE Onboarding_System SHALL reset onboarding_completed to false

### Requirement 11: 互動式教學提示

**User Story:** 作為新用戶，我希望在使用關鍵功能時能看到簡短的提示，幫助我理解如何使用。

#### Acceptance Criteria

1. THE Web_Interface SHALL display tooltips for key UI elements on first visit
2. THE Tooltips SHALL appear sequentially with "下一步" and "跳過" buttons
3. THE Tooltips SHALL highlight the target element with a spotlight effect
4. THE Onboarding_System SHALL show tooltips for: subscription button, filter menu, trigger scheduler button
5. WHEN a user clicks "下一步", THE Onboarding_System SHALL move to the next tooltip
6. WHEN a user clicks "跳過", THE Onboarding_System SHALL dismiss all remaining tooltips
7. THE Onboarding_System SHALL not show tooltips again after user completes or skips them

### Requirement 12: 推薦來源資料管理

**User Story:** 作為系統管理員，我希望能輕鬆管理推薦給新用戶的 RSS 來源清單。

#### Acceptance Criteria

1. THE Onboarding_System SHALL read Recommended_Feeds from feeds table with is_recommended flag
2. THE Feeds_Table SHALL include an is_recommended boolean column
3. THE Feeds_Table SHALL include a recommendation_priority integer column for sorting
4. WHEN querying Recommended_Feeds, THE Onboarding_System SHALL order by recommendation_priority
5. THE Onboarding_System SHALL support at least 20 recommended feeds across all categories
6. THE Recommended_Feeds SHALL be configurable without code changes
7. WHEN a feed is marked as recommended, THE Onboarding_System SHALL immediately include it in recommendations

### Requirement 13: 多語言支援準備

**User Story:** 作為國際用戶，我希望未來能看到我的語言的引導內容。

#### Acceptance Criteria

1. THE Onboarding_System SHALL store all UI text in separate language files
2. THE Language_Files SHALL support Traditional Chinese (zh-TW) as default
3. THE Onboarding_System SHALL use i18n keys for all onboarding text
4. THE User_Preferences SHALL include a preferred_language field
5. WHEN displaying onboarding content, THE Onboarding_System SHALL use the user's preferred_language
6. THE Onboarding_System SHALL fall back to zh-TW if preferred_language is not available
7. THE Language_Files SHALL be structured to easily add new languages in the future

### Requirement 14: 分析和追蹤

**User Story:** 作為產品經理，我希望能追蹤用戶的引導完成率和流失點，以優化引導流程。

#### Acceptance Criteria

1. THE Onboarding_System SHALL log onboarding events to analytics table
2. THE Analytics_Events SHALL include: onboarding_started, step_completed, onboarding_skipped, onboarding_finished
3. THE Analytics_Events SHALL record timestamp, user_id, event_type, and event_data
4. WHEN a user skips onboarding, THE Onboarding_System SHALL log the step where they skipped
5. THE Onboarding_System SHALL track time spent on each onboarding step
6. THE Onboarding_System SHALL provide a dashboard view of onboarding completion rates
7. THE Analytics_Dashboard SHALL show drop-off rates at each onboarding step

### Requirement 15: 效能和載入優化

**User Story:** 作為用戶，我希望引導流程載入快速，不會影響我使用平台的體驗。

#### Acceptance Criteria

1. THE Onboarding_System SHALL lazy-load onboarding components to reduce initial bundle size
2. THE Welcome_Modal SHALL appear within 500ms of page load
3. THE Recommended_Feeds SHALL be cached in browser for 24 hours
4. WHEN loading Recommended_Feeds, THE Onboarding_System SHALL show a loading skeleton
5. THE Onboarding_System SHALL prefetch next step content while user is on current step
6. THE Tooltips SHALL use CSS animations for smooth transitions
7. THE Onboarding_System SHALL not block main thread during initialization
