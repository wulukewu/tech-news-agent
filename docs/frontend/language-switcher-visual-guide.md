# Language Switcher Visual Guide

## 視覺效果預覽

### 桌面版 - Icon Variant

```
┌─────────────────────────────────────────────────────────┐
│  Logo    Articles  Reading List  Subscriptions    🌐 ☀️ 👤│
└─────────────────────────────────────────────────────────┘
                                                      ↓
                                              ┌──────────────┐
                                              │ 繁體中文   ✓ │
                                              │ English      │
                                              └──────────────┘
```

**特點**:

- 地球圖示 🌐 在右上角
- 點擊後彈出下拉選單
- 當前語言顯示勾選標記
- 與主題切換和用戶選單並排

### 手機版 - Compact Variant (抽屜選單)

```
┌──────────────────┐
│ 👤 Username    ✕ │
├──────────────────┤
│ 🏠 Articles      │
│ 📚 Reading List  │
│ 📡 Subscriptions │
│ ⚙️  Settings     │
├──────────────────┤
│ Language  繁 / EN│  ← Compact variant
│ Theme     ☀️ / 🌙│
├──────────────────┤
│ 🚪 Logout        │
└──────────────────┘
```

**特點**:

- 顯示 "繁 / EN" 文字
- 當前語言高亮
- 直接點擊切換
- 與主題切換一起放在底部

### Footer - Compact Variant

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  © 2026 Tech News Agent          繁 / EN  Built with... │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**特點**:

- 放在 Footer 底部欄
- 所有裝置都可見
- 不干擾主要內容

## 互動狀態

### Icon Variant 狀態

#### 1. 預設狀態

```
┌────┐
│ 🌐 │  ← 地球圖示，灰色
└────┘
```

#### 2. Hover 狀態

```
┌────┐
│ 🌐 │  ← 背景變淺，圖示變深
└────┘
```

#### 3. 開啟狀態

```
┌────┐
│ 🌐 │
└────┘
  ↓
┌──────────────┐
│ 繁體中文   ✓ │  ← 當前語言
│ English      │  ← 可選語言
└──────────────┘
```

#### 4. 選單項目 Hover

```
┌──────────────┐
│ 繁體中文   ✓ │
│ English      │  ← 背景高亮
└──────────────┘
```

### Compact Variant 狀態

#### 1. 預設狀態（英文）

```
繁  /  EN
↑      ↑
灰色   深色（當前）
```

#### 2. 預設狀態（中文）

```
繁  /  EN
↑      ↑
深色   灰色
（當前）
```

#### 3. Hover 狀態

```
繁  /  EN
↑
變深（hover）
```

## 顏色方案

### 淺色模式

- **背景**: `bg-background` (白色)
- **文字**: `text-foreground` (深灰)
- **次要文字**: `text-muted-foreground` (中灰)
- **Hover**: `hover:bg-accent` (淺灰)
- **當前語言**: `bg-accent` (淺灰) + `text-foreground` (深灰)
- **焦點環**: `focus:ring-primary` (藍色)

### 深色模式

- **背景**: `bg-background` (深灰)
- **文字**: `text-foreground` (淺灰)
- **次要文字**: `text-muted-foreground` (中灰)
- **Hover**: `hover:bg-accent` (深灰)
- **當前語言**: `bg-accent` (深灰) + `text-foreground` (淺灰)
- **焦點環**: `focus:ring-primary` (藍色)

## 尺寸規格

### Icon Variant

- **按鈕**: 40x40px (`w-10 h-10`)
- **圖示**: 20x20px (`w-5 h-5`)
- **下拉選單**: 192px 寬 (`w-48`)
- **選單項目**: 最小 44px 高 (`min-h-[44px]`)

### Compact Variant

- **按鈕**: 最小 44x44px (`min-w-[44px] min-h-[44px]`)
- **文字**: 14px (`text-sm`)
- **間距**: 8px (`gap-2`)

## 動畫效果

### 下拉選單動畫

```
開啟: fade-in + slide-in-from-top-2
持續時間: 200ms
緩動: ease-out
```

### 顏色過渡

```
屬性: color, background-color
持續時間: 200ms
緩動: ease-in-out
```

## 響應式斷點

### 桌面版 (≥768px)

- 導航列顯示 Icon variant
- Footer 顯示 Compact variant

### 手機版 (<768px)

- 導航列隱藏語言切換（在漢堡選單內）
- 抽屜選單顯示 Compact variant
- Footer 顯示 Compact variant

## 無障礙特性

### 鍵盤導航

```
Tab       → 移動焦點到語言切換器
Enter     → 開啟下拉選單 / 切換語言
Space     → 開啟下拉選單 / 切換語言
Escape    → 關閉下拉選單
Tab       → 在選單項目間移動
```

### 螢幕閱讀器

```
按鈕: "Language selector"
選項: "Switch to Traditional Chinese"
選項: "Switch to English"
狀態: aria-pressed="true" (當前語言)
宣告: "Language changed to [語言]"
```

### 焦點指示器

```
外框: 2px solid
顏色: ring-primary (藍色)
偏移: 2px
對比度: 3:1 (符合 WCAG AA)
```

## 實際使用場景

### 場景 1: 首次訪問

1. 系統偵測瀏覽器語言
2. 自動載入對應翻譯
3. 語言切換器顯示當前語言

### 場景 2: 切換語言

1. 使用者點擊語言切換器
2. 選擇想要的語言
3. UI 在 200ms 內更新
4. 偏好設定儲存

### 場景 3: 再次訪問

1. 系統載入儲存的偏好
2. UI 顯示偏好語言
3. 語言切換器反映選擇

---

**提示**: 這個設計確保語言切換功能在不干擾主要使用流程的情況下，始終可訪問且易於使用。
