# TypeScript Type Generation from Pydantic Models

## Overview

This script automatically generates TypeScript type definitions from backend Pydantic models, ensuring type safety across the frontend and backend.

**Task**: 8.4 - Generate TypeScript types from backend schemas
**Requirements**: 1.5, 8.1, 8.3

## Features

- ✅ Automatic TypeScript interface generation from Pydantic models
- ✅ Type mapping (Python → TypeScript)
- ✅ Field alias support (camelCase in TS, snake_case in Python)
- ✅ Optional field handling
- ✅ Generic type support
- ✅ Documentation preservation (docstrings → JSDoc comments)
- ✅ Field descriptions from Pydantic Field()

## Usage

### Generate Types

```bash
# From project root
python3 scripts/generate-types.py

# Or from frontend directory
npm run generate:types
```

### Output

Generated files in `frontend/types/api/`:

- `responses.ts` - API response formats
- `article.ts` - Article types
- `reading_list.ts` - Reading list types
- `feed.ts` - Feed and subscription types
- `recommendation.ts` - Recommendation types
- `analytics.ts` - Analytics types
- `onboarding.ts` - Onboarding types
- `index.ts` - Re-exports all types

## Type Mapping

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
| `Any`              | `any`                 |

## Examples

### Python Pydantic Model

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ReadingListItemResponse(BaseModel):
    """閱讀清單項目回應"""
    article_id: UUID = Field(..., description="文章 UUID", alias="articleId")
    title: str = Field(..., description="文章標題")
    rating: Optional[int] = Field(None, description="評分（1-5）")
```

### Generated TypeScript Interface

```typescript
/**
 * 閱讀清單項目回應
 */
export interface ReadingListItemResponse {
  /** 文章 UUID */
  articleId: string;
  /** 文章標題 */
  title: string;
  /** 評分（1-5） */
  rating?: number | null;
}
```

## Implementation Details

### AST Parsing

The script uses Python's `ast` module to parse Pydantic model definitions:

1. **Import Tracking**: Tracks imports to understand type dependencies
2. **Class Detection**: Identifies classes inheriting from `BaseModel`
3. **Field Extraction**: Extracts field names, types, and metadata
4. **Generic Support**: Handles generic type parameters (e.g., `Generic[T]`)

### Field Information Extraction

From Pydantic `Field()`:

- `description` → JSDoc comment
- `alias` → TypeScript field name
- `default=None` → Optional field (`?`)

### Type Conversion

Recursive type conversion handles:

- Simple types (`str` → `string`)
- Generic types (`List[T]` → `T[]`)
- Optional types (`Optional[T]` → `T | null`)
- Nested generics (`Dict[str, List[int]]` → `Record<string, number[]>`)

## Integration

### With API Client

```typescript
import { apiClient } from '@/lib/api';
import { ReadingListResponse } from '@/types/api';

const response = await apiClient.get<ReadingListResponse>('/api/reading-list');
// response is fully typed!
```

### With React Components

```typescript
import { ReadingListItemResponse } from '@/types/api';

interface Props {
  item: ReadingListItemResponse;
}

export function ReadingListItem({ item }: Props) {
  return (
    <div>
      <h3>{item.title}</h3>
      <span>Rating: {item.rating ?? 'Not rated'}</span>
    </div>
  );
}
```

## CI/CD Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Generate TypeScript types
  run: npm run generate:types
  working-directory: frontend

- name: Check for type changes
  run: |
    if [[ -n $(git status --porcelain frontend/types/api/) ]]; then
      echo "Error: Generated types are out of date"
      echo "Run 'npm run generate:types' and commit the changes"
      exit 1
    fi
```

## Maintenance

### When to Regenerate

- After adding new Pydantic models
- After modifying existing model fields
- After changing field types or aliases
- Before committing API contract changes

### Troubleshooting

**Types not generating:**

- Ensure model inherits from `BaseModel`
- Check model is in `backend/app/schemas/*.py`
- Verify Python syntax is valid

**Type mismatches:**

- Regenerate types: `npm run generate:types`
- Check field aliases match
- Verify type mapping is correct

## Requirements Validation

✅ **Requirement 1.5**: TypeScript generics for type-safe request/response handling

- Generated interfaces support generic types
- API client methods use generics with generated types

✅ **Requirement 8.1**: TypeScript interfaces for all API request/response types

- All Pydantic models generate corresponding TypeScript interfaces
- Request and response types are fully typed

✅ **Requirement 8.3**: Automatic type updates when API contracts change

- Script regenerates types from source of truth (Pydantic models)
- Single command updates all types
- Can be integrated into CI/CD pipeline

## Future Enhancements

- [ ] Validation rule generation (min/max, regex patterns)
- [ ] Enum generation from Python Enum classes
- [ ] Discriminated union support
- [ ] OpenAPI schema generation
- [ ] Type guards generation
- [ ] Zod schema generation for runtime validation
