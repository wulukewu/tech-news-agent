# QueryClient Provider 錯誤修復

## 錯誤訊息

```
Unhandled Runtime Error
Error: No QueryClient set, use QueryClientProvider to set one

Source: lib/hooks/useReadingList.ts (120:37)
```

## 問題原因

在路徑重構過程中，創建了 `frontend/app/app/layout.tsx`，這個 layout 覆蓋了根 layout 的 providers 層級，導致 `QueryClientProvider` 無法正確傳遞到子組件。

### 問題的 Layout 層級結構

```
RootLayout (app/layout.tsx)
  └── Providers (包含 QueryClientProvider)
      └── ConditionalLayout
          └── AppLayout (for /app/* routes)
              └── app/app/layout.tsx ❌ (多餘的 layout)
                  └── children (無法訪問 QueryClient)
```

## 解決方案

移除多餘的 `frontend/app/app/layout.tsx`，因為：

1. **ConditionalLayout 已經處理了認證和 layout**
   - 對於 `/app/*` 路徑，`ConditionalLayout` 會自動包裹 `AppLayout`
   - 不需要額外的 layout 層級

2. **避免 Provider 層級問題**
   - 每增加一層 layout 都可能導致 context 傳遞問題
   - 保持簡單的層級結構

### 修復後的 Layout 層級結構

```
RootLayout (app/layout.tsx)
  └── Providers (包含 QueryClientProvider) ✅
      └── ConditionalLayout
          └── AppLayout (for /app/* routes)
              └── app/app/settings/layout.tsx (僅用於 settings 側邊欄)
                  └── children (可以正常訪問 QueryClient) ✅
```

## 修改的檔案

- ❌ 刪除: `frontend/app/app/layout.tsx`
- ✅ 保留: `frontend/app/app/settings/layout.tsx` (僅添加 UI，不影響 providers)

## 為什麼 settings/layout.tsx 沒問題？

`frontend/app/app/settings/layout.tsx` 只是添加了側邊欄導航的 UI，並沒有：

- 重新包裹 providers
- 添加認證邏輯
- 改變 context 層級

它只是純粹的 UI layout，所以不會影響 `QueryClientProvider` 的傳遞。

## Next.js Layout 最佳實踐

### ✅ 正確的做法

1. **在根 layout 設定所有 providers**

   ```tsx
   // app/layout.tsx
   export default function RootLayout({ children }) {
     return (
       <html>
         <body>
           <Providers>
             {' '}
             {/* QueryClient, Theme, etc. */}
             {children}
           </Providers>
         </body>
       </html>
     );
   }
   ```

2. **子 layout 只添加 UI 結構**
   ```tsx
   // app/settings/layout.tsx
   export default function SettingsLayout({ children }) {
     return (
       <div className="flex">
         <Sidebar />
         <main>{children}</main>
       </div>
     );
   }
   ```

### ❌ 錯誤的做法

1. **在子 layout 重新包裹 providers**

   ```tsx
   // ❌ 不要這樣做
   export default function SubLayout({ children }) {
     return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
   }
   ```

2. **創建不必要的 layout 層級**
   ```tsx
   // ❌ 如果只是簡單的容器，不需要 layout
   export default function AppLayout({ children }) {
     return <div className="min-h-screen">{children}</div>;
   }
   ```

## 測試驗證

### 測試項目

- [x] `/app/articles` 頁面正常載入
- [x] `/app/reading-list` 可以使用 `useReadingList` hook
- [x] `/app/settings/notifications` 可以使用 `useQuery`
- [x] 所有使用 React Query 的頁面正常工作

### 測試方法

1. 訪問 `/app/reading-list`
2. 嘗試添加文章到閱讀清單
3. 確認沒有 "No QueryClient set" 錯誤

## 相關資源

- [Next.js Layouts Documentation](https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts)
- [React Query Context](https://tanstack.com/query/latest/docs/react/reference/QueryClientProvider)
- [Next.js App Router Best Practices](https://nextjs.org/docs/app/building-your-application/routing/route-groups)

## 總結

- ✅ 移除了多餘的 `app/app/layout.tsx`
- ✅ 保持簡單的 layout 層級結構
- ✅ 確保 `QueryClientProvider` 正確傳遞到所有子組件
- ✅ 所有頁面可以正常使用 React Query hooks
