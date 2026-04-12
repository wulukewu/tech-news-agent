# Auto-Generated API Types

This directory contains TypeScript type definitions automatically generated from backend Pydantic models.

## Overview

These types ensure type safety between the frontend and backend by automatically generating TypeScript interfaces from Python Pydantic schemas. This eliminates manual type synchronization and reduces the risk of type mismatches.

**Requirements Validated:**

- Requirement 1.5: Type-safe request/response handling
- Requirement 8.1: TypeScript interfaces for all API types
- Requirement 8.3: Automatic type updates when API contracts change

## Generated Files

- `responses.ts` - Standardized API response formats (SuccessResponse, ErrorResponse, PaginatedResponse)
- `article.ts` - Article-related types
- `reading_list.ts` - Reading list types
- `feed.ts` - Feed and subscription types
- `recommendation.ts` - Recommendation types
- `analytics.ts` - Analytics types
- `onboarding.ts` - Onboarding types
- `index.ts` - Re-exports all types

## Usage

### Import Types

```typescript
import {
  SuccessResponse,
  ErrorResponse,
  PaginatedResponse,
  ReadingListItemResponse,
  ArticleResponse,
} from '@/types/api';
```

### Use with API Client

```typescript
import { apiClient } from '@/lib/api';
import { ReadingListResponse, AddToReadingListRequest } from '@/types/api';

// Type-safe GET request
const response = await apiClient.get<ReadingListResponse>('/api/reading-list');

// Type-safe POST request
const request: AddToReadingListRequest = {
  article_id: '123e4567-e89b-12d3-a456-426614174000',
};
const result = await apiClient.post<MessageResponse>('/api/reading-list', request);
```

### Use with Standardized Responses

```typescript
import { SuccessResponse, PaginatedResponse, ArticleResponse } from '@/types/api';

// Success response
const response: SuccessResponse<ArticleResponse> = await apiClient.get('/api/articles/123');
console.log(response.data.title);

// Paginated response
const listResponse: PaginatedResponse<ArticleResponse> = await apiClient.get('/api/articles');
console.log(listResponse.data); // ArticleResponse[]
console.log(listResponse.pagination.total_count);
console.log(listResponse.pagination.has_next);
```

## Regenerating Types

Types are automatically generated from backend Pydantic models. To regenerate:

```bash
# From project root
npm run generate:types

# Or directly
python3 scripts/generate-types.py
```

**When to regenerate:**

- After adding new Pydantic models in `backend/app/schemas/`
- After modifying existing Pydantic model fields
- After changing field types or adding/removing fields
- Before committing API contract changes

## Type Generation Process

1. **Source**: Python Pydantic models in `backend/app/schemas/*.py`
2. **Script**: `scripts/generate-types.py` parses Python AST
3. **Output**: TypeScript interfaces in `frontend/types/api/*.ts`
4. **Mapping**: Python types → TypeScript types

### Type Mapping

| Python Type        | TypeScript Type       |
| ------------------ | --------------------- |
| `str`              | `string`              |
| `int`, `float`     | `number`              |
| `bool`             | `boolean`             |
| `datetime`, `date` | `string` (ISO 8601)   |
| `UUID`             | `string`              |
| `HttpUrl`          | `string`              |
| `Optional[T]`      | `T \| null`           |
| `List[T]`          | `T[]`                 |
| `Dict[K, V]`       | `Record<string, any>` |

### Field Aliases

Pydantic field aliases are automatically respected:

```python
# Python
class ReadingListItemResponse(BaseModel):
    article_id: UUID = Field(..., alias="articleId")
```

```typescript
// TypeScript
export interface ReadingListItemResponse {
  articleId: string; // Uses alias, not article_id
}
```

## CI/CD Integration

Add type generation to your CI pipeline to ensure types are always up-to-date:

```yaml
# .github/workflows/ci.yml
- name: Generate TypeScript types
  run: npm run generate:types

- name: Check for type changes
  run: |
    if [[ -n $(git status --porcelain frontend/types/api/) ]]; then
      echo "Error: Generated types are out of date"
      echo "Run 'npm run generate:types' and commit the changes"
      exit 1
    fi
```

## Best Practices

1. **Always regenerate after backend changes**: Run `npm run generate:types` after modifying Pydantic models
2. **Commit generated types**: Include generated types in version control
3. **Use generated types everywhere**: Never manually create types that duplicate backend models
4. **Review generated types**: Check generated types in code review to catch issues early
5. **Keep types in sync**: Add pre-commit hooks to ensure types are up-to-date

## Troubleshooting

### Types are out of sync

```bash
# Regenerate types
npm run generate:types

# Check what changed
git diff frontend/types/api/
```

### Missing types

If a Pydantic model isn't generating types:

1. Ensure it inherits from `BaseModel`
2. Check the model is in `backend/app/schemas/*.py`
3. Verify the Python syntax is valid
4. Check the generation script output for errors

### Type errors in frontend

If you get TypeScript errors after regenerating:

1. Check if field names changed (aliases)
2. Check if field types changed
3. Update API client calls to match new types
4. Run `npm run type-check` to find all errors

## Examples

### Complete API Call with Types

```typescript
import { apiClient } from '@/lib/api';
import {
  ReadingListResponse,
  AddToReadingListRequest,
  MessageResponse,
  UpdateRatingRequest,
} from '@/types/api';

// Get reading list
async function getReadingList(page: number = 1): Promise<ReadingListResponse> {
  return await apiClient.get<ReadingListResponse>(`/api/reading-list?page=${page}&page_size=20`);
}

// Add to reading list
async function addToReadingList(articleId: string): Promise<MessageResponse> {
  const request: AddToReadingListRequest = { article_id: articleId };
  return await apiClient.post<MessageResponse>('/api/reading-list', request);
}

// Update rating
async function updateRating(articleId: string, rating: number): Promise<MessageResponse> {
  const request: UpdateRatingRequest = { rating };
  return await apiClient.patch<MessageResponse>(`/api/reading-list/${articleId}/rating`, request);
}
```

### React Component with Types

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { ReadingListResponse, ReadingListItemResponse } from '@/types/api';

export function ReadingList() {
  const [items, setItems] = useState<ReadingListItemResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReadingList() {
      try {
        const response = await apiClient.get<ReadingListResponse>('/api/reading-list');
        setItems(response.items);
      } catch (error) {
        console.error('Failed to fetch reading list:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchReadingList();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {items.map((item) => (
        <li key={item.articleId}>
          <a href={item.url}>{item.title}</a>
          <span>{item.category}</span>
          <span>Rating: {item.rating ?? 'Not rated'}</span>
        </li>
      ))}
    </ul>
  );
}
```

## Related Documentation

- [API Client Documentation](../../lib/api/README.md)
- [Backend Schema Documentation](../../../backend/app/schemas/README.md)
- [Type Safety Guidelines](../../../docs/type-safety.md)
