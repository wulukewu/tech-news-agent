# Frontend TypeScript Errors Fix - Bugfix Design

## Overview

本設計文件描述修復前端專案中三個 TypeScript 型別錯誤的方法。這些錯誤導致執行 `npm run type-check` 時出現 30+ 個編譯錯誤，影響型別安全性和開發體驗。修復策略採用最小化變更原則，確保現有功能不受影響。

三個主要問題：

1. **FeedCard 屬性命名不一致**：元件使用 `feed.isSubscribed` (camelCase)，但型別定義為 `is_subscribed` (snake_case)
2. **Jest DOM 型別定義缺失**：測試檔案使用 Jest DOM matchers 但 TypeScript 找不到型別定義
3. **useAuth 匯入路徑不一致**：Navigation.tsx 已使用正確路徑 `@/lib/hooks/useAuth`，無需修改

修復方法：

- 修改 FeedCard.tsx 中的兩處屬性存取，從 `feed.isSubscribed` 改為 `feed.is_subscribed`
- 建立 `frontend/types/jest-dom.d.ts` 型別定義檔案，匯入 `@testing-library/jest-dom` 型別
- useAuth 匯入路徑已統一，無需修改

## Glossary

- **Bug_Condition (C)**: 觸發錯誤的條件 - TypeScript 編譯器無法找到正確的型別定義或屬性
- **Property (P)**: 期望的行為 - TypeScript 編譯通過，所有型別檢查正確
- **Preservation**: 必須保持不變的現有行為 - 執行時功能、測試結果、UI 顯示
- **FeedCard**: 位於 `frontend/components/FeedCard.tsx` 的元件，顯示 RSS feed 資訊和訂閱狀態
- **Feed.is_subscribed**: Feed 型別中的布林屬性，表示使用者是否訂閱該 feed（使用 snake_case 命名）
- **Jest DOM matchers**: @testing-library/jest-dom 提供的自訂 Jest matchers，如 `toBeInTheDocument()`, `toHaveClass()`, `toHaveAttribute()`
- **useAuth hook**: 位於 `frontend/lib/hooks/useAuth.ts`，re-export 自 `frontend/contexts/AuthContext.tsx` 的認證 hook

## Bug Details

### Bug Condition

錯誤在以下三種情況下發生：

1. **FeedCard 屬性存取錯誤**：當 TypeScript 編譯器檢查 FeedCard.tsx 時，發現元件存取 `feed.isSubscribed` 屬性，但 Feed 型別定義中只有 `is_subscribed` 屬性
2. **Jest DOM 型別缺失**：當 TypeScript 編譯器檢查測試檔案時，發現使用了 `toBeInTheDocument()` 等 matchers，但在 Jest 的 `expect` 型別定義中找不到這些方法
3. **useAuth 匯入路徑**：Navigation.tsx 已經使用正確路徑 `@/lib/hooks/useAuth`，此問題已解決

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type { file: string, code: string }
  OUTPUT: boolean

  RETURN (
    // Bug 1: FeedCard property mismatch
    (input.file == "frontend/components/FeedCard.tsx"
     AND input.code CONTAINS "feed.isSubscribed"
     AND Feed.type DEFINES "is_subscribed"
     AND Feed.type NOT DEFINES "isSubscribed")

    OR

    // Bug 2: Jest DOM types missing
    (input.file MATCHES "**/*.test.tsx"
     AND input.code CONTAINS ("toBeInTheDocument" OR "toHaveClass" OR "toHaveAttribute")
     AND TypeScript CANNOT RESOLVE these methods on expect().not)

    OR

    // Bug 3: useAuth import inconsistency (ALREADY FIXED)
    (input.file == "frontend/components/Navigation.tsx"
     AND input.code IMPORTS useAuth FROM "@/lib/hooks/useAuth"
     AND this is CORRECT)
  )
END FUNCTION
```

### Examples

**Bug 1 - FeedCard Property Mismatch:**

- **Current (Incorrect)**: `feed.isSubscribed` 在 FeedCard.tsx 第 30 行和第 46 行
- **Expected**: `feed.is_subscribed` 與 Feed 型別定義一致
- **Runtime Impact**: 執行時 `feed.isSubscribed` 返回 `undefined`，導致 Switch 元件狀態錯誤

**Bug 2 - Jest DOM Type Definitions:**

- **Current (Incorrect)**: TypeScript 報錯 "Property 'toBeInTheDocument' does not exist on type 'JestMatchers<HTMLElement>'"
- **Expected**: TypeScript 識別 Jest DOM matchers 的型別定義
- **Files Affected**:
  - `frontend/components/__tests__/ArticleCard.test.tsx` (11 處使用)
  - `frontend/components/__tests__/Navigation.test.tsx` (7 處使用)
  - `frontend/components/__tests__/FeedCard.test.tsx` (5 處使用)

**Bug 3 - useAuth Import Path:**

- **Current (Correct)**: Navigation.tsx 已使用 `import { useAuth } from '@/lib/hooks/useAuth'`
- **Status**: 此問題已解決，無需修改

**Edge Cases:**

- Feed 型別的其他屬性 (id, name, url, category) 使用 snake_case，應保持一致
- jest.setup.js 已經有 `require('@testing-library/jest-dom')`，但 TypeScript 需要額外的型別定義檔案
- useAuth hook 在 `lib/hooks/useAuth.ts` 中 re-export，確保匯入路徑統一

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- FeedCard 元件的 UI 顯示和互動行為必須完全相同（Switch 切換、hover 效果、卡片樣式）
- 所有測試案例必須繼續通過，測試邏輯和斷言不變
- useAuth hook 返回的認證狀態和方法 (isAuthenticated, user, logout, login, checkAuth) 必須相同
- Feed 型別的其他屬性存取 (id, name, url, category) 必須正常運作
- AuthProvider 的全域認證狀態管理必須不受影響

**Scope:**
所有不涉及以下三個特定修改的程式碼應完全不受影響：

- FeedCard.tsx 中 `feed.isSubscribed` 的兩處存取
- TypeScript 編譯器對 Jest DOM matchers 的型別檢查
- Navigation.tsx 的 useAuth 匯入（已正確，無需修改）

這包括：

- 所有其他元件的功能和樣式
- API 呼叫和資料流
- 路由和導航邏輯
- 其他測試檔案的執行
- 認證流程和狀態管理

## Hypothesized Root Cause

基於錯誤分析，最可能的原因是：

1. **FeedCard Property Mismatch - 命名慣例不一致**
   - Backend API 使用 Python/FastAPI，慣例使用 snake_case
   - Frontend TypeScript 型別定義正確反映 API 回應格式 (is_subscribed)
   - 但 FeedCard 元件開發時誤用了 JavaScript/TypeScript 慣例的 camelCase
   - 這是典型的跨語言專案命名慣例衝突

2. **Jest DOM Types Missing - TypeScript 設定不完整**
   - jest.setup.js 正確匯入了 `@testing-library/jest-dom` 的執行時程式碼
   - 但 TypeScript 編譯器需要額外的型別定義檔案 (.d.ts) 來擴展 Jest matchers
   - @testing-library/jest-dom 套件提供型別定義，但需要明確匯入到 TypeScript 專案中
   - 缺少 `frontend/types/jest-dom.d.ts` 或 tsconfig.json 中的型別參考

3. **useAuth Import Path - 已解決**
   - Navigation.tsx 已經使用正確的匯入路徑 `@/lib/hooks/useAuth`
   - `lib/hooks/useAuth.ts` 正確 re-export 了 AuthContext 的 useAuth
   - 此問題在需求文件中提到，但實際程式碼已經正確
   - 無需修改，僅需在設計文件中確認

4. **TypeScript Path Aliases 配置正確**
   - `@/` alias 正確指向 frontend/ 目錄
   - 所有匯入路徑都能正確解析
   - 不是路徑解析問題，而是型別定義問題

## Correctness Properties

Property 1: Bug Condition - TypeScript Compilation Success

_For any_ TypeScript 檔案在專案中，當執行 `npm run type-check` 時，修復後的程式碼 SHALL 通過所有型別檢查，不產生任何編譯錯誤，特別是：

- FeedCard.tsx 中的 `feed.is_subscribed` 屬性存取應被識別為有效
- 測試檔案中的 Jest DOM matchers 應被識別為有效的 expect 方法
- Navigation.tsx 的 useAuth 匯入應被識別為有效（已正確）

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Runtime Behavior and Test Results

_For any_ 使用者互動、測試執行、或元件渲染，修復後的程式碼 SHALL 產生與原始程式碼完全相同的執行時行為，保持：

- FeedCard 元件的訂閱狀態顯示和切換功能
- 所有測試案例的通過狀態和斷言結果
- useAuth hook 的認證狀態和方法回傳值
- Feed 型別其他屬性的正確存取

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

假設我們的根本原因分析正確：

**File 1**: `frontend/components/FeedCard.tsx`

**Function**: FeedCard component

**Specific Changes**:

1. **Line 30 - Switch checked prop**: 將 `checked={feed.isSubscribed}` 改為 `checked={feed.is_subscribed}`
   - 確保 Switch 元件正確顯示訂閱狀態
   - 使用與 Feed 型別定義一致的屬性名稱

2. **Line 46 - Conditional styling**: 將 `feed.isSubscribed && 'border-primary'` 改為 `feed.is_subscribed && 'border-primary'`
   - 確保已訂閱的 feed 卡片顯示正確的邊框樣式
   - 保持視覺回饋的一致性

**File 2**: `frontend/types/jest-dom.d.ts` (新建檔案)

**Purpose**: 擴展 Jest matchers 型別定義以包含 Jest DOM matchers

**Specific Changes**:

1. **建立型別定義檔案**: 新建 `frontend/types/jest-dom.d.ts`
   - 匯入 `@testing-library/jest-dom` 的型別定義
   - 使用 triple-slash directive 或 import 語法
   - 確保 TypeScript 編譯器能識別 Jest DOM matchers

2. **內容**:
   ```typescript
   import '@testing-library/jest-dom';
   ```

   - 這會自動擴展 Jest 的 `expect` 型別，加入所有 Jest DOM matchers
   - 不需要額外的型別宣告或 namespace 擴展

**File 3**: `frontend/components/Navigation.tsx`

**Status**: 無需修改

**Reason**:

- Navigation.tsx 已經使用正確的匯入路徑 `import { useAuth } from '@/lib/hooks/useAuth'`
- `lib/hooks/useAuth.ts` 正確 re-export 了 AuthContext 的 useAuth
- 此檔案符合專案的匯入慣例，無需變更

## Testing Strategy

### Validation Approach

測試策略採用兩階段方法：首先在未修復的程式碼上執行 TypeScript 編譯和測試，觀察錯誤；然後在修復後驗證編譯通過且所有測試繼續通過，確保功能不變。

### Exploratory Bug Condition Checking

**Goal**: 在實作修復前，先在未修復的程式碼上執行 TypeScript 編譯，確認錯誤訊息並理解根本原因。如果錯誤訊息與假設不符，需要重新分析。

**Test Plan**: 執行 `npm run type-check` 在未修復的程式碼上，觀察 TypeScript 編譯錯誤。記錄所有錯誤訊息、檔案位置、和錯誤類型。

**Test Cases**:

1. **FeedCard Property Error**: 執行 type-check，應看到 "Property 'isSubscribed' does not exist on type 'Feed'" 錯誤在 FeedCard.tsx (will fail on unfixed code)
2. **Jest DOM Type Error**: 執行 type-check，應看到 "Property 'toBeInTheDocument' does not exist on type 'JestMatchers<HTMLElement>'" 錯誤在測試檔案 (will fail on unfixed code)
3. **useAuth Import Check**: 執行 type-check，Navigation.tsx 的 useAuth 匯入應該沒有錯誤 (will pass on unfixed code - already correct)
4. **Runtime Behavior**: 執行 `npm test`，所有測試應該通過（執行時行為正確，只是型別檢查失敗） (may pass on unfixed code)

**Expected Counterexamples**:

- TypeScript 編譯器報告 30+ 個型別錯誤
- 主要錯誤來源：FeedCard.tsx (2 處) 和測試檔案 (23+ 處 Jest DOM matchers)
- Possible causes: 屬性命名不一致、型別定義檔案缺失、匯入路徑問題

### Fix Checking

**Goal**: 驗證對於所有觸發 bug condition 的輸入，修復後的程式碼產生期望的行為（TypeScript 編譯通過）。

**Pseudocode:**

```
FOR ALL file WHERE isBugCondition(file) DO
  result := typeCheck_fixed(file)
  ASSERT result.errors.length == 0
  ASSERT result.compilationSuccess == true
END FOR
```

**Test Cases**:

1. **FeedCard Type Check**: 執行 `npm run type-check`，FeedCard.tsx 應該沒有型別錯誤
2. **Test Files Type Check**: 執行 `npm run type-check`，所有測試檔案應該沒有 Jest DOM matcher 型別錯誤
3. **Full Project Type Check**: 執行 `npm run type-check`，整個專案應該 0 個錯誤
4. **IDE Type Hints**: 在 VSCode 中開啟 FeedCard.tsx 和測試檔案，應該沒有紅色波浪線

### Preservation Checking

**Goal**: 驗證對於所有不觸發 bug condition 的輸入，修復後的程式碼產生與原始程式碼相同的結果（執行時行為不變）。

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT runtimeBehavior_original(input) = runtimeBehavior_fixed(input)
  ASSERT testResults_original(input) = testResults_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing 建議用於 preservation checking，因為：

- 自動產生多種測試案例，涵蓋輸入域
- 捕捉手動單元測試可能遺漏的邊界情況
- 提供強保證：對於所有非 buggy 輸入，行為不變

**Test Plan**: 先在未修復的程式碼上觀察執行時行為（測試通過、UI 正常），然後撰寫 property-based tests 捕捉該行為，確保修復後行為相同。

**Test Cases**:

1. **FeedCard Rendering Preservation**: 觀察未修復程式碼的 FeedCard 渲染（雖然型別錯誤，但執行時可能因為 undefined 而有問題），修復後應正確顯示訂閱狀態
2. **Test Execution Preservation**: 執行 `npm test`，所有測試應該繼續通過，測試結果數量和狀態相同
3. **Switch Toggle Preservation**: 手動測試或自動化測試 Switch 元件的切換功能，應該正常運作
4. **Feed Card Styling Preservation**: 驗證已訂閱和未訂閱的 feed 卡片樣式正確（border-primary 條件樣式）
5. **useAuth Hook Preservation**: 驗證 Navigation.tsx 中的 useAuth hook 返回正確的認證狀態

### Unit Tests

- 執行現有的 FeedCard.test.tsx，驗證所有測試案例通過
- 執行現有的 Navigation.test.tsx，驗證認證相關測試通過
- 執行現有的 ArticleCard.test.tsx，驗證 Jest DOM matchers 正常運作
- 手動測試 FeedCard 元件的訂閱切換功能
- 驗證 TypeScript 編譯通過，無任何錯誤或警告

### Property-Based Tests

- 產生隨機的 Feed 物件（不同的 is_subscribed 值），驗證 FeedCard 正確渲染
- 產生隨機的測試斷言組合，驗證 Jest DOM matchers 型別定義完整
- 測試多種認證狀態，驗證 useAuth hook 在不同場景下的行為一致
- 驗證 Feed 型別的所有屬性（id, name, url, category, is_subscribed）都能正確存取

### Integration Tests

- 執行完整的測試套件 `npm test`，確保所有測試通過
- 執行 TypeScript 編譯 `npm run type-check`，確保 0 個錯誤
- 在瀏覽器中手動測試 Subscriptions 頁面，驗證 FeedCard 的訂閱切換功能
- 測試 Navigation 元件的登出功能，驗證 useAuth hook 正常運作
- 驗證深色模式和淺色模式下的 FeedCard 樣式正確
