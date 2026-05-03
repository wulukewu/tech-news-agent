# Settings Page React Component 錯誤修復

## 錯誤訊息

```
Error: The default export is not a React Component in page: "/app/settings"
```

## 問題原因

1. **使用了 Server-only API**: 原本使用 `redirect()` 函數，但這只能在 Server Components 中使用
2. **Layout 是 Client Component**: `settings/layout.tsx` 使用了 `'use client'`，導致所有子頁面也變成 Client Components
3. **Next.js 緩存**: Docker 容器中的 Next.js 可能緩存了舊版本

## 解決方案

### 1. 修改 page.tsx 使用客戶端路由

**修改前**:

```tsx
import { redirect } from 'next/navigation';

export default function SettingsPage() {
  redirect('/app/settings/notifications'); // ❌ Server-only API
}
```

**修改後**:

```tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/app/settings/notifications');
  }, [router]);

  return null; // ✅ 返回有效的 React 元素
}
```

### 2. 清除 Next.js 緩存

如果修改後仍然出現錯誤，需要清除緩存：

#### 方法 A: 重啟 Docker 容器（推薦）

```bash
# 停止容器
docker-compose down

# 清除 Next.js 緩存
rm -rf frontend/.next

# 重新啟動
docker-compose up -d
```

#### 方法 B: 在容器內清除緩存

```bash
# 進入容器
docker exec -it tech-news-agent-frontend-dev sh

# 刪除 .next 目錄
rm -rf .next

# 退出容器
exit

# 重啟容器
docker-compose restart frontend
```

#### 方法 C: 使用 npm 清除緩存

```bash
# 在 frontend 目錄
cd frontend
rm -rf .next
npm run dev
```

### 3. 替代方案：使用 Middleware 重定向

如果客戶端重定向有問題，可以使用 middleware：

**創建 `frontend/middleware.ts`**:

```tsx
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // 重定向 /app/settings 到 /app/settings/notifications
  if (request.nextUrl.pathname === '/app/settings') {
    return NextResponse.redirect(new URL('/app/settings/notifications', request.url));
  }
}

export const config = {
  matcher: '/app/settings',
};
```

然後刪除 `frontend/app/app/settings/page.tsx`。

## 為什麼會發生這個錯誤？

### Next.js App Router 的規則

1. **Server Components (預設)**:
   - 可以使用 `redirect()`
   - 不能使用 React hooks
   - 不能使用瀏覽器 API

2. **Client Components (`'use client'`)**:
   - 不能使用 `redirect()`
   - 可以使用 React hooks
   - 可以使用瀏覽器 API

3. **Layout 的影響**:
   - 如果 layout 是 Client Component，所有子頁面也會變成 Client Components
   - 這就是為什麼我們的 settings page 不能使用 `redirect()`

## 測試驗證

### 測試步驟

1. 清除緩存並重啟
2. 訪問 `http://localhost:3000/app/settings`
3. 應該自動重定向到 `http://localhost:3000/app/settings/notifications`
4. 不應該看到任何錯誤

### 預期結果

- ✅ 自動重定向成功
- ✅ 顯示 notifications 設定頁面
- ✅ 側邊欄正確高亮 "通知" 項目
- ✅ 沒有 console 錯誤

## 常見問題

### Q: 為什麼不直接刪除 page.tsx？

A: Next.js 要求每個路由都要有 `page.tsx`。如果刪除它，`/app/settings` 路由將不存在，會返回 404。

### Q: 為什麼不把 layout 改成 Server Component？

A: Settings layout 需要使用 `usePathname()` hook 來高亮當前頁面，這只能在 Client Component 中使用。

### Q: 可以混用 Server 和 Client Components 嗎？

A: 可以，但要注意：

- Server Component 可以導入 Client Component
- Client Component 不能導入 Server Component（除非通過 children prop）

## 最佳實踐

### 1. 重定向的選擇

| 場景             | 使用方法               | 位置              |
| ---------------- | ---------------------- | ----------------- |
| Server Component | `redirect()`           | page.tsx (Server) |
| Client Component | `router.replace()`     | page.tsx (Client) |
| 全域重定向       | Middleware             | middleware.ts     |
| 條件重定向       | `useEffect` + `router` | Client Component  |

### 2. Layout 設計

```tsx
// ✅ 好的做法：Layout 只處理 UI
'use client';

export default function Layout({ children }) {
  const pathname = usePathname(); // 需要 'use client'

  return (
    <div>
      <Sidebar pathname={pathname} />
      <main>{children}</main>
    </div>
  );
}
```

```tsx
// ❌ 避免：在 Layout 中處理數據獲取
'use client';

export default function Layout({ children }) {
  const { data } = useQuery(...); // 應該在 page 中處理

  return <div>{children}</div>;
}
```

## 相關資源

- [Next.js redirect() Documentation](https://nextjs.org/docs/app/api-reference/functions/redirect)
- [Next.js useRouter() Documentation](https://nextjs.org/docs/app/api-reference/functions/use-router)
- [Next.js Middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [Server vs Client Components](https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns)

## 總結

- ✅ 修改 page.tsx 使用客戶端路由
- ✅ 清除 Next.js 緩存
- ✅ 重啟 Docker 容器
- ✅ 測試重定向功能

如果問題持續，考慮使用 Middleware 方案。
