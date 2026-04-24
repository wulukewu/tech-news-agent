# Implementation Plan

## Bug Condition Exploration Tests (BEFORE Fix)

- [x] 1. Write bug condition exploration test for DM notification duplicates
  - **Property 1: Bug Condition** - DM Notifications Send Duplicate Articles
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate duplicate articles are sent
  - **Scoped PBT Approach**: Create test data with users, subscriptions, and articles. Send DM notifications multiple times and verify that duplicate articles are sent
  - Test implementation details from Bug Condition 1 in design:
    - User has subscriptions to feeds
    - Articles exist in the last 7 days timeframe
    - Articles are NOT filtered by sent status
    - Same articles appear in multiple DM notifications
  - The test assertions should match the Expected Behavior Properties from design:
    - For any DM notification request where articles have been previously sent, the system SHALL exclude those articles from the result set
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found:
    - Same 3 articles sent in Week 1 and Week 2 notifications
    - Article count grows instead of showing only new articles
    - No dm_sent_articles table exists or no LEFT JOIN exclusion
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Write bug condition exploration test for frontend undefined article_id
  - **Property 1: Bug Condition** - Frontend Sends Undefined article_id to API
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate undefined article_id is sent to backend
  - **Scoped PBT Approach**: Create test scenarios with malformed article objects or missing id properties. Attempt to call reading list API functions and verify that "undefined" is sent to the backend
  - Test implementation details from Bug Condition 2 in design:
    - article_id is undefined, null, or empty string
    - API method is one of: addToReadingList, updateStatus, updateRating, removeFromReadingList
    - Frontend makes API call without validation
  - The test assertions should match the Expected Behavior Properties from design:
    - For any reading list API call where article_id is undefined/null/empty, the system SHALL prevent the API call and handle the error gracefully
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found:
    - API receives { article_id: "undefined" } in request body
    - API receives DELETE /api/reading-list/undefined in URL
    - Backend returns 400 or 422 validation errors
    - No validation guards in frontend components
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.3, 1.4, 2.3, 2.4_

- [x] 3. Write bug condition exploration test for null rating rejection
  - **Property 1: Bug Condition** - Backend Rejects Null Rating Values
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate null ratings are rejected
  - **Scoped PBT Approach**: Attempt to send rating update requests with null values. Verify that backend rejects them with validation errors
  - Test implementation details from Bug Condition 3 in design:
    - Rating value is null
    - Request endpoint is /api/reading-list/{article_id}/rating
    - Request method is PATCH
    - UpdateRatingRequest schema rejects null
  - The test assertions should match the Expected Behavior Properties from design:
    - For any rating update request where rating is null, the system SHALL accept the null value and update the database to set rating to NULL
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found:
    - Backend returns 422 validation error: "Rating must be between 1 and 5"
    - Pydantic validation rejects null before reaching business logic
    - UpdateRatingRequest schema: rating: int = Field(..., ge=1, le=5) doesn't allow None
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.5, 1.6, 2.5, 2.6_

## Preservation Property Tests (BEFORE Fix)

- [x] 4. Write preservation property tests for DM notifications (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Buggy DM Notification Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for users with no sent articles (first-time users):
    - New users get all articles in time window (last 7 days)
    - Only subscribed feeds are included
    - Max 20 articles are returned
    - Articles are ordered by tinkering_index DESC
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For any DM notification request where no articles have been previously sent, the system SHALL produce the same result as the original function
    - Subscription filtering is preserved
    - Time window filtering (last 7 days) is preserved
    - Limit (20 articles max) is preserved
    - Ordering (tinkering_index DESC) is preserved
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. Write preservation property tests for frontend valid article_id (BEFORE implementing fix)
  - **Property 2: Preservation** - Valid Frontend API Calls Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for valid article_id values:
    - Valid UUIDs work correctly
    - Adding articles to reading list succeeds
    - Status updates work correctly
    - Rating updates work correctly
    - Removing articles works correctly
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For any reading list API call where article_id is valid, the system SHALL produce the same behavior as the original components
    - All existing API operations continue to function
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.4, 3.5_

- [x] 6. Write preservation property tests for valid rating updates (BEFORE implementing fix)
  - **Property 2: Preservation** - Valid Rating Update Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for valid integer ratings (1-5):
    - Ratings 1-5 work correctly
    - Ratings outside 1-5 are rejected
    - Non-integer ratings are rejected
    - Database is updated correctly
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For any rating update request where rating is an integer 1-5, the system SHALL produce the same validation behavior as the original schema
    - Integer constraint is preserved
    - Range validation (1-5) is preserved
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.6, 3.7_

## Implementation

- [x] 7. Fix for DM notification duplicates
  - [x] 7.1 Create database migration for dm_sent_articles table
    - Create new migration file in backend/scripts/ or appropriate migrations directory
    - Add CREATE TABLE statement for dm_sent_articles:
      - id UUID PRIMARY KEY DEFAULT gen_random_uuid()
      - user_id UUID REFERENCES users(id) ON DELETE CASCADE
      - article_id UUID REFERENCES articles(id) ON DELETE CASCADE
      - sent_at TIMESTAMPTZ DEFAULT now()
      - UNIQUE(user_id, article_id) constraint
    - Add indexes:
      - idx_dm_sent_articles_user_id ON dm_sent_articles(user_id)
      - idx_dm_sent_articles_sent_at ON dm_sent_articles(sent_at)
    - Test migration runs successfully on development database
    - _Bug_Condition: isBugCondition1(input) where input.days >= 1 AND user_has_subscriptions AND articles_exist_in_timeframe AND NOT articles_filtered_by_sent_status_
    - _Expected_Behavior: Articles are excluded from result set if they exist in dm_sent_articles for the user_
    - _Preservation: Subscription filtering, time window filtering, limit, and ordering are preserved_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3_

  - [x] 7.2 Add record_sent_articles() method to SupabaseService
    - Open backend/app/services/supabase_service.py
    - Add new async method record_sent_articles(discord_id: str, article_ids: List[UUID])
    - Get user_uuid from discord_id using get_or_create_user()
    - Create records list with (user_id, article_id) tuples
    - Use upsert with on_conflict='user_id,article_id' to handle duplicates
    - Add error handling and logging
    - _Bug_Condition: isBugCondition1(input) where articles are sent but not recorded_
    - _Expected_Behavior: Sent articles are recorded in dm_sent_articles table_
    - _Preservation: No impact on existing methods_
    - _Requirements: 2.2_

  - [x] 7.3 Modify get_user_articles() to exclude sent articles
    - Open backend/app/services/supabase_service.py
    - Locate get_user_articles() method
    - Add LEFT JOIN with dm_sent_articles table on article_id and user_id
    - Add WHERE clause: dm_sent_articles.id IS NULL
    - Consider using raw SQL or RPC for complex query if needed
    - Preserve existing filters: feed_id IN subscriptions, published_at >= cutoff, tinkering_index IS NOT NULL
    - Preserve existing ordering: ORDER BY tinkering_index DESC
    - Preserve existing limit: LIMIT parameter
    - Test query returns correct results
    - _Bug_Condition: isBugCondition1(input) where query includes already sent articles_
    - _Expected_Behavior: Query excludes articles in dm_sent_articles for the user_
    - _Preservation: Subscription filtering, time window, limit, and ordering unchanged_
    - _Requirements: 2.1, 3.1, 3.2, 3.3_

  - [x] 7.4 Update send_personalized_digest() to record sent articles
    - Open backend/app/services/dm_notification_service.py
    - Locate send_personalized_digest() method
    - After successful await user.send(embed=embed), extract article IDs from articles list
    - Call await supabase.record_sent_articles(discord_id, article_ids)
    - Add error handling for recording failures (log but don't fail DM send)
    - Add logging for successful recording
    - _Bug_Condition: isBugCondition1(input) where articles are sent but not tracked_
    - _Expected_Behavior: Sent articles are recorded after successful DM send_
    - _Preservation: DM embed formatting and content structure unchanged_
    - _Requirements: 2.2_

  - [x] 7.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - DM Notifications Exclude Sent Articles
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify no duplicate articles are sent across multiple notifications
    - Verify only new articles are included in subsequent notifications
    - Verify dm_sent_articles table is populated correctly
    - _Requirements: 2.1, 2.2_

  - [x] 7.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy DM Notification Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 4 - do NOT write new tests
    - Run preservation property tests from step 4
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm subscription filtering still works
    - Confirm time window filtering still works
    - Confirm limit (20 articles) still works
    - Confirm ordering (tinkering_index DESC) still works
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 8. Fix for frontend undefined article_id
  - [x] 8.1 Add validation guards to ReadingListItem component
    - Open frontend/components/reading-list/ReadingListItem.tsx
    - Add validation check at start of handleStatusChange: if (!item.articleId) { console.error(...); return; }
    - Add validation check at start of handleRemove: if (!item.articleId) { console.error(...); return; }
    - Add validation check at start of handleRatingChange: if (!item.articleId) { console.error(...); return; }
    - Consider adding toast notification for user feedback on validation failure
    - Test component with undefined articleId values
    - _Bug_Condition: isBugCondition2(input) where input.articleId === undefined/null/'' AND input.apiMethod IN ['updateStatus', 'updateRating', 'removeFromReadingList']_
    - _Expected_Behavior: API call is prevented and error is handled gracefully_
    - _Preservation: Valid article_id operations continue to work_
    - _Requirements: 2.3, 2.4, 3.4, 3.5_

  - [x] 8.2 Add validation guards to ArticleCard component
    - Open frontend/components/ArticleCard.tsx
    - Locate handleAddToReadingList function
    - Add validation check at start: if (!article.id) { console.error(...); toast.error('Unable to add article: Invalid article data'); return; }
    - Test component with undefined article.id values
    - _Bug_Condition: isBugCondition2(input) where input.articleId === undefined AND input.apiMethod === 'addToReadingList'_
    - _Expected_Behavior: API call is prevented and user sees error toast_
    - _Preservation: Valid article.id operations continue to work_
    - _Requirements: 2.3, 2.4, 3.4, 3.5_

  - [x] 8.3 Add runtime validation to reading list API functions
    - Open frontend/lib/api/readingList.ts
    - Add validation to addToReadingList: if (!articleId || articleId === 'undefined') { throw new Error('Invalid article_id: must be a valid UUID'); }
    - Add validation to updateReadingListStatus: if (!articleId || articleId === 'undefined') { throw new Error(...); }
    - Add validation to updateReadingListRating: if (!articleId || articleId === 'undefined') { throw new Error(...); }
    - Add validation to removeFromReadingList: if (!articleId || articleId === 'undefined') { throw new Error(...); }
    - Test all functions with invalid article_id values
    - _Bug_Condition: isBugCondition2(input) where input.articleId === undefined/null/''_
    - _Expected_Behavior: Functions throw error before making API call_
    - _Preservation: Valid article_id operations continue to work_
    - _Requirements: 2.3, 2.4, 3.4, 3.5_

  - [x] 8.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Frontend Validates article_id
    - **IMPORTANT**: Re-run the SAME test from task 2 - do NOT write a new test
    - The test from task 2 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 2
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify no API calls are made with undefined article_id
    - Verify error handling is triggered appropriately
    - Verify user sees appropriate error messages
    - _Requirements: 2.3, 2.4_

  - [x] 8.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Valid Frontend API Calls Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 5 - do NOT write new tests
    - Run preservation property tests from step 5
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm valid UUID operations still work
    - Confirm all API operations (add, update, remove) still work
    - Confirm error handling for other validation errors unchanged
    - _Requirements: 3.4, 3.5_

- [x] 9. Fix for null rating rejection
  - [x] 9.1 Update UpdateRatingRequest schema to accept null
    - Open backend/app/schemas/reading_list.py
    - Locate UpdateRatingRequest class
    - Change rating field from: rating: int = Field(..., ge=1, le=5)
    - To: rating: Optional[int] = Field(None, ge=1, le=5, description="評分（1-5）或 null 清除評分")
    - Update @validator('rating') to handle None case:
      - if v is None: return v
      - if not isinstance(v, int): raise ValueError(...)
      - if not (1 <= v <= 5): raise ValueError(...)
    - Update docstring to indicate null is allowed
    - Test schema validation with null, valid integers, and invalid values
    - _Bug_Condition: isBugCondition3(input) where input.rating === null_
    - _Expected_Behavior: Schema accepts null and allows clearing rating_
    - _Preservation: Valid ratings 1-5 still validated correctly_
    - _Requirements: 2.5, 2.6, 3.6, 3.7_

  - [x] 9.2 Update logging in update_reading_list_rating endpoint
    - Open backend/app/api/reading_list.py
    - Locate update_reading_list_rating() function
    - Update logging to handle null rating: "new_rating": request.rating if request.rating is not None else "null"
    - Verify endpoint correctly passes null to database update
    - Test endpoint with null rating values
    - _Bug_Condition: isBugCondition3(input) where input.rating === null_
    - _Expected_Behavior: Endpoint accepts null and updates database to NULL_
    - _Preservation: Valid rating updates continue to work_
    - _Requirements: 2.5, 2.6_

  - [x] 9.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Backend Accepts Null Rating
    - **IMPORTANT**: Re-run the SAME test from task 3 - do NOT write a new test
    - The test from task 3 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 3
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify null rating is accepted by schema
    - Verify database is updated to NULL
    - Verify API returns success response
    - _Requirements: 2.5, 2.6_

  - [x] 9.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Valid Rating Update Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 6 - do NOT write new tests
    - Run preservation property tests from step 6
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm ratings 1-5 still work correctly
    - Confirm ratings outside 1-5 are still rejected
    - Confirm non-integer ratings are still rejected
    - Confirm integer constraint and range validation preserved
    - _Requirements: 3.6, 3.7_

## Integration Tests

- [x] 10. Integration test for DM notification flow
  - Test full flow: query articles → send DM → record sent articles → query again
  - Verify multiple users receiving notifications simultaneously
  - Verify weekly digest schedule with overlapping time windows
  - Verify sent articles persist across service restarts
  - Test edge cases: empty sent articles, all articles sent, partial overlap
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

- [x] 11. Integration test for frontend reading list flow
  - Test full flow: render component → click action → API call → UI update
  - Test error boundaries catch validation errors
  - Test user sees appropriate error messages
  - Test that valid operations still work after validation errors
  - Test all reading list operations: add, remove, update status, update rating
  - _Requirements: 2.3, 2.4, 3.4, 3.5_

- [x] 12. Integration test for rating management flow
  - Test full flow: set rating → clear rating → set again
  - Test rating UI updates correctly after clearing
  - Test database state is consistent with UI state
  - Test that clearing rating doesn't affect other reading list properties (status, added_at)
  - Test concurrent rating updates from multiple users
  - _Requirements: 2.5, 2.6, 3.6, 3.7, 3.8_

## Checkpoint

- [x] 13. Checkpoint - Ensure all tests pass
  - Run all bug condition exploration tests - verify they now PASS
  - Run all preservation property tests - verify they still PASS
  - Run all integration tests - verify they PASS
  - Run full test suite to catch any regressions
  - Verify no new errors in logs
  - Ask the user if questions arise or if manual testing is needed
