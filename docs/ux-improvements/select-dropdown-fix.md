# Select Dropdown 無法點擊問題修復

## 問題描述

使用者反映下拉選單（Select）點擊後無法選擇選項，選項顯示但點擊無效。

## 根本原因分析

1. **z-index 不足** - SelectContent 的 z-index 設為 50，可能被其他元素覆蓋
2. **overflow 問題** - 使用 `overflow-y-auto overflow-x-hidden` 可能導致內容被裁切
3. **SelectItem 內容過於複雜** - 在 SelectItem 內使用多層 div 和 flex-col 可能影響點擊事件

## 解決方案

### 1. 提高 SelectContent 的 z-index

**檔案**: `frontend/components/ui/select.tsx`

**修改前**:

```tsx
className={cn(
  'relative z-50 max-h-[--radix-select-content-available-height] min-w-[8rem] overflow-y-auto overflow-x-hidden ...',
  // ...
)}
```

**修改後**:

```tsx
className={cn(
  'relative z-[100] max-h-96 min-w-[8rem] overflow-hidden ...',
  // ...
)}
```

**改進**:

- z-index 從 50 提升到 100，確保在最上層
- 使用固定的 `max-h-96` 取代 CSS 變數
- 改用 `overflow-hidden`，讓 Viewport 處理滾動

### 2. 調整 Viewport 的滾動處理

**修改前**:

```tsx
<SelectPrimitive.Viewport
  className={cn(
    'p-1',
    position === 'popper' &&
      'h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]'
  )}
>
```

**修改後**:

```tsx
<SelectPrimitive.Viewport
  className={cn(
    'p-1 max-h-[var(--radix-select-content-available-height)]',
    position === 'popper' &&
      'h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]'
  )}
>
```

**改進**:

- 在 Viewport 上添加 max-h 限制
- 讓 Viewport 處理內容滾動

### 3. 簡化 SelectItem 內容結構

**檔案**: `frontend/features/articles/components/SortingControls.tsx`

**修改前**:

```tsx
<SelectItem key={option.value} value={option.value}>
  <div className="flex items-center gap-2">
    <Icon className="h-4 w-4" />
    <div className="flex flex-col">
      <span>{option.label}</span>
      <span className="text-xs text-muted-foreground">{option.description}</span>
    </div>
  </div>
</SelectItem>
```

**修改後**:

```tsx
<SelectItem key={option.value} value={option.value}>
  <div className="flex items-center gap-2">
    <Icon className="h-4 w-4" />
    <span>{option.label}</span>
  </div>
</SelectItem>
```

**改進**:

- 移除多餘的 flex-col 層級
- 移除描述文字，保持選項簡潔
- 減少 DOM 層級，提高點擊響應

## 測試驗證

### 測試項目

- [x] Select 可以正常打開
- [x] 選項可以正常點擊
- [x] 選中的選項會正確顯示
- [x] z-index 足夠高，不會被其他元素覆蓋
- [x] 在不同螢幕尺寸下都能正常工作
- [ ] 鍵盤導航（上下箭頭、Enter）正常
- [ ] 螢幕閱讀器可以正確讀取

### 測試場景

1. **文章瀏覽頁面** - 排序控制的兩個 Select
2. **其他使用 Select 的頁面** - 確保修改不影響其他功能

## 相關檔案

- `frontend/components/ui/select.tsx` - Select UI 組件
- `frontend/features/articles/components/SortingControls.tsx` - 排序控制組件
- `frontend/app/dashboard/articles/components/SortSelector.tsx` - 另一個排序選擇器

## 後續改進建議

1. **添加 tooltip** - 如果需要顯示描述，可以使用 tooltip 而不是在選項內顯示
2. **鍵盤導航測試** - 確保鍵盤使用者也能正常操作
3. **無障礙測試** - 使用螢幕閱讀器測試
4. **統一 Select 樣式** - 確保所有 Select 組件使用一致的樣式

## 注意事項

- 這個修改會影響所有使用 Select 組件的地方
- 如果其他地方的 Select 也有問題，應該會一併修復
- 建議在不同瀏覽器測試（Chrome, Firefox, Safari）
