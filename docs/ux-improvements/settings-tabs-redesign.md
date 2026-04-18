# Settings Tabs 重新設計

## 問題

### 1. 404 錯誤

- 外觀、帳戶、偏好設定頁面不存在
- 點擊後出現 404 錯誤

### 2. 響應式設計問題

- 側邊欄在窄螢幕上會移到頂部
- 佔用太多垂直空間
- 描述文字在小螢幕上顯得冗餘

## 解決方案

### 1. 改用 Tabs 設計

**改進前（側邊欄）**:

```
┌─────────────────────────────────┐
│ 設定                            │
├──────────┬──────────────────────┤
│ 📱 通知  │                      │
│ 管理通知 │                      │
│          │                      │
│ 🎨 外觀  │     內容區域         │
│ 主題設定 │                      │
│          │                      │
│ 👤 帳戶  │                      │
│ 個人資料 │                      │
└──────────┴──────────────────────┘
```

**改進後（Tabs）**:

```
┌─────────────────────────────────┐
│ 設定                            │
├─────────────────────────────────┤
│ 📱通知  🎨外觀  👤帳戶  ⚙️偏好  │
│ ═════                           │
├─────────────────────────────────┤
│                                 │
│         內容區域                │
│                                 │
└─────────────────────────────────┘
```

### 2. 創建佔位頁面

為所有設定項目創建頁面，避免 404：

- ✅ `/app/settings/notifications` - 通知設定（已完成）
- ✅ `/app/settings/appearance` - 外觀設定（佔位）
- ✅ `/app/settings/account` - 帳戶設定（佔位）
- ✅ `/app/settings/preferences` - 偏好設定（佔位）

## 修改的檔案

### 1. Settings Layout (`frontend/app/app/settings/layout.tsx`)

**主要改進**:

- ✅ 改用水平 tabs 設計
- ✅ 移除描述文字（更簡潔）
- ✅ 添加 `overflow-x-auto`（支援水平滾動）
- ✅ 使用 border-bottom 高亮當前 tab
- ✅ 更好的響應式設計

**關鍵 CSS**:

```tsx
<nav className="flex space-x-8 overflow-x-auto">
  <Link
    className={cn(
      'flex items-center gap-2 px-1 py-4 border-b-2',
      isActive ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground'
    )}
  >
    <Icon className="h-4 w-4" />
    {item.title}
  </Link>
</nav>
```

### 2. 新增頁面

#### Appearance Page (`frontend/app/app/settings/appearance/page.tsx`)

```tsx
export default function AppearancePage() {
  return (
    <Card>
      <CardContent>
        <div className="text-center py-12">
          <Palette className="h-12 w-12 mx-auto mb-4" />
          <p>即將推出</p>
          <p>深色模式、語言選擇和其他外觀設定功能正在開發中</p>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### Account Page (`frontend/app/app/settings/account/page.tsx`)

```tsx
export default function AccountPage() {
  return (
    <Card>
      <CardContent>
        <div className="text-center py-12">
          <User className="h-12 w-12 mx-auto mb-4" />
          <p>即將推出</p>
          <p>個人資料編輯、密碼變更和帳戶安全功能正在開發中</p>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### Preferences Page (`frontend/app/app/settings/preferences/page.tsx`)

```tsx
export default function PreferencesPage() {
  return (
    <Card>
      <CardContent>
        <div className="text-center py-12">
          <Settings className="h-12 w-12 mx-auto mb-4" />
          <p>即將推出</p>
          <p>預設排序方式、每頁顯示數量和其他偏好設定功能正在開發中</p>
        </div>
      </CardContent>
    </Card>
  );
}
```

## 設計優點

### Tabs vs Sidebar

| 特性       | Sidebar               | Tabs        |
| ---------- | --------------------- | ----------- |
| 垂直空間   | ❌ 佔用較多           | ✅ 節省空間 |
| 水平空間   | ✅ 固定寬度           | ✅ 自適應   |
| 小螢幕     | ❌ 移到頂部，佔用空間 | ✅ 水平滾動 |
| 視覺清晰度 | ⚠️ 需要描述文字       | ✅ 簡潔明瞭 |
| 常見模式   | ⚠️ 較少見             | ✅ 廣泛使用 |

### 響應式行為

**桌面版 (>1024px)**:

```
┌─────────────────────────────────────────┐
│ 設定                                    │
├─────────────────────────────────────────┤
│ 📱通知    🎨外觀    👤帳戶    ⚙️偏好    │
│ ═════                                   │
├─────────────────────────────────────────┤
│                                         │
│              內容區域                   │
│                                         │
└─────────────────────────────────────────┘
```

**平板/手機版 (<1024px)**:

```
┌──────────────────────┐
│ 設定                 │
├──────────────────────┤
│ 📱通知  🎨外觀  👤帳戶│→
│ ═════               │
├──────────────────────┤
│                      │
│     內容區域         │
│                      │
└──────────────────────┘
```

_可以水平滾動查看更多 tabs_

## 使用者體驗改進

### 改進前

- ❌ 點擊外觀/帳戶/偏好出現 404
- ❌ 側邊欄在小螢幕佔用太多空間
- ❌ 描述文字造成視覺混亂
- ❌ 不符合常見的設定頁面模式

### 改進後

- ✅ 所有 tabs 都有對應頁面
- ✅ Tabs 設計節省垂直空間
- ✅ 簡潔的 icon + 文字
- ✅ 符合使用者習慣（如 GitHub, Gmail 設定頁）
- ✅ 更好的響應式體驗

## 未來擴展

### Appearance 頁面功能

- [ ] 主題切換（淺色/深色/自動）
- [ ] 字體大小調整
- [ ] 語言選擇
- [ ] 色彩主題自訂

### Account 頁面功能

- [ ] 個人資料編輯
- [ ] 頭像上傳
- [ ] 密碼變更
- [ ] 兩步驟驗證
- [ ] 帳戶刪除

### Preferences 頁面功能

- [ ] 預設排序方式
- [ ] 每頁顯示數量
- [ ] 預設篩選條件
- [ ] 鍵盤快捷鍵設定

## 參考設計

類似的 tabs 設計可以在以下網站看到：

- GitHub Settings
- Gmail Settings
- Twitter Settings
- Discord User Settings

## 總結

- ✅ 改用 tabs 設計，更符合使用者習慣
- ✅ 創建佔位頁面，避免 404
- ✅ 更好的響應式設計
- ✅ 節省垂直空間
- ✅ 視覺更簡潔清晰
