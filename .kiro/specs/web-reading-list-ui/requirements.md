# Requirements Document: Web Reading List UI

## Introduction

The Web Reading List UI feature provides a complete frontend interface for users to manage their saved articles. Users can view their reading list with pagination, filter by status (Unread/Read/Archived), update article status and ratings, and remove articles. The feature integrates with the existing backend API and follows established design patterns from the dashboard and subscriptions pages.

## Glossary

- **Reading_List_Page**: The main page component that displays the user's saved articles
- **Reading_List_Item**: A single article entry in the reading list with associated metadata
- **Status_Filter**: A UI component allowing users to filter articles by status (Unread, Read, Archived)
- **Rating_Selector**: An interactive component for setting article ratings (1-5 stars)
- **Article_Card**: An existing component on the dashboard that displays article information
- **API_Client**: The frontend service layer that communicates with the backend API
- **React_Query**: A data fetching and caching library used for state management
- **Reading_List_Status**: An enumeration of valid status values: Unread, Read, Archived
- **JWT_Token**: JSON Web Token used for authentication
- **Optimistic_Update**: A UI pattern where changes are displayed immediately before server confirmation

## Requirements

### Requirement 1: Display Reading List

**User Story:** As a user, I want to view my saved articles in a reading list, so that I can access and manage articles I want to read.

#### Acceptance Criteria

1. WHEN a user navigates to the reading list page, THE Reading_List_Page SHALL fetch and display all reading list items for the authenticated user
2. WHEN the reading list is loading, THE Reading_List_Page SHALL display skeleton loaders for 3-4 items
3. WHEN the reading list is empty, THE Reading_List_Page SHALL display an empty state message with a link to browse articles
4. WHEN the reading list contains items, THE Reading_List_Page SHALL display each item with title, URL, category, status, added date, and rating
5. THE Reading_List_Page SHALL display items in a responsive grid layout that adapts to mobile, tablet, and desktop screen sizes

### Requirement 2: Filter by Status

**User Story:** As a user, I want to filter my reading list by status, so that I can focus on unread, read, or archived articles.

#### Acceptance Criteria

1. WHEN a user views the reading list, THE Status_Filter SHALL display tabs for All, Unread, Read, and Archived
2. WHEN a user clicks a status tab, THE Reading_List_Page SHALL fetch and display only items matching the selected status
3. WHEN a status filter is applied, THE Status_Filter SHALL highlight the active tab with primary color and underline
4. WHERE status counts are available, THE Status_Filter SHALL display the count of items for each status next to the tab label
5. WHEN the filtered results are loading, THE Reading_List_Page SHALL fade out current items and show a loading indicator

### Requirement 3: Paginate Reading List

**User Story:** As a user, I want to load more articles as I scroll, so that I can browse large reading lists efficiently.

#### Acceptance Criteria

1. WHEN the reading list contains more than 20 items, THE Reading_List_Page SHALL display a "Load More" button below the last item
2. WHEN a user clicks "Load More", THE Reading_List_Page SHALL fetch the next page of items and append them to the current list
3. WHEN loading more items, THE Reading_List_Page SHALL display a spinner below the last item and disable the "Load More" button
4. WHEN all items have been loaded, THE Reading_List_Page SHALL hide the "Load More" button
5. THE Reading_List_Page SHALL maintain the user's scroll position when new items are appended

### Requirement 4: Add Article to Reading List

**User Story:** As a user, I want to add articles to my reading list from the dashboard, so that I can save articles for later reading.

#### Acceptance Criteria

1. WHEN a user clicks "Add to Reading List" on an Article_Card, THE Article_Card SHALL send a request to add the article to the reading list
2. WHEN the add request is in progress, THE Article_Card SHALL display a loading spinner icon and disable the button
3. WHEN the add request succeeds, THE Article_Card SHALL display a success toast message "Added to reading list" and change the button icon to BookmarkCheck
4. WHEN the add request fails, THE Article_Card SHALL display an error toast message and revert the button to its original state
5. IF the article already exists in the reading list, THEN THE Article_Card SHALL display an info toast message "Article already in reading list" and disable the button

### Requirement 5: Update Article Status

**User Story:** As a user, I want to mark articles as read or archived, so that I can organize my reading list.

#### Acceptance Criteria

1. WHEN a user clicks "Mark as Read" on a Reading_List_Item, THE Reading_List_Item SHALL update the article status to "Read"
2. WHEN a user clicks "Mark as Archived" on a Reading_List_Item, THE Reading_List_Item SHALL update the article status to "Archived"
3. WHEN a status update is in progress, THE Reading_List_Item SHALL display a loading spinner in the action button and disable all action buttons
4. WHEN a status update succeeds, THE Reading_List_Page SHALL display a success toast message "Status updated" and refresh the reading list
5. WHEN a status update fails, THE Reading_List_Page SHALL display an error toast message "Failed to update status" and maintain the current status

### Requirement 6: Rate Articles

**User Story:** As a user, I want to rate articles with 1-5 stars, so that I can remember which articles I found most valuable.

#### Acceptance Criteria

1. WHEN a user clicks on a star in the Rating_Selector, THE Rating_Selector SHALL set the rating to the clicked star value (1-5)
2. WHEN a user clicks on the currently selected star, THE Rating_Selector SHALL clear the rating (set to null)
3. WHEN a user hovers over a star, THE Rating_Selector SHALL preview the rating by filling stars up to the hovered position
4. WHEN a rating update is in progress, THE Rating_Selector SHALL display a subtle loading indicator and disable star interactions
5. WHEN a rating update succeeds, THE Reading_List_Page SHALL display the updated rating immediately using optimistic updates
6. WHEN a rating update fails, THE Reading_List_Page SHALL revert to the previous rating value within 100ms and display an error toast

### Requirement 7: Remove Articles from Reading List

**User Story:** As a user, I want to remove articles from my reading list, so that I can keep my list focused on relevant content.

#### Acceptance Criteria

1. WHEN a user clicks "Remove" on a Reading_List_Item, THE Reading_List_Item SHALL send a request to delete the article from the reading list
2. WHEN the remove request is in progress, THE Reading_List_Item SHALL display a loading spinner in the remove button and disable all action buttons
3. WHEN the remove request succeeds, THE Reading_List_Page SHALL remove the item from the UI immediately and display a success toast "Removed from reading list"
4. WHEN the remove request fails, THE Reading_List_Page SHALL display an error toast "Failed to remove from reading list" and keep the item visible
5. WHEN an item is removed, THE Reading_List_Page SHALL update the total count and pagination state accordingly

### Requirement 8: Handle Authentication

**User Story:** As a system, I want to enforce authentication on the reading list, so that only authenticated users can access their reading lists.

#### Acceptance Criteria

1. THE Reading_List_Page SHALL be wrapped in a ProtectedRoute component that requires authentication
2. WHEN an unauthenticated user attempts to access the reading list, THE ProtectedRoute SHALL redirect to the login page
3. WHEN an API request returns a 401 status, THE API_Client SHALL remove the JWT_Token from localStorage and redirect to the login page
4. THE API_Client SHALL include the JWT_Token in the Authorization header for all reading list API requests
5. WHEN a user logs out, THE Reading_List_Page SHALL clear all cached reading list data

### Requirement 9: Cache and Optimize Data Fetching

**User Story:** As a user, I want the reading list to load quickly, so that I can access my articles without waiting.

#### Acceptance Criteria

1. THE React_Query SHALL cache reading list data for 30 seconds (staleTime)
2. WHEN a user switches between status filters, THE React_Query SHALL serve cached data if available and fetch fresh data in the background
3. WHEN a user returns to the reading list page, THE React_Query SHALL automatically refetch data if the cache is stale
4. WHEN multiple components request the same reading list data simultaneously, THE React_Query SHALL deduplicate requests and make only one API call
5. WHEN a mutation succeeds (add, update, remove), THE React_Query SHALL invalidate the reading list cache and trigger a refetch

### Requirement 10: Provide Keyboard Navigation

**User Story:** As a user who relies on keyboard navigation, I want to navigate the reading list using keyboard shortcuts, so that I can use the feature without a mouse.

#### Acceptance Criteria

1. WHEN a user presses Tab, THE Reading_List_Page SHALL move focus to the next interactive element in logical order
2. WHEN a user presses Enter or Space on a focused button, THE Reading_List_Page SHALL activate the button action
3. WHEN a user presses Arrow keys on the Status_Filter tabs, THE Status_Filter SHALL move focus between tabs
4. WHEN a user presses Arrow keys on a focused Rating_Selector, THE Rating_Selector SHALL change the rating value
5. THE Reading_List_Page SHALL display visible focus indicators (ring-2 ring-primary) on all focused interactive elements

### Requirement 11: Support Screen Readers

**User Story:** As a user who relies on screen readers, I want the reading list to be accessible, so that I can understand and interact with all features.

#### Acceptance Criteria

1. THE Reading_List_Item SHALL use semantic HTML elements (article, button, nav) for proper structure
2. THE Reading_List_Item SHALL provide ARIA labels on icon-only buttons (e.g., "Mark as read", "Remove from list")
3. THE Rating_Selector SHALL include an ARIA label describing the current rating (e.g., "Rate article 3 out of 5 stars")
4. WHEN a toast notification appears, THE Reading_List_Page SHALL use ARIA live regions to announce the message to screen readers
5. THE Status_Filter SHALL use ARIA selected attribute to indicate the active tab

### Requirement 12: Handle Network Errors

**User Story:** As a user, I want to see clear error messages when network issues occur, so that I understand what went wrong and can retry.

#### Acceptance Criteria

1. WHEN a reading list fetch fails due to network error, THE Reading_List_Page SHALL display an error toast "Failed to load reading list. Please try again."
2. WHEN a reading list fetch fails, THE Reading_List_Page SHALL display a retry button in place of the content
3. WHEN a user clicks the retry button, THE Reading_List_Page SHALL attempt to fetch the reading list again
4. THE React_Query SHALL automatically retry failed requests up to 2 times before showing an error
5. WHEN a server error (500) occurs, THE Reading_List_Page SHALL display an error toast "Something went wrong. Please try again later." without automatic retries

### Requirement 13: Validate Input Data

**User Story:** As a system, I want to validate all user input, so that only valid data is sent to the backend.

#### Acceptance Criteria

1. THE Rating_Selector SHALL only allow rating values between 1 and 5 inclusive, or null
2. THE Reading_List_Item SHALL only allow status values from the Reading_List_Status enumeration (Unread, Read, Archived)
3. THE API_Client SHALL validate that article IDs are valid UUIDs before sending requests
4. WHEN invalid data is detected, THE Reading_List_Page SHALL display an error toast with a descriptive message
5. THE Reading_List_Page SHALL use TypeScript types to enforce correct data types at compile time

### Requirement 14: Respect User Motion Preferences

**User Story:** As a user who prefers reduced motion, I want animations to be disabled, so that the interface is comfortable to use.

#### Acceptance Criteria

1. WHEN the user's system has prefers-reduced-motion enabled, THE Reading_List_Page SHALL disable all transition animations
2. WHEN the user's system has prefers-reduced-motion enabled, THE Reading_List_Page SHALL disable hover scale effects
3. WHEN the user's system has prefers-reduced-motion enabled, THE Reading_List_Page SHALL still provide visual feedback through color changes and opacity
4. THE Reading_List_Page SHALL use CSS media query (prefers-reduced-motion: reduce) to detect user preference
5. THE Reading_List_Page SHALL provide alternative feedback mechanisms that don't rely solely on animation

### Requirement 15: Display Relative Timestamps

**User Story:** As a user, I want to see when articles were added in relative time format, so that I can quickly understand recency.

#### Acceptance Criteria

1. WHEN a Reading_List_Item displays the added date, THE Reading_List_Item SHALL format it as relative time (e.g., "2 days ago", "3 hours ago")
2. WHEN an article was added less than 1 minute ago, THE Reading_List_Item SHALL display "just now"
3. WHEN an article was added more than 7 days ago, THE Reading_List_Item SHALL display the absolute date (e.g., "Jan 15, 2024")
4. THE Reading_List_Item SHALL use the date-fns library for consistent date formatting
5. THE Reading_List_Item SHALL update relative timestamps when the component re-renders

### Requirement 16: Maintain Color Contrast

**User Story:** As a user with visual impairments, I want sufficient color contrast, so that I can read all text clearly.

#### Acceptance Criteria

1. THE Reading_List_Page SHALL ensure all body text has a contrast ratio of at least 4.5:1 against the background (WCAG AA)
2. THE Status_Filter SHALL ensure status badge text has a contrast ratio of at least 4.5:1 in both light and dark modes
3. THE Rating_Selector SHALL ensure star icons are visible with sufficient contrast in both filled and empty states
4. THE Reading_List_Item SHALL ensure action button text has a contrast ratio of at least 4.5:1
5. THE Reading_List_Page SHALL not rely on color alone to convey status information (also use text labels)

### Requirement 17: Implement Responsive Layout

**User Story:** As a user on different devices, I want the reading list to adapt to my screen size, so that I have an optimal experience on any device.

#### Acceptance Criteria

1. WHEN viewed on mobile (375px-767px), THE Reading_List_Page SHALL display items in a single column with compact spacing
2. WHEN viewed on mobile, THE Reading_List_Item SHALL display action buttons as icon-only with horizontal scrolling tabs
3. WHEN viewed on tablet (768px-1023px), THE Reading_List_Page SHALL display items in a single column with medium spacing
4. WHEN viewed on desktop (1024px+), THE Reading_List_Page SHALL display items in a max-width container (max-w-6xl) with generous spacing
5. THE Reading_List_Page SHALL ensure no horizontal scrolling occurs on any screen size

### Requirement 18: Prevent XSS Attacks

**User Story:** As a system, I want to prevent cross-site scripting attacks, so that user data remains secure.

#### Acceptance Criteria

1. THE Reading_List_Item SHALL use React's built-in escaping for all text content (titles, URLs)
2. THE Reading_List_Item SHALL not use dangerouslySetInnerHTML for any user-generated content
3. THE Reading_List_Item SHALL sanitize URLs before rendering them as links
4. THE Reading_List_Page SHALL rely on Content Security Policy headers to prevent inline script execution
5. THE API_Client SHALL validate and sanitize all input data before sending to the backend

### Requirement 19: Implement Rate Limiting Protection

**User Story:** As a system, I want to prevent API abuse through rate limiting, so that the service remains available to all users.

#### Acceptance Criteria

1. THE React_Query SHALL deduplicate simultaneous requests to the same endpoint
2. THE Rating_Selector SHALL debounce rating updates by 300ms to prevent rapid successive requests
3. THE Reading_List_Item SHALL disable action buttons during API requests to prevent duplicate submissions
4. THE API_Client SHALL respect backend rate limiting responses (429 status) and display appropriate error messages
5. THE Reading_List_Page SHALL implement exponential backoff for retries after rate limit errors

### Requirement 20: Parse and Format API Responses

**User Story:** As a system, I want to correctly parse API responses, so that data is displayed accurately in the UI.

#### Acceptance Criteria

1. WHEN the API_Client receives a reading list response, THE API_Client SHALL parse the JSON response into ReadingListResponse type
2. WHEN the API_Client receives an error response, THE API_Client SHALL parse the error message and display it to the user
3. THE API_Client SHALL validate that all required fields are present in the API response before passing to components
4. WHEN the API response contains unexpected data types, THE API_Client SHALL log an error and display a generic error message
5. THE API_Client SHALL transform backend field names (snake_case) to frontend field names (camelCase) consistently
