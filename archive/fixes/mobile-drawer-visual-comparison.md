# 手機版抽屜式選單修復 - 視覺對比

## 問題示意圖

### 修復前 ❌

```
┌─────────────────────────────┐
│  [≡] 登出                   │ ← 漢堡選單按鈕 + 頂部按鈕
├─────────────────────────────┤
│  👤 Username                │
│  ID: 12345678...            │ ← 用戶資訊區域
│                         [×] │
├─────────────────────────────┤
│  🏠 文庫                    │ ← 被遮擋！
│  📚 閱讀清單                │
│  📡 訂閱                    │
│  ⚙️  設定                   │
│  📊 分析                    │
│                             │
│  (可滾動區域)              │
│                             │
│                             │
├─────────────────────────────┤
│  語言: [中文 ▼]            │ ← 底部區域
│  主題: [深色 ▼]            │   (absolute 定位)
│  [登出]                    │   與內容重疊
└─────────────────────────────┘
```

**問題點：**

1. 導航項目被用戶資訊區域遮擋
2. 底部區域使用 `absolute` 定位，與內容重疊
3. 滾動區域高度計算錯誤 (`max-h-[calc(100vh-200px)]`)

### 修復後 ✅

```
┌─────────────────────────────┐
│  👤 Username                │ ← 用戶資訊區域
│  ID: 12345678...        [×] │   (flex-shrink-0)
├─────────────────────────────┤
│  🏠 文庫                    │ ← 清晰可見！
│  📚 閱讀清單                │
│  📡 訂閱                    │   (flex-1, 可滾動)
│  ⚙️  設定                   │
│  📊 分析                    │
│  ❤️  推薦                   │
│  📈 系統狀態                │
│                             │
│  ↕ (可滾動區域)            │
│                             │
├─────────────────────────────┤
│  語言: [中文 ▼]            │ ← 底部區域
│  主題: [深色 ▼]            │   (flex-shrink-0)
│  [登出]                    │   固定在底部
└─────────────────────────────┘
```

**改進點：**

1. ✅ 使用 Flexbox 垂直佈局 (`flex flex-col`)
2. ✅ 頂部固定 (`flex-shrink-0`)
3. ✅ 中間自動填充並可滾動 (`flex-1 overflow-y-auto`)
4. ✅ 底部固定 (`flex-shrink-0`)
5. ✅ 響應式寬度 (`w-[280px] sm:w-72`)

## 程式碼對比

### 修復前

```tsx
<nav className="absolute left-0 top-0 bottom-0 w-64 bg-card border-r shadow-xl">
  <div className="flex flex-col h-full">
    {/* 頂部 */}
    <div className="flex items-center gap-3 p-4 border-b">{/* 用戶資訊 */}</div>

    {/* 中間 - 高度計算錯誤 */}
    <div className="py-4 space-y-1 overflow-y-auto max-h-[calc(100vh-200px)]">{/* 導航項目 */}</div>

    {/* 底部 - absolute 定位會重疊 */}
    <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-card">{/* 設定和登出 */}</div>
  </div>
</nav>
```

### 修復後

```tsx
<nav className="absolute left-0 top-0 bottom-0 w-[280px] sm:w-72 bg-card border-r shadow-xl flex flex-col">
  {/* 頂部 - 固定高度 */}
  <div className="flex items-center gap-3 p-4 border-b flex-shrink-0">{/* 用戶資訊 */}</div>

  {/* 中間 - 自動填充剩餘空間 */}
  <div className="flex-1 py-4 space-y-1 overflow-y-auto">{/* 導航項目 */}</div>

  {/* 底部 - 固定高度 */}
  <div className="flex-shrink-0 p-4 border-t bg-card">{/* 設定和登出 */}</div>
</nav>
```

## Flexbox 佈局說明

```
┌─────────────────────────────┐
│  flex-shrink-0              │ ← 固定高度，不會被壓縮
│  (頂部區域)                 │
├─────────────────────────────┤
│                             │
│  flex-1                     │ ← 自動填充剩餘空間
│  overflow-y-auto            │   超出時可滾動
│  (主要內容區域)            │
│                             │
├─────────────────────────────┤
│  flex-shrink-0              │ ← 固定高度，不會被壓縮
│  (底部區域)                 │
└─────────────────────────────┘
```

## 關鍵 CSS 屬性

| 屬性                | 用途      | 效果                 |
| ------------------- | --------- | -------------------- |
| `flex flex-col`     | 容器      | 垂直 Flexbox 佈局    |
| `flex-shrink-0`     | 頂部/底部 | 固定高度，不會被壓縮 |
| `flex-1`            | 中間區域  | 自動填充剩餘空間     |
| `overflow-y-auto`   | 中間區域  | 內容超出時顯示滾動條 |
| `w-[280px] sm:w-72` | 容器      | 響應式寬度           |

## 測試建議

在以下裝置上測試：

- ✅ iPhone SE (375px)
- ✅ iPhone 12/13/14 (390px)
- ✅ iPhone 14 Pro Max (430px)
- ✅ Android 小螢幕 (360px)
- ✅ Android 中螢幕 (412px)

確認：

1. 所有導航項目都清晰可見
2. 可以順暢滾動
3. 底部區域固定在底部
4. 沒有內容重疊

## 相關檔案

- [修復文件](./mobile-drawer-layout-fix.md)
- [Navigation 元件](../../frontend/components/Navigation.tsx)
- [Sidebar 元件](../../frontend/components/layout/Sidebar.tsx)
