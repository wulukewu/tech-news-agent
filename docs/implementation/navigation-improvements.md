# Navigation 選取狀態改善

## 問題描述

原本的 navbar 選取狀態不夠明顯，用戶難以清楚識別當前所在的頁面。

## 改善範圍

我們改善了以下所有導航組件的選取狀態：

1. **主導航 (Navigation.tsx)** - 桌面版和手機版
2. **側邊欄 (Sidebar.tsx)** - 桌面版、手機版和底部導航
3. **設定頁面導航 (Settings Layout)** - 標籤式導航

## 改善方案

### 1. 主導航 (Navigation.tsx)

#### 桌面版導航 (Desktop Navigation)

**改善前:**

- 選取狀態: `bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground`
- 過渡效果: `transition-colors`
- 視覺效果較弱，不夠突出

**改善後:**

- 選取狀態: `bg-primary text-primary-foreground shadow-md font-semibold border border-primary/20`
- 過渡效果: `transition-all duration-200`
- 懸停效果: `hover:bg-muted/50 hover:shadow-sm`

#### 手機版導航 (Mobile Navigation)

**改善前:**

- 選取狀態: `bg-primary text-primary-foreground relative`
- 左側指示器: 使用 `before:` 偽元素創建 1px 寬的指示條

**改善後:**

- 選取狀態: `bg-primary text-primary-foreground shadow-lg font-semibold border-l-4 border-l-primary-foreground/30`
- 過渡效果: `transition-all duration-200`

### 2. 側邊欄 (Sidebar.tsx)

#### 桌面版側邊欄

**改善前:**

- 選取狀態: `bg-accent/50 text-accent-foreground` + 左側 1px 指示條

**改善後:**

- 選取狀態: `bg-primary text-primary-foreground shadow-md font-semibold border-l-4 border-l-primary-foreground/30`

#### 手機版側邊欄

**改善前:**

- 選取狀態: `bg-primary text-primary-foreground hover:bg-primary/90`

**改善後:**

- 選取狀態: `bg-primary text-primary-foreground shadow-lg font-semibold border-l-4 border-l-primary-foreground/30`

#### 底部導航

**改善前:**

- 選取狀態: `text-primary bg-primary/10`

**改善後:**

- 選取狀態: `text-primary-foreground bg-primary shadow-md font-semibold`

### 3. 設定頁面導航 (Settings Layout)

**改善前:**

- 選取狀態: `border-primary text-foreground`
- 過渡效果: `transition-colors`

**改善後:**

- 選取狀態: `border-primary text-primary font-semibold shadow-sm`
- 過渡效果: `transition-all duration-200`
- 懸停效果: `hover:text-foreground/80`

## 設計原則

### 1. 對比度增強

- 使用完整的 primary 色彩而非透明度版本
- 確保選取狀態在明暗主題下都清晰可見
- 使用 `text-primary` 或 `text-primary-foreground` 提升文字對比

### 2. 視覺層次

- 添加陰影效果創造深度感 (`shadow-md`, `shadow-lg`)
- 使用粗體字增強文字重要性 (`font-semibold`)
- 邊框提供清晰的邊界定義 (`border-l-4`)

### 3. 一致性

- 所有導航組件使用相同的設計語言
- 統一的過渡動畫時長 (200ms)
- 保持與整體設計系統的和諧
- 統一使用 4px 寬的左側邊框作為選取指示器

### 4. 可訪問性

- 保持足夠的顏色對比度
- 使用 `aria-current="page"` 標記當前頁面
- 支援鍵盤導航和焦點指示器
- 保持最小觸控目標尺寸 (44x44px)

## 技術實作

### 主導航桌面版樣式

```tsx
className={cn(
  'flex items-center gap-1.5 px-2.5 lg:px-3 py-2 rounded-md transition-all duration-200 cursor-pointer relative',
  'hover:bg-accent hover:text-accent-foreground hover:shadow-sm',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  'min-h-[44px] min-w-[44px]',
  isActive
    ? 'bg-primary text-primary-foreground shadow-md font-semibold border border-primary/20'
    : 'text-foreground hover:bg-muted/50'
)}
```

### 主導航手機版樣式

```tsx
className={cn(
  'flex items-center gap-3 px-3 py-3 min-h-[48px] w-full cursor-pointer transition-all duration-200 rounded-lg relative',
  'hover:bg-accent hover:text-accent-foreground',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  isActive
    ? 'bg-primary text-primary-foreground shadow-lg font-semibold border-l-4 border-l-primary-foreground/30'
    : 'hover:bg-muted/50'
)}
```

### 側邊欄樣式

```tsx
className={cn(
  'flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-all duration-200 cursor-pointer group relative',
  'hover:bg-accent hover:text-accent-foreground',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  isActive
    ? 'bg-primary text-primary-foreground shadow-md font-semibold border-l-4 border-l-primary-foreground/30'
    : 'hover:bg-muted/50'
)}
```

### 底部導航樣式

```tsx
className={cn(
  'flex flex-col items-center gap-1 px-2 py-2 text-xs font-medium rounded-lg transition-all duration-200 cursor-pointer relative min-h-[44px] min-w-[44px] justify-center',
  'hover:bg-accent hover:text-accent-foreground',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  isActive
    ? 'text-primary-foreground bg-primary shadow-md font-semibold'
    : 'hover:bg-muted/50'
)}
```

### 設定頁面導航樣式

```tsx
className={cn(
  'flex items-center gap-2 px-1 py-4 border-b-2 font-medium text-sm whitespace-nowrap transition-all duration-200',
  'hover:text-foreground hover:border-border',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  isActive
    ? 'border-primary text-primary font-semibold shadow-sm'
    : 'border-transparent text-muted-foreground hover:text-foreground/80'
)}
```

## 視覺改善總結

### 改善前的問題

- 選取狀態對比度不足，難以識別
- 缺乏視覺層次感
- 不同導航組件的選取狀態不一致
- 過渡動畫效果單調

### 改善後的優勢

- ✅ **強烈對比**: 使用完整 primary 色彩，清晰可見
- ✅ **立體感**: 添加陰影效果增加深度
- ✅ **一致性**: 所有導航組件使用統一的設計語言
- ✅ **流暢動畫**: 200ms 的平滑過渡效果
- ✅ **清晰指示**: 4px 寬的左側邊框作為選取指示器
- ✅ **字體強調**: 使用粗體字增強選取狀態的可讀性
- ✅ **可訪問性**: 保持良好的對比度和觸控目標尺寸

## 測試建議

1. **視覺測試**: 在明暗主題下測試選取狀態的可見度
2. **響應式測試**: 確認桌面版、平板和手機版的一致性
3. **可訪問性測試**: 使用螢幕閱讀器測試導航標記
4. **互動測試**: 確認懸停和焦點狀態正常工作
5. **對比度測試**: 確保符合 WCAG AA 標準 (4.5:1 對比度)

## 結果

改善後的導航選取狀態更加清晰明顯，用戶可以輕鬆識別當前所在的頁面。所有導航組件現在都使用一致的設計語言，提升了整體的用戶體驗和視覺一致性。
