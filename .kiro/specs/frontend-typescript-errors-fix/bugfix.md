# Bugfix Requirements Document

## Introduction

本文件描述前端專案中三個 TypeScript 型別錯誤和不一致問題的修復需求。這些問題導致執行 `npm run type-check` 時出現 30+ 個編譯錯誤，影響型別安全性和開發體驗。

**影響範圍：**

- FeedCard 元件在執行時可能存取到 undefined 屬性
- 所有測試檔案的 Jest DOM matchers 缺少型別定義
- 元件間匯入路徑不一致，造成維護困難

**環境：**

- Frontend: Next.js 14.2.0, TypeScript 5
- Testing: Jest 30.3.0, @testing-library/react 16.3.2
- 專案路徑: frontend/

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN FeedCard 元件使用 `feed.isSubscribed` (camelCase) 存取屬性 THEN 執行時會得到 undefined，因為 Feed 型別定義的是 `is_subscribed` (snake_case)

1.2 WHEN 測試檔案使用 `toBeInTheDocument()`, `toHaveClass()`, `toHaveAttribute()` 等 Jest DOM matchers THEN TypeScript 編譯器報錯找不到這些方法的型別定義

1.3 WHEN Navigation.tsx 從 `@/lib/hooks/useAuth` 匯入 useAuth，而其他元件從 `@/contexts/AuthContext` 匯入 THEN 造成匯入路徑不一致，增加維護成本和混淆

### Expected Behavior (Correct)

2.1 WHEN FeedCard 元件存取訂閱狀態 THEN 系統 SHALL 使用與 Feed 型別定義一致的屬性名稱 `is_subscribed`，確保執行時正確存取

2.2 WHEN 測試檔案使用 Jest DOM matchers THEN 系統 SHALL 正確識別這些方法的型別定義，TypeScript 編譯不應出現錯誤

2.3 WHEN 任何元件需要使用 useAuth hook THEN 系統 SHALL 統一從 `@/lib/hooks/useAuth` 匯入，保持一致的匯入模式

### Unchanged Behavior (Regression Prevention)

3.1 WHEN FeedCard 元件渲染訂閱狀態的 UI (Switch 元件) THEN 系統 SHALL CONTINUE TO 正確顯示和切換訂閱狀態

3.2 WHEN 測試執行時 THEN 系統 SHALL CONTINUE TO 正確執行所有測試案例，包括 Jest DOM matchers 的斷言

3.3 WHEN useAuth hook 被呼叫 THEN 系統 SHALL CONTINUE TO 返回相同的認證狀態和方法 (isAuthenticated, user, logout, login, checkAuth)

3.4 WHEN 元件使用 Feed 型別的其他屬性 (id, name, url, category) THEN 系統 SHALL CONTINUE TO 正確存取這些屬性

3.5 WHEN AuthProvider 提供認證上下文 THEN 系統 SHALL CONTINUE TO 正確管理全域認證狀態
