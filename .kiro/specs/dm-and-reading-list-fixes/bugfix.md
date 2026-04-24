# Bugfix Requirements Document

## Introduction

This document addresses three critical bugs in the tech news agent project affecting DM notifications and reading list functionality:

1. **DM Push Notifications Send Duplicate Articles** - Users receive the same articles repeatedly in weekly digest notifications due to lack of tracking for previously sent articles
2. **Reading List API Returns 400/422 Errors with "undefined"** - Frontend components fail to properly pass article_id, resulting in API validation errors
3. **Reading List Rating Cannot Be Cleared** - Backend schema rejects null ratings, preventing users from removing ratings once set

These bugs impact user experience by causing notification fatigue, API failures, and limiting rating management flexibility.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `send_personalized_digest()` is called for a user THEN the system queries the last 7 days of articles from subscribed feeds without checking if they were already sent

1.2 WHEN a user receives multiple DM notifications over time THEN the system sends the same articles repeatedly in each notification

1.3 WHEN frontend components call reading list API endpoints without a valid article_id THEN the system sends `undefined` as the article_id parameter

1.4 WHEN the backend receives `undefined` as article_id in OPTIONS or DELETE requests THEN the system returns 400 Bad Request or 422 Unprocessable Entity errors

1.5 WHEN a user attempts to clear a rating by sending `{ rating: null }` THEN the system rejects the request because the `UpdateRatingRequest` schema only accepts integers 1-5

1.6 WHEN the backend validates the rating field in `UpdateRatingRequest` THEN the system raises a validation error for null values

### Expected Behavior (Correct)

2.1 WHEN `send_personalized_digest()` is called for a user THEN the system SHALL query only NEW articles that have not been previously sent to that user

2.2 WHEN determining which articles to include in a DM notification THEN the system SHALL track which articles have been sent to each user and exclude them from future notifications

2.3 WHEN frontend components call reading list API endpoints THEN the system SHALL ensure a valid article_id is passed before making the API call

2.4 WHEN article_id is undefined or invalid in frontend components THEN the system SHALL prevent the API call or handle the error gracefully without sending invalid requests

2.5 WHEN a user attempts to clear a rating by sending `{ rating: null }` THEN the system SHALL accept the null value and remove the rating from the reading list item

2.6 WHEN the backend validates the rating field in `UpdateRatingRequest` THEN the system SHALL accept both integer values (1-5) and null values

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `send_personalized_digest()` queries articles for a user THEN the system SHALL CONTINUE TO filter by the user's subscribed feeds

3.2 WHEN `send_personalized_digest()` queries articles for a user THEN the system SHALL CONTINUE TO limit results to the last 7 days

3.3 WHEN `send_personalized_digest()` queries articles for a user THEN the system SHALL CONTINUE TO limit results to 20 articles maximum

3.4 WHEN frontend components call reading list API endpoints with valid article_id values THEN the system SHALL CONTINUE TO process requests successfully

3.5 WHEN the backend receives valid article_id parameters in API requests THEN the system SHALL CONTINUE TO perform the requested operations (add, remove, update status)

3.6 WHEN a user sets a valid rating (1-5) on a reading list item THEN the system SHALL CONTINUE TO accept and store the rating value

3.7 WHEN the backend validates rating values between 1-5 THEN the system SHALL CONTINUE TO enforce the integer constraint and range validation

3.8 WHEN the backend validates status values in reading list updates THEN the system SHALL CONTINUE TO enforce the allowed values (Unread, Read, Archived)
