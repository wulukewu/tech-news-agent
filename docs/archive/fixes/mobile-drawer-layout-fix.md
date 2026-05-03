# 手機版側邊欄佈局修復

## 問題描述

在手機版本中，側邊欄（抽屜式選單）的樣式出現問題：

1. **內容被遮擋** - 導航選項（如「文庫」）被頂部的用戶資訊區域遮住
2. **佈局不正確** - 底部區域使用 `absolute` 定位，導致與主要內容區域重疊
3. **滾動問題** - 導航項目區域的高度計算不正確

## 修復內容

### 1. Navigation 元件 (`frontend/components/Navigation.tsx`)

#### 修改前

```tsx
<nav className="absolute left-0 top-0 bottom-0 w-64 bg-card border-r shadow-xl animate-slide-in-from-left">
  <div className="flex flex-col h-full">
    {/* 用戶資訊 */}
    <div className="flex items-center gap-3 p-4 border-b">...</div>

    {/* 導航項目 */}
    <div className="py-4 space-y-1 overflow-y-auto max-h-[calc(100vh-200px)]">...</div>

    {/* 底部區域 */}
    <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-card space-y-3">...</div>
  </div>
</nav>
```

#### 修改後

```tsx
<nav className="absolute left-0 top-0 bottom-0 w-[280px] sm:w-72 bg-card border-r shadow-xl animate-slide-in-from-left flex flex-col">
  {/* 用戶資訊 - 固定在頂部 */}
  <div className="flex items-center gap-3 p-4 border-b flex-shrink-0">...</div>

  {/* 導航項目 - 可滾動的主要區域 */}
  <div className="flex-1 py-4 space-y-1 overflow-y-auto">...</div>

  {/* 底部區域 - 固定在底部 */}
  <div className="flex-shrink-0 p-4 border-t bg-card space-y-3">...</div>
</nav>
```

#### 關鍵改進

1. **Flexbox 佈局** - 在 `<nav>` 元素上添加 `flex flex-col`，使用 flexbox 垂直佈局
2. **固定頂部** - 用戶資訊區域使用 `flex-shrink-0`，防止被壓縮
3. **可滾動中間區域** - 導航項目使用 `flex-1`，自動填充剩餘空間，並可滾動
4. **固定底部** - 底部區域使用 `flex-shrink-0` 取代 `absolute` 定位
5. **響應式寬度** - 使用 `w-[280px] sm:w-72` 在小螢幕上更窄

### 2. Sidebar 元件 (`frontend/components/layout/Sidebar.tsx`)

雖然目前沒有在主要應用中使用，但也進行了類似的修復：

1. **提高按鈕層級** - 漢堡選單按鈕的 z-index 從 `z-50` 改為 `z-[60]`
2. **添加上方間距** - 側邊欄內容容器添加 `pt-16`，避免被按鈕遮擋
3. **改善視覺效果** - 按鈕添加 `shadow-sm` 提升可見度

## 測試驗證

- ✅ 編譯成功，無 TypeScript 錯誤
- ✅ 無 ESLint 錯誤（僅有既存的警告）
- ✅ 佈局使用標準 Flexbox，相容性良好

## 影響範圍

- `frontend/components/Navigation.tsx` - 主要修復
- `frontend/components/layout/Sidebar.tsx` - 預防性修復

## 相關檔案

- [Navigation 元件](../../frontend/components/Navigation.tsx)
- [Sidebar 元件](../../frontend/components/layout/Sidebar.tsx)

## 日期

2026-04-19
