# 路徑重構與 Settings 交互改進

## 改進概述

### 1. 路徑重構：`/dashboard/*` → `/app/*`

將所有應用路徑從 `/dashboard/*` 改為 `/app/*`，使 URL 更專業、更簡潔。

### 2. Settings 交互改進

改用側邊欄 tabs 的方式，讓設定項目更清晰易用。

## 路徑變更對照表

| 舊路徑                              | 新路徑                        | 說明     |
| ----------------------------------- | ----------------------------- | -------- |
| `/dashboard/articles`               | `/app/articles`               | 文章瀏覽 |
| `/dashboard/reading-list`           | `/app/reading-list`           | 閱讀清單 |
| `/dashboard/subscriptions`          | `/app/subscriptions`          | 訂閱管理 |
| `/dashboard/recommendations`        | `/app/recommendations`        | 推薦     |
| `/dashboard/analytics`              | `/app/analytics`              | 分析     |
| `/dashboard/settings`               | `/app/settings`               | 設定首頁 |
| `/dashboard/settings/notifications` | `/app/settings/notifications` | 通知設定 |
| `/dashboard/system-status`          | `/app/system-status`          | 系統狀態 |
| `/dashboard/profile`                | `/app/profile`                | 個人資料 |

## Settings 頁面改進

### 改進前

```
/dashboard/settings (列表頁面)
  ├── Card: 通知偏好設定 → 點擊進入 /dashboard/settings/notifications
  └── Card: 介面設定 (即將推出)
```

**問題**:

- 需要兩次點擊才能進入設定
- 沒有清晰的導航結構
- 不知道目前在哪個設定頁面

### 改進後

```
/app/settings (自動重定向到 /app/settings/notifications)
  ├── 左側邊欄 (Sidebar Tabs)
  │   ├── 通知 (/app/settings/notifications) ✓
  │   ├── 外觀 (/app/settings/appearance)
  │   ├── 帳戶 (/app/settings/account)
  │   └── 偏好設定 (/app/settings/preferences)
  └── 右側內容區域 (顯示選中的設定頁面)
```

**改進**:

- ✅ 一次點擊直接進入設定
- ✅ 清晰的側邊欄導航
- ✅ 當前頁面高亮顯示
- ✅ 響應式設計（手機版自動調整）

## 新的 Settings Layout

### 檔案結構

```
frontend/app/app/settings/
├── layout.tsx              # Settings 專用 layout（含側邊欄）
├── page.tsx                # 重定向到 notifications
├── notifications/
│   └── page.tsx           # 通知設定頁面
├── appearance/
│   └── page.tsx           # 外觀設定（待實作）
├── account/
│   └── page.tsx           # 帳戶設定（待實作）
└── preferences/
    └── page.tsx           # 偏好設定（待實作）
```

### Settings Layout 特點

#### 側邊欄導航

```tsx
const settingsNav = [
  {
    title: '通知',
    href: '/app/settings/notifications',
    icon: Bell,
    description: '管理通知偏好和頻率',
  },
  {
    title: '外觀',
    href: '/app/settings/appearance',
    icon: Palette,
    description: '主題和顯示設定',
  },
  // ...
];
```

#### 響應式設計

- **桌面版**: 左側固定側邊欄 (w-64) + 右側內容區域
- **手機版**: 側邊欄自動調整為垂直列表

#### 視覺反饋

- 當前頁面高亮顯示 (`bg-accent`)
- Hover 效果
- Focus 狀態（鍵盤導航）

## 修改的檔案清單

### 新增檔案

- `frontend/app/app/settings/layout.tsx` - Settings 專用 layout
- `frontend/app/app/settings/page.tsx` - 重定向頁面

### 移動的檔案

- `frontend/app/dashboard/*` → `frontend/app/app/*`
  - articles/
  - reading-list/
  - subscriptions/
  - recommendations/
  - analytics/
  - settings/
  - system-status/
  - profile/
  - layout.tsx
  - page.tsx

### 更新的檔案

- `frontend/components/Navigation.tsx` - 更新所有導航連結
- `frontend/components/layout/Sidebar.tsx` - 更新側邊欄連結
- `frontend/components/UserMenu.tsx` - 更新使用者選單連結
- `frontend/components/layout/Header.tsx` - 更新 header 連結
- `frontend/components/layout/Breadcrumb.tsx` - 更新麵包屑連結
- `frontend/components/PerformanceInitializer.tsx` - 更新預載入路徑
- `frontend/components/landing/LandingNav.tsx` - 更新登入後跳轉
- `frontend/components/ConditionalLayout.tsx` - 更新路由保護邏輯
- `frontend/__tests__/unit/features/notifications/NotificationSettingsPage.test.tsx` - 更新測試

## 向後相容性

### 建議的重定向配置

在 `next.config.js` 中添加：

```javascript
async redirects() {
  return [
    // Dashboard 路徑重定向
    {
      source: '/dashboard/:path*',
      destination: '/app/:path*',
      permanent: true, // 301 redirect
    },
  ];
}
```

這樣舊的 `/dashboard/*` 連結仍然可以正常工作。

## 使用者體驗改進

### 路徑改進

| 改進項目   | 改進前                   | 改進後             |
| ---------- | ------------------------ | ------------------ |
| URL 專業度 | ❌ `/dashboard/articles` | ✅ `/app/articles` |
| URL 長度   | ❌ 較長                  | ✅ 更短            |
| 語義清晰度 | ⚠️ dashboard 不夠明確    | ✅ app 更通用      |

### Settings 交互改進

| 改進項目   | 改進前              | 改進後             |
| ---------- | ------------------- | ------------------ |
| 進入設定   | ❌ 需要 2 次點擊    | ✅ 1 次點擊        |
| 導航清晰度 | ❌ 不清楚有哪些設定 | ✅ 側邊欄一目了然  |
| 當前位置   | ❌ 不明顯           | ✅ 高亮顯示        |
| 切換設定   | ❌ 需要返回再進入   | ✅ 直接點擊切換    |
| 響應式     | ⚠️ 手機版體驗一般   | ✅ 自動調整 layout |

## 測試檢查清單

### 路徑測試

- [ ] 所有導航連結指向正確的 `/app/*` 路徑
- [ ] 舊的 `/dashboard/*` 路徑正確重定向（如果配置了）
- [ ] 直接訪問 `/app/articles` 正常載入
- [ ] 登入後正確跳轉到 `/app/articles`

### Settings 測試

- [ ] 訪問 `/app/settings` 自動重定向到 `/app/settings/notifications`
- [ ] 側邊欄導航正常工作
- [ ] 當前頁面正確高亮
- [ ] 手機版 layout 正常顯示
- [ ] 鍵盤導航（Tab）正常工作

### 功能測試

- [ ] 所有頁面正常載入
- [ ] 導航欄功能正常
- [ ] 使用者選單連結正常
- [ ] 麵包屑導航正常
- [ ] 鍵盤快捷鍵正常

## 後續工作

### 待實作的 Settings 頁面

1. **外觀設定** (`/app/settings/appearance`)
   - 主題切換（淺色/深色/自動）
   - 字體大小
   - 語言選擇

2. **帳戶設定** (`/app/settings/account`)
   - 個人資料編輯
   - 密碼變更
   - 帳戶安全

3. **偏好設定** (`/app/settings/preferences`)
   - 預設排序方式
   - 每頁顯示數量
   - 其他一般偏好

### 清理工作

- [ ] 刪除舊的 `/dashboard` 目錄
- [ ] 更新所有文件中的路徑引用
- [ ] 更新 README.md
- [ ] 更新 API 文件

## 注意事項

1. **SEO 影響**: 如果有 SEO 考量，務必設定 301 重定向
2. **外部連結**: 檢查是否有外部連結使用舊路徑
3. **書籤**: 使用者的書籤需要更新（透過重定向解決）
4. **分析追蹤**: 更新 Google Analytics 等追蹤代碼的路徑配置

## 總結

這次改進帶來了：

- ✅ 更專業的 URL 結構
- ✅ 更清晰的 Settings 導航
- ✅ 更好的使用者體驗
- ✅ 更易維護的程式碼結構
- ✅ 更好的響應式設計

使用者現在可以更快速、更直觀地訪問和管理各種設定！
