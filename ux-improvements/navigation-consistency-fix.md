# 導航欄一致性修復

## 問題描述

使用者反映導航欄位置不一致：

- 在某些頁面（如 Dashboard, Reading List）導航欄在**頂部**
- 在 Notification Settings 頁面導航欄卻在**左側**

這導致使用體驗混亂，使用者需要在不同位置尋找導航選項。

## 根本原因

專案中存在兩個不同的路由結構和 layout 系統：

### 1. `/dashboard/*` 路由

- **Layout**: `frontend/app/dashboard/layout.tsx`
- **導航**: 使用 `ConditionalLayout` + 頂部 `Navigation` 組件
- **頁面**:
  - `/dashboard/articles`
  - `/dashboard/reading-list`
  - `/dashboard/subscriptions`
  - `/dashboard/settings`

### 2. `/(dashboard)/*` 路由

- **Layout**: `frontend/app/(dashboard)/layout.tsx` + `layout-client.tsx`
- **導航**: 使用左側 `Sidebar` 組件
- **頁面**:
  - `/(dashboard)/articles` (重複)
  - `/(dashboard)/settings/notifications` (問題頁面)

## 解決方案

### 統一使用 `/dashboard/*` 路由結構

將所有頁面統一到 `/dashboard/*` 路由下，使用頂部導航欄。

### 具體修改

#### 1. 移動 Notification Settings 頁面

**從**: `frontend/app/(dashboard)/settings/notifications/page.tsx`
**到**: `frontend/app/dashboard/settings/notifications/page.tsx`

使用 `smartRelocate` 工具自動更新所有 import 引用。

#### 2. 更新所有連結

**檔案**: `frontend/components/UserMenu.tsx`

```tsx
// 修改前
<Link href="/settings/notifications">

// 修改後
<Link href="/dashboard/settings/notifications">
```

**檔案**: `frontend/components/layout/Header.tsx`

```tsx
// 修改前
<Link href="/settings/notifications">通知設定</Link>

// 修改後
<Link href="/dashboard/settings/notifications">通知設定</Link>
```

**檔案**: `frontend/app/dashboard/settings/page.tsx`

```tsx
// 修改前
<Link href="/settings/notifications">

// 修改後
<Link href="/dashboard/settings/notifications">
```

**檔案**: `frontend/components/layout/Sidebar.tsx`

```tsx
// 修改前
{ href: '/settings', label: 'Settings', icon: Bell, shortcut: 'N' }

// 修改後
{ href: '/dashboard/settings', label: 'Settings', icon: Bell, shortcut: 'N' }
```

#### 3. 更新測試檔案

**檔案**: `frontend/__tests__/unit/features/notifications/NotificationSettingsPage.test.tsx`

```tsx
// 修改前
import NotificationSettingsPage from '@/app/settings/notifications/page';

// 修改後
import NotificationSettingsPage from '@/app/dashboard/settings/notifications/page';
```

## 修改後的路由結構

```
/dashboard/
├── articles/              # 文章瀏覽 (頂部導航)
├── reading-list/          # 閱讀清單 (頂部導航)
├── subscriptions/         # 訂閱管理 (頂部導航)
├── settings/              # 設定首頁 (頂部導航)
│   └── notifications/     # 通知設定 (頂部導航) ✅ 已修復
├── recommendations/       # 推薦 (頂部導航)
├── analytics/            # 分析 (頂部導航)
└── system-status/        # 系統狀態 (頂部導航)
```

## 後續清理建議

### 1. 移除 `(dashboard)` 目錄

`frontend/app/(dashboard)/` 目錄下的內容已經過時或重複，建議完全移除：

```bash
rm -rf frontend/app/(dashboard)
```

### 2. 統一導航組件

目前有兩個導航組件：

- `Navigation.tsx` - 頂部導航（保留）
- `Sidebar.tsx` - 左側導航（可以移除或保留作為備用）

建議：

- 保留 `Navigation.tsx` 作為主要導航
- 如果不需要左側導航，可以移除 `Sidebar.tsx`
- 如果未來需要左側導航，可以保留但不使用

### 3. 更新文件

更新以下文件以反映新的路由結構：

- README.md
- 開發文件
- API 文件

## 測試驗證

### 測試項目

- [x] Notification settings 頁面使用頂部導航
- [x] 所有連結指向正確的路徑
- [x] 導航欄在所有頁面保持一致
- [ ] 測試所有導航連結是否正常工作
- [ ] 測試鍵盤快捷鍵是否正常
- [ ] 測試手機版導航是否正常

### 測試路徑

1. 從 Dashboard 點擊 Settings
2. 從 Settings 點擊通知設定
3. 從 UserMenu 點擊 Notifications
4. 直接訪問 `/dashboard/settings/notifications`
5. 確認所有頁面都顯示頂部導航欄

## 使用者體驗改進

### 修改前

- ❌ 導航位置不一致（頂部 vs 左側）
- ❌ 使用者困惑
- ❌ 路由結構混亂

### 修改後

- ✅ 所有頁面使用統一的頂部導航
- ✅ 一致的使用體驗
- ✅ 清晰的路由結構
- ✅ 更容易維護

## 相關檔案

### 修改的檔案

- `frontend/app/dashboard/settings/notifications/page.tsx` (移動)
- `frontend/components/UserMenu.tsx`
- `frontend/components/layout/Header.tsx`
- `frontend/components/layout/Sidebar.tsx`
- `frontend/app/dashboard/settings/page.tsx`
- `frontend/__tests__/unit/features/notifications/NotificationSettingsPage.test.tsx`

### 待清理的檔案

- `frontend/app/(dashboard)/` (整個目錄)

## 注意事項

1. **向後相容性**: 舊的 `/settings/notifications` 路徑將無法訪問，需要確保沒有外部連結使用舊路徑
2. **重定向**: 可以考慮添加重定向規則，將舊路徑重定向到新路徑
3. **SEO**: 如果有 SEO 考量，需要設定 301 重定向

## 建議的重定向配置

在 `next.config.js` 中添加：

```javascript
async redirects() {
  return [
    {
      source: '/settings/notifications',
      destination: '/dashboard/settings/notifications',
      permanent: true, // 301 redirect
    },
    {
      source: '/settings/:path*',
      destination: '/dashboard/settings/:path*',
      permanent: true,
    },
  ];
}
```
