# Design Document: New User Onboarding System

## Overview

本設計文件定義技術新聞訂閱工具的新用戶引導系統（New User Onboarding System）的技術架構與實作細節。此系統旨在改善首次使用體驗，透過網頁介面和 Discord Bot 兩個管道提供完整的引導流程。

### System Goals

1. **降低新用戶流失率**：透過清晰的引導流程，幫助新用戶快速理解平台價值
2. **加速用戶啟動**：提供推薦訂閱來源，讓用戶無需自行尋找即可開始使用
3. **提升用戶體驗**：改善空狀態顯示，提供明確的下一步指引
4. **增強可觀測性**：追蹤引導完成率和流失點，支援持續優化

### Key Features

- **網頁端首次登入引導**：歡迎 Modal、推薦訂閱來源選擇、進度追蹤
- **Discord Bot 引導**：`/start` 指令、改善的 `/help` 指令、友善的錯誤訊息
- **空狀態改善**：Dashboard 和訂閱頁面的空狀態設計
- **進度持久化**：記錄用戶完成的引導步驟，避免重複顯示
- **互動式教學**：Tooltip 系統引導用戶使用關鍵功能
- **分析追蹤**：記錄引導事件，支援數據驅動的優化

### Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.11+
- **Database**: Supabase (PostgreSQL with pgvector)
- **Discord**: discord.py 2.0+
- **State Management**: React Context API
- **UI Components**: shadcn/ui, Lucide Icons

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├──────────────────────────────┬──────────────────────────────────┤
│      Web Interface           │       Discord Bot                │
│  (Next.js + React)           │     (discord.py)                 │
│                              │                                  │
│  - Onboarding Modal          │  - /start Command                │
│  - Empty States              │  - /help Command                 │
│  - Tooltip Tour              │  - Enhanced Error Messages       │
│  - Subscription Page         │  - Interactive Buttons           │
└──────────────┬───────────────┴────────────┬─────────────────────┘
               │                            │
               │         REST API           │
               │    (FastAPI Backend)       │
               │                            │
               ├────────────────────────────┤
               │                            │
               │   Onboarding Service       │
               │   - Progress Tracking      │
               │   - Recommendation Engine  │
               │   - Analytics Logger       │
               │                            │
               └────────────┬───────────────┘
                            │
                    ┌───────┴────────┐
                    │   Supabase     │
                    │  (PostgreSQL)  │
                    │                │
                    │  - users       │
                    │  - feeds       │
                    │  - user_prefs  │
                    │  - analytics   │
                    └────────────────┘
```

### Component Interaction Flow

#### Web Onboarding Flow

```
User Login → Check user_preferences.onboarding_completed
    │
    ├─ If false → Show Welcome Modal
    │              │
    │              ├─ User clicks "開始使用"
    │              │   │
    │              │   └─ Navigate to Subscription Recommendation
    │              │       │
    │              │       ├─ Display Recommended Feeds (grouped by category)
    │              │       │
    │              │       ├─ User selects feeds
    │              │       │
    │              │       └─ Subscribe & Mark onboarding_completed = true
    │              │
    │              └─ User clicks "稍後再說"
    │                  │
    │                  └─ Set onboarding_skipped = true
    │
    └─ If true → Show Dashboard
        │
        ├─ If no articles → Show Empty State
        │   │
        │   ├─ CTA: "管理訂閱" → Subscription Page
        │   │
        │   └─ CTA: "手動觸發抓取" → Trigger Scheduler
        │
        └─ If has articles → Show Article List
```

#### Discord Onboarding Flow

```
User executes any command for first time
    │
    └─ Check if first-time user
        │
        ├─ If yes → Auto-trigger /start guidance
        │   │
        │   ├─ Show welcome message
        │   │
        │   ├─ List available commands
        │   │
        │   └─ Show recommended feeds with quick subscribe buttons
        │
        └─ If no → Execute command normally
            │
            └─ If error occurs → Show friendly error message
                │
                ├─ Explain why error occurred
                │
                └─ Suggest next action (CTA)
```

### Data Flow

1. **User Registration**
   - Web: OAuth callback → Create user → Check onboarding status
   - Discord: First command → Create user → Auto-trigger /start

2. **Onboarding Progress**
   - Frontend/Bot → API → Update user_preferences
   - API → Query user_preferences → Return onboarding state

3. **Recommendation Engine**
   - API → Query feeds WHERE is_recommended = true
   - Sort by recommendation_priority
   - Return grouped by category

4. **Analytics Tracking**
   - Frontend/Bot → API → Insert analytics_events
   - Background job → Aggregate analytics → Generate reports

---

## Components and Interfaces

### Frontend Components

#### 1. OnboardingModal Component

**Purpose**: 首次登入時顯示的歡迎 Modal

**Props**:

```typescript
interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: () => void;
  onSkip: () => void;
}
```

**State**:

```typescript
interface OnboardingModalState {
  currentStep: 'welcome' | 'recommendations' | 'complete';
  selectedFeeds: UUID[];
  isLoading: boolean;
}
```

**Key Methods**:

- `handleStart()`: 開始引導流程
- `handleSkip()`: 跳過引導
- `handleFeedSelection(feedId: UUID)`: 選擇/取消選擇 Feed
- `handleComplete()`: 完成引導並訂閱選擇的 Feeds

#### 2. EmptyState Component

**Purpose**: 當頁面沒有內容時顯示的狀態畫面

**Props**:

```typescript
interface EmptyStateProps {
  type: 'no-subscriptions' | 'no-articles' | 'no-reading-list';
  title: string;
  description: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  schedulerStatus?: SchedulerStatus;
}
```

**Variants**:

- `NoSubscriptionsEmpty`: 沒有訂閱時顯示
- `NoArticlesEmpty`: 有訂閱但沒有文章時顯示
- `NoReadingListEmpty`: 閱讀清單為空時顯示

#### 3. TooltipTour Component

**Purpose**: 互動式教學提示系統

**Props**:

```typescript
interface TooltipTourProps {
  steps: TooltipStep[];
  isActive: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

interface TooltipStep {
  target: string; // CSS selector
  title: string;
  content: string;
  placement: 'top' | 'bottom' | 'left' | 'right';
  highlightPadding?: number;
}
```

**State**:

```typescript
interface TooltipTourState {
  currentStepIndex: number;
  isVisible: boolean;
}
```

**Key Methods**:

- `nextStep()`: 前往下一個提示
- `previousStep()`: 返回上一個提示
- `skipTour()`: 跳過所有提示
- `completeTour()`: 完成教學

#### 4. SubscriptionPage Component

**Purpose**: 訂閱管理頁面，支援分類瀏覽和推薦標記

**State**:

```typescript
interface SubscriptionPageState {
  feeds: FeedWithSubscription[];
  groupedFeeds: Map<string, FeedWithSubscription[]>;
  collapsedCategories: Set<string>;
  isLoading: boolean;
}

interface FeedWithSubscription {
  id: UUID;
  name: string;
  url: string;
  category: string;
  isRecommended: boolean;
  isSubscribed: boolean;
  recommendationPriority: number;
}
```

**Key Methods**:

- `toggleCategory(category: string)`: 展開/收合分類
- `toggleSubscription(feedId: UUID)`: 訂閱/取消訂閱
- `subscribeToAllRecommended()`: 訂閱所有推薦來源

#### 5. SchedulerStatusIndicator Component

**Purpose**: 顯示背景排程器狀態

**Props**:

```typescript
interface SchedulerStatusIndicatorProps {
  status: SchedulerStatus;
  onTrigger?: () => void;
}

interface SchedulerStatus {
  lastExecutionTime: Date | null;
  nextScheduledTime: Date | null;
  isRunning: boolean;
  lastExecutionArticleCount: number;
  estimatedTimeUntilArticles: string; // e.g., "5-10 分鐘"
}
```

### Backend Services

#### 1. OnboardingService

**Purpose**: 管理引導流程和進度追蹤

**Methods**:

```python
class OnboardingService:
    async def get_onboarding_status(self, user_id: UUID) -> OnboardingStatus
    async def update_onboarding_progress(
        self,
        user_id: UUID,
        step: str,
        completed: bool
    ) -> None
    async def mark_onboarding_completed(self, user_id: UUID) -> None
    async def mark_onboarding_skipped(self, user_id: UUID) -> None
    async def reset_onboarding(self, user_id: UUID) -> None
```

**Data Models**:

```python
class OnboardingStatus(BaseModel):
    onboarding_completed: bool
    onboarding_step: Optional[str]
    onboarding_skipped: bool
    tooltip_tour_completed: bool
```

#### 2. RecommendationService

**Purpose**: 管理推薦來源

**Methods**:

```python
class RecommendationService:
    async def get_recommended_feeds(self) -> List[RecommendedFeed]
    async def get_feeds_by_category(
        self,
        category: str
    ) -> List[RecommendedFeed]
    async def update_recommendation_status(
        self,
        feed_id: UUID,
        is_recommended: bool,
        priority: int
    ) -> None
```

**Data Models**:

```python
class RecommendedFeed(BaseModel):
    id: UUID
    name: str
    url: str
    category: str
    description: Optional[str]
    is_recommended: bool
    recommendation_priority: int
```

#### 3. AnalyticsService

**Purpose**: 追蹤引導事件和生成報告

**Methods**:

```python
class AnalyticsService:
    async def log_event(
        self,
        user_id: UUID,
        event_type: str,
        event_data: dict
    ) -> None
    async def get_onboarding_completion_rate(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> float
    async def get_drop_off_rates(self) -> Dict[str, float]
    async def get_average_time_per_step(self) -> Dict[str, float]
```

**Event Types**:

- `onboarding_started`
- `step_completed`
- `onboarding_skipped`
- `onboarding_finished`
- `tooltip_shown`
- `tooltip_skipped`
- `feed_subscribed_from_onboarding`

### Discord Bot Commands

#### 1. /start Command

**Purpose**: 首次使用引導

**Implementation**:

```python
@app_commands.command(name="start", description="開始使用指南")
async def start(self, interaction: discord.Interaction):
    # Check if first-time user
    # Show welcome message with:
    # - Platform overview
    # - Available commands list
    # - Quick start steps
    # - Recommended feeds with subscribe buttons
```

**Response Format**:

```
🎉 歡迎使用技術新聞訂閱工具！

📰 這個平台幫助你：
• 訂閱優質的技術 RSS 來源
• 每週自動抓取和分析文章
• 透過 AI 評分找到最值得閱讀的內容

🚀 快速開始：
1. 使用 /add_feed 訂閱感興趣的來源
2. 使用 /news_now 查看最新文章
3. 使用 /reading_list 管理你的閱讀清單

💡 推薦來源：
[Subscribe buttons for recommended feeds]

📖 查看所有指令：/help
```

#### 2. Enhanced /help Command

**Purpose**: 改善的指令說明

**Implementation**:

```python
@app_commands.command(name="help", description="查看所有可用指令")
async def help(self, interaction: discord.Interaction):
    # Group commands by category
    # Show syntax and examples
    # Ephemeral response
```

**Response Format**:

```
📚 指令說明

**訂閱管理**
• /add_feed - 訂閱 RSS 來源
  語法: /add_feed name:來源名稱 url:RSS網址 category:分類
  範例: /add_feed name:"Hacker News" url:https://... category:"Tech News"

• /list_feeds - 查看你的訂閱
• /unsubscribe_feed - 取消訂閱

**文章瀏覽**
• /news_now - 查看最新文章
• /trigger_fetch - 手動觸發文章抓取
• /scheduler_status - 查看排程器狀態

**閱讀清單**
• /reading_list view - 查看閱讀清單
• /reading_list recommend - 獲取推薦

💡 提示：首次使用？執行 /start 查看快速開始指南
```

### API Endpoints

#### 1. Onboarding Progress Endpoints

```typescript
// GET /api/onboarding/status
// 查詢引導進度
interface GetOnboardingStatusResponse {
  onboarding_completed: boolean;
  onboarding_step: string | null;
  onboarding_skipped: boolean;
  tooltip_tour_completed: boolean;
}

// POST /api/onboarding/progress
// 更新引導進度
interface UpdateOnboardingProgressRequest {
  step: string;
  completed: boolean;
}

// POST /api/onboarding/complete
// 標記引導完成

// POST /api/onboarding/skip
// 標記引導跳過

// POST /api/onboarding/reset
// 重置引導狀態
```

#### 2. Recommendation Endpoints

```typescript
// GET /api/feeds/recommended
// 查詢推薦來源
interface GetRecommendedFeedsResponse {
  feeds: RecommendedFeed[];
  grouped_by_category: Record<string, RecommendedFeed[]>;
}

// POST /api/subscriptions/batch
// 批次訂閱
interface BatchSubscribeRequest {
  feed_ids: UUID[];
}

interface BatchSubscribeResponse {
  subscribed_count: number;
  failed_count: number;
  errors: string[];
}
```

#### 3. Analytics Endpoints

```typescript
// POST /api/analytics/event
// 記錄分析事件
interface LogAnalyticsEventRequest {
  event_type: string;
  event_data: Record<string, any>;
}

// GET /api/analytics/onboarding/completion-rate
// 查詢引導完成率
interface GetCompletionRateResponse {
  completion_rate: number;
  total_users: number;
  completed_users: number;
  skipped_users: number;
}

// GET /api/analytics/onboarding/drop-off
// 查詢流失率
interface GetDropOffRatesResponse {
  drop_off_by_step: Record<string, number>;
}
```

---

## Data Models

### Database Schema Extensions

#### 1. user_preferences Table

**Purpose**: 儲存用戶的個人化設定和引導進度

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,

    -- Onboarding progress
    onboarding_completed BOOLEAN DEFAULT false,
    onboarding_step TEXT,
    onboarding_skipped BOOLEAN DEFAULT false,
    onboarding_started_at TIMESTAMPTZ,
    onboarding_completed_at TIMESTAMPTZ,

    -- Tooltip tour
    tooltip_tour_completed BOOLEAN DEFAULT false,
    tooltip_tour_skipped BOOLEAN DEFAULT false,

    -- Language preference
    preferred_language TEXT DEFAULT 'zh-TW',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_onboarding_completed ON user_preferences(onboarding_completed);
```

**Constraints**:

- `user_id` UNIQUE: 每個用戶只有一筆偏好設定
- `onboarding_step` CHECK: 只能是預定義的步驟值
- `preferred_language` CHECK: 只能是支援的語言代碼

#### 2. feeds Table Extensions

**Purpose**: 擴展 feeds 表格以支援推薦系統

```sql
ALTER TABLE feeds
ADD COLUMN is_recommended BOOLEAN DEFAULT false,
ADD COLUMN recommendation_priority INTEGER DEFAULT 0,
ADD COLUMN description TEXT,
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();

CREATE INDEX idx_feeds_is_recommended ON feeds(is_recommended);
CREATE INDEX idx_feeds_recommendation_priority ON feeds(recommendation_priority DESC);
```

**New Columns**:

- `is_recommended`: 是否為推薦來源
- `recommendation_priority`: 推薦優先級（數字越大越優先）
- `description`: 來源描述（用於引導頁面）
- `updated_at`: 最後更新時間

#### 3. analytics_events Table

**Purpose**: 追蹤引導事件和用戶行為

```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at DESC);
CREATE INDEX idx_analytics_events_event_data ON analytics_events USING GIN(event_data);
```

**Event Types**:

- `onboarding_started`: 開始引導
- `step_completed`: 完成某個步驟
- `onboarding_skipped`: 跳過引導
- `onboarding_finished`: 完成引導
- `tooltip_shown`: 顯示 Tooltip
- `tooltip_skipped`: 跳過 Tooltip
- `feed_subscribed_from_onboarding`: 從引導頁面訂閱

**Event Data Examples**:

```json
// onboarding_started
{
  "source": "web" | "discord",
  "timestamp": "2024-01-01T00:00:00Z"
}

// step_completed
{
  "step": "welcome" | "recommendations" | "complete",
  "time_spent_seconds": 30
}

// feed_subscribed_from_onboarding
{
  "feed_id": "uuid",
  "feed_name": "Hacker News",
  "category": "Tech News"
}
```

### TypeScript Type Definitions

```typescript
// User Preferences
interface UserPreferences {
  id: UUID;
  userId: UUID;
  onboardingCompleted: boolean;
  onboardingStep: string | null;
  onboardingSkipped: boolean;
  onboardingStartedAt: Date | null;
  onboardingCompletedAt: Date | null;
  tooltipTourCompleted: boolean;
  tooltipTourSkipped: boolean;
  preferredLanguage: string;
  createdAt: Date;
  updatedAt: Date;
}

// Recommended Feed
interface RecommendedFeed {
  id: UUID;
  name: string;
  url: string;
  category: string;
  description: string | null;
  isRecommended: boolean;
  recommendationPriority: number;
  isSubscribed: boolean; // Computed based on user subscriptions
}

// Analytics Event
interface AnalyticsEvent {
  id: UUID;
  userId: UUID;
  eventType: string;
  eventData: Record<string, any>;
  createdAt: Date;
}

// Onboarding Status
interface OnboardingStatus {
  completed: boolean;
  step: string | null;
  skipped: boolean;
  tooltipTourCompleted: boolean;
}
```

### Python Pydantic Models

```python
from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime

class UserPreferences(BaseModel):
    id: UUID4
    user_id: UUID4
    onboarding_completed: bool = False
    onboarding_step: Optional[str] = None
    onboarding_skipped: bool = False
    onboarding_started_at: Optional[datetime] = None
    onboarding_completed_at: Optional[datetime] = None
    tooltip_tour_completed: bool = False
    tooltip_tour_skipped: bool = False
    preferred_language: str = 'zh-TW'
    created_at: datetime
    updated_at: datetime

class RecommendedFeed(BaseModel):
    id: UUID4
    name: str
    url: str
    category: str
    description: Optional[str] = None
    is_recommended: bool = False
    recommendation_priority: int = 0
    is_subscribed: bool = False

class AnalyticsEvent(BaseModel):
    id: UUID4
    user_id: UUID4
    event_type: str
    event_data: Dict[str, Any]
    created_at: datetime

class OnboardingStatus(BaseModel):
    completed: bool
    step: Optional[str]
    skipped: bool
    tooltip_tour_completed: bool
```

---

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Onboarding Progress Persistence

_For any_ onboarding action (step completion, skip, or finish), the system SHALL persist the progress to the user_preferences table, and subsequent queries SHALL reflect the updated state.

**Validates: Requirements 1.4, 10.1, 10.3**

### Property 2: Onboarding Completion State Transition

_For any_ user who completes all onboarding steps, the onboarding_completed flag SHALL be set to true, and the onboarding_completed_at timestamp SHALL be recorded.

**Validates: Requirements 1.5**

### Property 3: Skip Functionality Persistence

_For any_ user who skips onboarding, the system SHALL set onboarding_skipped to true, and SHALL NOT display the onboarding modal on subsequent logins unless manually triggered.

**Validates: Requirements 1.6, 1.7**

### Property 4: Feed Subscription from Onboarding

_For any_ set of selected feeds during onboarding, after confirmation, the user SHALL be subscribed to all selected feeds, and the subscription count SHALL equal the number of selected feeds.

**Validates: Requirements 2.6, 2.7**

### Property 5: Empty State Conditional Display

_For any_ dashboard state where article count is zero, the Empty_State component SHALL be displayed; when article count is greater than zero, the article list SHALL be displayed instead.

**Validates: Requirements 3.1**

### Property 6: Scheduler Status Conditional Display

_For any_ user with subscriptions but no articles, the Empty_State SHALL include Scheduler_Status information; for users without subscriptions, the Empty_State SHALL show subscription prompts instead.

**Validates: Requirements 3.7**

### Property 7: Feed Grouping by Category

_For any_ list of feeds, when displayed on the Subscription_Page, feeds SHALL be grouped by category, and each category group SHALL contain only feeds with matching category values.

**Validates: Requirements 2.1, 4.1**

### Property 8: Recommended Feed Badge Display

_For any_ feed where is_recommended is true, the Subscription_Page SHALL display a "推薦" badge alongside the feed.

**Validates: Requirements 4.2**

### Property 9: Category Feed Count Display

_For any_ collapsed category on the Subscription_Page, the displayed feed count SHALL equal the actual number of feeds in that category.

**Validates: Requirements 4.5**

### Property 10: Subscription Count Accuracy

_For any_ user, the displayed subscription count on the Subscription_Page SHALL equal the number of records in user_subscriptions table for that user.

**Validates: Requirements 4.7**

### Property 11: Scheduler Status Running Indicator

_For any_ time when the scheduler is actively running, the Scheduler_Status component SHALL display a loading indicator; when not running, no loading indicator SHALL be shown.

**Validates: Requirements 5.4**

### Property 12: Manual Fetch Feedback

_For any_ user-triggered manual fetch action, the system SHALL display a progress toast notification within 2 seconds of the trigger.

**Validates: Requirements 5.5, 9.7**

### Property 13: Scheduler Completion Notification

_For any_ scheduler execution that completes successfully, the system SHALL display a success notification containing the count of newly fetched articles.

**Validates: Requirements 5.7**

### Property 14: Discord First-Time Command Detection

_For any_ user executing a Discord command for the first time, the system SHALL detect the first-time usage and either auto-trigger /start guidance or include a hint about the /start command.

**Validates: Requirements 6.6, 6.7**

### Property 15: Help Command Grouping

_For any_ command listed in the /help response, the command SHALL be grouped under one of the predefined categories (訂閱管理, 文章瀏覽, 閱讀清單), and each command SHALL include syntax and parameter descriptions.

**Validates: Requirements 7.2, 7.3**

### Property 16: Help Command Examples

_For any_ command listed in the /help response, at least one usage example SHALL be provided.

**Validates: Requirements 7.4**

### Property 17: Error Message with Suggestions

_For any_ command failure due to missing prerequisites or errors, the Discord_Bot SHALL provide an error message that includes either a CTA button or a command suggestion for the next action.

**Validates: Requirements 7.5, 8.2**

### Property 18: User-Friendly Error Transformation

_For any_ technical error (database errors, API errors), the Discord_Bot SHALL replace the technical error message with a user-friendly explanation that does not expose technical details.

**Validates: Requirements 8.4, 8.7**

### Property 19: No Subscription Error Explanation

_For any_ user executing /news_now without subscriptions, the Discord_Bot SHALL provide an explanation of why no articles are shown and suggest subscribing to feeds.

**Validates: Requirements 8.1, 8.3**

### Property 20: Rate Limit Feedback

_For any_ API quota exceeded or rate limit error, the Discord_Bot SHALL include an estimated wait time in the error message and suggest alternatives.

**Validates: Requirements 8.5, 8.6**

### Property 21: Filter Menu Article Count

_For any_ category in the Filter_Menu, the displayed article count SHALL equal the actual number of articles in that category.

**Validates: Requirements 9.4**

### Property 22: Read Later Button Feedback

_For any_ successful addition of an article to the reading list via Read_Later_Button, the system SHALL display feedback within 2 seconds.

**Validates: Requirements 9.5, 9.7**

### Property 23: Empty Reading List Suggestion

_For any_ user with an empty reading list, the Discord_Bot SHALL suggest using Read_Later buttons when the user views their reading list.

**Validates: Requirements 9.6**

### Property 24: Onboarding UI Conditional Display

_For any_ user, before displaying onboarding UI, the system SHALL check user_preferences; if onboarding_completed is true, onboarding modals SHALL NOT be displayed.

**Validates: Requirements 10.4, 10.5**

### Property 25: Onboarding Restart State Reset

_For any_ user who restarts onboarding from settings, the system SHALL reset onboarding_completed to false and clear onboarding_step.

**Validates: Requirements 10.6, 10.7**

### Property 26: Tooltip Sequential Display

_For any_ tooltip tour, tooltips SHALL appear sequentially, and each tooltip SHALL include "下一步" and "跳過" buttons for navigation.

**Validates: Requirements 11.2, 11.5, 11.6**

### Property 27: Tooltip Highlight Effect

_For any_ active tooltip, the target UI element SHALL be highlighted with a spotlight effect.

**Validates: Requirements 11.3**

### Property 28: Tooltip Persistence

_For any_ user who completes or skips the tooltip tour, the system SHALL set tooltip_tour_completed or tooltip_tour_skipped to true, and SHALL NOT display tooltips again on subsequent visits.

**Validates: Requirements 11.7**

### Property 29: Recommended Feeds Query

_For any_ query for recommended feeds, the system SHALL filter feeds WHERE is_recommended = true, and SHALL order results by recommendation_priority in descending order.

**Validates: Requirements 12.1, 12.4**

### Property 30: Recommended Feed Real-Time Updates

_For any_ feed that is marked as recommended (is_recommended set to true), the feed SHALL immediately appear in subsequent recommended feeds queries.

**Validates: Requirements 12.7**

### Property 31: Language Preference Display

_For any_ onboarding content display, the system SHALL use the user's preferred_language from user_preferences; if preferred_language is not available or null, the system SHALL fall back to zh-TW.

**Validates: Requirements 13.5, 13.6**

### Property 32: Analytics Event Logging

_For any_ onboarding event (started, step_completed, skipped, finished), the system SHALL create a record in analytics_events table with timestamp, user_id, event_type, and event_data.

**Validates: Requirements 14.1, 14.3**

### Property 33: Skip Event Step Tracking

_For any_ user who skips onboarding, the analytics event SHALL include the step where the skip occurred in the event_data.

**Validates: Requirements 14.4**

### Property 34: Step Time Tracking

_For any_ onboarding step completion, the analytics event SHALL include time_spent_seconds in the event_data.

**Validates: Requirements 14.5**

### Property 35: Welcome Modal Performance

_For any_ first-time user login, the Welcome_Modal SHALL appear within 500ms of page load completion.

**Validates: Requirements 15.2**

### Property 36: Recommended Feeds Caching

_For any_ recommended feeds query, the results SHALL be cached in the browser with a 24-hour expiration time, and subsequent queries within 24 hours SHALL use the cached data.

**Validates: Requirements 15.3**

### Property 37: Loading Skeleton Display

_For any_ recommended feeds loading operation, while the data is being fetched, the system SHALL display a loading skeleton UI.

**Validates: Requirements 15.4**

### Property 38: Content Prefetching

_For any_ user on an onboarding step, the system SHALL prefetch the content for the next step while the user is viewing the current step.

**Validates: Requirements 15.5**

---

## Error Handling

### Error Categories

#### 1. User Input Errors

**Scenarios**:

- Invalid feed selection (no feeds selected)
- Invalid language preference
- Invalid step navigation

**Handling Strategy**:

- Display inline validation messages
- Prevent form submission until errors are resolved
- Provide clear guidance on how to fix the error
- Log validation errors for analytics

**Example**:

```typescript
if (selectedFeeds.length === 0) {
  showError('請至少選擇一個訂閱來源');
  return;
}
```

#### 2. Network Errors

**Scenarios**:

- API request timeout
- Connection lost during onboarding
- Slow network causing delays

**Handling Strategy**:

- Implement retry logic with exponential backoff
- Show loading states with timeout warnings
- Allow users to retry failed operations
- Cache progress locally to prevent data loss

**Example**:

```typescript
try {
  await subscribeToFeeds(selectedFeeds);
} catch (error) {
  if (error.code === 'NETWORK_ERROR') {
    showRetryDialog('網路連線失敗，請檢查您的網路連線後重試');
  }
}
```

#### 3. Database Errors

**Scenarios**:

- Failed to save onboarding progress
- Failed to query user preferences
- Failed to subscribe to feeds
- Constraint violations

**Handling Strategy**:

- Wrap database operations in try-catch blocks
- Use SupabaseServiceError for consistent error handling
- Provide user-friendly error messages
- Log detailed errors for debugging
- Implement transaction rollback for multi-step operations

**Example**:

```python
try:
    await onboarding_service.mark_onboarding_completed(user_id)
except SupabaseServiceError as e:
    logger.error(f"Failed to mark onboarding completed: {e}")
    raise HTTPException(
        status_code=500,
        detail="無法儲存引導進度，請稍後再試"
    )
```

#### 4. Discord Bot Errors

**Scenarios**:

- Command execution failures
- Missing permissions
- Rate limiting
- API quota exceeded

**Handling Strategy**:

- Replace technical errors with user-friendly messages
- Provide actionable suggestions
- Include estimated wait times for rate limits
- Log errors with context for debugging

**Example**:

```python
try:
    await interaction.response.send_message(content)
except discord.errors.Forbidden:
    await interaction.followup.send(
        "❌ 機器人沒有權限執行此操作，請聯繫伺服器管理員",
        ephemeral=True
    )
```

#### 5. State Inconsistency Errors

**Scenarios**:

- User preferences not found after registration
- Onboarding step out of sequence
- Conflicting state flags (completed and skipped both true)

**Handling Strategy**:

- Implement state validation before operations
- Auto-correct minor inconsistencies
- Reset to safe default state if corruption detected
- Log inconsistencies for investigation

**Example**:

```python
def validate_onboarding_state(preferences: UserPreferences):
    if preferences.onboarding_completed and preferences.onboarding_skipped:
        # Inconsistent state, prioritize completed
        preferences.onboarding_skipped = False
        logger.warning(f"Corrected inconsistent state for user {preferences.user_id}")
```

### Error Recovery Strategies

#### Graceful Degradation

- If analytics logging fails, continue with onboarding
- If recommended feeds fail to load, show all feeds
- If tooltip tour fails, allow manual navigation

#### Local State Backup

- Cache onboarding progress in localStorage
- Restore from cache if server state is lost
- Sync cache with server when connection restored

#### User Communication

- Always inform users when errors occur
- Provide clear next steps
- Offer alternative paths when primary path fails

---

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, UI component rendering, and integration points
- **Property tests**: Verify universal properties across all inputs, state transitions, and data persistence

Both approaches are complementary and necessary for comprehensive coverage. Unit tests catch concrete bugs and verify specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Unit Testing

#### Frontend Unit Tests (Jest + React Testing Library)

**Component Tests**:

```typescript
// OnboardingModal.test.tsx
describe('OnboardingModal', () => {
  it('should display welcome message on first step', () => {
    // Test specific UI rendering
  });

  it('should navigate to recommendations when "開始使用" is clicked', () => {
    // Test navigation behavior
  });

  it('should close modal when "稍後再說" is clicked', () => {
    // Test skip functionality
  });
});

// EmptyState.test.tsx
describe('EmptyState', () => {
  it('should display "還沒有文章" heading for no-articles state', () => {
    // Test specific text content
  });

  it('should show scheduler status when user has subscriptions', () => {
    // Test conditional display
  });
});

// TooltipTour.test.tsx
describe('TooltipTour', () => {
  it('should highlight target element with spotlight effect', () => {
    // Test visual effect application
  });

  it('should show tooltips for subscription button, filter menu, and trigger button', () => {
    // Test specific tooltip targets
  });
});
```

**API Integration Tests**:

```typescript
// onboarding.api.test.ts
describe('Onboarding API', () => {
  it('should return onboarding status for authenticated user', async () => {
    // Test API endpoint
  });

  it('should update onboarding progress', async () => {
    // Test progress update
  });
});
```

#### Backend Unit Tests (pytest)

**Service Tests**:

```python
# test_onboarding_service.py
def test_get_onboarding_status_returns_correct_structure():
    """Test that onboarding status has all required fields"""
    # Test specific data structure

def test_mark_onboarding_completed_sets_timestamp():
    """Test that completion timestamp is recorded"""
    # Test specific behavior

# test_recommendation_service.py
def test_get_recommended_feeds_includes_required_categories():
    """Test that at least AI, Web Development, Security categories exist"""
    # Test minimum requirements

def test_recommended_feeds_ordered_by_priority():
    """Test that feeds are sorted by recommendation_priority"""
    # Test ordering behavior
```

**Discord Bot Tests**:

```python
# test_discord_commands.py
@pytest.mark.asyncio
async def test_start_command_sends_welcome_message():
    """Test that /start command sends correct welcome message"""
    # Test command response

@pytest.mark.asyncio
async def test_help_command_is_ephemeral():
    """Test that /help response is only visible to user"""
    # Test message visibility

@pytest.mark.asyncio
async def test_error_message_includes_suggestion():
    """Test that errors include actionable suggestions"""
    # Test error handling
```

### Property-Based Testing

#### Configuration

Use **Hypothesis** for Python and **fast-check** for TypeScript property-based testing.

**Test Configuration**:

- Minimum 100 iterations per property test
- Each test must reference its design document property
- Tag format: `Feature: new-user-onboarding-system, Property {number}: {property_text}`

#### Python Property Tests (Hypothesis)

```python
from hypothesis import given, strategies as st
import pytest

# Property 1: Onboarding Progress Persistence
@given(
    user_id=st.uuids(),
    step=st.sampled_from(['welcome', 'recommendations', 'complete']),
    completed=st.booleans()
)
@pytest.mark.property_test
async def test_property_1_onboarding_progress_persistence(user_id, step, completed):
    """
    Feature: new-user-onboarding-system, Property 1: Onboarding Progress Persistence

    For any onboarding action, the system SHALL persist the progress to the
    user_preferences table, and subsequent queries SHALL reflect the updated state.
    """
    # Update progress
    await onboarding_service.update_onboarding_progress(user_id, step, completed)

    # Query status
    status = await onboarding_service.get_onboarding_status(user_id)

    # Verify persistence
    if completed:
        assert status.onboarding_step == step
```

```python
# Property 2: Onboarding Completion State Transition
@given(user_id=st.uuids())
@pytest.mark.property_test
async def test_property_2_onboarding_completion_state_transition(user_id):
    """
    Feature: new-user-onboarding-system, Property 2: Onboarding Completion State Transition

    For any user who completes all onboarding steps, the onboarding_completed flag
    SHALL be set to true, and the onboarding_completed_at timestamp SHALL be recorded.
    """
    # Complete all steps
    await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
    await onboarding_service.update_onboarding_progress(user_id, 'recommendations', True)
    await onboarding_service.mark_onboarding_completed(user_id)

    # Query status
    status = await onboarding_service.get_onboarding_status(user_id)
    preferences = await supabase.get_user_preferences(user_id)

    # Verify completion
    assert status.onboarding_completed is True
    assert preferences.onboarding_completed_at is not None

# Property 4: Feed Subscription from Onboarding
@given(
    user_id=st.uuids(),
    feed_ids=st.lists(st.uuids(), min_size=1, max_size=10)
)
@pytest.mark.property_test
async def test_property_4_feed_subscription_from_onboarding(user_id, feed_ids):
    """
    Feature: new-user-onboarding-system, Property 4: Feed Subscription from Onboarding

    For any set of selected feeds during onboarding, after confirmation, the user
    SHALL be subscribed to all selected feeds, and the subscription count SHALL
    equal the number of selected feeds.
    """
    # Subscribe to feeds
    result = await subscription_service.batch_subscribe(user_id, feed_ids)

    # Query subscriptions
    subscriptions = await supabase.get_user_subscriptions(user_id)
    subscribed_feed_ids = {sub.feed_id for sub in subscriptions}

    # Verify all feeds are subscribed
    assert len(subscribed_feed_ids.intersection(set(feed_ids))) == len(feed_ids)
    assert result.subscribed_count == len(feed_ids)

# Property 10: Subscription Count Accuracy
@given(user_id=st.uuids())
@pytest.mark.property_test
async def test_property_10_subscription_count_accuracy(user_id):
    """
    Feature: new-user-onboarding-system, Property 10: Subscription Count Accuracy

    For any user, the displayed subscription count on the Subscription_Page SHALL
    equal the number of records in user_subscriptions table for that user.
    """
    # Get subscriptions from database
    db_subscriptions = await supabase.get_user_subscriptions(user_id)
    db_count = len(db_subscriptions)

    # Get displayed count from API
    response = await client.get(f'/api/subscriptions/count', headers=auth_headers)
    displayed_count = response.json()['count']

    # Verify counts match
    assert displayed_count == db_count
```

```python
# Property 24: Onboarding UI Conditional Display
@given(
    user_id=st.uuids(),
    onboarding_completed=st.booleans()
)
@pytest.mark.property_test
async def test_property_24_onboarding_ui_conditional_display(user_id, onboarding_completed):
    """
    Feature: new-user-onboarding-system, Property 24: Onboarding UI Conditional Display

    For any user, before displaying onboarding UI, the system SHALL check
    user_preferences; if onboarding_completed is true, onboarding modals SHALL NOT be displayed.
    """
    # Set onboarding status
    await supabase.update_user_preferences(
        user_id,
        {'onboarding_completed': onboarding_completed}
    )

    # Check if modal should be shown
    should_show = await onboarding_service.should_show_onboarding(user_id)

    # Verify conditional display
    if onboarding_completed:
        assert should_show is False
    else:
        assert should_show is True

# Property 32: Analytics Event Logging
@given(
    user_id=st.uuids(),
    event_type=st.sampled_from([
        'onboarding_started',
        'step_completed',
        'onboarding_skipped',
        'onboarding_finished'
    ]),
    event_data=st.dictionaries(st.text(), st.text())
)
@pytest.mark.property_test
async def test_property_32_analytics_event_logging(user_id, event_type, event_data):
    """
    Feature: new-user-onboarding-system, Property 32: Analytics Event Logging

    For any onboarding event, the system SHALL create a record in analytics_events
    table with timestamp, user_id, event_type, and event_data.
    """
    # Log event
    await analytics_service.log_event(user_id, event_type, event_data)

    # Query events
    events = await supabase.get_analytics_events(
        user_id=user_id,
        event_type=event_type
    )

    # Verify event was logged
    assert len(events) > 0
    latest_event = events[0]
    assert latest_event.user_id == user_id
    assert latest_event.event_type == event_type
    assert latest_event.created_at is not None
```

#### TypeScript Property Tests (fast-check)

```typescript
import fc from 'fast-check';

// Property 5: Empty State Conditional Display
describe('Property 5: Empty State Conditional Display', () => {
  it('should display empty state when article count is zero', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ id: fc.uuid(), title: fc.string() })),
        (articles) => {
          const { container } = render(
            <Dashboard articles={articles} />
          );

          const hasEmptyState = container.querySelector('[data-testid="empty-state"]') !== null;
          const hasArticleList = container.querySelector('[data-testid="article-list"]') !== null;

          if (articles.length === 0) {
            expect(hasEmptyState).toBe(true);
            expect(hasArticleList).toBe(false);
          } else {
            expect(hasEmptyState).toBe(false);
            expect(hasArticleList).toBe(true);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

```typescript
// Property 7: Feed Grouping by Category
describe('Property 7: Feed Grouping by Category', () => {
  it('should group feeds by category correctly', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            name: fc.string(),
            category: fc.constantFrom('AI', 'Web Development', 'Security', 'DevOps')
          })
        ),
        (feeds) => {
          const grouped = groupFeedsByCategory(feeds);

          // Verify each group contains only feeds with matching category
          for (const [category, categoryFeeds] of Object.entries(grouped)) {
            categoryFeeds.forEach(feed => {
              expect(feed.category).toBe(category);
            });
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

// Property 26: Tooltip Sequential Display
describe('Property 26: Tooltip Sequential Display', () => {
  it('should display tooltips sequentially with navigation buttons', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            target: fc.string(),
            title: fc.string(),
            content: fc.string()
          }),
          { minLength: 1, maxLength: 5 }
        ),
        (steps) => {
          const { container, getByText } = render(
            <TooltipTour steps={steps} isActive={true} />
          );

          // Verify first tooltip is shown
          expect(getByText(steps[0].title)).toBeInTheDocument();

          // Verify navigation buttons exist
          expect(getByText('下一步')).toBeInTheDocument();
          expect(getByText('跳過')).toBeInTheDocument();
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Integration Testing

#### End-to-End Tests (Playwright)

```typescript
// e2e/onboarding.spec.ts
test('complete onboarding flow', async ({ page }) => {
  // Login as new user
  await page.goto('/auth/login');
  await loginAsNewUser(page);

  // Verify welcome modal appears
  await expect(page.locator('[data-testid="welcome-modal"]')).toBeVisible();

  // Click "開始使用"
  await page.click('button:has-text("開始使用")');

  // Select recommended feeds
  await page.click('[data-testid="feed-checkbox-1"]');
  await page.click('[data-testid="feed-checkbox-2"]');

  // Confirm selection
  await page.click('button:has-text("確認訂閱")');

  // Verify success message
  await expect(page.locator('text=已訂閱 2 個來源')).toBeVisible();

  // Verify onboarding is marked complete
  const status = await page.evaluate(() => {
    return fetch('/api/onboarding/status').then((r) => r.json());
  });
  expect(status.onboarding_completed).toBe(true);
});

test('skip onboarding flow', async ({ page }) => {
  await page.goto('/auth/login');
  await loginAsNewUser(page);

  // Click "稍後再說"
  await page.click('button:has-text("稍後再說")');

  // Verify modal is closed
  await expect(page.locator('[data-testid="welcome-modal"]')).not.toBeVisible();

  // Reload page
  await page.reload();

  // Verify modal does not appear again
  await expect(page.locator('[data-testid="welcome-modal"]')).not.toBeVisible();
});
```

### Test Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Property Tests**: All 38 correctness properties implemented
- **Integration Tests**: All critical user flows covered
- **E2E Tests**: Complete onboarding flow, skip flow, error scenarios

### Testing Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use fixtures and teardown to clean up test data
3. **Mocking**: Mock external dependencies (Supabase, Discord API) in unit tests
4. **Real Data**: Use real database in integration tests with test isolation
5. **Performance**: Property tests should complete within reasonable time (< 30s per property)
6. **Readability**: Test names should clearly describe what is being tested
7. **Documentation**: Each property test must reference its design document property

---

## Implementation Plan

### Phase 1: Database Schema (Week 1)

**Tasks**:

1. Create user_preferences table migration
2. Add is_recommended and recommendation_priority columns to feeds table
3. Create analytics_events table migration
4. Seed recommended feeds data
5. Write database schema tests

**Deliverables**:

- SQL migration scripts
- Seed data script
- Schema validation tests

### Phase 2: Backend Services (Week 2-3)

**Tasks**:

1. Implement OnboardingService
   - get_onboarding_status()
   - update_onboarding_progress()
   - mark_onboarding_completed()
   - mark_onboarding_skipped()
   - reset_onboarding()

2. Implement RecommendationService
   - get_recommended_feeds()
   - get_feeds_by_category()

3. Implement AnalyticsService
   - log_event()
   - get_onboarding_completion_rate()
   - get_drop_off_rates()

4. Create API endpoints
   - /api/onboarding/\* endpoints
   - /api/feeds/recommended
   - /api/subscriptions/batch
   - /api/analytics/\* endpoints

**Deliverables**:

- Service implementations
- API endpoints
- Unit tests
- Property tests for services

### Phase 3: Frontend Components (Week 4-5)

**Tasks**:

1. Implement OnboardingModal component
   - Welcome step
   - Recommendations step
   - Completion step
   - Skip functionality

2. Implement EmptyState component
   - NoSubscriptionsEmpty variant
   - NoArticlesEmpty variant
   - NoReadingListEmpty variant

3. Implement TooltipTour component
   - Sequential tooltip display
   - Spotlight highlighting
   - Navigation controls

4. Implement SubscriptionPage enhancements
   - Category grouping
   - Collapsible sections
   - Recommended badges
   - Subscription count display

5. Implement SchedulerStatusIndicator component

**Deliverables**:

- React components
- Component unit tests
- Storybook stories
- Property tests for UI logic

### Phase 4: Discord Bot Enhancements (Week 6)

**Tasks**:

1. Implement /start command
   - Welcome message
   - Command listing
   - Quick start guide
   - Recommended feeds with subscribe buttons

2. Enhance /help command
   - Category grouping
   - Syntax and examples
   - Ephemeral responses

3. Improve error messages
   - User-friendly transformations
   - Actionable suggestions
   - Rate limit handling

4. Add first-time user detection
   - Auto-trigger /start
   - Include hints in responses

**Deliverables**:

- Discord bot commands
- Error handling improvements
- Bot unit tests

### Phase 5: Integration & Testing (Week 7)

**Tasks**:

1. Integration testing
   - API integration tests
   - Database integration tests
   - Discord bot integration tests

2. E2E testing
   - Complete onboarding flow
   - Skip flow
   - Error scenarios
   - Mobile responsive testing

3. Performance testing
   - Modal load time
   - API response times
   - Database query optimization

**Deliverables**:

- Integration test suite
- E2E test suite
- Performance benchmarks

### Phase 6: Analytics & Monitoring (Week 8)

**Tasks**:

1. Implement analytics dashboard
   - Completion rate visualization
   - Drop-off rate charts
   - Time spent per step
   - User flow diagrams

2. Set up monitoring
   - Error tracking (Sentry)
   - Performance monitoring
   - User behavior tracking

3. A/B testing setup
   - Test different onboarding flows
   - Test different recommended feeds
   - Test different messaging

**Deliverables**:

- Analytics dashboard
- Monitoring setup
- A/B testing framework

### Phase 7: Documentation & Launch (Week 9)

**Tasks**:

1. Write user documentation
   - User guide for web onboarding
   - Discord bot command guide
   - FAQ

2. Write developer documentation
   - API documentation
   - Component documentation
   - Testing guide

3. Prepare launch
   - Feature flags setup
   - Gradual rollout plan
   - Rollback procedures

**Deliverables**:

- User documentation
- Developer documentation
- Launch plan

---

## Security Considerations

### Data Privacy

1. **User Preferences**: Store minimal personal data, only what's necessary for onboarding
2. **Analytics Events**: Anonymize sensitive data in event_data
3. **Access Control**: Ensure users can only access their own preferences and analytics

### Authentication

1. **API Endpoints**: All onboarding endpoints require authentication
2. **Token Validation**: Validate JWT tokens on every request
3. **Session Management**: Implement proper session timeout and refresh

### Input Validation

1. **Feed Selection**: Validate feed IDs exist before subscribing
2. **Step Validation**: Ensure onboarding steps are valid values
3. **Language Preference**: Validate language codes against supported languages

### Rate Limiting

1. **API Endpoints**: Implement rate limiting on onboarding endpoints
2. **Discord Bot**: Respect Discord rate limits
3. **Analytics Logging**: Prevent spam by rate limiting event logging

---

## Performance Optimization

### Frontend Performance

#### Code Splitting

```typescript
// Lazy load onboarding components
const OnboardingModal = lazy(() => import('./components/OnboardingModal'));
const TooltipTour = lazy(() => import('./components/TooltipTour'));

// Use Suspense for loading states
<Suspense fallback={<LoadingSkeleton />}>
  <OnboardingModal />
</Suspense>
```

#### Caching Strategy

1. **Recommended Feeds**: Cache in browser for 24 hours
2. **User Preferences**: Cache in memory, invalidate on updates
3. **Analytics Events**: Batch and send periodically

#### Bundle Size Optimization

- Lazy load onboarding components (target: < 50KB)
- Use tree shaking to remove unused code
- Compress images and icons
- Use SVG sprites for icons

### Backend Performance

#### Database Optimization

```sql
-- Indexes for fast queries
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_feeds_is_recommended ON feeds(is_recommended);
CREATE INDEX idx_analytics_events_user_id_created_at
  ON analytics_events(user_id, created_at DESC);
```

#### Query Optimization

1. **Batch Operations**: Use batch insert for analytics events
2. **Connection Pooling**: Reuse database connections
3. **Query Caching**: Cache recommended feeds query results

#### API Response Time Targets

- GET /api/onboarding/status: < 100ms
- POST /api/onboarding/progress: < 200ms
- GET /api/feeds/recommended: < 150ms
- POST /api/analytics/event: < 50ms (async)

### Discord Bot Performance

1. **Defer Responses**: Use `interaction.response.defer()` for long operations
2. **Batch Queries**: Fetch all needed data in one query
3. **Cache Commands**: Cache command metadata to reduce API calls

---

## Monitoring and Observability

### Metrics to Track

#### Onboarding Metrics

- Onboarding completion rate
- Average time to complete onboarding
- Drop-off rate at each step
- Skip rate
- Feeds selected per user (average, median, distribution)

#### Performance Metrics

- Modal load time (p50, p95, p99)
- API response times
- Database query times
- Error rates

#### User Behavior Metrics

- Tooltip engagement rate
- Empty state CTA click rate
- Recommended feeds acceptance rate
- Time spent on each onboarding step

### Logging Strategy

#### Log Levels

- **DEBUG**: Detailed flow information
- **INFO**: Key events (onboarding started, completed, skipped)
- **WARNING**: Recoverable errors, state inconsistencies
- **ERROR**: Unrecoverable errors, exceptions

#### Structured Logging

```python
logger.info(
    "Onboarding completed",
    extra={
        "user_id": str(user_id),
        "time_spent_seconds": time_spent,
        "feeds_selected": len(selected_feeds),
        "source": "web"
    }
)
```

### Alerting

#### Critical Alerts

- Onboarding completion rate drops below 50%
- API error rate exceeds 5%
- Database connection failures
- Discord bot command failures exceed 10%

#### Warning Alerts

- Modal load time exceeds 1 second
- Drop-off rate at any step exceeds 30%
- Analytics event logging failures

---

## Deployment Strategy

### Feature Flags

Use feature flags to control rollout and enable quick rollback:

```typescript
// Feature flag configuration
const FEATURE_FLAGS = {
  ONBOARDING_MODAL: 'onboarding_modal_enabled',
  TOOLTIP_TOUR: 'tooltip_tour_enabled',
  RECOMMENDED_FEEDS: 'recommended_feeds_enabled',
  ANALYTICS_TRACKING: 'analytics_tracking_enabled',
};

// Usage
if (featureFlags.isEnabled(FEATURE_FLAGS.ONBOARDING_MODAL)) {
  showOnboardingModal();
}
```

### Gradual Rollout Plan

#### Week 1: Internal Testing (0% users)

- Deploy to staging environment
- Internal team testing
- Fix critical bugs

#### Week 2: Beta Testing (5% users)

- Enable for 5% of new users
- Monitor metrics closely
- Gather user feedback

#### Week 3: Expanded Beta (25% users)

- Increase to 25% of new users
- Analyze completion rates
- Optimize based on data

#### Week 4: Full Rollout (100% users)

- Enable for all new users
- Continue monitoring
- Iterate based on feedback

### Rollback Procedures

#### Immediate Rollback Triggers

- Onboarding completion rate drops below 30%
- Critical bugs affecting user registration
- Database performance degradation
- API error rate exceeds 10%

#### Rollback Steps

1. Disable feature flags
2. Revert database migrations if necessary
3. Clear cached data
4. Notify users of temporary issues
5. Investigate and fix issues
6. Re-deploy with fixes

### Database Migration Strategy

#### Forward Migration

```sql
-- V1: Create user_preferences table
CREATE TABLE user_preferences (...);

-- V2: Add columns to feeds table
ALTER TABLE feeds ADD COLUMN is_recommended BOOLEAN DEFAULT false;
ALTER TABLE feeds ADD COLUMN recommendation_priority INTEGER DEFAULT 0;

-- V3: Create analytics_events table
CREATE TABLE analytics_events (...);
```

#### Backward Compatibility

- Ensure old code can run with new schema
- Use default values for new columns
- Implement graceful degradation

#### Rollback Migration

```sql
-- Rollback V3
DROP TABLE analytics_events;

-- Rollback V2
ALTER TABLE feeds DROP COLUMN is_recommended;
ALTER TABLE feeds DROP COLUMN recommendation_priority;

-- Rollback V1
DROP TABLE user_preferences;
```

---

## Future Enhancements

### Phase 2 Features (Post-Launch)

1. **Personalized Recommendations**
   - ML-based feed recommendations
   - Based on user reading history
   - Collaborative filtering

2. **Interactive Tutorials**
   - Video tutorials
   - Interactive walkthroughs
   - Gamification elements

3. **Multi-language Support**
   - English (en-US)
   - Simplified Chinese (zh-CN)
   - Japanese (ja-JP)

4. **Advanced Analytics**
   - User cohort analysis
   - Funnel visualization
   - Predictive churn modeling

5. **A/B Testing Framework**
   - Test different onboarding flows
   - Test different messaging
   - Automated winner selection

### Long-term Vision

- **AI-Powered Onboarding**: Adaptive onboarding based on user behavior
- **Social Onboarding**: Invite friends, share recommendations
- **Mobile App**: Native mobile onboarding experience
- **Voice Onboarding**: Voice-guided setup for accessibility

---

## Conclusion

This design document provides a comprehensive technical specification for the New User Onboarding System. The system is designed to:

1. **Reduce user friction** through clear, step-by-step guidance
2. **Accelerate time-to-value** with recommended feeds and quick setup
3. **Improve user retention** through better first impressions
4. **Enable data-driven optimization** with comprehensive analytics

The implementation follows best practices for:

- **Scalability**: Efficient database design and caching strategies
- **Maintainability**: Modular architecture and comprehensive testing
- **Reliability**: Error handling and graceful degradation
- **Observability**: Structured logging and metrics tracking

By following this design, we will create an onboarding experience that welcomes new users, helps them understand the platform's value, and sets them up for long-term success.
