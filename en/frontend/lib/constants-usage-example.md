# ERROR_MESSAGES and SUCCESS_MESSAGES Usage Example

## Overview

The `ERROR_MESSAGES` and `SUCCESS_MESSAGES` constants in `frontend/lib/constants/index.ts` now contain **translation keys** instead of hardcoded text. This allows for bilingual support.

## How to Use

### Before (Hardcoded Text)

```typescript
import { ERROR_MESSAGES } from '@/lib/constants';

// This would display Chinese text directly
const errorMessage = ERROR_MESSAGES.NETWORK_ERROR;
// Result: "網路連線異常，請檢查您的網路設定"
```

### After (Translation Keys)

```typescript
import { ERROR_MESSAGES } from '@/lib/constants';
import { useI18n } from '@/contexts/I18nContext';

function MyComponent() {
  const { t } = useI18n();

  // Translate the key to get the localized message
  const errorMessage = t(ERROR_MESSAGES.NETWORK_ERROR);
  // Result (zh-TW): "網路連線異常，請檢查您的網路設定"
  // Result (en-US): "Network connection error. Please check your network settings"

  return <div>{errorMessage}</div>;
}
```

## Available Constants

### ERROR_MESSAGES

```typescript
ERROR_MESSAGES.NETWORK_ERROR; // 'errors.network-error'
ERROR_MESSAGES.ANALYSIS_TIMEOUT; // 'errors.analysis-timeout'
ERROR_MESSAGES.INSUFFICIENT_PERMISSIONS; // 'errors.insufficient-permissions'
ERROR_MESSAGES.RATE_LIMIT_EXCEEDED; // 'errors.rate-limit-exceeded'
ERROR_MESSAGES.INVALID_INPUT; // 'errors.invalid-input'
ERROR_MESSAGES.SERVER_ERROR; // 'errors.server-error'
ERROR_MESSAGES.NOT_FOUND; // 'errors.not-found'
ERROR_MESSAGES.UNAUTHORIZED; // 'errors.unauthorized'
```

### SUCCESS_MESSAGES

```typescript
SUCCESS_MESSAGES.ARTICLE_SAVED; // 'success.article-saved'
SUCCESS_MESSAGES.ARTICLE_REMOVED; // 'success.article-removed'
SUCCESS_MESSAGES.SETTINGS_SAVED; // 'success.settings-saved'
SUCCESS_MESSAGES.ANALYSIS_COPIED; // 'success.analysis-copied'
SUCCESS_MESSAGES.SUBSCRIPTION_ADDED; // 'success.subscription-added'
SUCCESS_MESSAGES.SUBSCRIPTION_REMOVED; // 'success.subscription-removed'
```

## Complete Example

```typescript
'use client';

import { useState } from 'react';
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from '@/lib/constants';
import { useI18n } from '@/contexts/I18nContext';
import { toast } from '@/components/ui/use-toast';

export function ArticleActions({ articleId }: { articleId: string }) {
  const { t } = useI18n();
  const [loading, setLoading] = useState(false);

  const handleSaveArticle = async () => {
    setLoading(true);
    try {
      await saveArticle(articleId);

      // Show success message in user's language
      toast({
        title: t(SUCCESS_MESSAGES.ARTICLE_SAVED),
        variant: 'success',
      });
    } catch (error) {
      // Show error message in user's language
      toast({
        title: t(ERROR_MESSAGES.SERVER_ERROR),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleSaveArticle} disabled={loading}>
      {loading ? 'Saving...' : 'Save Article'}
    </button>
  );
}
```

## Notes

- Always use the `t()` function from `useI18n()` to translate the keys
- The constants now store translation keys, not the actual text
- This pattern ensures consistent error/success messages across the application
- All translations are defined in `frontend/locales/zh-TW.json` and `frontend/locales/en-US.json`
