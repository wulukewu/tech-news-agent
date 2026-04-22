# Discord Bot Cog Responsibilities Documentation

**Created:** 2024
**Purpose:** Define clear single responsibilities for each Discord bot cog, identify overlapping functionality, and establish responsibility boundaries.
**Related Requirements:** 7.1, 7.5

---

## Overview

The Tech News Agent Discord bot is organized into 7 cogs, each handling specific aspects of bot functionality. This document establishes clear responsibility boundaries to improve maintainability and prevent feature overlap.

---

## Cog Responsibility Matrix

### 1. **AdminCommands** (`admin_commands.py`)

**Single Responsibility:** System administration and scheduler management

**Core Functions:**

- Manual scheduler triggering (`/trigger_fetch`)
- Scheduler health monitoring (`/scheduler_status`)
- System-level operations

**Boundaries:**

- ✅ DOES: Manage background jobs and system health
- ❌ DOES NOT: Handle user data, subscriptions, or content delivery
- ❌ DOES NOT: Interact with articles or reading lists

**Dependencies:**

- `app.tasks.scheduler` (background_fetch_job, get_scheduler_health)

**Access Level:** Admin/System operations

---

### 2. **NewsCommands** (`news_commands.py`)

**Single Responsibility:** Content discovery and personalized news delivery

**Core Functions:**

- Fetch personalized news (`/news_now`)
- User registration (via `ensure_user_registered` helper)
- Article filtering by user subscriptions
- Content presentation with interactive views

**Boundaries:**

- ✅ DOES: Deliver personalized article feeds
- ✅ DOES: Register new users automatically
- ✅ DOES: Query articles based on subscriptions
- ❌ DOES NOT: Manage subscriptions (delegates to SubscriptionCommands)
- ❌ DOES NOT: Handle reading list operations (delegates to ReadingListCog)
- ❌ DOES NOT: Implement button/select callbacks (delegates to InteractionsCog)

**Dependencies:**

- `SupabaseService` (user registration, subscription queries, article queries)
- `InteractionsCog` (ReadLaterView, FilterView, DeepDiveView)

**Access Level:** All users

---

### 3. **InteractionsCog** (`interactions.py`)

**Single Responsibility:** UI component definitions and interaction callbacks

**Core Functions:**

- Define interactive UI components (buttons, selects, views)
- Handle button callbacks (ReadLaterButton, MarkReadButton, DeepDiveButton)
- Handle select callbacks (FilterSelect, RatingSelect)
- Manage view composition (ReadLaterView, FilterView, DeepDiveView, MarkReadView)

**Boundaries:**

- ✅ DOES: Define reusable UI components
- ✅ DOES: Handle user interactions with buttons/selects
- ✅ DOES: Call services for data operations (save to reading list, mark as read, etc.)
- ❌ DOES NOT: Define slash commands
- ❌ DOES NOT: Implement business logic (delegates to services)
- ❌ DOES NOT: Handle persistent views (delegates to PersistentViews)

**Components Defined:**

- `ReadLaterButton` - Save article to reading list
- `ReadLaterView` - Container for read later buttons
- `FilterSelect` - Filter articles by category
- `FilterView` - Container for filter select
- `DeepDiveButton` - Generate AI deep dive analysis
- `DeepDiveView` - Container for deep dive buttons
- `MarkReadButton` - Mark article as read
- `MarkReadView` - Container for mark read buttons

**Dependencies:**

- `SupabaseService` (save_to_reading_list, update_article_status, update_article_rating)
- `LLMService` (generate_deep_dive)

**Access Level:** Component library (used by other cogs)

---

### 4. **PersistentViews** (`persistent_views.py`)

**Single Responsibility:** Bot restart-resilient UI components

**Core Functions:**

- Define persistent UI components with `timeout=None`
- Handle interactions after bot restarts
- Parse article IDs from custom_ids
- Reload necessary data from database
- Log post-restart interactions

**Boundaries:**

- ✅ DOES: Implement persistent versions of interactive components
- ✅ DOES: Handle custom_id parsing and state reconstruction
- ✅ DOES: Gracefully handle message context loss
- ❌ DOES NOT: Define non-persistent components (delegates to InteractionsCog)
- ❌ DOES NOT: Implement business logic (delegates to services)

**Components Defined:**

- `PersistentReadLaterButton` - Persistent read later button
- `PersistentMarkReadButton` - Persistent mark read button
- `PersistentRatingSelect` - Persistent rating select
- `PersistentDeepDiveButton` - Persistent deep dive button
- `PersistentInteractionView` - Container for all persistent components

**Key Features:**

- Custom ID parsing (`parse_article_id_from_custom_id`)
- Comprehensive logging (`log_persistent_interaction`)
- Error handling for missing messages/data

**Dependencies:**

- `SupabaseService` (save_to_reading_list, update_article_status, update_article_rating)
- `LLMService` (generate_deep_dive)

**Access Level:** Component library (registered in bot setup_hook)

---

### 5. **ReadingListCog** (`reading_list.py`)

**Single Responsibility:** Reading list management and recommendations

**Core Functions:**

- View reading list (`/reading_list view`)
- Generate AI recommendations (`/reading_list recommend`)
- Pagination for reading list items
- Article rating and status management

**Boundaries:**

- ✅ DOES: Manage reading list display and pagination
- ✅ DOES: Generate personalized recommendations based on ratings
- ✅ DOES: Provide UI for marking articles as read and rating
- ❌ DOES NOT: Handle initial article saving (delegates to InteractionsCog)
- ❌ DOES NOT: Fetch news articles (delegates to NewsCommands)

**Components Defined:**

- `MarkAsReadButton` - Mark article as read (reading list context)
- `RatingSelect` - Rate article 1-5 stars
- `PrevPageButton` / `NextPageButton` - Pagination controls
- `PaginationView` - Paginated reading list view
- `ReadingListGroup` - Slash command group

**Dependencies:**

- `SupabaseService` (get_reading_list, get_highly_rated_articles, update_article_status, update_article_rating)
- `LLMService` (generate_reading_recommendation)
- `app.bot.utils.validators` (validate_rating)

**Access Level:** All users

---

### 6. **SubscriptionCommands** (`subscription_commands.py`)

**Single Responsibility:** RSS feed subscription management

**Core Functions:**

- Add new feed subscription (`/add_feed`)
- List user subscriptions (`/list_feeds`)
- Unsubscribe from feeds (`/unsubscribe_feed`)
- Feed validation and sanitization

**Boundaries:**

- ✅ DOES: Manage user subscriptions to RSS feeds
- ✅ DOES: Create new feeds in database if they don't exist
- ✅ DOES: Validate and sanitize feed data
- ❌ DOES NOT: Fetch or display articles (delegates to NewsCommands)
- ❌ DOES NOT: Handle reading list operations (delegates to ReadingListCog)

**Dependencies:**

- `SupabaseService` (subscribe_to_feed, get_user_subscriptions, unsubscribe_from_feed)
- `app.bot.utils.decorators` (ensure_user_registered)
- `app.bot.utils.validators` (validate_and_sanitize_feed_data, validate_uuid)

**Access Level:** All users

---

### 7. **NotificationSettings** (`notification_settings.py`)

**Single Responsibility:** User notification preference management

**Core Functions:**

- Enable/disable DM notifications (`/notifications`)
- View notification status (`/notification_status`)

**Boundaries:**

- ✅ DOES: Manage user notification preferences
- ✅ DOES: Update notification settings in database
- ❌ DOES NOT: Send actual notifications (handled by DM notification service)
- ❌ DOES NOT: Manage subscriptions (delegates to SubscriptionCommands)

**Dependencies:**

- `SupabaseService` (update_notification_settings, get_notification_settings)

**Access Level:** All users

---

## Overlapping Functionality Analysis

### 🔴 **IDENTIFIED OVERLAPS**

#### 1. **User Registration**

- **Location:** `NewsCommands.ensure_user_registered()` (local helper function)
- **Issue:** User registration logic is duplicated in multiple places
- **Impact:** Inconsistent user registration behavior
- **Recommendation:**
  - ✅ Move to `app.bot.utils.decorators.ensure_user_registered` (already exists)
  - ✅ Remove local implementation from `news_commands.py`
  - ✅ Use decorator consistently across all cogs

#### 2. **Interactive Button Definitions**

- **Locations:**
  - `InteractionsCog`: ReadLaterButton, MarkReadButton, DeepDiveButton
  - `PersistentViews`: PersistentReadLaterButton, PersistentMarkReadButton, PersistentDeepDiveButton
  - `ReadingListCog`: MarkAsReadButton, RatingSelect
- **Issue:** Similar button logic implemented in multiple places
- **Impact:** Code duplication, inconsistent error handling
- **Recommendation:**
  - ✅ Keep separation between persistent and non-persistent components
  - ✅ Document when to use each type
  - ⚠️ Consider extracting common callback logic to shared service methods

#### 3. **Article Status Updates**

- **Locations:**
  - `InteractionsCog.MarkReadButton`
  - `PersistentViews.PersistentMarkReadButton`
  - `ReadingListCog.MarkAsReadButton`
- **Issue:** Same database operation called from multiple UI components
- **Impact:** Acceptable - different UI contexts require different components
- **Recommendation:** ✅ No change needed - this is proper separation of concerns

#### 4. **Rating Functionality**

- **Locations:**
  - `InteractionsCog.RatingSelect` (not currently implemented)
  - `PersistentViews.PersistentRatingSelect`
  - `ReadingListCog.RatingSelect`
- **Issue:** Rating UI only exists in ReadingListCog and PersistentViews
- **Impact:** Inconsistent - rating not available in news_now context
- **Recommendation:**
  - ⚠️ Consider adding rating to InteractionsCog for consistency
  - ⚠️ Or document that rating is only available in reading list context

---

## Responsibility Boundaries

### **Command Layer** (Slash Commands)

- `AdminCommands` - System operations
- `NewsCommands` - Content delivery
- `SubscriptionCommands` - Subscription management
- `NotificationSettings` - Notification preferences
- `ReadingListCog` - Reading list operations

**Rule:** Commands should delegate business logic to services, not implement it directly.

---

### **UI Component Layer** (Buttons, Selects, Views)

- `InteractionsCog` - Non-persistent interactive components
- `PersistentViews` - Persistent interactive components (survive bot restarts)

**Rule:** UI components should call services for data operations, not implement business logic.

---

### **Service Layer** (Business Logic)

- `SupabaseService` - Database operations
- `LLMService` - AI/LLM operations
- `RSSService` - RSS feed parsing
- `DMNotificationService` - Notification delivery

**Rule:** Services should be stateless and reusable across cogs.

---

## Data Flow Patterns

### **Pattern 1: User Command → Service → Database**

```
User executes /add_feed
  → SubscriptionCommands.add_feed()
    → validate_and_sanitize_feed_data()
    → ensure_user_registered()
    → SupabaseService.subscribe_to_feed()
      → Database INSERT
```

### **Pattern 2: User Command → Query → UI Components**

```
User executes /news_now
  → NewsCommands.news_now()
    → ensure_user_registered()
    → SupabaseService.get_user_subscriptions()
    → SupabaseService.query_articles()
    → InteractionsCog.ReadLaterView (with buttons)
      → User clicks button
        → InteractionsCog.ReadLaterButton.callback()
          → SupabaseService.save_to_reading_list()
```

### **Pattern 3: Persistent Interaction → State Reconstruction → Service**

```
Bot restarts
  → User clicks persistent button
    → PersistentViews.PersistentReadLaterButton.callback()
      → parse_article_id_from_custom_id()
      → SupabaseService.save_to_reading_list()
      → log_persistent_interaction()
```

---

## Consolidation Recommendations

### **High Priority**

1. **Consolidate User Registration**
   - Remove `ensure_user_registered()` from `news_commands.py`
   - Use `@ensure_user_registered` decorator from `app.bot.utils.decorators`
   - Apply consistently across all cogs

2. **Document Component Selection Guidelines**
   - Create decision tree: When to use persistent vs non-persistent components
   - Document timeout behavior and bot restart implications

### **Medium Priority**

3. **Extract Common Error Handling**
   - Create shared error response builders
   - Standardize error messages across cogs
   - Centralize logging patterns

4. **Standardize Service Access**
   - Consider dependency injection for services
   - Avoid creating new service instances in every method
   - Implement service singleton pattern

### **Low Priority**

5. **Consider Cog Merging**
   - `InteractionsCog` + `PersistentViews` → Single "Components" cog with persistent/non-persistent sections
   - Evaluate if separation provides value or just adds complexity

---

## Testing Boundaries

### **Unit Test Scope by Cog**

- **AdminCommands**: Mock scheduler functions, test command responses
- **NewsCommands**: Mock SupabaseService, test article filtering and formatting
- **InteractionsCog**: Test button callbacks, view composition
- **PersistentViews**: Test custom_id parsing, state reconstruction
- **ReadingListCog**: Test pagination logic, recommendation generation
- **SubscriptionCommands**: Test feed validation, subscription logic
- **NotificationSettings**: Test preference updates

### **Integration Test Scope**

- User flow: Subscribe → Fetch news → Save to reading list → Rate article
- Persistent interaction: Bot restart → Button still works
- Error handling: Database failure → User sees friendly error

---

## Future Considerations

### **Potential New Cogs**

1. **AnalyticsCog** - User behavior tracking and insights
2. **OnboardingCog** - New user onboarding flow
3. **FeedbackCog** - User feedback and bug reporting

### **Potential Cog Splits**

1. **InteractionsCog** → Split into:
   - `ButtonsCog` - Button definitions
   - `SelectsCog` - Select menu definitions
   - `ViewsCog` - View composition

### **Potential Cog Merges**

1. **NotificationSettings** + **SubscriptionCommands** → `UserPreferencesCog`
   - Rationale: Both manage user preferences
   - Benefit: Single source of truth for user settings

---

## Conclusion

The current 7-cog architecture provides good separation of concerns with clear boundaries:

- **AdminCommands**: System operations
- **NewsCommands**: Content delivery
- **InteractionsCog**: UI components (non-persistent)
- **PersistentViews**: UI components (persistent)
- **ReadingListCog**: Reading list management
- **SubscriptionCommands**: Subscription management
- **NotificationSettings**: Notification preferences

**Key Improvements Needed:**

1. Consolidate user registration logic
2. Document component selection guidelines
3. Standardize error handling patterns

**Overlaps Identified:**

1. User registration (needs consolidation)
2. Button definitions (acceptable - different contexts)
3. Service calls (acceptable - proper separation of concerns)

This documentation serves as the foundation for maintaining clear responsibility boundaries as the bot evolves.
