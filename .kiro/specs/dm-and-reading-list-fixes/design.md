# DM and Reading List Fixes Bugfix Design

## Overview

This design addresses three critical bugs affecting the tech news agent's DM notification system and reading list functionality:

1. **DM Notification Duplicates**: Users receive the same articles repeatedly in weekly digest notifications because the system doesn't track which articles have been sent
2. **Frontend Undefined article_id**: Frontend components fail to validate article_id before API calls, sending "undefined" and causing 400/422 errors
3. **Null Rating Rejection**: Backend schema rejects null ratings, preventing users from clearing ratings once set

The fix strategy involves:

- Adding a new `dm_sent_articles` table to track sent notifications
- Modifying `get_user_articles()` to exclude previously sent articles
- Adding frontend validation to prevent undefined article_id
- Updating `UpdateRatingRequest` schema to accept null values

## Glossary

- **Bug_Condition_1 (C1)**: DM notification query includes articles already sent to the user
- **Bug_Condition_2 (C2)**: Frontend API call with undefined or invalid article_id
- **Bug_Condition_3 (C3)**: Backend rating update request with null value
- **Property (P)**: The desired behavior for each bug condition
- **Preservation**: Existing functionality that must remain unchanged
- **dm_sent_articles**: New tracking table storing (user_id, article_id, sent_at) for DM notifications
- **get_user_articles()**: Method in `SupabaseService` that queries articles for DM notifications
- **UpdateRatingRequest**: Pydantic schema in `backend/app/schemas/reading_list.py` that validates rating updates
- **ReadingListItem**: Frontend component in `frontend/components/reading-list/ReadingListItem.tsx`
- **ArticleCard**: Frontend component in `frontend/components/ArticleCard.tsx`

## Bug Details

### Bug Condition 1: DM Notification Duplicates

The bug manifests when `send_personalized_digest()` is called multiple times for the same user over different weeks. The `get_user_articles()` method queries the last 7 days of articles from subscribed feeds without checking if they were already sent in previous notifications.

**Formal Specification:**

```
FUNCTION isBugCondition1(input)
  INPUT: input of type { discord_id: string, days: int, limit: int }
  OUTPUT: boolean

  RETURN input.days >= 1
         AND user_has_subscriptions(input.discord_id)
         AND articles_exist_in_timeframe(input.discord_id, input.days)
         AND NOT articles_filtered_by_sent_status(input.discord_id)
END FUNCTION
```

### Bug Condition 2: Frontend Undefined article_id

The bug manifests when frontend components (ReadingListItem, ArticleCard) call reading list API endpoints without ensuring article_id is defined. This occurs when the article object is malformed or the id property is missing.

**Formal Specification:**

```
FUNCTION isBugCondition2(input)
  INPUT: input of type { articleId: string | undefined, apiMethod: string }
  OUTPUT: boolean

  RETURN input.articleId === undefined
         OR input.articleId === null
         OR input.articleId === ''
         AND input.apiMethod IN ['addToReadingList', 'updateStatus', 'updateRating', 'removeFromReadingList']
END FUNCTION
```

### Bug Condition 3: Null Rating Rejection

The bug manifests when a user attempts to clear a rating by sending `{ rating: null }` to the PATCH `/api/reading-list/{article_id}/rating` endpoint. The `UpdateRatingRequest` schema only accepts integers 1-5, causing validation errors.

**Formal Specification:**

```
FUNCTION isBugCondition3(input)
  INPUT: input of type { rating: int | null }
  OUTPUT: boolean

  RETURN input.rating === null
         AND request_endpoint === '/api/reading-list/{article_id}/rating'
         AND request_method === 'PATCH'
END FUNCTION
```

### Examples

**Bug 1 Examples:**

- User receives DM on Week 1 with articles A, B, C (published in last 7 days)
- User receives DM on Week 2 with articles A, B, C, D, E (A, B, C are duplicates)
- Expected: Week 2 should only include D, E (new articles)

**Bug 2 Examples:**

- ArticleCard component calls `addToReadingList(article.id)` where `article.id` is undefined → API receives `{ article_id: "undefined" }` → 422 error
- ReadingListItem calls `onRemove(item.articleId)` where `item.articleId` is null → DELETE `/api/reading-list/null` → 400 error
- Expected: Frontend should validate article_id before API call or handle gracefully

**Bug 3 Examples:**

- User rates article with 4 stars, then clicks same star to clear rating → Frontend sends `{ rating: null }` → Backend returns 422 validation error
- Expected: Backend should accept null and remove rating from database

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

**For Bug 1 (DM Notifications):**

- `send_personalized_digest()` must continue to filter by user's subscribed feeds
- `send_personalized_digest()` must continue to limit results to the last 7 days
- `send_personalized_digest()` must continue to limit results to 20 articles maximum
- `send_personalized_digest()` must continue to order by tinkering_index descending
- DM embed formatting and content structure must remain unchanged

**For Bug 2 (Frontend Validation):**

- Reading list API endpoints with valid article_id must continue to work
- All existing API operations (add, remove, update status, update rating) must continue to function
- API error handling for other validation errors must remain unchanged

**For Bug 3 (Null Rating):**

- Backend must continue to accept and validate ratings 1-5
- Backend must continue to enforce integer constraint for non-null ratings
- Backend must continue to validate status values (Unread, Read, Archived)
- Database rating column must continue to allow NULL values (already nullable)

**Scope:**
All inputs that do NOT involve the three bug conditions should be completely unaffected by this fix. This includes:

- DM notifications for users with no previous sent articles
- Frontend API calls with valid article_id values
- Backend rating updates with valid integer values (1-5)
- All other reading list operations (status updates, article removal)

## Hypothesized Root Cause

Based on the bug descriptions and code analysis, the most likely issues are:

### Bug 1: DM Notification Duplicates

1. **Missing Sent Article Tracking**: The system has no table or mechanism to track which articles have been sent to which users
   - `get_user_articles()` only filters by time range (last 7 days) and subscriptions
   - No JOIN or WHERE clause excludes previously sent articles
   - Database schema lacks a `dm_sent_articles` or similar tracking table

2. **No Deduplication Logic**: The `send_personalized_digest()` method doesn't implement any deduplication
   - After successfully sending a DM, no record is created
   - Subsequent calls query the same time window without exclusions

### Bug 2: Frontend Undefined article_id

1. **Missing Validation Guards**: Frontend components don't validate article_id before API calls
   - `ReadingListItem.tsx` directly passes `item.articleId` without checking if it's defined
   - `ArticleCard.tsx` directly passes `article.id` without validation
   - No early return or error handling for undefined/null values

2. **Type Safety Not Enforced**: TypeScript types may allow undefined values
   - `ReadingListItem` type may have `articleId?: string` (optional)
   - Runtime validation doesn't match type definitions

3. **API Client Doesn't Validate**: The `apiClient` in `frontend/lib/api/readingList.ts` doesn't validate parameters
   - Functions accept `articleId: string` but don't check for undefined at runtime
   - URL construction with undefined creates invalid endpoints

### Bug 3: Null Rating Rejection

1. **Schema Too Restrictive**: `UpdateRatingRequest` schema only accepts integers 1-5
   - `rating: int = Field(..., ge=1, le=5)` uses required field with constraints
   - Pydantic validation rejects null before reaching business logic
   - Should be `rating: Optional[int] = Field(None, ge=1, le=5)`

2. **Validator Doesn't Handle Null**: The custom validator doesn't check for null
   - `@validator('rating')` assumes value is always present
   - Should handle None case explicitly

## Correctness Properties

Property 1: Bug Condition 1 - DM Notifications Exclude Sent Articles

_For any_ DM notification request where articles have been previously sent to the user (isBugCondition1 returns true), the fixed `get_user_articles()` function SHALL exclude those articles from the result set, ensuring users only receive new articles they haven't been notified about.

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition 2 - Frontend Validates article_id

_For any_ reading list API call where article_id is undefined, null, or empty (isBugCondition2 returns true), the fixed frontend components SHALL prevent the API call and handle the error gracefully (log warning, show toast, or skip operation), ensuring no invalid requests are sent to the backend.

**Validates: Requirements 2.3, 2.4**

Property 3: Bug Condition 3 - Backend Accepts Null Rating

_For any_ rating update request where rating is null (isBugCondition3 returns true), the fixed `UpdateRatingRequest` schema SHALL accept the null value and the backend SHALL update the database to set rating to NULL, allowing users to clear ratings.

**Validates: Requirements 2.5, 2.6**

Property 4: Preservation - Non-Buggy DM Notifications

_For any_ DM notification request where no articles have been previously sent (NOT isBugCondition1), the fixed `get_user_articles()` function SHALL produce the same result as the original function, preserving the existing behavior of filtering by subscriptions, time range, and tinkering_index.

**Validates: Requirements 3.1, 3.2, 3.3**

Property 5: Preservation - Valid Frontend API Calls

_For any_ reading list API call where article_id is valid (NOT isBugCondition2), the fixed frontend components SHALL produce the same behavior as the original components, preserving all existing API operations.

**Validates: Requirements 3.4, 3.5**

Property 6: Preservation - Valid Rating Updates

_For any_ rating update request where rating is an integer 1-5 (NOT isBugCondition3), the fixed `UpdateRatingRequest` schema SHALL produce the same validation behavior as the original schema, preserving integer constraint and range validation.

**Validates: Requirements 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

#### Bug 1: DM Notification Duplicates

**File**: `backend/scripts/init_supabase.sql` (or new migration file)

**Database Schema Changes**:

1. **Create `dm_sent_articles` table**:

   ```sql
   CREATE TABLE dm_sent_articles (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID REFERENCES users(id) ON DELETE CASCADE,
       article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
       sent_at TIMESTAMPTZ DEFAULT now(),
       UNIQUE(user_id, article_id)
   );

   CREATE INDEX idx_dm_sent_articles_user_id ON dm_sent_articles(user_id);
   CREATE INDEX idx_dm_sent_articles_sent_at ON dm_sent_articles(sent_at);
   ```

**File**: `backend/app/services/supabase_service.py`

**Function**: `get_user_articles()`

**Specific Changes**:

1. **Add LEFT JOIN to exclude sent articles**:
   - After querying subscriptions, add LEFT JOIN with `dm_sent_articles`
   - Add WHERE clause: `WHERE dm_sent_articles.id IS NULL`
   - This excludes articles that have a matching record in `dm_sent_articles`

2. **Example query modification**:

   ```python
   response = self.client.table('articles')\
       .select('id, title, url, published_at, tinkering_index, ai_summary, feed_id, feeds(category)')\
       .in_('feed_id', feed_ids)\
       .gte('published_at', cutoff_date.isoformat())\
       .not_.is_('tinkering_index', 'null')\
       .order('tinkering_index', desc=True)\
       .limit(limit)\
       .execute()
   ```

   Becomes:

   ```python
   # Use raw SQL or complex query to exclude sent articles
   query = f"""
   SELECT a.id, a.title, a.url, a.published_at, a.tinkering_index,
          a.ai_summary, a.feed_id, f.category
   FROM articles a
   JOIN feeds f ON a.feed_id = f.id
   LEFT JOIN dm_sent_articles dsa ON dsa.article_id = a.id AND dsa.user_id = '{user_uuid}'
   WHERE a.feed_id IN ({','.join(["'" + str(fid) + "'" for fid in feed_ids])})
     AND a.published_at >= '{cutoff_date.isoformat()}'
     AND a.tinkering_index IS NOT NULL
     AND dsa.id IS NULL
   ORDER BY a.tinkering_index DESC
   LIMIT {limit}
   """
   response = self.client.rpc('execute_sql', {'query': query}).execute()
   ```

3. **Add method to record sent articles**:
   ```python
   async def record_sent_articles(
       self,
       discord_id: str,
       article_ids: List[UUID]
   ) -> None:
       """Record articles that have been sent via DM notification"""
       user_uuid = await self.get_or_create_user(discord_id)

       records = [
           {'user_id': str(user_uuid), 'article_id': str(aid)}
           for aid in article_ids
       ]

       self.client.table('dm_sent_articles')\
           .upsert(records, on_conflict='user_id,article_id')\
           .execute()
   ```

**File**: `backend/app/services/dm_notification_service.py`

**Function**: `send_personalized_digest()`

**Specific Changes**:

1. **Record sent articles after successful DM**:
   - After `await user.send(embed=embed)` succeeds
   - Extract article IDs from `articles` list
   - Call `await supabase.record_sent_articles(discord_id, article_ids)`

2. **Example implementation**:
   ```python
   try:
       await user.send(embed=embed)

       # Record sent articles
       article_ids = [article.id for article in articles]  # Assuming ArticleSchema has id
       await supabase.record_sent_articles(discord_id, article_ids)

       logger.info(f"Successfully sent digest DM to user {discord_id}")
       return True
   except discord.Forbidden:
       # ... existing error handling
   ```

#### Bug 2: Frontend Undefined article_id

**File**: `frontend/components/reading-list/ReadingListItem.tsx`

**Specific Changes**:

1. **Add validation guards in event handlers**:

   ```typescript
   const handleStatusChange = async (status: ReadingListStatus) => {
     if (!item.articleId) {
       console.error('Cannot update status: article_id is undefined');
       return;
     }
     setLoadingAction('status');
     try {
       await onStatusChange(item.articleId, status);
     } finally {
       setLoadingAction(null);
     }
   };

   const handleRemove = async () => {
     if (!item.articleId) {
       console.error('Cannot remove article: article_id is undefined');
       return;
     }
     // ... rest of implementation
   };

   const handleRatingChange = async (rating: number | null) => {
     if (!item.articleId) {
       console.error('Cannot update rating: article_id is undefined');
       return;
     }
     // ... rest of implementation
   };
   ```

**File**: `frontend/components/ArticleCard.tsx`

**Specific Changes**:

1. **Add validation in handleAddToReadingList**:
   ```typescript
   const handleAddToReadingList = async () => {
     if (!article.id) {
       console.error('Cannot add to reading list: article.id is undefined');
       toast.error('Unable to add article: Invalid article data');
       return;
     }
     try {
       await addToReadingList.mutateAsync(article.id);
       setIsAdded(true);
     } catch (error) {
       console.error('Failed to add to reading list:', error);
     }
   };
   ```

**File**: `frontend/lib/api/readingList.ts`

**Specific Changes**:

1. **Add runtime validation in API functions**:

   ```typescript
   export async function addToReadingList(
     articleId: string,
   ): Promise<{ message: string; articleId: string }> {
     if (!articleId || articleId === 'undefined') {
       throw new Error('Invalid article_id: must be a valid UUID');
     }
     return apiClient.post('/api/reading-list', { article_id: articleId });
   }

   export async function updateReadingListStatus(
     articleId: string,
     status: ReadingListStatus,
   ): Promise<{ message: string; status: string }> {
     if (!articleId || articleId === 'undefined') {
       throw new Error('Invalid article_id: must be a valid UUID');
     }
     return apiClient.patch(`/api/reading-list/${articleId}/status`, {
       status,
     });
   }

   // Similar validation for updateReadingListRating and removeFromReadingList
   ```

#### Bug 3: Null Rating Rejection

**File**: `backend/app/schemas/reading_list.py`

**Schema**: `UpdateRatingRequest`

**Specific Changes**:

1. **Change rating field to Optional**:

   ```python
   class UpdateRatingRequest(BaseModel):
       """更新評分請求"""
       rating: Optional[int] = Field(None, ge=1, le=5, description="評分（1-5）或 null 清除評分")

       @validator('rating')
       def validate_rating(cls, v):
           if v is None:
               return v  # Allow null to clear rating
           if not isinstance(v, int):
               raise ValueError("Rating must be an integer or null")
           if not (1 <= v <= 5):
               raise ValueError("Rating must be between 1 and 5")
           return v
   ```

2. **Update docstring**:
   - Change description to indicate null is allowed
   - Update API documentation comments

**File**: `backend/app/api/reading_list.py`

**Function**: `update_reading_list_rating()`

**Specific Changes**:

1. **Handle null rating in database update**:
   - The existing code already handles this correctly: `{'rating': request.rating}`
   - PostgreSQL will set the column to NULL when `request.rating` is None
   - No changes needed in the endpoint logic

2. **Update logging to handle null**:
   ```python
   logger.info(
       f"Updating reading list rating",
       extra={
           "discord_id": discord_id,
           "article_id": str(article_id),
           "new_rating": request.rating if request.rating is not None else "null"
       }
   )
   ```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

#### Bug 1: DM Notification Duplicates

**Test Plan**: Create test data with users, subscriptions, and articles. Send DM notifications multiple times and verify that duplicate articles are sent. Run these tests on the UNFIXED code to observe failures.

**Test Cases**:

1. **First DM Send Test**: Send DM to user with 3 articles (will pass on unfixed code)
2. **Second DM Send Test**: Send DM again to same user, verify same 3 articles are sent (will demonstrate bug on unfixed code)
3. **New Articles Test**: Add 2 new articles, send DM, verify all 5 articles are sent instead of just 2 (will demonstrate bug on unfixed code)
4. **Multiple Users Test**: Verify tracking is per-user, not global (may pass or fail on unfixed code)

**Expected Counterexamples**:

- Same articles appear in multiple DM notifications to the same user
- Article count grows instead of showing only new articles
- Possible causes: no `dm_sent_articles` table, no LEFT JOIN exclusion, no recording after send

#### Bug 2: Frontend Undefined article_id

**Test Plan**: Create test scenarios with malformed article objects or missing id properties. Attempt to call reading list API functions and verify that "undefined" is sent to the backend. Run these tests on the UNFIXED code.

**Test Cases**:

1. **Undefined article.id Test**: Call `addToReadingList(undefined)` and verify 422 error (will fail on unfixed code)
2. **Null articleId Test**: Call `updateReadingListStatus(null, 'Read')` and verify 400 error (will fail on unfixed code)
3. **Empty string Test**: Call `removeFromReadingList('')` and verify 400 error (will fail on unfixed code)
4. **Component Integration Test**: Render ReadingListItem with `item.articleId = undefined` and click remove button (will fail on unfixed code)

**Expected Counterexamples**:

- API receives `{ article_id: "undefined" }` in request body
- API receives DELETE `/api/reading-list/undefined` in URL
- Backend returns 400 or 422 validation errors
- Possible causes: no validation guards, no runtime checks, TypeScript types not enforced

#### Bug 3: Null Rating Rejection

**Test Plan**: Attempt to send rating update requests with null values. Verify that backend rejects them with validation errors. Run these tests on the UNFIXED code.

**Test Cases**:

1. **Null Rating Test**: Send PATCH with `{ rating: null }` and verify 422 error (will fail on unfixed code)
2. **Clear Rating UI Test**: Click same star rating twice to clear, verify 422 error (will fail on unfixed code)
3. **Valid Rating Test**: Send PATCH with `{ rating: 3 }` and verify success (will pass on unfixed code)
4. **Invalid Rating Test**: Send PATCH with `{ rating: 6 }` and verify 422 error (will pass on unfixed code)

**Expected Counterexamples**:

- Backend returns 422 validation error: "Rating must be between 1 and 5"
- Pydantic validation rejects null before reaching business logic
- Possible causes: `rating: int = Field(..., ge=1, le=5)` doesn't allow None, validator doesn't handle null

### Fix Checking

**Goal**: Verify that for all inputs where the bug conditions hold, the fixed functions produce the expected behavior.

#### Bug 1: DM Notification Duplicates

**Pseudocode:**

```
FOR ALL input WHERE isBugCondition1(input) DO
  articles := get_user_articles_fixed(input.discord_id, input.days, input.limit)
  sent_articles := get_sent_articles(input.discord_id)
  ASSERT articles INTERSECT sent_articles = EMPTY_SET
  ASSERT all articles are NEW (not in sent_articles)
END FOR
```

**Property-Based Test Strategy**:

- Generate random users with random subscriptions
- Generate random articles in different time windows
- Send DM notifications multiple times
- Verify no duplicates across notifications
- Verify only new articles are included

#### Bug 2: Frontend Undefined article_id

**Pseudocode:**

```
FOR ALL input WHERE isBugCondition2(input) DO
  result := api_function_fixed(input.articleId, ...)
  ASSERT result is ERROR or EARLY_RETURN
  ASSERT NO API call was made to backend
  ASSERT error is logged or toast is shown
END FOR
```

**Property-Based Test Strategy**:

- Generate random invalid article_id values (undefined, null, '', 'undefined')
- Call each API function with invalid values
- Verify no network requests are made
- Verify error handling is triggered

#### Bug 3: Null Rating Rejection

**Pseudocode:**

```
FOR ALL input WHERE isBugCondition3(input) DO
  result := update_rating_fixed(article_id, null)
  ASSERT result is SUCCESS
  ASSERT database rating is NULL
  ASSERT response includes rating: null
END FOR
```

**Property-Based Test Strategy**:

- Generate random articles with existing ratings
- Send null rating updates
- Verify database is updated to NULL
- Verify API returns success

### Preservation Checking

**Goal**: Verify that for all inputs where the bug conditions do NOT hold, the fixed functions produce the same result as the original functions.

#### Bug 1: DM Notification Duplicates

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition1(input) DO
  ASSERT get_user_articles_original(input) = get_user_articles_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for users with no sent articles, then write property-based tests capturing that behavior.

**Test Cases**:

1. **First-Time User Test**: Observe that new users get all articles in time window on unfixed code, then verify this continues after fix
2. **Subscription Filtering Test**: Observe that only subscribed feeds are included on unfixed code, then verify this continues after fix
3. **Time Window Test**: Observe that only last 7 days are included on unfixed code, then verify this continues after fix
4. **Limit Test**: Observe that max 20 articles are returned on unfixed code, then verify this continues after fix
5. **Ordering Test**: Observe that articles are ordered by tinkering_index DESC on unfixed code, then verify this continues after fix

#### Bug 2: Frontend Undefined article_id

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition2(input) DO
  ASSERT api_function_original(input) = api_function_fixed(input)
END FOR
```

**Test Plan**: Observe behavior on UNFIXED code for valid article_id values, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Valid UUID Test**: Observe that valid UUIDs work correctly on unfixed code, then verify this continues after fix
2. **Add to Reading List Test**: Observe that adding articles works on unfixed code, then verify this continues after fix
3. **Update Status Test**: Observe that status updates work on unfixed code, then verify this continues after fix
4. **Update Rating Test**: Observe that rating updates work on unfixed code, then verify this continues after fix
5. **Remove Test**: Observe that removing articles works on unfixed code, then verify this continues after fix

#### Bug 3: Null Rating Rejection

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition3(input) DO
  ASSERT update_rating_original(input) = update_rating_fixed(input)
END FOR
```

**Test Plan**: Observe behavior on UNFIXED code for valid integer ratings (1-5), then write property-based tests capturing that behavior.

**Test Cases**:

1. **Valid Rating 1-5 Test**: Observe that ratings 1-5 work correctly on unfixed code, then verify this continues after fix
2. **Rating Validation Test**: Observe that ratings outside 1-5 are rejected on unfixed code, then verify this continues after fix
3. **Non-Integer Test**: Observe that non-integer ratings are rejected on unfixed code, then verify this continues after fix
4. **Database Update Test**: Observe that database is updated correctly on unfixed code, then verify this continues after fix

### Unit Tests

**Bug 1: DM Notification Duplicates**

- Test `dm_sent_articles` table creation and constraints
- Test `record_sent_articles()` method with various inputs
- Test `get_user_articles()` with and without sent articles
- Test edge cases: empty sent articles, all articles sent, partial overlap

**Bug 2: Frontend Undefined article_id**

- Test validation guards in ReadingListItem handlers
- Test validation guards in ArticleCard handler
- Test API function validation with invalid inputs
- Test error logging and toast messages

**Bug 3: Null Rating Rejection**

- Test `UpdateRatingRequest` schema with null rating
- Test `UpdateRatingRequest` schema with valid ratings 1-5
- Test `UpdateRatingRequest` schema with invalid ratings
- Test database update with null rating

### Property-Based Tests

**Bug 1: DM Notification Duplicates**

- Generate random users, subscriptions, and articles
- Send multiple DM notifications over time
- Verify no article is sent twice to the same user
- Verify all new articles are included in notifications
- Verify sent articles are correctly recorded in database

**Bug 2: Frontend Undefined article_id**

- Generate random invalid article_id values
- Call all API functions with invalid values
- Verify no network requests are made
- Verify error handling is consistent across all functions

**Bug 3: Null Rating Rejection**

- Generate random articles with various rating states
- Send null rating updates
- Verify database is updated to NULL
- Verify valid ratings still work correctly

### Integration Tests

**Bug 1: DM Notification Duplicates**

- Test full DM notification flow: query articles → send DM → record sent articles
- Test multiple users receiving notifications simultaneously
- Test weekly digest schedule with overlapping time windows
- Test that sent articles persist across service restarts

**Bug 2: Frontend Undefined article_id**

- Test full reading list flow: render component → click action → API call
- Test error boundaries catch validation errors
- Test user sees appropriate error messages
- Test that valid operations still work after validation errors

**Bug 3: Null Rating Rejection**

- Test full rating flow: set rating → clear rating → set again
- Test rating UI updates correctly after clearing
- Test database state is consistent with UI state
- Test that clearing rating doesn't affect other reading list properties
