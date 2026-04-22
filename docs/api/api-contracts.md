# API Contracts and Type Definitions

> **Comprehensive API Documentation**
> This document defines all API contracts, type definitions, and interface specifications for the Tech News Agent application.
> Last Updated: 2024-12-19

---

## 📋 Overview

This document provides complete API contracts and type definitions for the Tech News Agent application. All APIs follow standardized response formats and include comprehensive TypeScript/Python type definitions for type safety.

### API Design Principles

- **Consistent Response Format**: All endpoints return standardized success/error responses
- **Type Safety**: Complete TypeScript and Python type definitions
- **RESTful Design**: Resource-based URLs with appropriate HTTP methods
- **Error Handling**: Standardized error codes and user-friendly messages
- **Pagination**: Consistent pagination metadata for list endpoints
- **Versioning**: API versioning support for backward compatibility

---

## 🌐 Base Configuration

### Base URLs

| Environment     | Base URL                                   |
| --------------- | ------------------------------------------ |
| **Development** | `http://localhost:8000`                    |
| **Staging**     | `https://staging-api.technews.example.com` |
| **Production**  | `https://api.technews.example.com`         |

### Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

### Content Type

All requests and responses use JSON:

```http
Content-Type: application/json
```

---

## 📊 Standardized Response Formats

### Success Response

```typescript
interface SuccessResponse<T> {
  data: T;
  metadata?: {
    pagination?: PaginationMetadata;
    timestamp: string;
    request_id: string;
  };
}
```

**Example**:

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Advanced TypeScript Patterns",
    "url": "https://example.com/article"
  },
  "metadata": {
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Error Response

```typescript
interface ErrorResponse {
  error: string;
  error_code: string;
  details?: ErrorDetail[];
  metadata: {
    timestamp: string;
    request_id: string;
  };
}

interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}
```

**Example**:

```json
{
  "error": "Validation failed",
  "error_code": "VALIDATION_FAILED",
  "details": [
    {
      "field": "title",
      "message": "Title is required",
      "code": "required"
    }
  ],
  "metadata": {
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Pagination Metadata

```typescript
interface PaginationMetadata {
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}
```

**Example**:

```json
{
  "data": [...],
  "metadata": {
    "pagination": {
      "total": 150,
      "page": 2,
      "page_size": 20,
      "has_next": true,
      "has_previous": true
    },
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

---

## 🔐 Authentication API

### POST /api/auth/discord/login

Initiate Discord OAuth2 login flow.

**Request**: No body required

**Response**: Redirects to Discord OAuth2 authorization URL

**Example**:

```http
POST /api/auth/discord/login
```

### GET /api/auth/discord/callback

Handle Discord OAuth2 callback and issue JWT token.

**Query Parameters**:

- `code` (string, required): OAuth2 authorization code
- `state` (string, optional): CSRF protection state

**Response**:

```typescript
interface AuthCallbackResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}
```

**Example**:

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 604800,
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "discord_id": "123456789012345678",
      "username": "john_doe",
      "avatar_url": "https://cdn.discordapp.com/avatars/...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

### GET /api/auth/me

Get current authenticated user information.

**Headers**: `Authorization: Bearer <token>`

**Response**:

```typescript
interface CurrentUserResponse {
  user: User;
}
```

### POST /api/auth/logout

Logout and revoke JWT token.

**Headers**: `Authorization: Bearer <token>`

**Response**: Empty success response

---

## 👤 User API

### User Type Definition

```typescript
interface User {
  id: string;
  discord_id: string;
  username: string;
  discriminator: string;
  avatar_url: string | null;
  email: string | null;
  created_at: string;
  updated_at: string;
}
```

```python
class User(BaseModel):
    id: UUID
    discord_id: str
    username: str
    discriminator: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

### GET /api/users/me

Get current user profile.

**Headers**: `Authorization: Bearer <token>`

**Response**: `SuccessResponse<User>`

### PUT /api/users/me

Update current user profile.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```typescript
interface UpdateUserRequest {
  username?: string;
  email?: string;
}
```

**Response**: `SuccessResponse<User>`

---

## 📰 Articles API

### Article Type Definition

```typescript
interface Article {
  id: string;
  title: string;
  url: string;
  feed_id: string;
  feed_name: string;
  feed_category: string;
  published_at: string;
  tinkering_index: number | null;
  ai_summary: string | null;
  embedding: number[] | null;
  created_at: string;
  updated_at: string;
}
```

```python
class Article(BaseModel):
    id: UUID
    title: str
    url: HttpUrl
    feed_id: UUID
    feed_name: str
    feed_category: str
    published_at: datetime
    tinkering_index: Optional[int] = Field(None, ge=1, le=5)
    ai_summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime
```

### GET /api/articles

Get articles for the authenticated user.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:

- `page` (integer, optional, default=1): Page number
- `page_size` (integer, optional, default=20): Items per page
- `category` (string, optional): Filter by feed category
- `tinkering_index` (integer, optional): Filter by tinkering index
- `published_after` (string, optional): ISO date string
- `search` (string, optional): Search in title and summary

**Response**: `SuccessResponse<Article[]>` with pagination metadata

**Example**:

```http
GET /api/articles?page=1&page_size=20&category=AI&tinkering_index=4
```

### GET /api/articles/{article_id}

Get a specific article by ID.

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:

- `article_id` (string, required): Article UUID

**Response**: `SuccessResponse<Article>`

**Errors**:

- `404`: Article not found
- `403`: Access denied (article not in user's subscribed feeds)

### POST /api/articles/{article_id}/deep-dive

Generate deep dive analysis for an article.

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:

- `article_id` (string, required): Article UUID

**Response**:

```typescript
interface DeepDiveResponse {
  analysis: string;
  generated_at: string;
}
```

---

## 📡 Feeds API

### Feed Type Definition

```typescript
interface Feed {
  id: string;
  name: string;
  url: string;
  category: string;
  description: string | null;
  is_active: boolean;
  last_fetched_at: string | null;
  article_count: number;
  created_at: string;
  updated_at: string;
}
```

```python
class Feed(BaseModel):
    id: UUID
    name: str
    url: HttpUrl
    category: str
    description: Optional[str] = None
    is_active: bool = True
    last_fetched_at: Optional[datetime] = None
    article_count: int = 0
    created_at: datetime
    updated_at: datetime
```

### GET /api/feeds

Get all available feeds.

**Query Parameters**:

- `page` (integer, optional, default=1): Page number
- `page_size` (integer, optional, default=50): Items per page
- `category` (string, optional): Filter by category
- `is_active` (boolean, optional): Filter by active status

**Response**: `SuccessResponse<Feed[]>` with pagination metadata

### POST /api/feeds

Create a new feed (admin only).

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```typescript
interface CreateFeedRequest {
  name: string;
  url: string;
  category: string;
  description?: string;
}
```

**Response**: `SuccessResponse<Feed>`

### GET /api/feeds/{feed_id}

Get a specific feed by ID.

**Path Parameters**:

- `feed_id` (string, required): Feed UUID

**Response**: `SuccessResponse<Feed>`

---

## 📚 User Subscriptions API

### Subscription Type Definition

```typescript
interface UserSubscription {
  id: string;
  user_id: string;
  feed_id: string;
  feed: Feed;
  subscribed_at: string;
}
```

```python
class UserSubscription(BaseModel):
    id: UUID
    user_id: UUID
    feed_id: UUID
    feed: Feed
    subscribed_at: datetime
```

### GET /api/subscriptions

Get user's feed subscriptions.

**Headers**: `Authorization: Bearer <token>`

**Response**: `SuccessResponse<UserSubscription[]>`

### POST /api/subscriptions

Subscribe to a feed.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```typescript
interface SubscribeRequest {
  feed_id: string;
}
```

**Response**: `SuccessResponse<UserSubscription>`

**Errors**:

- `404`: Feed not found
- `409`: Already subscribed to this feed

### DELETE /api/subscriptions/{feed_id}

Unsubscribe from a feed.

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:

- `feed_id` (string, required): Feed UUID

**Response**: Empty success response

**Errors**:

- `404`: Subscription not found

---

## 📖 Reading List API

### Reading List Item Type Definition

```typescript
interface ReadingListItem {
  id: string;
  user_id: string;
  article_id: string;
  article: Article;
  status: 'Unread' | 'Read' | 'Archived';
  rating: number | null;
  notes: string | null;
  added_at: string;
  updated_at: string;
}
```

```python
class ReadingListItem(BaseModel):
    id: UUID
    user_id: UUID
    article_id: UUID
    article: Article
    status: Literal["Unread", "Read", "Archived"]
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    added_at: datetime
    updated_at: datetime
```

### GET /api/reading-list

Get user's reading list.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:

- `page` (integer, optional, default=1): Page number
- `page_size` (integer, optional, default=20): Items per page
- `status` (string, optional): Filter by status ("Unread", "Read", "Archived")
- `rating` (integer, optional): Filter by rating (1-5)

**Response**: `SuccessResponse<ReadingListItem[]>` with pagination metadata

### POST /api/reading-list

Add article to reading list.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```typescript
interface AddToReadingListRequest {
  article_id: string;
  notes?: string;
}
```

**Response**: `SuccessResponse<ReadingListItem>`

**Errors**:

- `404`: Article not found
- `409`: Article already in reading list

### PUT /api/reading-list/{item_id}

Update reading list item.

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:

- `item_id` (string, required): Reading list item UUID

**Request Body**:

```typescript
interface UpdateReadingListItemRequest {
  status?: 'Unread' | 'Read' | 'Archived';
  rating?: number | null;
  notes?: string | null;
}
```

**Response**: `SuccessResponse<ReadingListItem>`

### DELETE /api/reading-list/{item_id}

Remove item from reading list.

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:

- `item_id` (string, required): Reading list item UUID

**Response**: Empty success response

---

## 🤖 Recommendations API

### GET /api/recommendations

Get personalized article recommendations.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:

- `limit` (integer, optional, default=10): Number of recommendations

**Response**:

```typescript
interface RecommendationsResponse {
  recommendations: Article[];
  reasoning: string;
  generated_at: string;
}
```

### POST /api/recommendations/feedback

Provide feedback on recommendations.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```typescript
interface RecommendationFeedbackRequest {
  article_id: string;
  feedback: 'helpful' | 'not_helpful' | 'irrelevant';
  notes?: string;
}
```

**Response**: Empty success response

---

## 📊 Analytics API

### GET /api/analytics/reading-stats

Get user's reading statistics.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:

- `period` (string, optional, default="month"): "week", "month", "quarter", "year"

**Response**:

```typescript
interface ReadingStatsResponse {
  period: string;
  articles_read: number;
  articles_added: number;
  average_rating: number;
  top_categories: Array<{
    category: string;
    count: number;
  }>;
  reading_streak: number;
  total_reading_time_minutes: number;
}
```

---

## 🔧 System API

### GET /api/health

System health check.

**Response**:

```typescript
interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  checks: {
    database: boolean;
    external_apis: boolean;
    cache: boolean;
    scheduler: boolean;
  };
  timestamp: string;
}
```

### GET /api/health/scheduler

Scheduler-specific health check.

**Response**:

```typescript
interface SchedulerHealthResponse {
  is_healthy: boolean;
  last_execution_time: string | null;
  articles_processed: number;
  failed_operations: number;
  total_operations: number;
  issues: string[];
}
```

### POST /api/logs

Receive frontend logs (internal endpoint).

**Request Body**:

```typescript
interface LogsRequest {
  logs: Array<{
    timestamp: string;
    level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
    message: string;
    context?: Record<string, any>;
    userAgent?: string;
    url?: string;
    userId?: string;
  }>;
}
```

**Response**: Empty success response

---

## 🚨 Error Codes

### Authentication Errors (401, 403)

| Code                            | Description                       | HTTP Status |
| ------------------------------- | --------------------------------- | ----------- |
| `AUTH_INVALID_TOKEN`            | JWT token is invalid or malformed | 401         |
| `AUTH_TOKEN_EXPIRED`            | JWT token has expired             | 401         |
| `AUTH_MISSING_TOKEN`            | Authorization header is missing   | 401         |
| `AUTH_INSUFFICIENT_PERMISSIONS` | User lacks required permissions   | 403         |
| `AUTH_OAUTH_FAILED`             | Discord OAuth2 flow failed        | 401         |

### Validation Errors (422)

| Code                        | Description                     | HTTP Status |
| --------------------------- | ------------------------------- | ----------- |
| `VALIDATION_FAILED`         | Request validation failed       | 422         |
| `VALIDATION_MISSING_FIELD`  | Required field is missing       | 422         |
| `VALIDATION_INVALID_FORMAT` | Field format is invalid         | 422         |
| `VALIDATION_BUSINESS_RULE`  | Business rule validation failed | 422         |

### Resource Errors (404, 409)

| Code                      | Description                  | HTTP Status |
| ------------------------- | ---------------------------- | ----------- |
| `RESOURCE_NOT_FOUND`      | Requested resource not found | 404         |
| `RESOURCE_ALREADY_EXISTS` | Resource already exists      | 409         |
| `RESOURCE_CONFLICT`       | Resource state conflict      | 409         |

### External Service Errors (502, 503)

| Code                           | Description                        | HTTP Status |
| ------------------------------ | ---------------------------------- | ----------- |
| `EXTERNAL_SERVICE_UNAVAILABLE` | External service is unavailable    | 503         |
| `EXTERNAL_SERVICE_TIMEOUT`     | External service request timed out | 504         |
| `EXTERNAL_API_ERROR`           | External API returned an error     | 502         |
| `EXTERNAL_RSS_FETCH_FAILED`    | RSS feed fetch failed              | 502         |
| `EXTERNAL_LLM_ERROR`           | LLM service error                  | 502         |

### Rate Limiting (429)

| Code                  | Description             | HTTP Status |
| --------------------- | ----------------------- | ----------- |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | 429         |

### Internal Errors (500)

| Code                   | Description                    | HTTP Status |
| ---------------------- | ------------------------------ | ----------- |
| `INTERNAL_ERROR`       | Internal server error          | 500         |
| `INTERNAL_UNEXPECTED`  | Unexpected internal error      | 500         |
| `DB_CONNECTION_FAILED` | Database connection failed     | 500         |
| `DB_QUERY_FAILED`      | Database query failed          | 500         |
| `CONFIG_MISSING`       | Required configuration missing | 500         |
| `CONFIG_INVALID`       | Configuration is invalid       | 500         |

---

## 🔄 API Versioning

### Version Header

Include API version in requests:

```http
API-Version: v1
```

### Version in URL (Alternative)

```http
GET /api/v1/articles
```

### Deprecation Notice

Deprecated endpoints include deprecation headers:

```http
Deprecation: true
Sunset: 2025-06-01T00:00:00Z
Link: </api/v2/articles>; rel="successor-version"
```

---

## 📝 Request/Response Examples

### Complete Article Listing Example

**Request**:

```http
GET /api/articles?page=1&page_size=5&category=AI HTTP/1.1
Host: api.technews.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
API-Version: v1
```

**Response**:

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Advanced Machine Learning Techniques",
      "url": "https://example.com/ml-techniques",
      "feed_id": "456e7890-e89b-12d3-a456-426614174001",
      "feed_name": "AI Research Blog",
      "feed_category": "AI",
      "published_at": "2024-12-18T15:30:00Z",
      "tinkering_index": 4,
      "ai_summary": "This article explores advanced ML techniques including...",
      "embedding": null,
      "created_at": "2024-12-18T16:00:00Z",
      "updated_at": "2024-12-18T16:00:00Z"
    }
  ],
  "metadata": {
    "pagination": {
      "total": 150,
      "page": 1,
      "page_size": 5,
      "has_next": true,
      "has_previous": false
    },
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Error Response Example

**Request**:

```http
POST /api/reading-list HTTP/1.1
Host: api.technews.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "article_id": "invalid-uuid"
}
```

**Response**:

```json
{
  "error": "Validation failed",
  "error_code": "VALIDATION_FAILED",
  "details": [
    {
      "field": "article_id",
      "message": "Invalid UUID format",
      "code": "invalid_uuid"
    }
  ],
  "metadata": {
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_987654321"
  }
}
```

---

## 🛠️ Client SDK Examples

### TypeScript/JavaScript Client

```typescript
import { apiClient } from './lib/api/client';

// Get articles
const articles = await apiClient.get<SuccessResponse<Article[]>>('/api/articles');

// Add to reading list
const readingListItem = await apiClient.post<SuccessResponse<ReadingListItem>>(
  '/api/reading-list',
  { article_id: '123e4567-e89b-12d3-a456-426614174000' }
);

// Handle errors
try {
  const article = await apiClient.get<SuccessResponse<Article>>('/api/articles/invalid-id');
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`API Error: ${error.message} (${error.code})`);
  }
}
```

### Python Client

```python
import httpx
from typing import Optional, List

class TechNewsClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"} if token else {}
        )

    async def get_articles(self, page: int = 1, category: Optional[str] = None) -> List[Article]:
        params = {"page": page}
        if category:
            params["category"] = category

        response = await self.client.get("/api/articles", params=params)
        response.raise_for_status()

        data = response.json()
        return [Article(**article) for article in data["data"]]

    async def add_to_reading_list(self, article_id: str) -> ReadingListItem:
        response = await self.client.post(
            "/api/reading-list",
            json={"article_id": article_id}
        )
        response.raise_for_status()

        data = response.json()
        return ReadingListItem(**data["data"])
```

---

## 📚 OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

- **Development**: `http://localhost:8000/docs`
- **Production**: `https://api.technews.example.com/docs`

### Generate Client SDKs

```bash
# Generate TypeScript client
openapi-generator-cli generate \
  -i https://api.technews.example.com/openapi.json \
  -g typescript-axios \
  -o ./generated/typescript-client

# Generate Python client
openapi-generator-cli generate \
  -i https://api.technews.example.com/openapi.json \
  -g python \
  -o ./generated/python-client
```

---

## 🔍 Testing API Contracts

### Contract Testing

```typescript
// API contract tests
describe('Articles API Contract', () => {
  test('GET /api/articles returns correct structure', async () => {
    const response = await apiClient.get('/api/articles');

    expect(response).toMatchObject({
      data: expect.arrayContaining([
        expect.objectContaining({
          id: expect.any(String),
          title: expect.any(String),
          url: expect.any(String),
          feed_id: expect.any(String),
          published_at: expect.any(String),
        }),
      ]),
      metadata: expect.objectContaining({
        pagination: expect.objectContaining({
          total: expect.any(Number),
          page: expect.any(Number),
          page_size: expect.any(Number),
          has_next: expect.any(Boolean),
          has_previous: expect.any(Boolean),
        }),
        timestamp: expect.any(String),
        request_id: expect.any(String),
      }),
    });
  });
});
```

### Schema Validation

```python
import pytest
from pydantic import ValidationError

def test_article_schema_validation():
    # Valid article data
    valid_data = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Test Article",
        "url": "https://example.com/article",
        "feed_id": "456e7890-e89b-12d3-a456-426614174001",
        "feed_name": "Test Feed",
        "feed_category": "Tech",
        "published_at": "2024-12-19T10:30:00Z",
        "created_at": "2024-12-19T10:30:00Z",
        "updated_at": "2024-12-19T10:30:00Z"
    }

    article = Article(**valid_data)
    assert article.title == "Test Article"

    # Invalid data should raise ValidationError
    invalid_data = {**valid_data, "tinkering_index": 10}  # Invalid range

    with pytest.raises(ValidationError):
        Article(**invalid_data)
```

---

**Document Version**: 1.0.0
**Last Updated**: 2024-12-19
**Next Review**: 2025-03-19

This API documentation serves as the definitive reference for all client integrations and provides complete type safety through comprehensive TypeScript and Python type definitions.
