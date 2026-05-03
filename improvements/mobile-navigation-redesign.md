# 手機版導航重新設計

## 問題分析

### 原有設計的問題

1. **功能分散** - 主要導航在抽屜選單，次要功能在頭像下拉選單
2. **內容不足** - 抽屜選單只有 3 個主要選項，感覺空蕩蕩
3. **操作繁瑣** - 用戶需要點擊兩個不同的地方才能訪問所有功能
4. **不直觀** - 新用戶不知道頭像裡還有更多功能

### 用戶體驗問題

```
原有設計：
┌─────────────────────────────┐
│  [≡] Logo    🌐 🌙 👤      │ ← 頂部導航欄
└─────────────────────────────┘

點擊 [≡] 打開抽屜：
┌─────────────────────────────┐
│  👤 Username            [×] │
├─────────────────────────────┤
│  🏠 文章                    │ ← 只有 3 個選項
│  📚 閱讀清單                │   感覺很空
│  📡 訂閱                    │
│                             │
│  (大片空白)                 │
│                             │
├─────────────────────────────┤
│  語言: [中文 ▼]            │
│  主題: [深色 ▼]            │
│  [登出]                    │
└─────────────────────────────┘

點擊 👤 打開下拉選單：
┌──────────────────┐
│  Username        │
│  email@test.com  │
├──────────────────┤
│  👤 個人資料     │ ← 更多功能藏在這裡
│  📊 分析         │   用戶可能找不到
│  ⚙️  設定        │
│  🔔 通知         │
│  📈 系統狀態     │
├──────────────────┤
│  🚪 登出         │
└──────────────────┘
```

## 新設計方案

### 設計理念

1. **一站式導航** - 所有功能集中在一個抽屜選單
2. **清晰分組** - 主要功能和次要功能分開顯示
3. **內容豐富** - 抽屜選單包含所有導航選項
4. **易於發現** - 用戶一眼就能看到所有可用功能

### 新的抽屜式選單設計

```
點擊 [≡] 打開抽屜：
┌─────────────────────────────┐
│  👤 Username            [×] │ ← 用戶資訊（含 email）
│  email@test.com             │
├─────────────────────────────┤
│  主選單                     │ ← 分組標題
│                             │
│  🏠 文章                    │ ← 主要功能
│  📚 閱讀清單                │   (3 個核心功能)
│  📡 訂閱                    │
│                             │
├─────────────────────────────┤
│  更多功能                   │ ← 分組標題
│                             │
│  ❤️  推薦                   │ ← 次要功能
│  📊 分析                    │   (4 個進階功能)
│  ⚙️  設定                   │
│  📈 系統狀態                │
│                             │
├─────────────────────────────┤
│  語言: [中文 ▼]            │ ← 設定區域
│  主題: [深色 ▼]            │
│  [登出]                    │
└─────────────────────────────┘
```

## 實作細節

### 1. 整合所有導航項目

```tsx
{/* Main navigation section */}
<div className="px-2 py-2">
  <p className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
    {t('nav.main-menu')}
  </p>
  <div className="space-y-1">
    {translatedMainNavItems.map((item) => (
      // 主要導航項目
    ))}
  </div>
</div>

{/* Divider */}
<div className="my-2 border-t" />

{/* Secondary navigation section */}
<div className="px-2 py-2">
  <p className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
    {t('nav.more')}
  </p>
  <div className="space-y-1">
    {translatedSecondaryNavItems.map((item) => (
      // 次要導航項目
    ))}
  </div>
</div>
```

### 2. 改進的用戶資訊顯示

```tsx
{
  /* User profile section at top */
}
{
  user && (
    <div className="flex items-center gap-3 p-4 border-b flex-shrink-0">
      <Avatar className="h-10 w-10">
        {user.avatar && <AvatarImage src={user.avatar} alt={user.username || 'User'} />}
        <AvatarFallback>{user.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{user.username}</p>
        {user.email && <p className="text-xs text-muted-foreground truncate">{user.email}</p>}
      </div>
      <Button variant="ghost" size="sm" onClick={closeDrawer}>
        <X className="h-5 w-5" />
      </Button>
    </div>
  );
}
```

### 3. 視覺改進

- **分組標題** - 使用小寫字母、灰色、粗體、大寫樣式
- **圓角按鈕** - 導航項目使用 `rounded-lg` 而非直角
- **更好的間距** - 使用 `py-2` 和 `space-y-1` 提供適當間距
- **清晰的分隔線** - 使用 `border-t` 分隔不同區域

## 優勢對比

| 特性       | 原有設計              | 新設計              |
| ---------- | --------------------- | ------------------- |
| 功能集中度 | ❌ 分散在兩個地方     | ✅ 集中在一個抽屜   |
| 內容豐富度 | ❌ 抽屜只有 3 個選項  | ✅ 抽屜有 7 個選項  |
| 易於發現   | ❌ 次要功能藏在頭像下 | ✅ 所有功能一目了然 |
| 操作步驟   | ❌ 需要點擊不同位置   | ✅ 一次點擊訪問所有 |
| 視覺層次   | ❌ 沒有明確分組       | ✅ 清晰的分組標題   |
| 用戶資訊   | ❌ 只顯示用戶名       | ✅ 顯示用戶名和郵箱 |

## 桌面版保持不變

桌面版仍然使用：

- 頂部導航欄顯示主要功能（文章、閱讀清單、訂閱）
- UserMenu 下拉選單顯示次要功能（推薦、分析、設定、系統狀態）

這樣可以充分利用桌面版的寬螢幕空間。

## 翻譯支援

新增翻譯鍵：

- `nav.main-menu` - "主選單" / "Main Menu"
- `nav.more` - "更多功能" / "More"

## 測試建議

### 功能測試

- ✅ 所有 7 個導航項目都可點擊
- ✅ 點擊後正確導航並關閉抽屜
- ✅ 分組標題正確顯示
- ✅ 用戶資訊完整顯示

### 視覺測試

- ✅ 分組標題樣式正確（小字、灰色、粗體、大寫）
- ✅ 導航項目有圓角
- ✅ 間距適當，不擁擠
- ✅ 分隔線清晰可見

### 響應式測試

- ✅ iPhone SE (375px)
- ✅ iPhone 12/13/14 (390px)
- ✅ Android 小螢幕 (360px)

## 相關檔案

- [Navigation 元件](../../frontend/components/Navigation.tsx)
- [中文翻譯](../../frontend/locales/zh-TW.json)
- [英文翻譯](../../frontend/locales/en-US.json)

## 日期

2026-04-19
